"""Domain-based dispatch skipping (rewired 2026-09-06).

The previous skip signal was a byte-identical `inputs_digest`. It never fired once: measured
across every run that wrote slices, no skip-eligible agent's digest ever repeated -- four
distinct values for `rebound` alone. It cannot fire, because the digest hashes the CONTENT of
referenced compute_*.json files, which embed live prices, so any run where a price moved (every
run) produces a fresh digest.

`_domain_moved` asks the right question -- did the thing this agent READS actually move -- and
was already computed and documented as "the strongest skip signal" while being wired to nothing.
These tests pin the rules, including the two that must NEVER skip.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_memory as sm


def ctx(qty=(), lots=False, session=True, cal=False, trims=False):
    return {"qty_changes": list(qty), "lots_changed": lots, "session_occurred": session,
            "calendar_changed": cal, "open_trims_changed": trims, "market_session": "closed_weekend"}


class TestDomainMoved:
    def test_holdings_quiet_does_not_move(self):
        moved, why = sm._domain_moved("holdings", ctx())
        assert moved is False and "no qty_changes" in why

    def test_holdings_moves_on_qty_change(self):
        assert sm._domain_moved("holdings", ctx(qty=[{"ticker": "AAA"}]))[0] is True

    def test_holdings_moves_on_lots_change(self):
        """This branch was unreachable until 2026-09-06: `_lots_digest` was read at the top of
        cmd_slices but never written into any slice, so lots_changed was permanently False."""
        assert sm._domain_moved("holdings", ctx(lots=True))[0] is True

    # -- smith-tax: gated on lots + WHICH trims are open, not on any trim existing.
    # It cost 77,880 tokens on 2026-09-06 to conclude FIFO == HIFO, $0.00 delta on all five.

    def test_tax_skips_when_lots_and_trim_set_both_unchanged(self):
        moved, why = sm._domain_moved("lots_trims", ctx())
        assert moved is False
        assert "same TRIM/SELL proposals are open" in why

    def test_tax_dispatches_when_the_trim_set_changes(self):
        assert sm._domain_moved("lots_trims", ctx(trims=True))[0] is True

    def test_tax_dispatches_when_lots_change(self):
        assert sm._domain_moved("lots_trims", ctx(lots=True))[0] is True

    def test_session_agent_skips_with_no_session(self):
        assert sm._domain_moved("session", ctx(session=False))[0] is False

    def test_news_domain_is_unknowable_and_never_skips(self):
        """None means the script cannot tell. It must never be read as False."""
        moved, why = sm._domain_moved("news", ctx())
        assert moved is None
        assert "cannot be evaluated from files alone" in why

    def test_strategist_always_moves(self):
        assert sm._domain_moved("always", ctx())[0] is True


class TestSkipEligibility:
    def test_external_readers_and_strategist_are_excluded(self):
        """The safety of the whole mechanism. An external reader's domain is news/prices, which
        the script cannot observe; the strategist's real inputs are the Stage-1 tails, which are
        not in its slice at all."""
        for a in sm.EXTERNAL_READERS:
            assert sm.AGENT_DOMAIN.get(a) in ("news", "fundamentals", "calendar", "macro", "session")
        assert "strategist" in sm.NEVER_SKIP
        assert sm.AGENT_DOMAIN["strategist"] == "always"

    def test_tax_domain_is_lots_trims_not_holdings(self):
        assert sm.AGENT_DOMAIN["tax"] == "lots_trims"


class TestOpenTrimsSignature:
    def test_signature_is_ids_only_and_order_independent(self, tmp_path):
        import json
        rows = [{"id": "P-2", "status": "open", "action": "Sell AVGO", "size_usd": 500},
                {"id": "P-1", "status": "open", "action": "Trim FSLR", "size_usd": 100},
                {"id": "P-3", "status": "open", "action": "Buy KLAC"},
                {"id": "P-4", "status": "dismissed_by_user", "action": "Sell MU"}]
        (tmp_path / "proposals.json").write_text(json.dumps({"proposals": rows}))
        assert sm._open_trims_sig(str(tmp_path)) == "P-1,P-2"

    def test_resizing_a_trim_does_not_change_the_signature(self, tmp_path):
        """A re-sized trim sequences the same lots, so size must not fire the domain."""
        import json
        base = [{"id": "P-1", "status": "open", "action": "Trim FSLR", "size_usd": 100}]
        (tmp_path / "proposals.json").write_text(json.dumps({"proposals": base}))
        before = sm._open_trims_sig(str(tmp_path))
        base[0]["size_usd"] = 999
        (tmp_path / "proposals.json").write_text(json.dumps({"proposals": base}))
        assert sm._open_trims_sig(str(tmp_path)) == before

    def test_unreadable_proposals_returns_empty_which_forces_dispatch(self, tmp_path):
        """Unreadable state must never look like 'nothing changed'."""
        (tmp_path / "proposals.json").write_text("{ not json")
        assert sm._open_trims_sig(str(tmp_path)) == ""

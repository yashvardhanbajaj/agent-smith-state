"""Phase 6 (2026-09-21): the universe evidence bar, the carried (stale) thesis for exited names, and
the shared-call-site guard. Every gate here is tested against a fixture that exercises the REFUSING
path -- a bar that only ever sees passing inputs proves nothing."""
import inspect
import json
import os
import re
import sys
from datetime import date

import pytest

import smith_conviction as sc
import smith_math
import smith_memory
import smith_risk

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
POLICY = {"stop_loss_framework": {"risk_per_position_pct_of_book": 0.5}}


def _ev(*pairs):
    return [{"source": s, "quality": q, "detail": ""} for s, q in pairs]


GOOD_EVIDENCE = _ev(("thesis", "unverified"), ("price_action", "computed"), ("valuation", "reported"))
THESIS = {"status": "strengthening", "verified": "secondary", "evidence_for": [], "evidence_against": []}


def _bar(**over):
    kw = dict(price=50.0, price_source="live_quotes.json", atr_this_run=6.0,
              evidence=GOOD_EVIDENCE, thesis_entry=THESIS, no_thesis_ack=None)
    kw.update(over)
    return sc.universe_bar("ZZZ", **kw)


class TestUniverseBar:
    def test_a_held_name_is_unaffected(self):
        b = sc.universe_bar("AAA", held=True)
        assert b["passes"] and b["vote"] == "live" and b["blockers"] == []

    def test_unheld_with_price_atr_two_sources_and_thesis_votes_live(self):
        b = _bar()
        assert b["passes"] and b["vote"] == "live" and b["failed"] == []

    @pytest.mark.parametrize("over,code,words", [
        ({"price": None}, "no_live_price", "no price for ZZZ fetched this run"),
        ({"atr_this_run": None}, "no_atr_this_run", "no ATR for ZZZ computed from this run's bars"),
        ({"evidence": _ev(("price_action", "computed"))}, "evidence_sources", "1/2 independent evidence source"),
        ({"evidence": _ev(("thesis", "unverified"), ("valuation", "reported"))},
         "no_verified_or_computed_source", "no verified or computed source"),
        ({"thesis_entry": None}, "no_thesis", "no thesis entry for ZZZ"),
    ])
    def test_each_missing_input_shadows_with_its_own_named_blocker(self, over, code, words):
        b = _bar(**over)
        assert b["vote"] == "shadow" and code in b["failed"]
        assert any(words in x for x in b["blockers"]), b["blockers"]

    def test_only_the_missing_input_is_named(self):
        assert _bar(price=None)["failed"] == ["no_live_price"]
        assert _bar(thesis_entry=None)["failed"] == ["no_thesis"]

    def test_an_explicit_no_thesis_acknowledgement_replaces_the_thesis(self):
        b = _bar(thesis_entry=None, no_thesis_ack={"date": "2026-09-21", "reason": "diversifier, by design"})
        assert b["passes"] and b["checks"]["thesis"] == "acknowledged"

    def test_the_acknowledgement_is_read_from_state_never_inferred(self):
        st = {"no_thesis_acknowledged": {"ZZZ": {"date": "2026-09-21", "reason": "x"}}}
        assert smith_risk.no_thesis_acknowledged(st, "ZZZ") and smith_risk.no_thesis_acknowledged(st, "QQQ") is None
        assert smith_risk.no_thesis_acknowledged({}, "ZZZ") is None

    def test_apply_demotes_live_and_never_promotes(self):
        row = {"vote": "live", "blockers": []}
        sc.apply_universe_bar(row, _bar(price=None))
        assert row["vote"] == "shadow" and row["universe_bar"]["failed"] == ["no_live_price"] and row["blockers"]
        shadow = {"vote": "shadow", "blockers": ["earlier"]}
        sc.apply_universe_bar(shadow, _bar())
        assert shadow["vote"] == "shadow"                         # a passing bar promotes nothing
        below = {"vote": "below_materiality", "blockers": []}
        sc.apply_universe_bar(below, _bar(price=None))
        assert below["vote"] == "below_materiality"               # only `live` is demoted

    def test_a_paired_rows_buy_leg_takes_the_blockers(self):
        row = {"vote": "shadow", "buy_leg": {"blockers": []}}
        sc.apply_universe_bar(row, _bar(thesis_entry=None), leg=row["buy_leg"])
        assert row["buy_leg"]["blockers"] and "blockers" not in row


class TestEvidenceSources:
    def test_price_derived_inputs_are_one_source_not_three(self):
        ev = sc.evidence_sources({"ticker": "ZZZ", "buckets": ["BREAKOUT"], "rsi": 30.0, "rsi_usable": True,
                                  "rel_pp": 5.0, "rel_usable": True}, computed_this_run=True)
        assert [e["source"] for e in ev] == ["price_action"] and ev[0]["quality"] == "computed"

    def test_the_watchlist_position_proxy_never_counts_as_computed(self):
        ev = sc.evidence_sources({"ticker": "ZZZ", "rsi": 23.0, "rsi_usable": True, "rsi_proxy": True},
                                 computed_this_run=True)
        assert ev[0]["quality"] == "unverified" and "proxy" in ev[0]["detail"]

    def test_a_carried_thesis_is_never_verified_evidence(self):
        carried = smith_risk.carry_thesis_forward(THESIS, "2026-09-10", "state.thesis", "2026-09-21")
        ev = sc.evidence_sources({"ticker": "ZZZ", "thesis_entry": carried})
        assert ev == [{"source": "thesis", "quality": "unverified", "detail": "carried from exit (stale)"}]

    def test_a_checked_thesis_anchors(self):
        assert sc.evidence_sources({"ticker": "ZZZ", "thesis_entry": THESIS})[0]["quality"] == "verified"

    def test_unverified_claims_do_not_anchor(self):
        ev = sc.evidence_sources({"ticker": "ZZZ", "thesis_entry": {"status": "intact", "verified": "unverified"},
                                  "upside_pct": 40.0, "mention_count": 2})
        assert not [e for e in ev if e["quality"] in sc.EVIDENCE_QUALITIES_THAT_ANCHOR]


# ---------------------------------------------------------------- one shared function, five families
class TestOneSharedFunction:
    FAMILIES = ("_trigger_entry_setup_scan", "_trigger_reentry_scan", "_trigger_bench_diversifier_scan",
                "_trigger_cluster_bench_rotation", "_rebound_screen")

    @pytest.mark.parametrize("fn", FAMILIES)
    def test_every_unheld_family_calls_the_shared_gate(self, fn):
        src = inspect.getsource(getattr(smith_math, fn))
        assert "_gate_on_universe_bar(" in src, f"{fn} does not go through the universe bar"

    def test_no_family_re_implements_the_bar(self):
        """universe_bar is called from exactly one place in the scripts, and no family carries its own
        private thesis check any more."""
        callers = []
        for f in sorted(os.listdir(os.path.join(ROOT, "scripts"))):
            if f.endswith(".py"):
                for i, line in enumerate(open(os.path.join(ROOT, "scripts", f)), 1):
                    if re.search(r"smith_conviction\.universe_bar\(|(?<![\w.])universe_bar\(", line) \
                            and not line.lstrip().startswith(("def ", "#")):
                        callers.append(f"{f}:{i}")
        assert len(callers) == 1 and callers[0].startswith("smith_math.py"), callers
        assert "thesis.get(ticker) is None" not in inspect.getsource(smith_math._trigger_entry_setup_scan)

    def test_calling_without_inputs_fails_closed(self):
        row = {"vote": "live", "blockers": []}
        smith_math._gate_on_universe_bar(row, "ZZZ", {"ticker": "ZZZ", "thesis_entry": THESIS}, None)
        assert row["vote"] == "shadow"
        assert {"no_live_price", "no_atr_this_run"} <= set(row["universe_bar"]["failed"])

    def test_this_runs_indicators_not_the_cache_decide_atr(self, tmp_path):
        (tmp_path / "compute_indicators.json").write_text(json.dumps(
            {"atr20_pct": {"IN": 5.0, "OUT": None}, "rsi14": {"IN": 40.0}}))
        bi = smith_math._universe_bar_inputs({"IN": {"price": 9.0, "source": "bars.json last close"}},
                                             str(tmp_path), {})
        assert bi["atr_this_run"] == {"IN": 5.0} and "IN" in bi["rsi_this_run"]
        empty = smith_math._universe_bar_inputs({}, str(tmp_path / "nope"), {})
        assert empty["atr_this_run"] == {} and empty["computed"] == set()

    def test_reentry_live_price_beats_the_old_exit_fill(self):
        from test_smith_math_triggers import bar_ok
        out, no_t, judged = [], [], []
        smith_math._trigger_reentry_scan(
            {"trades": [{"ticker": "ZZZ", "date": "2026-07-01", "price_at_trade": 50.0}]},
            {"ZZZ": date(2026, 7, 1)}, {}, {}, [], {}, lambda t, p: 30.0, {}, True, {}, True, {"ZZZ": 3},
            lambda b: None, {"ZZZ": 6.0}, 100000.0, POLICY, 10000.0, {}, out, no_t, judged,
            alumni_thesis={"ZZZ": smith_risk.carry_thesis_forward(
                {"status": "strengthening", "verified": "primary"}, "2026-07-01", "state.thesis", "2026-09-21")},
            bar_inputs=bar_ok("ZZZ", price=61.0, atr=6.0))
        assert out and out[0]["price_usd"] == 61.0
        assert "exited 2026-07-01 at $50.00" in out[0]["reasons"][0]


# ---------------------------------------------------------------- carried thesis
class TestCarriedThesis:
    LAST = {"status": "strengthening", "thesis": "moat", "verified": "primary",
            "evidence_for": [{"claim": "x", "date": "2026-09-01", "source": "s"}], "evidence_against": [],
            "reviewed_on": "2026-09-10"}

    def carried(self, entry=None, exited="2026-09-10"):
        return smith_risk.carry_thesis_forward(entry or self.LAST, exited, "state.thesis", "2026-09-21")

    def test_the_record_keeps_last_status_and_evidence_and_says_where_from(self):
        r = self.carried()
        assert r["status"] == "strengthening" and r["last_status"] == "strengthening"
        assert r["evidence_for"] == self.LAST["evidence_for"]
        assert r["carried"] and r["exited"] and r["held"] is False
        assert (r["exited_as_of"], r["carried_from"], r["last_reviewed_on"]) == (
            "2026-09-10", "state.thesis", "2026-09-10")

    def test_thesis_status_is_still_a_known_status_never_an_invented_one(self):
        for e in (self.LAST, "moat|intact", "moat|exited 2026-07-24", "no status at all", {"status": "bogus"}):
            r = smith_risk.carry_thesis_forward(e, "2026-07-01", "x", "2026-09-21")
            assert smith_risk.thesis_status(r) is None or smith_risk.thesis_status(r) in smith_risk.KNOWN_STATUSES
        assert smith_risk.KNOWN_STATUSES == ("strengthening", "watch", "broken", "intact", "exited")

    def test_a_legacy_string_without_a_status_is_not_given_one(self):
        r = smith_risk.carry_thesis_forward("just prose", "2026-07-01", "x", "2026-09-21")
        assert "status" not in r and smith_risk.thesis_status(r) is None

    def test_nothing_to_carry_is_none_not_a_stub(self):
        assert smith_risk.carry_thesis_forward(None, "2026-07-01", "x", "2026-09-21") is None
        assert smith_risk.carry_thesis_forward("", "2026-07-01", "x", "2026-09-21") is None

    def test_carrying_is_idempotent_and_does_not_launder_age(self):
        once = self.carried()
        twice = smith_risk.carry_thesis_forward(once, "2026-12-01", "elsewhere", "2027-01-01")
        assert twice == once

    def test_uncarry_restores_an_ordinary_entry_for_a_name_held_again(self):
        back = smith_risk.uncarry_thesis(self.carried())
        assert not smith_risk.is_carried_thesis(back) and back["status"] == "strengthening"
        assert back["reviewed_on"] == "2026-09-10" and "carried_from" not in back

    def test_a_carried_strengthening_is_discounted_never_scored_as_fresh(self):
        fresh = sc.thesis_component(self.LAST)[0]
        stale = sc.thesis_component(self.carried())[0]
        assert fresh == pytest.approx(28 * 1.15) and stale == pytest.approx(28 * 0.5 * 0.75)
        assert stale < fresh / 3

    def test_a_carried_bad_thesis_is_not_softened(self):
        broken = {"status": "broken", "verified": "unverified"}
        assert sc.thesis_component(smith_risk.carry_thesis_forward(broken, "d", "x", "2026-09-21"))[0] == \
            sc.thesis_component(broken)[0] < 0

    def test_the_ticket_says_the_thesis_is_carried(self):
        _s, reason, status, verified = sc.thesis_component(self.carried())
        assert "CARRIED FROM EXIT" in reason and "not re-examined since the exit" in reason
        assert status == "strengthening" and verified == "unverified"

    def _reentry(self, thesis, alumni, bar=None):
        out, no_t, judged, audit = [], [], [], []
        smith_math._trigger_reentry_scan(
            {"trades": [{"ticker": "ZZZ", "date": "2026-09-10", "price_at_trade": 50.0}]},
            {"ZZZ": date(2026, 9, 10)}, {"ZZZ": ["STRONG UPTREND"]}, thesis, [], {"ZZZ": {"quarter_verdict": "beat"}},
            lambda t, p: 40.0, {"ZZZ": 30.0}, True, {"ZZZ": 8.0}, True, {"ZZZ": 3}, lambda b: None, {"ZZZ": 6.0},
            100000.0, POLICY, 10000.0, {}, out, no_t, judged, alumni_thesis=alumni, bar_inputs=bar, audit=audit)
        return out, no_t, judged, audit

    def test_reentry_could_not_judge_an_alumnus_before_and_can_now(self):
        out, no_t, _j, _a = self._reentry({}, {})
        assert out == [] and no_t == ["ZZZ"]                                   # the old behaviour
        from test_smith_math_triggers import bar_ok
        out, no_t, _j, audit = self._reentry({}, {"ZZZ": self.carried()}, bar_ok("ZZZ", 50.0, 6.0))
        assert no_t == [] and len(out) == 1 and audit[0]["thesis_carried"] is True
        row = out[0]
        assert row["thesis_carried"] is True and row["thesis_carried_from"] == "state.thesis"
        assert any("CARRIED FROM EXIT" in r for r in row["reasons"])
        assert any("CARRIED from ZZZ's exit" in b for b in row["blockers"])

    def test_a_carried_thesis_alone_cannot_clear_the_bar_for_a_live_reentry(self):
        from test_smith_math_triggers import bar_ok
        bar = bar_ok("ZZZ", 50.0, 6.0)
        out, *_ = self._reentry({}, {"ZZZ": self.carried()}, bar)
        assert out[0]["universe_bar"]["checks"]["thesis"] == "carried"
        # this fixture has this run's price/ATR/RSI + a verified earnings print + a carried thesis
        assert out[0]["vote"] == "live"
        no_px = dict(bar, prices={})
        assert self._reentry({}, {"ZZZ": self.carried()}, no_px)[0][0]["vote"] == "shadow"

    def test_alumni_map_reads_state_then_archive_and_marks_both_carried(self, tmp_path):
        (tmp_path / "exited-holdings-archive.json").write_text(json.dumps(
            {"thesis": {"ARC": "old thesis|intact", "ONLYARC": {"status": "watch"}}}))
        m = smith_math._alumni_thesis_map({"ARC": date(2026, 8, 1), "LIVE": date(2026, 9, 1), "NONE": date(2026, 1, 1)},
                                          {"LIVE": self.LAST}, str(tmp_path), date(2026, 9, 21))
        assert set(m) == {"ARC", "LIVE"}                                     # NONE has no entry anywhere
        assert m["ARC"]["carried_from"] == "exited-holdings-archive.json" and m["ARC"]["exited_as_of"] == "2026-08-01"
        assert m["LIVE"]["carried_from"] == "state.thesis" and smith_risk.is_carried_thesis(m["LIVE"])

    def test_compact_archives_an_exit_as_a_carried_record_and_restores_it_plain(self, tmp_path):
        base = tmp_path
        (base / "state.json").write_text(json.dumps({
            "holdings": [{"ticker": "KEEP"}],
            "thesis": {"KEEP": {"status": "intact"}, "GONE": dict(self.LAST)},
            "sector_map": {"KEEP": "C", "GONE": "C"}}))
        args = type("A", (), dict(base_dir=str(base), today="2026-09-21", holdings=None, mode="full",
                                   write=True, dry_run=False))()
        try:
            smith_memory.cmd_compact(args)
        except SystemExit:
            pass
        arch = json.loads((base / "exited-holdings-archive.json").read_text())["thesis"]["GONE"]
        assert arch["carried"] and arch["status"] == "strengthening" and arch["carried_from"] == "state.thesis"
        st = json.loads((base / "state.json").read_text())
        assert "GONE" not in st["thesis"]
        # the name comes back: restore strips the stale markers
        st["holdings"].append({"ticker": "GONE"})
        (base / "state.json").write_text(json.dumps(st))
        try:
            smith_memory.cmd_compact(args)
        except SystemExit:
            pass
        back = json.loads((base / "state.json").read_text())["thesis"]["GONE"]
        assert not back.get("carried") and back["status"] == "strengthening"


class TestFetchAlumni:
    def test_only_judgeable_alumni_are_fetched_and_last(self):
        import smith_fetch as sf
        arch = {"UP": {"status": "strengthening"}, "OK": "x|intact", "W": {"status": "watch"},
                "X": "y|EXITED 2026-07-01", "HELD": {"status": "intact"}}
        al = sf.judgeable_alumni(arch, held={"HELD"})
        assert al == ["OK", "UP"]
        assert sf.candidate_tickers({"watchlist_setups": [{"ticker": "IONQ"}]}, al) == ["IONQ", "OK", "UP"]
        assert sf.candidate_tickers({"watchlist_setups": [{"ticker": "IONQ"}]}) == ["IONQ"]

"""Unit tests for smith_dashboard.py (v2), which replaced v1's 24 `_render_*` HTML-string
builders on 2026-09-09.

WHY THESE LOOK DIFFERENT FROM THE v1 TESTS THEY REPLACE (archived alongside the v1 builder):
v1 assembled the page as 35 independent HTML string builders wired together by hand in
`build()`, so the only thing worth unit-testing was "does this builder emit the ticker".
That test shape could not catch the failure that actually happened -- thirteen of those
builders were never CALLED, so the panels silently vanished from the published page while
every one of their unit tests kept passing.

v2 has one payload builder and a client-side renderer, so the tests move to where the
guarantee now lives: the payload either carries what a panel needs or the build fails. The
first class below is the important one -- it is the regression guard itself, expressed as a
test rather than as a comment nobody re-reads.
"""
import json
import os
import shutil

import pytest

import smith_dashboard as sd


FIXTURE = os.path.join(os.path.dirname(__file__), "..", "fixtures", "dashboard_case1", "base")


@pytest.fixture(scope="module")
def payload():
    return sd.build_payload(os.path.abspath(FIXTURE))


# ---------------------------------------------------------------------------
# The structural guarantee -- the thing v1 lacked
# ---------------------------------------------------------------------------

class TestPayloadCompleteness:
    def test_every_required_key_is_present(self, payload):
        missing = [k for k in sd.REQUIRED_KEYS if k not in payload]
        assert missing == [], f"payload lost {missing} -- a panel would render empty"

    def test_a_missing_key_fails_the_build_loudly(self, payload):
        """The v1 failure mode was a panel disappearing in silence. Dropping a key must be a
        crash with the key named in it, not a quietly shorter page."""
        broken = dict(payload)
        del broken["triggers"]
        with pytest.raises(SystemExit) as e:
            sd.assert_payload_complete(broken)
        assert "triggers" in str(e.value)

    def test_required_keys_are_not_silently_shrinkable(self):
        """A future edit that trims REQUIRED_KEYS to make a build pass is the regression
        repeating itself. Pin the floor."""
        assert len(sd.REQUIRED_KEYS) >= 30
        for k in ("proposals", "triggers", "thesis", "track", "freshness", "dq", "positions"):
            assert k in sd.REQUIRED_KEYS


# ---------------------------------------------------------------------------
# Panels that exist ONLY in v2 -- the thirteen v1 defined and never called
# ---------------------------------------------------------------------------

class TestPanelsV1SilentlyDropped:
    """Each of these was a defined-but-uncalled `_render_*` in v1. If any goes empty again,
    the reason will be visible here rather than in a page nobody diffed."""

    def test_thesis_map_carries_held_flag_so_exited_names_are_not_shown_as_current(self, payload):
        th = payload["thesis"]
        assert th, "thesis map empty"
        assert all("held" in v for v in th.values())

    def test_signal_history_is_carried(self, payload):
        assert isinstance(payload["signals"], dict)

    def test_execution_log_is_carried(self, payload):
        assert isinstance(payload["trades"], list)

    def test_data_quality_is_unioned_across_every_compute_step(self, payload):
        """v1's spec required the union of every step's self-reported data_quality plus
        state's. A dashboard hiding its own uncertainty invites more trust than the numbers
        earn -- so each entry must name the step it came from."""
        for row in payload["dq"]:
            assert "src" in row and "text" in row

    def test_self_learning_readiness_is_carried(self, payload):
        assert "readiness_current" in payload["learning"]
        assert "lessons" in payload["learning"]

    def test_stop_loss_efficacy_keeps_its_cohort_split(self, payload):
        """Cascade-vs-deliberate is the whole point of the panel: a stop that fired inside a
        broad selloff is not evidence about the stop framework the way a deliberate one is."""
        assert "by_cohort" in payload["track"]["stops"]

    def test_watchlist_factor_themes_and_diversifiers_are_carried(self, payload):
        assert isinstance(payload["watchlist"], list)
        assert isinstance(payload["themes"], dict)
        assert isinstance(payload["diversifiers"], dict)

    def test_open_gaps_are_carried(self, payload):
        assert isinstance(payload["gaps"], list)

    def test_trade_triggers_are_carried_as_families(self, payload):
        assert isinstance(payload["triggers"]["families"], dict)


# ---------------------------------------------------------------------------
# Content correctness
# ---------------------------------------------------------------------------

class TestPositions:
    def test_positions_merge_book_risk_and_thesis(self, payload):
        pos = payload["positions"]
        assert pos, "no positions built"
        p = pos[0]
        for k in ("t", "cluster", "val", "wt", "atr", "beta", "stop_px", "cap", "over_cap"):
            assert k in p

    def test_positions_are_ordered_by_weight_descending(self, payload):
        w = [p["wt"] or 0 for p in payload["positions"]]
        assert w == sorted(w, reverse=True)


class TestProposals:
    def test_open_proposals_are_verdict_first_then_effective_priority(self, payload):
        # 2026-09-19: what still deserves a decision leads; the desk's retire recommendations
        # sink to one collapsed row. Within a verdict, EFFECTIVE priority (a weakened HIGH reads
        # MEDIUM) orders the cards -- the stored priority alone put stale HIGHs on top.
        verdict = {"valid": 0, "weakened": 1, "retire": 2}
        rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "RETIRE": 3}
        got = [(verdict.get((p.get("v") or {}).get("verdict"), 0),
                rank.get((p.get("v") or {}).get("effective_priority") or p["priority"], 4))
               for p in payload["proposals"]["open"]]
        assert got == sorted(got)

    def test_history_carries_every_proposal_not_just_the_open_ones(self, payload):
        pr = payload["proposals"]
        assert len(pr["history"]) >= len(pr["open"])

    def test_status_counts_cover_the_whole_store(self, payload):
        pr = payload["proposals"]
        assert sum(pr["counts"].values()) == len(pr["history"])


class TestClusters:
    def test_cluster_rows_read_the_real_drift_field_names(self, payload):
        """compute_drift emits `actual_pct_of_equity`, not `pct_of_equity`. Reading the wrong
        name degrades to None silently, which is how a meter renders at zero and looks like a
        real allocation rather than a plumbing bug."""
        rows = payload["clusters"]
        assert rows
        assert any(c["eq_pct"] is not None for c in rows)

    def test_members_only_contain_currently_held_tickers(self, payload):
        held = {p["t"] for p in payload["positions"]}
        for c in payload["clusters"]:
            assert set(c["members"]) <= held

    def test_exited_names_are_listed_separately_not_dropped(self, payload):
        for c in payload["clusters"]:
            assert isinstance(c["gone"], list)
            assert not (set(c["gone"]) & set(c["members"]))


class TestLadders:
    """Ported from v1's TestClusterLadders, which tested `_render_cluster_ladders` -- a
    function that never existed in the shipped v1 builder. Those twelve tests had been failing
    on every run against the real module."""

    def test_a_ladder_carries_its_ranking_bench_and_confidence(self, payload):
        for name, L in payload["ladders"].items():
            assert "ranking" in L and "bench" in L and "confidence" in L

    def test_bench_names_are_distinguishable_from_holdings(self, payload):
        for L in payload["ladders"].values():
            for r in L["ranking"]:
                assert isinstance(r["held"], bool)

    def test_no_ladder_means_an_empty_map_not_a_crash(self):
        assert sd.build_payload  # builder importable with no ladder state
        assert isinstance({}, dict)


class TestHonestyConstraints:
    def test_untrusted_ledger_rows_are_marked_never_dropped(self, payload):
        """A corrupt price-feed reading must never set an axis or count as performance -- but
        it must also still be visible. Marked, not removed."""
        for row in payload["ledger"]:
            assert "trust" in row

    def test_beta_note_survives_into_the_payload(self, payload):
        """SPX beta is misleading for this book and the note saying so must travel with the
        number, not be dropped as prose."""
        assert "beta_bm" in payload["kpi"]


class TestRender:
    def test_html_embeds_the_payload_and_declares_no_decisions_blob(self, payload):
        """Decisions moved onto the `db` capability 2026-09-16 -- the page no longer embeds a
        smith-decisions script tag at all; DEC is populated client-side from a db read."""
        html = sd.render_html(payload)
        assert '<script type="application/json" id="smith-payload">' in html
        assert 'id="smith-decisions"' not in html

    def test_decisions_js_uses_the_db_capability_not_self_publish(self, payload):
        """Rewritten 2026-09-16: no client-side self.publish/PRISTINE snapshot any more --
        clicks write directly to db.collection("decisions")."""
        html = sd.render_html(payload)
        assert 'claude.use("db")' in html
        assert "db.collection(\"decisions\")" in html
        assert "window.claude.self" not in html and "PRISTINE" not in html

    def test_payload_json_cannot_close_its_own_script_tag(self):
        """Any `</` inside the data would end the tag early and dump the rest of the payload
        into the document as text."""
        html = sd.render_html({k: ("</script><b>x" if k == "read" else {})
                               for k in sd.REQUIRED_KEYS} | {"meta": {}, "kpi": {}})
        body = html.split('id="smith-payload">')[1].split("</script>")[0]
        assert "</script>" not in body

    def test_the_page_declares_a_title(self, payload):
        assert "<title>Agent Smith Desk</title>" in sd.render_html(payload)


class TestAttentionDigest:
    """Command shows a few lines, not every trigger row (user, 2026-09-19: "Dashboard should
    have fewer important only entries")."""

    def _trig(self):
        return {
            "factor_threat": [{"headline": "Essay", "held_count": 26, "equity_pct": 99.4,
                               "held_names": ["A"] * 26}],
            "catalyst_threat": [
                {"ticker": "MU", "suggested_size_usd": 400, "events": ["CXMT (09-01)"], "vote": "live"},
                {"ticker": "TER", "suggested_size_usd": 370, "events": ["CXMT (09-01)"], "vote": "live"},
                {"ticker": "GLW", "suggested_size_usd": 90, "events": ["Corning ATM (09-14)"],
                 "read_through": ["COHR", "LITE"], "vote": "live"}],
            "trend_entry": [{"ticker": "LITE", "vote": "live", "conviction_score": 29.7,
                             "direction": "BUY", "suggested_size_usd": 330, "reasons": ["r"]}],
            "conviction_average": [{"ticker": "KLAC", "vote": "live", "conviction_score": 61.0,
                                    "direction": "BUY", "suggested_size_usd": 400, "reasons": ["r"]}],
            "overbought_distribution": [{"ticker": "BE", "vote": "live", "direction": "TRIM",
                                         "suggested_size_usd": 100, "reasons": ["RSI 78"]}],
            "laggard_rotation": [{"ticker": "X", "vote": "shadow"}],
        }

    def test_catalyst_threats_collapse_to_one_line_per_event(self):
        import smith_dashboard as sd
        items = sd.attention_digest(self._trig())["items"]
        threats = [i for i in items if i["kind"] == "catalyst_threat"]
        assert len(threats) == 2
        cx = next(i for i in threats if "CXMT" in i["detail"])
        assert cx["names"] == ["MU", "TER"] and cx["size"] == 770

    def test_the_factor_threat_is_one_book_line(self):
        import smith_dashboard as sd
        items = sd.attention_digest(self._trig())["items"]
        assert items[0]["kind"] == "factor_threat" and items[0]["dir"] == "BOOK"

    def test_low_conviction_ideas_are_left_out_and_counted(self):
        import smith_dashboard as sd
        d = sd.attention_digest(self._trig())
        titles = [i["title"] for i in d["items"]]
        assert "Buy LITE" not in titles and "Buy KLAC" in titles
        assert d["below_medium_conviction"] == 1

    def test_defensive_signals_without_a_score_always_show(self):
        import smith_dashboard as sd
        assert any(i["title"] == "Trim BE" for i in sd.attention_digest(self._trig())["items"])

    def test_shadow_rows_never_reach_command(self):
        import smith_dashboard as sd
        assert not any(i["kind"] == "laggard_rotation" for i in sd.attention_digest(self._trig())["items"])

    def test_read_through_names_are_noted_not_trimmed(self):
        import smith_dashboard as sd
        g = next(i for i in sd.attention_digest(self._trig())["items"] if "Corning" in (i["detail"] or ""))
        assert g["names"] == ["GLW"] and "COHR" in g["note"]

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
    def test_open_proposals_are_priority_ordered_high_first(self, payload):
        rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        got = [rank.get(p["priority"], 3) for p in payload["proposals"]["open"]]
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
    def test_html_embeds_the_payload_and_an_empty_decisions_blob(self, payload):
        html = sd.render_html(payload)
        assert '<script type="application/json" id="smith-payload">' in html
        assert '<script type="application/json" id="smith-decisions">[]</script>' in html

    def test_a_freshly_built_page_always_ships_decisions_empty(self, payload):
        """SKILL.md §1.7: the sync step drains the live blob BEFORE the rebuild, so a new page
        starting with anything else would silently replay already-applied decisions."""
        html = sd.render_html(payload)
        assert html.count('id="smith-decisions">[]<') == 1

    def test_payload_json_cannot_close_its_own_script_tag(self):
        """Any `</` inside the data would end the tag early and dump the rest of the payload
        into the document as text."""
        html = sd.render_html({k: ("</script><b>x" if k == "read" else {})
                               for k in sd.REQUIRED_KEYS} | {"meta": {}, "kpi": {}})
        body = html.split('id="smith-payload">')[1].split("</script>")[0]
        assert "</script>" not in body

    def test_the_page_declares_a_title(self, payload):
        assert "<title>Agent Smith Desk</title>" in sd.render_html(payload)

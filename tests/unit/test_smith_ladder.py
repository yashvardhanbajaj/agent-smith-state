"""cmd_ladder and the cluster-room sizing clamp (added 2026-09-08).

Two things are pinned here.

1. rel_intra_pp. _trigger_cluster_rotation ranked cluster members on `rel_pp` from
   data_cache.rel_strength_1m, which is ALWAYS SMH-relative for the whole book -- so power and
   hyperscaler names were being ranked against a semiconductor ETF. rel_intra_pp measures each
   member against its own cluster's mean return instead, which is benchmark-free by construction.
   The reordering is not cosmetic: on the live 2026-09-07 book AVGO went from worst-in-cluster on
   SMH (-13.31pp) to second-best on intra (+5.19pp), and a live proposal was selling it.

2. cluster_room_usd. smith_conviction.clamp_size has taken a cluster_room_usd argument since it
   was written and every caller passed None, so its documented promise ("never push a cluster
   over its ceiling") was never once enforced. The subtle half is the SAME-CLUSTER credit-back:
   a rotation is a swap, so the sale funds the purchase and clamping the buy to the cluster's
   standing room would zero the buy leg of any rotation inside a full cluster -- silently
   converting a rotation into a naked sell.
"""
import json
import os

import pytest

import smith_math
import smith_core


# ---------------------------------------------------------------------------
# _pair_cluster_room_usd -- the swap-aware clamp input
# ---------------------------------------------------------------------------

ROWS = {"Full": {"cluster_room_usd": 0.0},
        "Roomy": {"cluster_room_usd": 5000.0},
        "Unbanded": {"cluster_room_usd": None}}


class TestPairClusterRoom:
    def test_cross_cluster_buy_is_clamped_to_the_buy_clusters_room(self):
        assert smith_math._pair_cluster_room_usd(ROWS, "Roomy", "Full", sell_size=900.0) == 0.0

    def test_same_cluster_swap_credits_the_sale_back(self):
        # The rotation this protects: sell 900 of a laggard in a cluster with zero standing
        # room, buy 900 of the leader in the SAME cluster. Net cluster weight is unchanged, so
        # a 0.0 clamp here would be wrong -- and would turn the rotation into a naked sell.
        assert smith_math._pair_cluster_room_usd(ROWS, "Full", "Full", sell_size=900.0) == 900.0

    def test_unbanded_cluster_is_non_binding_not_zero(self):
        # clamp_size's own rule: unknown != a reason to block.
        assert smith_math._pair_cluster_room_usd(ROWS, "Roomy", "Unbanded", 900.0) is None

    def test_missing_drift_is_non_binding(self):
        assert smith_math._pair_cluster_room_usd({}, "A", "B", 900.0) is None
        assert smith_math._pair_cluster_room_usd(None, "A", "B", 900.0) is None

    def test_room_never_goes_negative(self):
        assert smith_math._pair_cluster_room_usd({"X": {"cluster_room_usd": -500.0}},
                                                  "Y", "X", sell_size=0.0) == 0.0


class TestClusterRotationRespectsClusterRoom:
    """The end-to-end version of the credit-back: a same-cluster rotation inside a cluster that
    is already at its ceiling must still size its buy leg."""

    def _pair(self, cluster_rows):
        from test_smith_math_triggers import _conv_row
        out = []
        conv = {"LAG": _conv_row(3000.0, "Semis", rel_pp=-5.0),
                "PERF": _conv_row(1000.0, "Semis", rel_pp=5.0)}
        smith_math._trigger_cluster_rotation(
            conv, {"LAG": "stuck|watch", "PERF": "running|strengthening"}, out,
            cluster_rows=cluster_rows)
        return out[0]

    def test_full_cluster_still_sizes_the_buy_leg(self):
        pair = self._pair({"Semis": {"cluster_room_usd": 0.0}})
        assert pair["buy_leg"]["suggested_size_usd"] == pytest.approx(900.0)  # 30% of 3000
        assert pair["buy_leg"]["clamped_by"] is None

    def test_no_drift_data_degrades_to_the_prior_behaviour(self):
        assert self._pair({})["buy_leg"]["suggested_size_usd"] == pytest.approx(900.0)


class TestProfitRotationRespectsClusterRoom:
    """profit_rotation pairs are frequently CROSS-cluster, which is where the clamp genuinely
    binds -- this is the case the None argument had been silently skipping."""

    def test_cross_cluster_buy_is_clamped_by_the_buy_clusters_ceiling(self):
        from test_smith_math_triggers import _conv_row, POLICY
        out = []
        conv = {"SELL_ME": _conv_row(2000.0, "Compute", rel_pp=10.0),
                "BUY_ME": _conv_row(500.0, "Networking", rel_pp=-8.0)}
        smith_math._trigger_profit_rotation(
            names_stretched={"SELL_ME"}, conviction_by_ticker=conv,
            thesis={"SELL_ME": "extended|watch", "BUY_ME": "cheap|strengthening"},
            total_book=100000.0, policy=POLICY, profit_rotation=out,
            cluster_rows={"Networking": {"cluster_room_usd": 150.0}})
        assert out[0]["buy_leg"]["suggested_size_usd"] == pytest.approx(150.0)
        assert out[0]["buy_leg"]["clamped_by"] == "cluster ceiling room"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

class TestLadderSlug:
    def test_derives_a_stable_slug_from_the_cluster_name(self):
        assert smith_math._ladder_slug("AI Semis/Fabs", None) == "ai_semis_fabs"
        assert smith_math._ladder_slug("Compute/Hyperscaler OEM", {}) == "compute_hyperscaler_oem"

    def test_playbook_slug_wins_for_readability(self):
        assert smith_math._ladder_slug("AI Memory/Storage", {"slug": "memory"}) == "memory"

    def test_playbook_slug_is_sanitised(self):
        # The slug becomes an agent key and a filename (slice_cluster_<slug>.json).
        assert smith_math._ladder_slug("X", {"slug": "Bad Slug/../x"}) == "badslugx"

    def test_sibling_clusters_do_not_collide(self):
        a = smith_math._ladder_slug("Compute/Hyperscaler", None)
        b = smith_math._ladder_slug("Compute/Hyperscaler OEM", None)
        assert a != b


class TestStdev:
    def test_sample_stdev(self):
        assert smith_math._stdev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]) == pytest.approx(2.13809, rel=1e-4)

    def test_single_value_has_no_dispersion(self):
        assert smith_math._stdev([3.0]) == 0.0
        assert smith_math._stdev([]) == 0.0


class TestLadderTrackRecord:
    """The falsifiability hook. A ranking nobody checks becomes a confident-nonsense generator,
    and this layer is allowed to touch a live trigger only because it is scored."""
    from datetime import date
    TODAY = date(2026, 9, 8)

    def test_scores_a_correct_call(self):
        tr = smith_math._ladder_track_record(
            {"leader": "GOOD", "laggard": "BAD", "as_of": "2026-08-20", "confidence": "high"},
            {"GOOD": 10.0, "BAD": 2.0}, self.TODAY)
        assert tr["correct"] is True and tr["spread_pp"] == 8.0
        assert tr["ladder_confidence_at_call"] == "high"

    def test_scores_a_wrong_call(self):
        tr = smith_math._ladder_track_record(
            {"leader": "GOOD", "laggard": "BAD", "as_of": "2026-08-20"},
            {"GOOD": 1.0, "BAD": 6.0}, self.TODAY)
        assert tr["correct"] is False and tr["spread_pp"] == -5.0

    def test_an_unscoreable_call_is_not_a_wrong_call(self):
        tr = smith_math._ladder_track_record(
            {"leader": "GOOD", "laggard": "BAD"}, {"GOOD": 1.0}, self.TODAY)
        assert tr["scored"] is False and "correct" not in tr

    def test_no_prior_ladder_scores_nothing(self):
        assert smith_math._ladder_track_record({}, {"A": 1.0}, self.TODAY) is None
        assert smith_math._ladder_track_record(None, {"A": 1.0}, self.TODAY) is None


# ---------------------------------------------------------------------------
# cmd_ladder, end to end
# ---------------------------------------------------------------------------

class _Args:
    def __init__(self, base_dir, run_dir, today="2026-09-08"):
        self.base_dir, self.run_dir, self.today = base_dir, run_dir, today


def _build(tmp_path, positions, *, abs_returns, atr=None, clusters_in_drift=None,
           prior_ladders=None, cursor=None, triggers=None, rel_as_of="2026-09-06",
           earnings=None, playbooks=None):
    base, rd = tmp_path / "base", tmp_path / "rd"
    base.mkdir(); rd.mkdir()
    (rd / "compute_risk.json").write_text(json.dumps({
        "positions": positions, "total_book_usd": 10000.0}))
    (rd / "compute_drift.json").write_text(json.dumps({
        "invested_equity_usd": 10000.0,
        "cluster_table": clusters_in_drift or []}))
    (rd / "compute_rotation.json").write_text(json.dumps({"tickers": {}}))
    if triggers is not None:
        (rd / "compute_triggers.json").write_text(json.dumps(triggers))
    (base / "state.json").write_text(json.dumps({
        "data_cache": {
            "rel_strength_1m": {"as_of": rel_as_of, "values_abs_pct": abs_returns,
                                "values_pp": {}},
            "atr20": {"values_pct": atr or {}},
            "rsi14": {"values": {}},
            "earnings_calendar": earnings or {}},
        "thesis": {}, "cluster_ladders": prior_ladders or {},
        "cluster_scan_cursor": cursor or {}}))
    (base / "policy.json").write_text(json.dumps({"cluster_playbooks": playbooks or {}}))
    return _Args(str(base), str(rd))


def _run(capsys, args):
    smith_math.cmd_ladder(args)
    return json.loads(capsys.readouterr().out)


def _pos(t, cluster, mv=1000.0, **kw):
    d = {"ticker": t, "cluster": cluster, "market_value_usd": mv, "over_cap": False,
         "headroom_usd": 5000.0, "atr20_pct": 5.0, "cap_multiple": 0.5}
    d.update(kw)
    return d


class TestRelIntraPp:
    def test_members_are_ranked_against_their_own_cluster_mean(self, tmp_path, capsys):
        # The live 2026-09-07 case in miniature: the whole cluster is up a lot, so every member
        # looks weak against a hot external benchmark -- but internally there is a clear order.
        args = _build(tmp_path,
                      [_pos("A", "C"), _pos("B", "C"), _pos("D", "C")],
                      abs_returns={"A": 20.0, "B": 10.0, "D": 0.0})
        out = _run(capsys, args)
        c = out["clusters"]["C"]
        assert c["mean_return_1m_pct"] == 10.0
        assert [m["ticker"] for m in c["members"]] == ["A", "B", "D"]
        assert [m["rel_intra_pp"] for m in c["members"]] == [10.0, 0.0, -10.0]
        assert c["leader_by_price"] == "A" and c["laggard_by_price"] == "D"

    def test_the_mean_is_equal_weighted_not_value_weighted(self, tmp_path, capsys):
        # A value-weighted mean would let the largest holding define the bar it is then judged
        # against -- an oversized laggard would drag the mean down until it looked like a leader.
        args = _build(tmp_path,
                      [_pos("BIG", "C", mv=90000.0), _pos("S1", "C", mv=100.0),
                       _pos("S2", "C", mv=100.0)],
                      abs_returns={"BIG": -10.0, "S1": 10.0, "S2": 10.0})
        out = _run(capsys, args)
        assert out["clusters"]["C"]["mean_return_1m_pct"] == pytest.approx(10.0 / 3, abs=1e-3)
        assert out["clusters"]["C"]["laggard_by_price"] == "BIG"

    def test_uncovered_members_are_listed_not_ranked(self, tmp_path, capsys):
        args = _build(tmp_path, [_pos("A", "C"), _pos("B", "C"), _pos("GHOST", "C")],
                      abs_returns={"A": 5.0, "B": -5.0})
        out = _run(capsys, args)
        c = out["clusters"]["C"]
        assert c["return_coverage"] == {"with_return": 2, "total": 3, "missing": ["GHOST"]}
        assert c["members"][-1]["ticker"] == "GHOST"       # sorted to the end
        assert c["members"][-1]["rel_intra_pp"] is None
        assert c["laggard_by_price"] == "B"                # never an unranked name


class TestCoverageAndDispersion:
    def test_thin_coverage_is_flagged_as_a_partial_ranking(self, tmp_path, capsys):
        args = _build(tmp_path, [_pos("A", "C"), _pos("B", "C"), _pos("D", "C")],
                      abs_returns={"A": 5.0})
        out = _run(capsys, args)
        assert any("PARTIAL ranking" in q and "B, D" in q for q in out["data_quality"])

    def test_single_covered_member_has_no_dispersion_and_no_ends(self, tmp_path, capsys):
        # None, not 0.0: "moves as one block" is a finding, and a missing measurement must
        # never be dressed as one.
        args = _build(tmp_path, [_pos("A", "C"), _pos("B", "C"), _pos("D", "C")],
                      abs_returns={"A": 5.0})
        c = _run(capsys, args)["clusters"]["C"]
        assert c["dispersion_pp"] is None
        assert c["leader_by_price"] is None and c["laggard_by_price"] is None

    def test_stale_return_cache_is_reported_and_not_estimated(self, tmp_path, capsys):
        args = _build(tmp_path, [_pos("A", "C"), _pos("B", "C"), _pos("D", "C")],
                      abs_returns={"A": 5.0, "B": 1.0, "D": -5.0}, rel_as_of="2026-01-01")
        out = _run(capsys, args)
        assert out["return_basis"]["usable"] is False
        assert any("unusable" in q for q in out["data_quality"])


class TestRedundancyCandidates:
    def test_near_identical_move_and_volatility_pairs_are_screened(self, tmp_path, capsys):
        args = _build(tmp_path, [_pos("TWIN1", "C"), _pos("TWIN2", "C"), _pos("OTHER", "C")],
                      abs_returns={"TWIN1": 5.0, "TWIN2": 5.5, "OTHER": -20.0},
                      atr={"TWIN1": 5.0, "TWIN2": 5.2, "OTHER": 5.1})
        pairs = _run(capsys, args)["clusters"]["C"]["redundancy_candidates"]
        # pairs are emitted in ladder-rank order, best performer first
        assert [p["pair"] for p in pairs] == [["TWIN2", "TWIN1"]]

    def test_it_is_a_screen_and_says_so(self, tmp_path, capsys):
        args = _build(tmp_path, [_pos("T1", "C"), _pos("T2", "C"), _pos("T3", "C")],
                      abs_returns={"T1": 5.0, "T2": 5.1, "T3": -30.0},
                      atr={"T1": 5.0, "T2": 5.0, "T3": 5.0})
        note = _run(capsys, args)["clusters"]["C"]["redundancy_candidates"][0]["note"]
        assert "CANDIDATE" in note and "business judgment" in note


class TestEligibility:
    def test_a_cluster_below_min_members_is_ineligible(self, tmp_path, capsys):
        args = _build(tmp_path, [_pos("A", "Small"), _pos("B", "Small")],
                      abs_returns={"A": 5.0, "B": -5.0})
        out = _run(capsys, args)
        assert out["clusters"]["Small"]["eligible"] is False
        assert out["dispatch"] == []

    def test_a_cluster_with_nothing_to_rotate_into_is_ineligible(self, tmp_path, capsys):
        args = _build(tmp_path,
                      [_pos("A", "C", over_cap=True), _pos("B", "C", over_cap=True),
                       _pos("D", "C")],
                      abs_returns={"A": 5.0, "B": 1.0, "D": -5.0})
        out = _run(capsys, args)
        assert out["clusters"]["C"]["eligible"] is False
        assert "under their ATR cap" in out["clusters"]["C"]["ineligible_reasons"][0]


class TestDispatchGate:
    def _three(self, cluster):
        """Distinct ATRs so the redundancy screen never fires -- these tests isolate the
        staleness and dispersion legs of the gate, and a stray +1 would hide a real change."""
        return [_pos("A" + cluster, cluster, atr20_pct=3.0),
                _pos("B" + cluster, cluster, atr20_pct=9.0),
                _pos("D" + cluster, cluster, atr20_pct=15.0)]

    def test_an_unranked_cluster_scores_the_staleness_points(self, tmp_path, capsys):
        args = _build(tmp_path, self._three("C"),
                      abs_returns={"AC": 1.0, "BC": 0.0, "DC": -1.0})
        row = _run(capsys, args)["dispatch"][0]
        assert row["priority_score"] == 3 and "no ladder yet" in row["reasons"][0]

    def test_a_fresh_ladder_scores_no_staleness_points(self, tmp_path, capsys):
        args = _build(tmp_path, self._three("C"),
                      abs_returns={"AC": 1.0, "BC": 0.0, "DC": -1.0},
                      prior_ladders={"C": {"as_of": "2026-09-06", "confidence": "high"}})
        out = _run(capsys, args)
        assert out["dispatch"][0]["priority_score"] == 0
        assert out["clusters"]["C"]["prior_ladder"]["stale"] is False

    def test_a_ladder_past_its_ttl_is_stale_again(self, tmp_path, capsys):
        stale_by_one = "2026-08-24"   # 15 days before 2026-09-08, TTL is 14
        args = _build(tmp_path, self._three("C"),
                      abs_returns={"AC": 1.0, "BC": 0.0, "DC": -1.0},
                      prior_ladders={"C": {"as_of": stale_by_one}})
        assert _run(capsys, args)["clusters"]["C"]["prior_ladder"]["stale"] is True

    def test_dispersion_breach_earnings_and_redundancy_all_score(self, tmp_path, capsys):
        args = _build(tmp_path, self._three("C"),
                      abs_returns={"AC": 10.0, "BC": 9.5, "DC": -10.0},
                      atr={"AC": 5.0, "BC": 5.0, "DC": 5.0},
                      clusters_in_drift=[{"cluster": "C", "breach": True, "breach_edge": "over",
                                          "cluster_room_usd": 0.0}],
                      earnings={"AC": {"date": "2026-09-10"}},
                      triggers={"cluster_rotation": [{"cluster": "C"}]})
        row = _run(capsys, args)["dispatch"][0]
        # 3 stale + 2 dispersion + 2 live pair + 2 breach + 1 earnings + 1 redundancy
        assert row["priority_score"] == 11

    def test_a_block_moving_cluster_scores_no_dispersion_points(self, tmp_path, capsys):
        args = _build(tmp_path, self._three("C"),
                      abs_returns={"AC": 5.1, "BC": 5.0, "DC": 4.9})
        assert _run(capsys, args)["dispatch"][0]["priority_score"] == 3

    def test_only_max_dispatch_clusters_are_selected(self, tmp_path, capsys):
        pos, rets = [], {}
        for name in "VWXYZ":
            pos += self._three(name)
            rets.update({"A" + name: 9.0, "B" + name: 0.0, "D" + name: -9.0})
        out = _run(capsys, _build(tmp_path, pos, abs_returns=rets))
        assert len(out["dispatch"]) == 5
        assert len(out["dispatch_selected"]) == smith_core.LADDER_MAX_DISPATCH
        assert out["dispatch_selected"] == [r["agent"] for r in out["dispatch"][:3]]

    def test_the_cursor_breaks_ties_toward_the_least_recently_seen(self, tmp_path, capsys):
        pos, rets = [], {}
        for name in "XYZ":
            pos += self._three(name)
            rets.update({"A" + name: 9.0, "B" + name: 0.0, "D" + name: -9.0})
        # All three tie on score; Z was looked at longest ago, so it goes first.
        out = _run(capsys, _build(tmp_path, pos, abs_returns=rets,
                                  cursor={"X": "2026-09-07", "Y": "2026-09-01", "Z": "2026-07-01"}))
        assert out["dispatch_selected_clusters"] == ["Z", "Y", "X"]

    def test_dispersion_breaks_a_remaining_tie(self, tmp_path, capsys):
        pos = self._three("Q") + self._three("W")
        rets = {"AQ": 1.0, "BQ": 0.0, "DQ": -1.0,      # tight
                "AW": 40.0, "BW": 0.0, "DW": -40.0}    # wide
        out = _run(capsys, _build(tmp_path, pos, abs_returns=rets))
        assert out["dispatch_selected_clusters"][0] == "W"


class TestLadderMisc:
    def test_agent_key_is_the_slug_prefixed(self, tmp_path, capsys):
        args = _build(tmp_path,
                      [_pos("A", "AI Memory/Storage"), _pos("B", "AI Memory/Storage"),
                       _pos("D", "AI Memory/Storage")],
                      abs_returns={"A": 9.0, "B": 0.0, "D": -9.0},
                      playbooks={"AI Memory/Storage": {"slug": "memory",
                                                       "differentiators": ["HBM4 qual"]}})
        out = _run(capsys, args)
        assert out["dispatch"][0]["agent"] == "cluster_memory"
        c = out["clusters"]["AI Memory/Storage"]
        assert c["playbook_present"] is True and c["differentiators"] == ["HBM4 qual"]

    def test_unclassified_holdings_are_surfaced_not_ranked_silently(self, tmp_path, capsys):
        args = _build(tmp_path, [_pos("A", "Unclassified"), _pos("B", "Unclassified"),
                                 _pos("D", "Unclassified")],
                      abs_returns={"A": 9.0, "B": 0.0, "D": -9.0})
        out = _run(capsys, args)
        assert any("Unclassified in sector_map" in q for q in out["data_quality"])

    def test_missing_risk_file_degrades_rather_than_raises(self, tmp_path, capsys):
        base, rd = tmp_path / "b", tmp_path / "r"
        base.mkdir(); rd.mkdir()
        out = _run(capsys, _Args(str(base), str(rd)))
        assert out["clusters"] == {} and out["dispatch"] == []
        assert "compute_risk.json not found" in out["data_quality"][0]

    def test_a_missing_triggers_file_costs_points_but_does_not_fail(self, tmp_path, capsys):
        args = _build(tmp_path, [_pos("A", "C"), _pos("B", "C"), _pos("D", "C")],
                      abs_returns={"A": 9.0, "B": 0.0, "D": -9.0})   # no compute_triggers.json
        out = _run(capsys, args)
        assert out["dispatch"][0]["priority_score"] == 5     # 3 stale + 2 dispersion, no pair


# ---------------------------------------------------------------------------
# PHASE 3 -- the ladder drives cluster_rotation, behind a confidence gate
# ---------------------------------------------------------------------------

from datetime import date          # noqa: E402  (kept beside the tests that use it)

import smith_risk                  # noqa: E402

TODAY = date(2026, 9, 8)


def _ladder(confidence="high", as_of="2026-09-06", order=("BEST", "MID", "WORST"),
            track_record=None, reads=True):
    return {"as_of": as_of, "confidence": confidence,
            "leader": order[0], "laggard": order[-1],
            "track_record": track_record or [],
            "ranking": [{"rank": i + 1, "ticker": t, "held": True,
                         "verdict": ("leader" if i == 0 else
                                     "laggard" if i == len(order) - 1 else "middle"),
                         "differentiator_reads": ([{"axis": "1.6T timing",
                                                    "read": f"{t} qualified first"}]
                                                  if reads else [])}
                        for i, t in enumerate(order)]}


class TestLadderAuthority:
    """The gate. `full` buys the thesis relaxation, which is the risky half of this change."""

    def test_high_confidence_and_fresh_gets_full_authority(self):
        assert smith_risk.ladder_authority(_ladder("high"), TODAY)[0] == "full"

    def test_medium_confidence_gets_ordering_but_not_the_relaxation(self):
        assert smith_risk.ladder_authority(_ladder("medium"), TODAY)[0] == "rank"

    def test_low_confidence_gets_nothing(self):
        assert smith_risk.ladder_authority(_ladder("low"), TODAY)[0] == "none"

    def test_an_unset_confidence_gets_nothing(self):
        assert smith_risk.ladder_authority(_ladder(""), TODAY)[0] == "none"

    def test_a_stale_ladder_gets_nothing_however_confident(self):
        auth, _, why = smith_risk.ladder_authority(_ladder("high", as_of="2026-08-01"), TODAY)
        assert auth == "none" and "38d old" in why[0]

    def test_an_unparseable_as_of_gets_nothing_rather_than_being_assumed_fresh(self):
        assert smith_risk.ladder_authority({"confidence": "high", "as_of": "soon"}, TODAY)[0] == "none"
        assert smith_risk.ladder_authority({"confidence": "high"}, TODAY)[0] == "none"

    def test_a_failing_track_record_forces_low_and_withdraws_authority(self):
        """The agent does not grade its own homework. A ranking that is measured and failing
        must not keep sizing trades -- this is the condition the whole layer was allowed on."""
        tr = [{"scored": True, "correct": False}] * 5 + [{"scored": True, "correct": True}]
        auth, conf, why = smith_risk.ladder_authority(_ladder("high", track_record=tr), TODAY)
        assert auth == "none" and conf == "low"
        assert "below coin-flip" in why[0]

    def test_a_small_failing_sample_is_reported_but_not_acted_on(self):
        # 2-of-3 is noise, and acting on it is the small-sample overreaction the journal's own
        # hit-rate machinery avoids.
        tr = [{"scored": True, "correct": False}] * 2 + [{"scored": True, "correct": True}]
        auth, conf, why = smith_risk.ladder_authority(_ladder("high", track_record=tr), TODAY)
        assert auth == "full" and conf == "high"
        assert any("below the sample bar" in w for w in why)

    def test_exactly_coin_flip_keeps_authority(self):
        tr = [{"scored": True, "correct": True}] * 3 + [{"scored": True, "correct": False}] * 3
        assert smith_risk.ladder_authority(_ladder("high", track_record=tr), TODAY)[0] == "full"

    def test_unscoreable_calls_do_not_count_against_the_record(self):
        tr = [{"scored": False}] * 10 + [{"scored": True, "correct": True}]
        assert smith_risk.ladder_authority(_ladder("high", track_record=tr), TODAY)[0] == "full"


class TestLadderDrivenRotation:
    def _run(self, ladder, conv, thesis):
        out = []
        smith_math._trigger_cluster_rotation(conv, thesis, out, cluster_rows={},
                                             cluster_ladders={"C": ladder} if ladder else {},
                                             today=TODAY)
        return out

    def _conv(self, **over):
        from test_smith_math_triggers import _conv_row
        base = {"BEST": _conv_row(1000.0, "C", rel_pp=-8.0),    # ladder #1, but PRICE laggard
                "MID": _conv_row(1000.0, "C", rel_pp=0.0),
                "WORST": _conv_row(3000.0, "C", rel_pp=9.0)}    # ladder #3, but PRICE leader
        base.update(over)
        return base

    INTACT = {"BEST": "x|strengthening", "MID": "x|intact", "WORST": "x|intact"}
    WATCH = {"BEST": "x|strengthening", "MID": "x|intact", "WORST": "x|watch"}
    # A thesis the PRICE rule can actually fire on: its laggard leg needs rel_pp<0 AND watch,
    # which only BEST (-8pp) satisfies. Used to prove the fallback still works, so a fallback
    # test cannot pass merely because nothing fired.
    PRICE_RULE = {"BEST": "x|watch", "MID": "x|intact", "WORST": "x|strengthening"}

    def test_the_ladder_inverts_the_price_ranking(self):
        """The whole point. On price, WORST is the leader (+9pp) and BEST the laggard (-8pp);
        the ladder says the opposite, and the ladder wins."""
        pairs = self._run(_ladder("high"), self._conv(), self.INTACT)
        assert len(pairs) == 1
        assert pairs[0]["sell_leg"]["ticker"] == "WORST"
        assert pairs[0]["buy_leg"]["ticker"] == "BEST"
        assert pairs[0]["ladder_driven"] is True

    def test_full_authority_unlocks_the_intact_laggard(self):
        """The most common real case: 16 strengthening / 16 watch / 0 broken, so a `watch`-only
        sell gate can never rotate an intact name."""
        assert self._run(_ladder("high"), self._conv(), self.INTACT)[0]["sell_leg"]["ticker"] == "WORST"

    def test_medium_authority_still_requires_a_watch_thesis_to_sell(self):
        assert self._run(_ladder("medium"), self._conv(), self.INTACT) == []
        pairs = self._run(_ladder("medium"), self._conv(), self.WATCH)
        assert pairs[0]["sell_leg"]["ticker"] == "WORST" and pairs[0]["ladder_driven"] is True

    def test_full_authority_will_not_sell_a_strengthening_name(self):
        """The relaxation is `not strengthening`, not `anything goes`."""
        thesis = dict(self.INTACT, WORST="x|strengthening")
        assert self._run(_ladder("high"), self._conv(), thesis) == []

    def test_a_low_confidence_ladder_falls_back_to_the_price_rule(self):
        pairs = self._run(_ladder("low"), self._conv(), self.PRICE_RULE)
        assert pairs[0]["ladder_driven"] is False
        assert pairs[0]["sell_leg"]["ticker"] == "BEST"      # the PRICE laggard, -8pp
        assert pairs[0]["buy_leg"]["ticker"] == "WORST"      # the PRICE leader, +9pp

    def test_a_stale_ladder_falls_back_even_at_high_confidence(self):
        pairs = self._run(_ladder("high", as_of="2026-07-01"), self._conv(), self.PRICE_RULE)
        assert pairs[0]["ladder_driven"] is False and pairs[0]["ladder_authority"] == "none"

    def test_no_ladder_reproduces_the_pre_existing_behaviour_exactly(self):
        from test_smith_math_triggers import _conv_row
        conv = {"LAG": _conv_row(1000.0, "C", rel_pp=-5.0),
                "PERF": _conv_row(1000.0, "C", rel_pp=5.0)}
        pairs = self._run(None, conv, {"LAG": "x|watch", "PERF": "x|strengthening"})
        assert pairs[0]["sell_leg"]["ticker"] == "LAG" and pairs[0]["buy_leg"]["ticker"] == "PERF"
        assert pairs[0]["ladder_driven"] is False
        assert "relative-strength leader" in pairs[0]["retires_when"]

    def test_the_reason_cites_the_differentiator_axis_not_a_price_delta(self):
        pairs = self._run(_ladder("high"), self._conv(), self.INTACT)
        why = pairs[0]["buy_leg"]["reasons"][0]
        assert "1.6T timing" in why and "qualified first" in why
        assert "pp" not in why

    def test_a_ladder_with_no_reads_still_names_the_rank(self):
        pairs = self._run(_ladder("high", reads=False), self._conv(), self.INTACT)
        assert "ranks BEST #1 of 3" in pairs[0]["buy_leg"]["reasons"][0]

    def test_the_retirement_condition_names_what_the_pair_was_built_on(self):
        """A ladder-driven pair revalidated against a price fact nobody used is a pair that
        retires for the wrong reason."""
        pairs = self._run(_ladder("high"), self._conv(), self.INTACT)
        assert "ladder no longer ranks BEST above WORST" in pairs[0]["retires_when"]

    def test_an_over_cap_member_appears_on_neither_leg(self):
        """It cannot be bought (already past its risk cap) and selling it is trim_risk_cap's
        job, not a rotation's. The rest of the cluster still rotates around it."""
        from test_smith_math_triggers import _conv_row
        conv = self._conv(WORST=_conv_row(3000.0, "C", rel_pp=9.0, over_cap=True))
        pairs = self._run(_ladder("high"), conv, self.INTACT)
        assert pairs and "WORST" not in (pairs[0]["sell_leg"]["ticker"],
                                          pairs[0]["buy_leg"]["ticker"])

    def test_a_cluster_with_only_one_eligible_member_produces_nothing(self):
        from test_smith_math_triggers import _conv_row
        conv = self._conv(WORST=_conv_row(3000.0, "C", rel_pp=9.0, over_cap=True),
                          MID=_conv_row(1000.0, "C", rel_pp=0.0, over_cap=True))
        assert self._run(_ladder("high"), conv, self.INTACT) == []

    def test_the_pair_id_shape_is_unchanged_so_paired_retirement_still_works(self):
        """_retire_orphaned_rotation_legs keys off this prefix; without it, 19 of 19 earlier
        rotation pairs died half-open."""
        pairs = self._run(_ladder("high"), self._conv(), self.INTACT)
        assert pairs[0]["pair_id"] == "cluster_rotation-WORST-BEST"

    def test_the_largest_bottom_third_position_is_sold_not_merely_the_last_rank(self):
        """With ten names the difference between rank 9 and 10 is inside the agent's own
        resolution; dead money costs most where the position is biggest."""
        from test_smith_math_triggers import _conv_row
        order = tuple(f"N{i}" for i in range(9))
        conv = {t: _conv_row(100.0, "C", rel_pp=0.0) for t in order}
        conv["N6"] = _conv_row(9000.0, "C", rel_pp=0.0)     # bottom third, much the largest
        thesis = {t: "x|intact" for t in order}
        thesis["N0"] = "x|strengthening"
        pairs = self._run(_ladder("high", order=order), conv, thesis)
        assert pairs[0]["sell_leg"]["ticker"] == "N6"
        assert pairs[0]["buy_leg"]["ticker"] == "N0"

    def test_a_ladder_naming_only_unheld_names_falls_back(self):
        pairs = self._run(_ladder("high", order=("GHOST1", "GHOST2", "GHOST3")),
                          self._conv(), self.PRICE_RULE)
        assert pairs and pairs[0]["ladder_driven"] is False

    def test_provenance_is_recorded_on_every_pair(self):
        pairs = self._run(_ladder("high"), self._conv(), self.INTACT)
        p = pairs[0]
        assert p["ladder_as_of"] == "2026-09-06" and p["ladder_confidence"] == "high"
        assert p["ladder_authority"] == "full" and p["ladder_authority_reasons"]


# ---------------------------------------------------------------------------
# PHASE 4 -- the two SHADOW triggers
# ---------------------------------------------------------------------------

import smith_core                # noqa: E402


class TestPairedTriggerRegistry:
    """PAIRED_TRIGGERS exists because the pair of trigger names was written out by hand at FOUR
    sites in smith_lifecycle.py. Adding a fifth paired trigger without updating all four
    reintroduces the orphaning bug that killed 19 of 19 rotation pairs -- silently."""

    def test_both_new_paired_triggers_are_registered(self):
        assert {"cluster_bench_rotation", "cluster_consolidation"} <= smith_core.PAIRED_TRIGGERS
        assert {"profit_rotation", "cluster_rotation"} <= smith_core.PAIRED_TRIGGERS

    def test_the_prefixes_derive_from_the_set_so_they_cannot_drift(self):
        assert smith_core.PAIRED_TRIGGER_PREFIXES == tuple(
            f"{t}-" for t in sorted(smith_core.PAIRED_TRIGGERS))

    def test_every_pair_id_this_module_emits_matches_a_registered_prefix(self):
        for tt in smith_core.PAIRED_TRIGGERS:
            assert f"{tt}-SELL-BUY".startswith(smith_core.PAIRED_TRIGGER_PREFIXES)

    def test_the_new_pairs_are_shadow_voted(self):
        """A new signal class earns its vote before it gets one."""
        assert {"cluster_bench_rotation", "cluster_consolidation"} <= smith_core.SHADOW_TRIGGERS
        assert not ({"cluster_bench_rotation", "cluster_consolidation"} & smith_core.LIVE_TRIGGERS)

    def test_cluster_bench_rotation_does_not_collide_with_cluster_rotations_prefix(self):
        """`cluster_bench_rotation-X-Y` must not be mistaken for a cluster_rotation pair."""
        assert not "cluster_bench_rotation-A-B".startswith("cluster_rotation-")


class TestClusterBenchRotation:
    def _run(self, ladder, *, held_bench=False, conv=None):
        from test_smith_math_triggers import _conv_row
        conv = conv or {"BEST": _conv_row(1000.0, "C", rel_pp=0.0),
                        "WORST": _conv_row(3000.0, "C", rel_pp=0.0)}
        risk = {t: {} for t in conv}
        if held_bench:
            risk["NEWNAME"] = {}
        out = []
        smith_math._trigger_cluster_bench_rotation(
            {"C": ladder}, conv, {"BEST": "x|strengthening", "WORST": "x|intact"},
            risk, TODAY, out)
        return out

    def _bench_ladder(self, **kw):
        L = _ladder(order=("BEST", "MID", "WORST"), **kw)
        L["bench"] = [{"ticker": "NEWNAME", "price_usd": 42.0, "why_better_than": "WORST",
                       "entry_condition": "below $40"}]
        return L

    def test_it_pairs_the_ladder_laggard_with_a_bench_name(self):
        pairs = self._run(self._bench_ladder())
        assert len(pairs) == 1
        assert pairs[0]["sell_leg"]["ticker"] == "WORST"
        assert pairs[0]["buy_leg"]["ticker"] == "NEWNAME"

    def test_it_is_shadow_and_says_why(self):
        p = self._run(self._bench_ladder())[0]
        assert p["vote"] == "shadow"
        assert "never-held name" in p["buy_leg"]["blockers"][0]

    def test_the_buy_leg_is_not_sized(self):
        """A never-held name has no lot, no thesis entry and no journal history -- sizing it
        here would be the whole point of the shadow vote skipped."""
        assert self._run(self._bench_ladder())[0]["buy_leg"]["suggested_size_usd"] is None

    def test_a_bench_name_that_is_actually_held_is_skipped(self):
        """That is cluster_rotation's job, and cluster_rotation is LIVE. A bench entry naming a
        holding is a stale ladder, not an idea."""
        assert self._run(self._bench_ladder(), held_bench=True) == []

    def test_no_bench_produces_nothing(self):
        assert self._run(_ladder()) == []

    def test_it_requires_the_same_ladder_authority_a_live_rotation_does(self):
        assert self._run(self._bench_ladder(confidence="low")) == []
        assert self._run(self._bench_ladder(as_of="2026-01-01")) == []

    def test_the_sell_leg_is_not_relaxed_just_because_the_vote_is_shadow(self):
        """The shadow-ness is entirely about the buy. At `medium` the sell leg still needs a
        watch thesis, and WORST here is only `intact`."""
        assert self._run(self._bench_ladder(confidence="medium")) == []

    def test_the_entry_condition_travels_with_the_proposal(self):
        p = self._run(self._bench_ladder())[0]
        assert any("below $40" in r for r in p["buy_leg"]["reasons"])


class TestClusterConsolidation:
    def _run(self, pairs_in, *, over_cap_keep=False):
        from test_smith_math_triggers import _conv_row
        conv = {"KEEP": _conv_row(1000.0, "C", rel_pp=0.0, over_cap=over_cap_keep),
                "DROP": _conv_row(2500.0, "C", rel_pp=0.0),
                "OTHER": _conv_row(500.0, "C", rel_pp=0.0)}
        L = _ladder(order=("KEEP", "DROP", "OTHER"))
        L["redundant_pairs"] = pairs_in
        out = []
        smith_math._trigger_cluster_consolidation({"C": L}, conv, {t: {} for t in conv},
                                                  TODAY, out)
        return out

    REDUNDANT = [{"pair": ["KEEP", "DROP"], "verdict": "redundant", "keep": "KEEP",
                  "drop": "DROP", "same_bet_because": "same customer, same process step"}]

    def test_it_collapses_the_drop_side_into_the_keep_side(self):
        p = self._run(self.REDUNDANT)[0]
        assert p["sell_leg"]["ticker"] == "DROP" and p["buy_leg"]["ticker"] == "KEEP"
        assert p["vote"] == "shadow"

    def test_it_sells_the_whole_position_because_the_exposure_is_kept(self):
        """This is the only rotation here that does not change factor exposure at all -- it
        shortens the tail. A partial sale would leave the redundancy in place."""
        p = self._run(self.REDUNDANT)[0]
        assert p["sell_leg"]["suggested_size_usd"] == 2500.0
        assert p["buy_leg"]["suggested_size_usd"] == 2500.0

    def test_a_distinct_verdict_produces_nothing(self):
        """A candidate the agent looked at and called distinct is a judgment already made."""
        assert self._run([dict(self.REDUNDANT[0], verdict="distinct")]) == []

    def test_an_unjudged_candidate_produces_nothing(self):
        """cmd_ladder's screen is a resemblance, never a cause. Only the agent's explicit
        `redundant` verdict acts."""
        assert self._run([{"pair": ["KEEP", "DROP"]}]) == []

    def test_the_drop_side_is_inferred_only_for_a_two_name_pair(self):
        assert self._run([{"pair": ["KEEP", "DROP"], "verdict": "redundant",
                           "keep": "KEEP"}])[0]["sell_leg"]["ticker"] == "DROP"
        # Guessing which of three to sell is not a gap worth filling silently.
        assert self._run([{"pair": ["KEEP", "DROP", "OTHER"], "verdict": "redundant",
                           "keep": "KEEP"}]) == []

    def test_it_will_not_add_to_a_name_already_past_its_risk_cap(self):
        assert self._run(self.REDUNDANT, over_cap_keep=True) == []

    def test_an_unheld_side_produces_nothing(self):
        assert self._run([{"pair": ["KEEP", "GHOST"], "verdict": "redundant",
                           "keep": "KEEP", "drop": "GHOST"}]) == []

    def test_it_requires_ladder_authority(self):
        from test_smith_math_triggers import _conv_row
        conv = {"KEEP": _conv_row(1000.0, "C", rel_pp=0.0), "DROP": _conv_row(2500.0, "C", rel_pp=0.0)}
        L = _ladder(confidence="low")
        L["redundant_pairs"] = self.REDUNDANT
        out = []
        smith_math._trigger_cluster_consolidation({"C": L}, conv, {t: {} for t in conv},
                                                  TODAY, out)
        assert out == []

import copy, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import smith_memory as M
import smith_perf as P

BASE = {"mandate": {"risk_budget_pct": 25}, "drawdown_risk_off_pct": 20,
        "stop_loss_framework": {"aggregate_open_risk_cap_pct_of_book": 10},
        "drawdown_trim_ladder": [{"drawdown_pct": -15, "aggregate_cap_pct": 8},
                                 {"drawdown_pct": -20, "aggregate_cap_pct": 0}],
        "stress_limit": {"shock_pct": -35, "max_loss_pct_of_book": 20}, "target_position_count": [15, 20]}


def test_envelope_ok_and_each_incoherence_is_caught():
    assert M.validate_risk_envelope(BASE) == []
    bad = copy.deepcopy(BASE); bad["drawdown_risk_off_pct"] = 25
    assert any("risk-off" in x for x in M.validate_risk_envelope(bad))
    bad = copy.deepcopy(BASE); bad["drawdown_trim_ladder"][0]["aggregate_cap_pct"] = 12
    assert any("raises the aggregate cap" in x for x in M.validate_risk_envelope(bad))
    bad = copy.deepcopy(BASE); bad["stress_limit"]["max_loss_pct_of_book"] = 30
    assert any("stress_limit" in x for x in M.validate_risk_envelope(bad))
    bad = copy.deepcopy(BASE); bad["target_position_count"] = [20, 15]
    assert any("target_position_count" in x for x in M.validate_risk_envelope(bad))


def test_owner_hash_detects_owner_edits_but_not_desk_edits():
    pol = dict(BASE, governance={"confirmed_on": "d"}, cluster_targets={"A": {"target_pct": 5}})
    pol["governance"]["owner_layer_hash"] = M.owner_hash(pol)
    assert M.validate_governance(pol) == []
    pol["cluster_targets"]["A"]["target_pct"] = 9            # desk layer: free
    assert M.validate_governance(pol) == []
    pol["drawdown_risk_off_pct"] = 22                         # owner layer: flagged
    assert any("owner-layer policy changed" in x for x in M.validate_governance(pol))


def _series(n, ret, start="2026-01-01"):
    import datetime as d
    t = d.date.fromisoformat(start)
    return [{"d": str(t + d.timedelta(days=i)), "value_usd": 20000.0, "ret": ret} for i in range(n)]


def test_objective_check_needs_history_then_flags(monkeypatch):
    pol = {"mandate": {"evaluation": {"window_months": 12, "underperformance_tolerance_pp": 10, "min_sessions": 50}}}
    assert P.objective_check(_series(10, 0.0), {}, "SMH", pol, "2026-06-01", 10000)["status"] == "insufficient_history"
    assert P.objective_check([], {}, "SMH", {}, "2026-06-01", 1)["status"] == "not_configured"
    monkeypatch.setattr(P, "chain", lambda s, b, bench=None: {"twr_pct": 5.0, "benchmark_pct": 30.0, "excess_pp": -25.0})
    r = P.objective_check(_series(120, 0.0), {}, "SMH", pol, "2026-06-01", 10000)
    assert r["status"] == "review_flag" and "never a trade" in r["action"]
    monkeypatch.setattr(P, "chain", lambda s, b, bench=None: {"twr_pct": 5.0, "benchmark_pct": 8.0, "excess_pp": -3.0})
    assert P.objective_check(_series(120, 0.0), {}, "SMH", pol, "2026-06-01", 10000)["status"] == "within_tolerance"


def test_gap_multiplier_tiers_and_off_switch():
    import smith_risk as R
    cfg = {"base": 1.15, "event": 1.5, "event_window_sessions": 5}
    assert R.gap_multiplier(None, None) == (1.0, None)
    assert R.gap_multiplier(30, cfg) == (1.15, None)
    assert R.gap_multiplier(None, cfg) == (1.15, None)
    assert R.gap_multiplier(3, cfg)[0] == 1.5 and R.gap_multiplier(7, cfg)[0] == 1.5
    assert R.gap_multiplier(8, cfg)[0] == 1.15 and R.gap_multiplier(-1, cfg)[0] == 1.15


def test_gap_allowance_validation():
    bad = copy.deepcopy(BASE); bad["stop_loss_framework"]["gap_allowance"] = {"base": 1.3, "event": 1.1}
    assert any("gap_allowance" in x for x in M.validate_risk_envelope(bad))


def test_accepted_card_retires_only_with_explicit_flag():
    import smith_lifecycle as L
    props = [{"id": "P-1", "status": "accepted_by_user"}]
    assert L.dismiss_proposal_core(props, "P-1", "r") is None and props[0]["status"] == "accepted_by_user"
    assert L.dismiss_proposal_core(props, "P-1", "r", actor="user", allow_accepted=True)["status"] == "dismissed_by_user"


def test_sub_floor_single_leg_buy_is_demoted_but_shadow_and_unfunded_are_not():
    import smith_math as SM, smith_ticket as T
    sizing = T.sizing_context(42000.0, {}, {"CIEN": 8.0})
    live = {"ticker": "CIEN", "vote": "live", "suggested_size_usd": 100.0}
    SM._apply_buy_materiality(live, sizing)
    assert live["vote"] == "below_materiality" and live["materiality_shortfall_usd"] > 0
    shadow = {"ticker": "CIEN", "vote": "shadow", "suggested_size_usd": 100.0}
    SM._apply_buy_materiality(shadow, sizing)
    assert shadow["vote"] == "shadow"
    unfunded = {"ticker": "CIEN", "vote": "live", "suggested_size_usd": 0}
    SM._apply_buy_materiality(unfunded, sizing)
    assert unfunded["vote"] == "live"
    big = {"ticker": "CIEN", "vote": "live", "suggested_size_usd": 5000.0}
    SM._apply_buy_materiality(big, sizing)
    assert big["vote"] == "live"


def test_consolidation_ranks_lowest_conviction_sub_scale_names_only_when_over_target():
    import smith_ticket as T
    pol = {"target_position_count": [2, 3], "trade_materiality": {"min_position_pct_of_book": 2.0}}
    pos = [{"ticker": t, "market_value_usd": mv, "cluster": "c"} for t, mv in
           (("A", 5000.0), ("B", 300.0), ("C", 200.0), ("D", 100.0), ("E", 4000.0))]
    conv = {"B": {"conviction_score": 30}, "C": {"conviction_score": 5}, "D": {"conviction_score": 50}}
    b = T.consolidation_candidates(pos, conv, {}, 10000.0, pol)
    assert b["min_position_usd"] == 400.0 and b["excess_over_target"] == 2
    assert [c["ticker"] for c in b["candidates"]] == ["C", "B"]            # lowest conviction first, capped at the excess
    assert {r["ticker"] for r in b["sub_scale"]} == {"B", "C", "D"}
    ok = T.consolidation_candidates(pos[:3], conv, {}, 10000.0, dict(pol, target_position_count=[2, 5]))
    assert ok["candidates"] == [] and ok["excess_over_target"] == 0
    assert T.min_position_effective_usd(10000.0, {}) == 400.0


def test_superseded_dust_flag_closes_only_on_a_measured_real_position():
    import datetime
    flag = {"ticker": "TER", "opened": "2026-08-19", "kind": "user_decision",
            "flag": "DUST POSITION -- 0.00273sh / ~$1.10 after the stop"}
    other = {"ticker": "CIEN", "opened": "2026-09-01", "kind": "user_decision", "flag": "DUST POSITION -- tiny"}
    unrelated = {"ticker": "TER", "opened": "2026-09-01", "kind": "user_decision", "flag": "Something else about TER"}
    st = {"open_flags": [dict(flag), dict(other), dict(unrelated)]}
    moves, writes = [], {}
    M._compact_flags_and_notes(st, {"TER", "CIEN"}, datetime.date(2026, 9, 21), "/nonexistent", moves, writes,
                               {"TER": 1852.96, "CIEN": 2.98})
    kept = {f["ticker"] + f["flag"][:4] for f in st["open_flags"]}
    assert kept == {"CIENDUST", "TERSome"}                        # TER dust closed; CIEN (still dust) and the non-dust flag stay
    # with no measured values nothing is closed
    st2 = {"open_flags": [dict(flag)]}
    M._compact_flags_and_notes(st2, {"TER"}, datetime.date(2026, 9, 21), "/nonexistent", [], {}, None)
    assert len(st2["open_flags"]) == 1

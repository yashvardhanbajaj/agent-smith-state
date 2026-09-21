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

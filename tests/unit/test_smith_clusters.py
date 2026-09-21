import copy, os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import smith_clusters as C

POLICY = {"cluster_targets": {"A": {"target_pct": 10, "band_pct": [5, 15]}}, "ai_capex_clusters": ["A"],
          "cluster_playbooks": {"A": {"slug": "a", "differentiators": ["x", "y", "z"]}}}


def test_overlay_does_not_mutate_and_marks_source():
    st, pol = {"sector_map": {"T": "A"}}, copy.deepcopy(POLICY)
    out = C.overlay(pol, st)
    assert pol == POLICY and out["cluster_targets"]["A"]["source"] == "policy"


def test_desk_target_overrides_seed_and_new_cluster_is_created():
    st = {"sector_map": {"WDC": "Storage"}}
    C.set_cluster(st, "A", "2026-09-21", "trim", target_pct=6)
    C.set_cluster(st, "Storage", "2026-09-21", "new group", target_pct=3, ai_capex=True)
    out = C.overlay(POLICY, st)
    assert out["cluster_targets"]["A"]["target_pct"] == 6 and out["cluster_targets"]["A"]["source"] == "desk"
    assert out["cluster_targets"]["Storage"]["band_pct"] == [0.0, 6.0]
    assert "Storage" in out["ai_capex_clusters"]
    assert out["cluster_playbooks"]["Storage"]["generated"] is True      # no playbook needed


def test_remove_target_makes_it_exposure_only_and_reversible():
    st = {}
    C.set_cluster(st, "A", "2026-09-21", "not needed", remove_target=True, ai_capex=False)
    out = C.overlay(POLICY, st)
    assert "A" not in out["cluster_targets"] and "A" not in out["ai_capex_clusters"]
    C.set_cluster(st, "A", "2026-09-22", "back", target_pct=8)
    assert C.overlay(POLICY, st)["cluster_targets"]["A"]["target_pct"] == 8
    assert len(st["cluster_book"]["A"]["history"]) == 2


def test_validation_and_rationale_required():
    st = {}
    with pytest.raises(ValueError):
        C.set_cluster(st, "A", "d", "")
    with pytest.raises(ValueError):
        C.set_cluster(st, "A", "d", "r", target_pct=20, band_pct=[1, 5])
    with pytest.raises(ValueError):
        C.assign_ticker(st, "X", "A", "d", " ")


def test_assign_ticker_logs_and_creates_group():
    st = {"sector_map": {"WDC": "Memory"}}
    assert C.assign_ticker(st, "WDC", "HDD", "2026-09-21", "pure HDD") == "Memory"
    assert st["sector_map"]["WDC"] == "HDD" and st["cluster_assignments_log"][0]["to"] == "HDD"
    assert C.exposure(st["sector_map"], {"WDC": 3.0, "Q": 1.0})["HDD"]["weight_pct"] == 3.0


def test_fluid_mode_relaxes_fence_checks():
    import smith_memory as M
    pol = dict(POLICY, cluster_target_denominator="invested_equity", cluster_targets_mode="fluid")
    st = {"sector_map": {"T": "Brand New"}, "holdings": [{"ticker": "T"}]}
    d = M.validate_policy(C.overlay(pol, st), st)
    assert not any("sum to" in x or "absent from cluster_targets" in x for x in d)
    fence = dict(pol); fence.pop("cluster_targets_mode")
    assert any("sum to" in x for x in M.validate_policy(C.overlay(fence, st), st))

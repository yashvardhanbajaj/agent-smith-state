"""Scorecard honesty (Phase 0 of the proposal-engine rebuild, 2026-09-20).

cmd_score's docstring said superseded restatements are excluded so "one idea counts once"; the
code scored them: 58 of 88 scored rows were superseded and the 88 rows were 43 distinct ideas.
These tests pin the corrected denominator, the reachable benchmark, the alpha-relative HOLD rule,
and the shrink guard that must stay armed.
"""
import json
import types

import pytest

import smith_lifecycle as sl

TODAY = "2026-09-20"


def prop(pid, ticker="QCOM", action="Buy QCOM", direction="BUY", status="auto_retired",
         date="2026-08-05", p0=100.0, b0=500.0, **kw):
    d = {"id": pid, "ticker": ticker, "action": action, "direction_bucket": direction,
         "status": status, "date": date, "price_at_proposal": p0,
         "trigger_type": "conviction_average", "size_usd": 500.0}
    if b0 is not None:
        d["benchmark_price_at_proposal"] = b0
        d["benchmark_ticker"] = "SMH"
    d.update(kw)
    return d


def run_score(tmp_path, capsys, props, prices, run_dir=None, mi=None, rebase=False, scorecard=None):
    (tmp_path / "proposals.json").write_text(json.dumps(
        {"proposals": props, "scorecard": scorecard or {}}))
    pj = tmp_path / "prices.json"
    pj.write_text(json.dumps(prices))
    if mi is not None:
        rd = tmp_path / "run"
        rd.mkdir()
        (rd / "market_inputs.json").write_text(json.dumps(mi))
        run_dir = str(rd)
    args = types.SimpleNamespace(base_dir=str(tmp_path), prices_json=str(pj), today=TODAY,
                                 dry_run=True, run_dir=run_dir, rebase_scorecard=rebase)
    sl.cmd_score(args)
    return json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def test_one_idea_restated_four_times_is_one_idea_four_rows(tmp_path, capsys):
    # three superseded restatements would be scored before the fix; the 4 rows here are all
    # scoreable statuses so n_rows is 4 while the idea key collapses them to one
    props = [prop(f"P-{i}", status="auto_retired") for i in range(4)]
    out = run_score(tmp_path, capsys, props, {"QCOM": 110.0, "SMH": 550.0})
    sc = out["scorecard"]
    assert sc["n_rows"] == 4 and sc["n_ideas"] == 1
    assert sc["by_direction"]["BUY"]["n_rows"] == 4
    assert sc["by_direction"]["BUY"]["n_ideas"] == 1


def test_superseded_row_is_not_scored(tmp_path, capsys):
    props = [prop("P-1", status="superseded"), prop("P-2", ticker="MU", action="Buy MU")]
    out = run_score(tmp_path, capsys, props, {"QCOM": 110.0, "MU": 110.0, "SMH": 550.0})
    assert [r["id"] for r in out["rows"]] == ["P-2"]
    assert "outcome_verdict" not in props[0]


def test_absent_benchmark_price_is_named_in_needs_prices(tmp_path, capsys):
    out = run_score(tmp_path, capsys, [prop("P-1")], {"QCOM": 110.0})
    assert "SMH" in out["needs_prices"]
    row = out["rows"][0]
    assert row["scored_vs"] == "absolute (benchmark price not supplied)"
    assert any("benchmark price not supplied" in m for m in out["data_quality"])


def test_missing_anchor_is_a_different_diagnostic(tmp_path, capsys):
    out = run_score(tmp_path, capsys, [prop("P-1", b0=None)], {"QCOM": 110.0, "SMH": 550.0})
    assert out["rows"][0]["scored_vs"] == "absolute (no anchor)"
    assert "SMH" not in out["needs_prices"]


def test_benchmark_is_sourced_from_market_inputs_when_run_dir_given(tmp_path, capsys):
    out = run_score(tmp_path, capsys, [prop("P-1")], {"QCOM": 110.0}, mi={"smh": 550.0})
    row = out["rows"][0]
    assert row["scored_vs"] == "alpha vs SMH"
    assert row["benchmark_move_pct"] == 10.0
    assert out["needs_prices"] == []
    assert out["scorecard"]["alpha_scored_count"] == 1


def test_hold_that_moved_8pct_but_beat_its_benchmark_worked(tmp_path, capsys):
    # +8% would have MISSED under |move| < 2%; benchmark fell 5%, so the name beat it by 13pp
    p = prop("P-1", ticker="MU", action="Hold MU", direction="HOLD", b0=600.0)
    out = run_score(tmp_path, capsys, [p], {"MU": 108.0, "SMH": 570.0})
    assert out["rows"][0]["verdict"] == "worked"
    assert out["rows"][0]["scored_vs"].startswith("alpha vs SMH")


def test_hold_that_lagged_its_benchmark_missed_and_no_benchmark_is_unscoreable(tmp_path, capsys):
    lag = prop("P-1", ticker="MU", action="Hold MU", direction="HOLD", b0=600.0)
    out = run_score(tmp_path, capsys, [lag], {"MU": 100.0, "SMH": 660.0})
    assert out["rows"][0]["verdict"] == "missed"
    noanchor = prop("P-2", ticker="MU", action="Hold MU", direction="HOLD", b0=None)
    out = run_score(tmp_path, capsys, [noanchor], {"MU": 100.0, "SMH": 660.0})
    assert out["rows"][0]["verdict"] == "unscoreable"
    assert out["scorecard"]["n_rows"] == 0            # not graded, not counted


def test_hold_is_excluded_from_the_headline(tmp_path, capsys):
    props = [prop("P-1"), prop("P-2", ticker="MU", action="Hold MU", direction="HOLD", b0=600.0)]
    out = run_score(tmp_path, capsys, props, {"QCOM": 110.0, "MU": 108.0, "SMH": 570.0})
    sc = out["scorecard"]
    assert sc["overall"]["n"] == 1 and sc["by_direction"]["HOLD"]["n"] == 1
    assert sc["n_rows"] == 2


def test_shrink_guard_still_refuses_without_the_flag_and_rebase_records_why(tmp_path, capsys):
    props = [prop("P-1"), prop("P-2", ticker="MU", action="Buy MU", status="superseded",
                               outcome_verdict="missed")]
    prices = {"QCOM": 110.0, "MU": 110.0, "SMH": 550.0}
    out = run_score(tmp_path, capsys, props, prices, scorecard={"scored_count": 2})
    assert out.get("refused") is True

    props = [prop("P-1"), prop("P-2", ticker="MU", action="Buy MU", status="superseded",
                               outcome_verdict="missed")]
    out = run_score(tmp_path, capsys, props, prices, scorecard={"scored_count": 2}, rebase=True)
    assert not out.get("refused")
    assert out["scorecard"]["rebase"]["from_scored_count"] == 2
    assert any("SCORECARD REBASED 2 -> 1" in m for m in out["data_quality"])


def test_rebase_does_not_excuse_missing_prices(tmp_path, capsys):
    # the drop is from a missing price, not a definitional change: still refused
    props = [prop("P-1"), prop("P-2", ticker="MU", action="Buy MU")]
    out = run_score(tmp_path, capsys, props, {"QCOM": 110.0, "SMH": 550.0},
                    scorecard={"scored_count": 2}, rebase=True)
    assert out.get("refused") is True and "MU" in out["needs_prices"]


def test_idea_key_buckets_by_month():
    a = sl.idea_key(prop("P-1", date="2026-08-05"))
    assert a == sl.idea_key(prop("P-2", date="2026-08-29"))
    assert a != sl.idea_key(prop("P-3", date="2026-09-01"))


def test_worst_bullish_bucket_is_chosen_not_the_first():
    import smith_math as sm
    hr = {"GOOD": {"n": 3, "hit_rate_pct": 66.7, "payoff_ratio": 8.1},
          "BAD": {"n": 15, "hit_rate_pct": 20.0, "payoff_ratio": 1.2}}
    tr = sm.worst_bullish_track_record(["GOOD", "BAD"], hr, {})
    assert tr["hit_rate_pct"] == 20.0 and tr["interim"] is False
    assert sm.worst_bullish_track_record(["BAD", "GOOD"], hr, {}) == tr
    assert sm.worst_bullish_track_record(["X"], {}, {}) is None


def test_readiness_counter_excludes_ungraded_and_superseded(tmp_path):
    import smith_learning
    props = [{"id": "P-1", "outcome_verdict": "worked"},
             {"id": "P-2", "outcome_verdict": "needs_anchor_review"},
             {"id": "P-3", "outcome_verdict": "unscoreable"},
             {"id": "P-4", "outcome_verdict": "missed", "status": "superseded"},
             {"id": "P-5", "outcome_verdict": "missed"}]
    (tmp_path / "proposals.json").write_text(json.dumps({"proposals": props}))
    c = smith_learning.scored_proposal_counts(str(tmp_path))
    assert c["scored"] == 2 and c["decided"] == 2

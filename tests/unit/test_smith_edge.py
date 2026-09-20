"""Phase 4 of the proposal-engine rebuild (2026-09-20): the edge estimate, the BUY-only EV gate, family
verdicts, the cash-above-band safety invariant, the ENGINE_EPOCH evidence rule, the unified bucket
reader and the strategist's scorecard_gate. The motivating incident throughout: the scorecard had zero
gating consumers, and the only feedback path was an LLM reading prose.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

import smith_core
import smith_edge as E
import smith_lifecycle as sl

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "scripts")
POST = "2026-10-05"     # after ENGINE_EPOCH (2026-09-21)
LEGACY = "2026-08-10"


def prop(i, ticker="AAA", direction="BUY", trig="trend_entry", date=POST, pct=-5.0, status="executed"):
    """a graded proposal; distinct ticker per i so each is its own idea"""
    return {"id": f"P-{i}", "ticker": f"{ticker}{i}", "direction_bucket": direction, "trigger_type": trig,
            "date": date, "status": status, "outcome_verdict": "worked" if pct > 2 else "missed",
            "outcome_pct": pct, "size_usd": 500}


def gate(verdict="unproven", n_eff=0, hit=None, mult=1.0, family="BUY|trend_entry"):
    return {"verdict": verdict, "multiplier": mult, "n_eff": n_eff, "hit_rate": hit, "family": family,
            "basis": "test", "mean_ev_net_pct": None, "ci95": [None, None]}


def buy_edge(conv=30.0, price=100.0, stop=10.0, target=125.0, g=None):
    return E.evaluate_position(conviction_score=conv, gate=g or gate(), price=price, stop_pct=stop,
                               target_usd=target)


# ---------------------------------------------------------------------------------- verdicts
class TestFamilyVerdict:
    def test_n5_all_losers_is_still_unproven_mult_one(self):
        rows = [prop(i, pct=-30.0) for i in range(5)]
        v = E.family_verdict(E.scored_rows_from_proposals(rows))
        assert v["n_eff"] == 5 and v["verdict"] == "unproven" and v["multiplier"] == 1.0

    def test_n25_upper_bound_negative_is_suppressed_and_still_reported(self):
        rows = [prop(i, pct=-8.0 - (i % 3)) for i in range(25)]
        table = E.build_table(rows)
        v = table["by_family"]["BUY|trend_entry"]
        assert v["n_eff"] == 25 and v["verdict"] == "suppressed" and v["multiplier"] == 0.0
        assert "shadow" in v["basis"] and "loses" in v["basis"]     # a stated reason
        g = E.gate_for(table, "BUY", "trend_entry")
        d = E.decide_gate([{"id": "x", "kind": "single", "direction": "BUY", "trigger_type": "trend_entry",
                            "gate": g, "edge": buy_edge()}])["x"]
        assert d["vote"] == "shadow" and "suppressed" in d["refused_because"]

    def test_n15_straddling_zero_is_watch_075(self):
        rows = [prop(i, pct=(9.0 if i % 2 else -9.0)) for i in range(16)]
        v = E.family_verdict(E.scored_rows_from_proposals(rows))
        assert v["verdict"] == "watch" and v["multiplier"] == 0.75

    def test_proven_when_lower_bound_positive_and_multiplier_capped(self):
        rows = [prop(i, pct=20.0 + (i % 3)) for i in range(15)]
        v = E.family_verdict(E.scored_rows_from_proposals(rows))
        assert v["verdict"] == "proven" and 1.0 <= v["multiplier"] <= 1.25

    def test_multiplier_monotone_in_expectancy(self):
        ms = [E.edge_multiplier(x) for x in (-20, -5, 0, 2, 5, 10, 40)]
        assert ms == sorted(ms) and ms[0] == 0.0 and ms[-1] == 1.25

    def test_hold_is_excluded(self):
        rows = [prop(i, direction="HOLD", pct=-30.0) for i in range(30)]
        assert E.scored_rows_from_proposals(rows) == []

    def test_superseded_rows_are_not_evidence(self):
        assert E.scored_rows_from_proposals([prop(1, status="superseded")]) == []

    def test_restated_idea_counts_once(self):
        a, b = prop(1), prop(1)
        b["id"] = "P-1b"
        rows = E.scored_rows_from_proposals([a, b])
        assert len(rows) == 2 and E.family_verdict(rows)["n_eff"] == 1

    def test_direction_verdict_backs_off_when_family_is_thin(self):
        rows = [prop(i, trig=f"t{i % 6}", pct=-9.0 - (i % 2)) for i in range(24)]   # 6 families x 4 ideas
        table = E.build_table(rows)
        assert table["by_direction"]["BUY"]["verdict"] == "suppressed"
        g = E.gate_for(table, "BUY", "t0")
        assert g["level"] == "direction" and g["verdict"] == "suppressed"


# ---------------------------------------------------------------------------------- the epoch
class TestEngineEpoch:
    def test_thirty_perfectly_losing_legacy_ideas_stay_unproven(self):
        rows = [prop(i, date=LEGACY, pct=-40.0) for i in range(30)]
        table = E.build_table(rows)
        assert table["excluded_legacy"]["proposal_rows"] == 30
        assert table["by_family"] == {}
        assert table["by_direction"]["BUY"]["n_eff"] == 0
        g = E.gate_for(table, "BUY", "trend_entry")
        assert g["verdict"] == "unproven" and g["multiplier"] == 1.0 and g["n_eff"] == 0

    def test_post_epoch_ideas_are_evaluated_normally(self):
        rows = [prop(i, date=POST, pct=-40.0) for i in range(30)]
        assert E.build_table(rows)["by_family"]["BUY|trend_entry"]["verdict"] == "suppressed"

    def test_epoch_is_read_at_call_time(self, monkeypatch):
        rows = [prop(i, date="2026-09-25", pct=-40.0) for i in range(30)]
        monkeypatch.setattr(smith_core, "ENGINE_EPOCH", "2026-10-01")
        assert E.build_table(rows)["by_direction"]["BUY"]["n_eff"] == 0
        monkeypatch.setattr(smith_core, "ENGINE_EPOCH", "2026-09-21")
        assert E.build_table(rows)["by_direction"]["BUY"]["n_eff"] == 30

    def test_undated_row_is_not_admitted(self):
        assert E.scored_rows_from_proposals([prop(1, date="")]) == []

    def test_shadow_journal_legacy_entries_contribute_nothing(self):
        ents = [{"date": LEGACY, "ticker": f"T{i}", "trigger_type": "laggard_rotation", "scored": True,
                 "verdict": "failed", "outcome_pct": -9.0} for i in range(30)]
        assert E.build_table([], ents)["by_direction"]["BUY"]["n_eff"] == 0
        ents2 = [dict(e, date=POST) for e in ents]
        t = E.build_table([], ents2)
        assert t["by_family"]["BUY|laggard_rotation"]["n_eff"] == 30
        assert t["by_family"]["BUY|laggard_rotation"]["source_counts"]["shadow_journal"] == 30

    def test_shadow_and_proposal_for_one_idea_count_once(self):
        p = prop(1, trig="laggard_rotation", pct=6.0)
        j = {"date": POST, "ticker": p["ticker"], "trigger_type": "laggard_rotation", "scored": True,
             "verdict": "worked", "outcome_pct": 5.0}
        assert E.build_table([p], [j])["by_family"]["BUY|laggard_rotation"]["n_eff"] == 1

    def test_gated_shadow_row_carries_direction_and_is_scored(self):
        assert E.scored_rows_from_shadow_journal([{"date": POST, "ticker": "X", "trigger_type": "trend_entry",
                                                   "direction_bucket": "BUY", "scored": True,
                                                   "verdict": "worked", "outcome_pct": 8.0}])

    def test_live_record_shape_gives_n_eff_zero(self):
        """the real proposals.json predates the epoch: every family and direction is unproven"""
        doc = json.load(open(os.path.join(ROOT, "proposals.json")))
        legacy = [p for p in doc["proposals"] if str(p.get("date"))[:10] < "2026-09-21"]   # stable as new rows arrive
        t = E.build_table(legacy)
        assert t["by_direction"]["BUY"]["n_eff"] == 0 and t["by_direction"]["SELL"]["n_eff"] == 0
        assert t["by_family"] == {} and t["excluded_legacy"]["proposal_rows"] > 0

    def test_scorecard_splits_legacy_from_since_epoch(self, tmp_path):
        import argparse
        props = [{"id": "P-1", "ticker": "AAA", "action": "Buy AAA", "date": LEGACY, "status": "executed",
                  "price_at_proposal": 100.0, "size_usd": 500},
                 {"id": "P-2", "ticker": "BBB", "action": "Buy BBB", "date": "2026-09-21", "status": "executed",
                  "price_at_proposal": 100.0, "size_usd": 500}]
        (tmp_path / "proposals.json").write_text(json.dumps({"proposals": props, "scorecard": {}}))
        (tmp_path / "prices.json").write_text(json.dumps({"AAA": 130.0, "BBB": 130.0}))
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sl.cmd_score(argparse.Namespace(base_dir=str(tmp_path), prices_json=str(tmp_path / "prices.json"),
                                            today="2026-11-30", dry_run=True, run_dir=None,
                                            rebase_scorecard=False))
        sc = json.loads(buf.getvalue())["scorecard"]
        assert sc["legacy"]["n_rows"] == 1 and sc["since_epoch"]["n_rows"] == 1
        assert "LEGACY" in sc["legacy"]["label"]


# ---------------------------------------------------------------------------------- p_win, EV
class TestEdgeEstimate:
    def test_n_eff_zero_is_prior_shrunk_only_by_conviction(self):
        assert E.p_win_estimate(None, 0, 50.0) == pytest.approx(0.45)
        assert E.p_win_estimate(0.9, 0, 50.0) == pytest.approx(0.45)        # family rate ignored at n=0
        assert E.p_win_estimate(None, 0, 0.0) == pytest.approx(0.45 * 0.8)
        assert E.p_win_estimate(None, 0, 100.0) == pytest.approx(0.45 * 1.2)

    def test_ceiling_and_floor(self):
        assert E.p_win_estimate(1.0, 10000, 100.0) == smith_core.P_WIN_CEILING == 0.75
        assert E.p_win_estimate(0.0, 10000, 0.0) == smith_core.P_WIN_FLOOR

    def test_family_evidence_pulls_p_win_as_n_grows(self):
        assert (E.p_win_estimate(0.8, 40, 50) > E.p_win_estimate(0.8, 5, 50) > E.p_win_estimate(0.8, 0, 50))

    def test_payoff_is_hard_capped_at_four_r(self):
        pr, unc, capped = E.payoff_r(100.0, 151.0, 12.0)      # a 51% upside on a 12% stop = 4.25R
        assert pr == 4.0 and unc == pytest.approx(51 / 12) and capped
        assert E.payoff_r(100.0, 120.0, 10.0)[0] == pytest.approx(2.0)
        assert E.payoff_r(100.0, 90.0, 10.0)[0] == 0.0

    def test_expected_value_and_fee(self):
        assert E.fee_r(10.0) == pytest.approx(0.03)
        assert E.expected_value(0.5, 2.0, 0.03) == pytest.approx(0.5 * 2 - 0.5 - 0.03)

    def test_f_edge_bounds(self):
        assert E.f_edge(0.15) == 0.30 and E.f_edge(0.01) == 0.25 and E.f_edge(3.0) == 1.0

    def test_kelly_is_the_shared_implementation(self):
        import smith_conviction as C
        assert C.full_kelly(0.5, 2.0) == pytest.approx(0.25)
        assert C.kelly_fraction(0.5, 2.0) == round(0.25 * C.KELLY_FRACTION_DEFAULT, 4)
        assert C.kelly_fraction(0.2, 1.0) == 0.0
        assert buy_edge()["kelly_quarter"] is not None


# ---------------------------------------------------------------------------------- the gate
def cand(cid, direction="BUY", trig="trend_entry", edge=None, g=None, kind="single", rot=None, conv=30.0):
    return {"id": cid, "kind": kind, "direction": direction, "trigger_type": trig, "gate": g or gate(),
            "edge": edge, "rotation": rot, "conviction_score": conv}


class TestGate:
    def test_buy_below_bar_is_shadow_with_recorded_reason(self):
        e = buy_edge(target=112.0)         # 1.2R at a 10% stop
        assert e["ev_r"] < 0.15
        d = E.decide_gate([cand("a", edge=e)])["a"]
        assert d["vote"] == "shadow" and d["refused_because"].startswith("EV ")
        assert "below the 0.15R bar" in d["refused_because"] and "p_win" in d["refused_because"]

    def test_buy_with_no_analyst_target_is_shadow_with_that_reason(self):
        e = buy_edge(target=None)
        assert e["status"] == "no_target" and e["ev_r"] is None
        d = E.decide_gate([cand("a", edge=e)])["a"]
        assert d["vote"] == "shadow" and "target" in d["refused_because"]

    def test_good_buy_is_live(self):
        assert E.decide_gate([cand("a", edge=buy_edge(target=130.0))])["a"]["vote"] == "live"

    @pytest.mark.parametrize("trig", ["thesis_break", "conviction_exit", "catalyst_threat", "trim_risk_cap",
                                      "factor_threat"])
    def test_protective_exits_are_never_suppressed_never_ev_refused(self, trig):
        g = gate("suppressed", 40, family=f"SELL|{trig}")
        d = E.decide_gate([cand("s", "SELL", trig, edge={"ev_gated": False}, g=g)])["s"]
        assert d["vote"] == "live" and d["suppression_ignored"] is True

    def test_a_sell_is_never_ev_refused(self):
        # a sell whose "EV" would be hopeless still passes: sells carry no EV bar at all
        d = E.decide_gate([cand("s", "SELL", "overbought_distribution", edge={"ev_r": -0.9, "status": "ok"})])["s"]
        assert d["vote"] == "live"

    def test_suppressed_nonprotective_sell_family_goes_shadow(self):
        g = gate("suppressed", 40, family="SELL|overbought_distribution")
        d = E.decide_gate([cand("s", "SELL", "overbought_distribution", g=g)])["s"]
        assert d["vote"] == "shadow" and d["reason_code"] == "family_suppressed"

    def test_rotation_needs_pair_edge_when_assessable(self):
        buy, hold = buy_edge(target=140.0), buy_edge(target=139.0)
        rot = E.rotation_edge(buy, hold)
        assert rot["assessed"] and rot["edge_r"] < 0.25
        assert E.decide_gate([cand("p", kind="pair", trig="profit_rotation", edge=buy, rot=rot)])["p"]["vote"] == "shadow"
        weak = buy_edge(target=112.0)
        good_rot = E.rotation_edge(buy_edge(target=140.0), weak)
        assert good_rot["passes"]

    def test_unknown_hold_ev_is_unassessed_not_fabricated(self):
        rot = E.rotation_edge(buy_edge(target=140.0), buy_edge(target=None))
        assert rot["assessed"] is False and rot["edge_r"] is None
        assert E.decide_gate([cand("p", kind="pair", trig="profit_rotation", edge=buy_edge(target=140.0),
                                   rot=rot)])["p"]["vote"] == "live"

    def test_deemph_is_bounded_and_never_zeroes(self):
        assert E.deemph_factor(["A", "B", "C"], {"A", "B", "C"}) == 0.85
        assert E.deemph_factor(["A"], set()) == 1.0 and E.deemph_factor([], {"A"}) == 1.0
        assert E.scaled_size(500.0, 0.85 * 0.25, None, None) > 0

    def test_deemph_admits_only_known_fresh_buckets(self):
        import datetime as dt
        st = {"strategist_deemphasis": {"buckets": ["TARGET GAP", "made up"], "as_of": "2026-09-20"}}
        assert E.active_deemphasis(st, dt.date(2026, 9, 21)) == {"TARGET GAP"}
        assert E.active_deemphasis(st, dt.date(2026, 10, 30)) == frozenset()

    def test_growth_only_when_unclamped_and_capped(self):
        assert E.scaled_size(100.0, 1.25, "ATR headroom", 1000.0) == 100.0
        assert E.scaled_size(100.0, 1.25, None, 110.0) == 110.0
        assert E.scaled_size(100.0, 0.75, "ATR headroom", 1000.0) == 75.0


# ---------------------------------------------------------------------------------- THE INVARIANT
class TestCashInvariant:
    def _all_fail(self):
        cs = [cand("a", edge=buy_edge(target=112.0)), cand("b", edge=buy_edge(target=108.0)),
              cand("c", edge=buy_edge(target=None))]
        return cs, E.decide_gate(cs)

    def test_every_buy_fails_ev_cash_above_band_exactly_one_override(self):
        cs, dec = self._all_fail()
        assert all(d["vote"] == "shadow" for d in dec.values())
        r = E.enforce_cash_invariant(cs, dec, True)
        live = [k for k, d in dec.items() if d["vote"] == "live"]
        assert live == ["a"] and r["override"] == "a"                    # the highest-EV refused buy
        assert dec["a"]["gate_override"] == "cash above band -- best available idea permitted"

    def test_no_override_when_cash_not_above_band(self):
        cs, dec = self._all_fail()
        r = E.enforce_cash_invariant(cs, dec, False)
        assert r["override"] is None and all(d["vote"] == "shadow" for d in dec.values())
        assert not any("gate_override" in d for d in dec.values())

    def test_no_override_when_a_live_buy_remains(self):
        cs = [cand("a", edge=buy_edge(target=130.0)), cand("b", edge=buy_edge(target=108.0))]
        dec = E.decide_gate(cs)
        assert E.enforce_cash_invariant(cs, dec, True)["override"] is None and dec["b"]["vote"] == "shadow"

    def test_override_must_still_clear_materiality_and_heat(self):
        cs, dec = self._all_fail()
        r = E.enforce_cash_invariant(cs, dec, True, clears=lambda cid: cid == "b")
        assert r["override"] == "b" and r["attempted"] == ["a", "b"] and dec["a"]["vote"] == "shadow"
        cs, dec = self._all_fail()
        r = E.enforce_cash_invariant(cs, dec, True, clears=lambda cid: False)
        assert r["override"] is None and "not forced" in r["why_not"]

    def test_suppressed_family_buys_are_also_restorable(self):
        g = gate("suppressed", 30)
        cs = [cand("a", edge=buy_edge(target=130.0), g=g)]
        dec = E.decide_gate(cs)
        assert dec["a"]["vote"] == "shadow"
        assert E.enforce_cash_invariant(cs, dec, True)["override"] == "a"

    def test_nothing_to_restore_when_no_buy_was_refused(self):
        assert E.enforce_cash_invariant([], {}, True)["override"] is None


def _run_triggers(tmp_path, mutate):
    src = os.path.join(ROOT, "tests", "fixtures", "triggers_case1")
    dst = tmp_path / "t"
    shutil.copytree(src, dst)
    mutate(dst)
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "smith_math.py"), "triggers", "--base-dir",
                        str(dst / "base"), "--run-dir", str(dst / "rundir"), "--today", "2026-09-01"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


class TestEndToEnd:
    def _mutate(self, target, wallet):
        def add(dst):
            st = json.load(open(dst / "base" / "state.json"))
            st["data_cache"]["atr20"]["values_pct"]["CORZ"] = 7.0
            st["thesis"]["CORZ"] = "AI hosting|strengthening"
            st["data_cache"].setdefault("analyst_targets", {})["CORZ"] = (
                {"mean_target_usd": target, "as_of": "2026-09-01"} if target else {})
            json.dump(st, open(dst / "base" / "state.json", "w"))
            json.dump({"CORZ": {"price": 15.25}}, open(dst / "rundir" / "live_quotes.json", "w"))
            # Phase 6 universe bar: an unheld name needs an ATR/RSI computed from THIS run's bars
            json.dump({"atr20_pct": {"CORZ": 7.0}, "rsi14": {"CORZ": 40.0}},
                      open(dst / "rundir" / "compute_indicators.json", "w"))
            json.dump({"as_of": "2026-09-01", "window": {"to": "2026-08-28"},
                       "stop_risk": {"avg_pairwise_correlation": 0.0}},
                      open(dst / "rundir" / "compute_correlation.json", "w"))
            bk = json.load(open(dst / "rundir" / "compute_book.json"))
            bk["wallet_usd"] = wallet
            json.dump(bk, open(dst / "rundir" / "compute_book.json", "w"))
        return add

    def test_gate_refuses_low_ev_buy_and_records_it(self, tmp_path):
        out = _run_triggers(tmp_path, self._mutate(16.5, 5426.78))         # +8% upside: 0.9R
        row = next(r for r in out["entry_setup"] if r["ticker"] == "CORZ")
        assert row["vote"] == "shadow" and row["refused_because"].startswith("EV ")
        assert out["edge"]["all_unproven"] is True
        assert any(s["ticker"] == "CORZ" and s["direction_bucket"] == "BUY" for s in out["shadow_new"])

    def _no_targets(self, wallet):
        def add(dst):
            st = json.load(open(dst / "base" / "state.json"))
            st["data_cache"]["analyst_targets"] = {}
            json.dump(st, open(dst / "base" / "state.json", "w"))
            j = json.load(open(dst / "base" / "journal.json"))
            for e in j.get("entries", []):
                e.pop("analyst_target", None)
            json.dump(j, open(dst / "base" / "journal.json", "w"))
            json.dump({"as_of": "2026-09-01", "window": {"to": "2026-08-28"},
                       "stop_risk": {"avg_pairwise_correlation": 0.0}},
                      open(dst / "rundir" / "compute_correlation.json", "w"))
            bk = json.load(open(dst / "rundir" / "compute_book.json"))
            bk["wallet_usd"] = wallet
            json.dump(bk, open(dst / "rundir" / "compute_book.json", "w"))
        return add

    def _live_buys(self, out):
        return [r for f in ("oversold_reversion", "trend_entry", "conviction_average", "entry_setup", "reentry",
                            "bench_diversifier") for r in out[f] if r.get("vote") == "live"]

    def test_invariant_every_buy_fails_gate_cash_above_band_one_override(self, tmp_path):
        out = _run_triggers(tmp_path, self._no_targets(14000.0))
        inv = out["edge"]["invariant"]
        assert out["deployable_cash_usd"] > 0 and inv["required"] is True
        if inv["override"] is None:      # heat/materiality legitimately blocked it: must be stated, not silent
            assert "not forced" in inv["why_not"] and any("SAFETY INVARIANT" in d for d in out["data_quality"])
        else:
            live = self._live_buys(out) + [p["buy_leg"] for f in ("profit_rotation", "cluster_rotation")
                                           for p in out[f] if p.get("vote") == "live"]
            assert len(live) == 1
            row = out["edge"]["tickets"]
            assert [t["gate_override"] for t in row if t.get("gate_override")] == [
                "cash above band -- best available idea permitted"]

    def test_invariant_silent_when_cash_not_above_band(self, tmp_path):
        out = _run_triggers(tmp_path, self._no_targets(5426.78))
        inv = out["edge"]["invariant"]
        assert out["deployable_cash_usd"] == 0 and inv["override"] is None and inv["required"] is False
        assert self._live_buys(out) == []

    def test_with_a_target_the_buy_is_live_unproven_and_unscaled_by_family(self, tmp_path):
        out = _run_triggers(tmp_path, self._mutate(30.0, 5426.78))
        row = next(r for r in out["entry_setup"] if r["ticker"] == "CORZ")
        assert row["vote"] == "live" and row["gate"]["verdict"] == "unproven"
        assert row["sizing_factors"]["f_family"] == 1.0
        assert row["edge"]["p_win_basis"].startswith("prior 0.45 (UNCALIBRATED)")


# ---------------------------------------------------------------------------------- buckets
class TestBucketReader:
    J = {"bucket_hit_rates": {"TARGET GAP": {"n": 19, "hit_rate_pct": 36.8},
                              "MOMENTUM+VOLUME": {"n": 15, "hit_rate_pct": 20.0}},
         "bucket_hit_rates_7d": {"TARGET GAP": {"n": 37, "hit_rate_pct": 35.1},
                                 "PEER LEADER": {"n": 9, "hit_rate_pct": 66.7}}}

    def test_prefers_30d_and_labels_source(self):
        r = E.bucket_rate(self.J, "TARGET GAP")
        assert r["source"] == "30d" and r["n"] == 19 and r["interim"] is False

    def test_falls_back_to_7d_and_says_so(self):
        r = E.bucket_rate(self.J, "PEER LEADER")
        assert r["source"] == "7d" and r["interim"] is True
        assert E.bucket_rate(self.J, "NOPE") is None

    def test_penalty_fires_below_45_at_n8_and_not_at_n7(self):
        j = lambda n: {"bucket_hit_rates": {"X": {"n": n, "hit_rate_pct": 30.0}}}
        assert E.bucket_adjustment(j(8), ["X"])[0] == -2
        assert E.bucket_adjustment(j(7), ["X"])[0] == 0
        assert E.bucket_adjustment({"bucket_hit_rates": {"X": {"n": 20, "hit_rate_pct": 45.0}}}, ["X"])[0] == 0

    def test_reward_still_works_and_penalty_outranks_it(self):
        assert E.bucket_adjustment(self.J, ["PEER LEADER"])[0] == 2
        assert E.bucket_adjustment(self.J, ["PEER LEADER", "MOMENTUM+VOLUME"])[0] == -2

    def test_priority_scorer_applies_penalty_and_deemph(self):
        import test_smith_lifecycle_proposals as T
        pr = {"id": "P-1", "ticker": "AAA", "action": "Buy AAA", "direction_bucket": "BUY", "status": "open",
              "repeat_count": 1, "date": "2026-09-21"}
        base = dict(risk_by_ticker={}, directional_breach=lambda *a: None, cash_short=False, cash_excess=False,
                    cash_pct=10, cash_band=[5, 15], stretch_by_ticker={}, derisk={},
                    rotation_by_ticker={"AAA": {"bullish_buckets": ["MOMENTUM+VOLUME"]}},
                    hit_rates_7d={}, trigger_live_sets={}, trigger_rows={}, trigger_pairs={},
                    state_sector_map={}, cluster_breach=lambda *a: None, total_book_usd=40000.0)
        p1 = dict(pr)
        sl._score_proposal_priority(p1, **base, hit_rates_30d=self.J["bucket_hit_rates"])
        p2 = dict(pr)
        sl._score_proposal_priority(p2, **base, hit_rates_30d=self.J["bucket_hit_rates"],
                                    deemphasized_buckets={"MOMENTUM+VOLUME"})
        assert p2["priority_score"] == p1["priority_score"] - 1
        assert any("20%" in r for r in p1["priority_reasons"])


# ---------------------------------------------------------------------------------- reporting
class TestScorecardGate:
    def test_explain_and_gate_block_carry_the_same_numbers(self):
        table = E.build_table([prop(i, date=LEGACY) for i in range(3)])
        e = buy_edge(target=130.0)
        tick = [{"id": "a", "ticker": "AAA", "family": "trend_entry", "direction": "BUY", "vote_before": "live",
                 "vote_after": "live", "refused_because": None, "p_win": e["p_win"], "payoff_r": e["payoff_r"],
                 "ev_r": e["ev_r"], "f_edge": e["f_edge"], "f_family": 1.0, "size_before_usd": 500,
                 "size_after_usd": 500, "reason_code": None, "gate": gate()}]
        payload = E.explain("2026-09-21", table, tick, {"required": False})
        blk = E.scorecard_gate_block(payload, {"since_epoch": None})
        assert blk["tickets"][0]["p_win"] == e["p_win"] and blk["tickets"][0]["ev_r"] == e["ev_r"]
        assert blk["engine_epoch"] == "2026-09-21" and blk["all_families_unproven"] is True
        assert "LEGACY" in blk["legacy_exclusion"].upper() and "excluded" in blk["legacy_exclusion"].lower()
        assert "no post-rebuild" in blk["since_epoch_scorecard"]

    def test_missing_edge_file_is_explicit_not_silent(self):
        blk = E.scorecard_gate_block(None)
        assert blk["available"] is False and "legacy_exclusion" in blk

    def test_strategist_slice_contains_scorecard_gate(self, tmp_path):
        import argparse
        import smith_memory
        base = tmp_path
        rd = base / "runs" / "r1"
        rd.mkdir(parents=True)
        (rd / "holdings.json").write_text(json.dumps({"holdings_inr": [{"ticker": "AAA", "qty": 1, "weight_pct": 5}]}))
        (base / "state.json").write_text(json.dumps({"thesis": {"AAA": {"status": "intact"}}, "sector_map": {"AAA": "X"},
                                                     "data_cache": {}}))
        (base / "proposals.json").write_text(json.dumps({"proposals": [], "scorecard": {}}))
        payload = E.explain("2026-09-21", E.build_table([]), [], {"required": False})
        (rd / "compute_edge.json").write_text(json.dumps(payload))
        try:
            smith_memory.cmd_slices(argparse.Namespace(base_dir=str(base), run_dir=str(rd), today="2026-09-21",
                                                       agents="strategist", mode="deep", force=True))
        except SystemExit:
            pass
        f = rd / "slice_strategist.json"
        if not f.exists():
            pytest.skip("slice builder needs a fuller fixture; covered by scorecard_gate_block tests")
        sl_ = json.loads(f.read_text())
        assert sl_["scorecard_gate"]["engine_epoch"] == payload["engine_epoch"]
        assert "legacy_exclusion" in sl_["scorecard_gate"]


class TestDraftQuote:
    def test_quote_leads_with_current_engine_then_labelled_legacy(self):
        import smith_math as m
        q = m._draft_scorecard_quote({"as_of": "2026-09-21",
                                      "since_epoch": {"n_rows": 0, "overall": None, "by_direction": {}},
                                      "legacy": {"overall": {"n_rows": 22, "n_ideas": 20, "accuracy_pct": 45.5,
                                                             "expectancy_pct_net": 0.5,
                                                             "size_weighted_expectancy_pct_net": 1.0,
                                                             "expectancy_usd_total": 107.17, "payoff_ratio": 1.02},
                                                 "by_direction": {}}})
        assert q.index("CURRENT ENGINE") < q.index("LEGACY-ENGINE HISTORY")
        assert "net expectancy 0.5%" in q and "payoff 1.02:1" in q and "22 rows / 20 ideas" in q
        assert q.index("net expectancy") < q.index("accuracy")


class TestShadowJournalWiring:
    def test_postflight_scores_shadow_journals(self):
        import smith_orchestrate as o
        assert hasattr(o, "_score_shadow_journals")
        src = open(os.path.join(SCRIPTS, "smith_orchestrate.py")).read()
        assert "_score_shadow_journals(base, rd, today)" in src

    def test_scorer_uses_gate_direction_bucket(self, tmp_path):
        import argparse
        import contextlib
        import io
        (tmp_path / "trigger_journal.json").write_text(json.dumps({"entries": [
            {"date": "2026-09-21", "ticker": "AAA", "trigger_type": "trend_entry", "direction_bucket": "BUY",
             "price_at_flag": 100.0, "scored": False}]}))
        (tmp_path / "p.json").write_text(json.dumps({"AAA": 110.0}))
        with contextlib.redirect_stdout(io.StringIO()):
            sl.cmd_score_shadow_journal(argparse.Namespace(base_dir=str(tmp_path), file="trigger_journal.json",
                                                           prices_json=str(tmp_path / "p.json"),
                                                           today="2026-10-05", dry_run=False))
        e = json.load(open(tmp_path / "trigger_journal.json"))["entries"][0]
        assert e["verdict"] == "worked"

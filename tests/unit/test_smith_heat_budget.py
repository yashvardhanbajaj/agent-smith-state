"""Phase 3 of the proposal-engine rebuild (2026-09-20): a correlation-adjusted portfolio heat budget
shared by every buy candidate of a run, plus the two formerly inert caps (max_single_position_pct,
max_ai_capex_factor_pct) as real named clamps.

The motivating incident: policy.stop_loss_framework records the 10% aggregate-open-risk cap
breached at 13.028% (2026-08-26) and 11.947% (2026-08-30) while sizing carried on at the full
per-position formula -- the cap only ever printed a warning. On the LIVE book (heat 6.45% vs the
10% cap) this phase is deliberately non-binding, so it is proven here on FIXTURE books that are
over their cap, never only on live data.
"""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

import pytest

import smith_conviction
import smith_core
import smith_math
import smith_risk
import smith_ticket as T

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "scripts")
TODAY = dt.date(2026, 9, 20)
BOOK = 42541.95                       # the live 2026-09-20 book
H_LIVE = 2743.98                      # its aggregate open risk (6.45%)
POLICY = {"stop_loss_framework": {"risk_per_position_pct_of_book": 0.5,
                                  "aggregate_open_risk_cap_pct_of_book": 10}}


def fresh_corr(rho, window_to="2026-09-18"):
    return {"as_of": "2026-09-20", "window": {"to": window_to},
            "stop_risk": {"avg_pairwise_correlation": rho}}


def budget_for(h=H_LIVE, rho=0.401, book=BOOK, corr=None, floor=smith_core.HEAT_FLOOR_AT_FULL_CORRELATION):
    cr = T.correlation_read(fresh_corr(rho) if corr is None else corr, TODAY)
    return T.heat_budget(h, book, 10, cr, floor)


def single(id, score, size, stop=5.0, floor=0.0, ticker=None, cluster=None, is_ai=False):
    return {"id": id, "kind": "single", "ticker": ticker or id, "score": score, "size_usd": size,
            "stop_pct": stop, "floor_usd": floor, "cluster": cluster, "is_ai": is_ai}


def pair(id, score, buy_size, buy_stop, freed, ticker=None, floor=0.0, cluster=None, sell_cluster=None,
         sell_size=0.0, is_ai=False, sell_is_ai=False):
    return {"id": id, "kind": "pair", "ticker": ticker or id, "score": score, "size_usd": buy_size,
            "stop_pct": buy_stop, "floor_usd": floor, "cluster": cluster, "is_ai": is_ai,
            "freed_risk_usd": freed, "sell_size_usd": sell_size, "sell_cluster": sell_cluster,
            "sell_is_ai": sell_is_ai}


# ---------------------------------------------------------------------------
# the budget itself
# ---------------------------------------------------------------------------
class TestBudget:
    def test_live_book_numbers(self):
        b = budget_for(rho=0.401)
        assert b["h_max_usd"] == pytest.approx(4254.19, abs=0.01)
        # the plan quoted $3,692 (rho 0.44); at the live rho 0.401 it is $3,742.42
        assert b["h_eff_max_usd"] == pytest.approx(3742.42, abs=0.02)
        assert b["r_free_usd"] == pytest.approx(998.44, abs=0.02)
        assert not b["over_cap"] and b["rho_measured"]

    def test_rho_zero_gives_the_whole_cap_and_rho_point_nine_gives_less(self):
        b0, b9 = budget_for(rho=0.0), budget_for(rho=0.9)
        assert b0["h_eff_max_usd"] == pytest.approx(b0["h_max_usd"])          # no correlation: full cap
        assert b9["h_eff_max_usd"] == pytest.approx(b9["h_max_usd"] * (0.70 + 0.30 * 0.10), abs=0.02)
        assert b9["h_eff_max_usd"] < b0["h_eff_max_usd"]
        assert b0["r_free_usd"] > b9["r_free_usd"]

    def test_full_correlation_is_the_floor_not_zero(self):
        b = budget_for(rho=1.0)
        assert b["h_eff_max_usd"] == pytest.approx(b["h_max_usd"] * 0.70, abs=0.02)

    def test_rho_is_clamped_to_unit_interval(self):
        assert budget_for(rho=-0.4)["rho_used"] == 0.0
        assert budget_for(rho=1.7)["rho_used"] == 1.0

    @pytest.mark.parametrize("corr,why", [
        ({}, "absent"),
        (None, "absent"),
        ({"degraded": True, "reason": "no perf_bars"}, "degraded"),
        ({"as_of": "2026-09-20", "window": {"to": "2026-09-18"}, "stop_risk": {}}, "no stop_risk"),
        (fresh_corr(0.10, window_to="2026-08-01"), "old"),           # 50 days stale
        (fresh_corr(0.10, window_to="garbage"), "parseable"),
    ])
    def test_missing_or_stale_correlation_uses_the_conservative_bound_and_says_so(self, corr, why):
        b = budget_for(corr=corr if corr is not None else {})
        assert not b["rho_measured"] and b["rho_used"] == 1.0
        assert b["h_eff_max_usd"] == pytest.approx(b["h_max_usd"] * 0.70, abs=0.02)
        assert "CONSERVATIVE BOUND" in b["rho_basis"] and why in b["rho_basis"]

    def test_a_missing_correlation_is_never_read_as_zero(self):
        # a stale 0.0 must NOT hand the book a diversification credit
        stale = budget_for(corr=fresh_corr(0.0, window_to="2026-08-01"))
        assert stale["h_eff_max_usd"] < budget_for(rho=0.0)["h_eff_max_usd"]

    def test_over_cap_is_tested_against_the_adjusted_budget_not_the_raw_cap(self):
        # 6.45% is under the raw 10% cap, but at rho 0.9 the adjusted budget is 7.3% -> still fine;
        # a 7.5% book is over the adjusted cap while under the raw one
        h = 0.075 * BOOK
        assert budget_for(h=h, rho=0.9)["over_cap"] and not budget_for(h=h, rho=0.0)["over_cap"]

    def test_heat_policy_defaults_and_bad_values_fall_back(self):
        assert T.heat_policy(None) == {"heat_floor": 0.70, "cluster_sub_budget": True, "confirmed": False}
        assert T.heat_policy({"heat_floor_at_full_correlation": "x", "cluster_sub_budget": "yes"})["heat_floor"] == 0.70
        assert T.heat_policy({"heat_floor_at_full_correlation": 0.5, "cluster_sub_budget": False,
                              "confirmed": True}) == {"heat_floor": 0.5, "cluster_sub_budget": False, "confirmed": True}

    def test_correlation_max_age_boundary(self):
        assert T.correlation_read(fresh_corr(0.4, "2026-09-13"), TODAY)["measured"]          # 7d: ok
        assert not T.correlation_read(fresh_corr(0.4, "2026-09-12"), TODAY)["measured"]      # 8d: stale


# ---------------------------------------------------------------------------
# greedy allocation
# ---------------------------------------------------------------------------
class TestAllocation:
    def test_greedy_by_key_and_stops_exactly_at_r_free(self):
        b = budget_for()                                   # R_free 998.44
        # four $10k-ish tickets at 5% stop = $500 of risk each; highest score first
        cands = [single("low", 10, 10000), single("hi", 90, 10000), single("mid", 50, 10000), single("lo2", 20, 10000)]
        res = T.allocate_heat(cands, b)["decisions"]
        assert res["hi"]["status"] == "fit" and res["hi"]["risk_usd"] == 500.0
        # second: $500 wanted vs $498.44 left -> partial, sized to EXACTLY what is left
        assert res["mid"]["status"] == "clamped" and res["mid"]["clamped_by"] == "heat_room"
        assert res["mid"]["size_usd"] == pytest.approx(498.44 / 0.05, abs=0.02)
        assert res["mid"]["risk_usd"] == pytest.approx(498.44, abs=0.01)
        # the budget is spent: the rest are deferred, not dropped, in score order
        assert res["lo2"]["status"] == "deferred" and res["low"]["status"] == "deferred"

    def test_total_allocated_never_exceeds_r_free(self):
        b = budget_for()
        cands = [single(f"t{i}", 100 - i, 7000 + 900 * i, stop=4 + i % 5) for i in range(12)]
        out = T.allocate_heat(cands, b)
        spent = sum(d["net_risk_usd"] for d in out["decisions"].values() if d["status"] in ("fit", "clamped"))
        assert spent <= b["r_free_usd"] + 0.05
        assert out["h_after_usd"] <= b["h_eff_max_usd"] + 0.05

    def test_deferred_ticket_is_emitted_with_reason_and_would_be_size(self):
        b = budget_for()
        res = T.allocate_heat([single("a", 90, 19000), single("b", 80, 3000, floor=1000.0)], b)["decisions"]
        # a takes ~all of the room; b's remaining room buys less than its materiality floor -> deferred
        d = res["b"]
        assert d["status"] == "deferred" and d["deferred_by"] == "portfolio heat budget"
        assert d["would_be_size_usd"] == 3000 and d["size_usd"] is None
        assert "of net new risk" in d["deferred_reason"]

    def test_partial_fit_must_still_clear_materiality(self):
        b = budget_for()
        big = single("a", 90, 19000)                       # leaves ~$48 of risk = $960 at 5%
        fits = T.allocate_heat([big, single("b", 80, 3000, floor=900.0)], b)["decisions"]["b"]
        assert fits["status"] == "clamped" and fits["clamped_by"] == "heat_room" and fits["size_usd"] >= 900.0
        gone = T.allocate_heat([big, single("b", 80, 3000, floor=1000.0)], b)["decisions"]["b"]
        assert gone["status"] == "deferred"

    def test_every_decision_carries_the_heat_fields(self):
        b = budget_for()
        res = T.allocate_heat([single("a", 90, 4000), single("b", 80, 4000)], b)["decisions"]
        assert res["a"]["book_heat_before_usd"] == H_LIVE
        assert res["a"]["book_heat_after_usd"] == pytest.approx(H_LIVE + 200.0)
        assert res["b"]["book_heat_before_usd"] == res["a"]["book_heat_after_usd"]
        assert res["b"]["heat_room_remaining_usd"] == pytest.approx(b["h_eff_max_usd"] - res["b"]["book_heat_after_usd"], abs=0.01)

    def test_key_is_one_named_function_and_swapping_it_reorders(self, monkeypatch):
        b = budget_for()
        cands = [single("a", 90, 10000), single("b", 10, 10000)]
        assert T.allocate_heat(cands, b)["decisions"]["a"]["status"] == "fit"
        assert T.allocate_heat(cands, b)["decisions"]["b"]["status"] == "clamped"
        # Phase 4's swap is ONE line: re-point the key, and the OTHER ticket now goes first
        monkeypatch.setattr(T, "allocation_priority", lambda c: -(c.get("score") or 0))
        swapped = T.allocate_heat(cands, b)["decisions"]
        assert swapped["b"]["status"] == "fit" and swapped["a"]["status"] == "clamped"
        # ...and an explicit key= override also works without touching the module
        monkeypatch.undo()
        assert T.allocate_heat(cands, b, key=lambda c: -c["score"])["decisions"]["b"]["status"] == "fit"

    def test_ordering_key_reads_conviction_score_today(self):
        assert T.allocation_priority({"score": 41.5}) == 41.5 and T.allocation_priority({}) == 0.0


# ---------------------------------------------------------------------------
# a FIXTURE book already over its cap -- the case live data can never test
# ---------------------------------------------------------------------------
class TestOverCap:
    def over(self):
        b = budget_for(h=0.09 * BOOK, rho=0.5)             # 9% heat, adjusted budget ~8.5%
        assert b["over_cap"] and b["r_free_usd"] == 0.0
        return b

    def test_zero_new_net_risk_buys_each_naming_the_reason(self):
        b = self.over()
        res = T.allocate_heat([single("a", 90, 500), single("b", 50, 2000), single("c", 10, 100)], b)["decisions"]
        for k in "abc":
            assert res[k]["status"] == "deferred" and res[k]["deferred_by"] == "portfolio heat budget"
            assert "exceeds the correlation-adjusted budget" in res[k]["deferred_reason"]
            assert f"${b['h_usd']:,.2f}" in res[k]["deferred_reason"] and f"${b['h_eff_max_usd']:,.2f}" in res[k]["deferred_reason"]

    def test_risk_neutral_rotation_still_emits_while_singles_defer(self):
        b = self.over()
        out = T.allocate_heat([pair("rot", 40, 800, 6.25, freed=50.0), single("buy", 90, 500)], b)
        assert out["decisions"]["rot"]["status"] == "fit" and out["decisions"]["rot"]["size_usd"] == 800
        assert out["decisions"]["buy"]["status"] == "deferred"

    def test_no_sell_credit_is_taken_on_an_over_cap_book(self):
        b = self.over()
        out = T.allocate_heat([single("buy", 90, 500)], b, standalone_credit_usd=400.0)
        assert out["credit_usd"] == 0.0 and out["decisions"]["buy"]["status"] == "deferred"

    def test_a_derisking_pair_does_not_raise_the_budget_when_over_cap(self):
        b = self.over()
        out = T.allocate_heat([pair("rot", 90, 400, 5.0, freed=100.0), single("buy", 50, 500)], b)
        assert out["decisions"]["rot"]["status"] == "fit" and out["remaining_usd"] == 0.0
        assert out["decisions"]["buy"]["status"] == "deferred"

    def test_the_gate_names_itself_even_when_a_static_cap_would_also_zero_the_ticket(self):
        b = self.over()
        res = T.allocate_heat([single("a", 90, 500, ticker="a")], b,
                              rooms={"single_position_usd": {"a": 0.0}})["decisions"]["a"]
        assert res["status"] == "deferred" and "exceeds the correlation-adjusted budget" in res["deferred_reason"]

    def test_pairs_with_positive_net_are_deferred_whole_when_over_cap(self):
        b = self.over()
        d = T.allocate_heat([pair("rot", 40, 2000, 5.0, freed=10.0)], b)["decisions"]["rot"]
        assert d["status"] == "deferred" and d["net_risk_usd"] == 90.0


# ---------------------------------------------------------------------------
# rotations: only NET risk counts; a sell that will not execute frees nothing
# ---------------------------------------------------------------------------
class TestRotations:
    def test_net_nonpositive_pair_always_fits_even_with_no_room(self):
        b = budget_for(h=3742.42)                          # R_free = 0, not over cap
        assert b["r_free_usd"] == 0.0 and not b["over_cap"]
        out = T.allocate_heat([pair("flat", 50, 1000, 5.0, freed=50.0), pair("neg", 40, 800, 5.0, freed=60.0)], b)
        assert out["decisions"]["flat"]["status"] == "fit" and out["decisions"]["neg"]["status"] == "fit"

    def test_positive_net_consumes_exactly_the_net(self):
        b = budget_for()
        out = T.allocate_heat([pair("p", 50, 2000, 5.0, freed=30.0)], b)
        d = out["decisions"]["p"]
        assert d["risk_usd"] == 100.0 and d["net_risk_usd"] == 70.0
        assert out["remaining_usd"] == pytest.approx(b["r_free_usd"] - 70.0, abs=0.01)

    def test_positive_net_larger_than_room_defers_the_whole_pair(self):
        b = budget_for()
        d = T.allocate_heat([pair("p", 50, 40000, 5.0, freed=30.0)], b)["decisions"]["p"]
        assert d["status"] == "deferred" and d["size_usd"] is None      # never half a rotation

    def test_pair_credit_arithmetic(self):
        b = budget_for(h=3742.42 - 20.0)                   # R_free = 20
        out = T.allocate_heat([pair("rot", 90, 1000, 5.0, freed=80.0), single("s", 10, 2000)], b)["decisions"]
        assert out["s"]["status"] == "clamped" and out["s"]["clamped_by"] == "heat_room"
        assert out["s"]["risk_usd"] == pytest.approx(50.0, abs=0.01)       # 20 free + 30 retired by the pair

    def test_standalone_sell_credit_raises_room_only_when_supplied(self):
        b = budget_for()
        want = b["r_free_usd"] + 100.0
        s = single("s", 50, want / 0.05)
        assert T.allocate_heat([s], b)["decisions"]["s"]["status"] == "clamped"
        assert T.allocate_heat([s], b, standalone_credit_usd=100.0)["decisions"]["s"]["status"] == "fit"

    def test_pair_shrunk_below_materiality_neither_consumes_nor_frees(self):
        b = budget_for()
        p = pair("p", 90, 800, 5.0, freed=40.0, ticker="AAA", floor=700.0)
        out = T.allocate_heat([p], b, rooms={"single_position_usd": {"AAA": 300.0}})
        d = out["decisions"]["p"]
        assert d["status"] == "below_materiality" and d["net_risk_usd"] == 0.0
        assert out["remaining_usd"] == b["r_free_usd"]     # not raised by the un-executed sell's $40


# ---------------------------------------------------------------------------
# the static caps: single_position / ai_capex / cluster_risk_budget only ever SHRINK
# ---------------------------------------------------------------------------
class TestStaticCaps:
    def test_clamp_size_is_backward_compatible(self):
        assert smith_conviction.clamp_size(1000, 800, 600, 900) == (600.0, "cluster ceiling room")
        assert smith_conviction.clamp_size(1000, None, None, None) == (1000.0, None)
        assert smith_conviction.clamp_size(0, 5, 5, 5) == (0.0, None)
        assert smith_conviction.clamp_size(1000, 800, None, 500) == (500.0, "deployable cash")

    @pytest.mark.parametrize("kw,name", [("single_position_room_usd", "single_position"),
                                         ("ai_capex_room_usd", "ai_capex"),
                                         ("cluster_risk_room_usd", "cluster_risk_budget"),
                                         ("heat_room_usd", "heat_room")])
    def test_each_new_clamp_names_itself_and_only_shrinks(self, kw, name):
        assert smith_conviction.clamp_size(1000, None, None, None, **{kw: 400}) == (400.0, name)
        assert smith_conviction.clamp_size(1000, None, None, None, **{kw: 4000}) == (1000.0, None)   # never larger
        assert smith_conviction.clamp_size(1000, None, None, None, **{kw: 0}) == (0.0, name)
        assert smith_conviction.clamp_size(1000, None, None, None, **{kw: -50}) == (0.0, name)

    def test_older_clamp_keeps_the_name_on_a_tie(self):
        assert smith_conviction.clamp_size(1000, 400, None, None, single_position_room_usd=400) == (400.0, "ATR headroom")

    def test_single_position_room_is_exact_on_a_moving_denominator(self):
        # 12% of invested equity, cash-funded: (l*E - mv)/(1 - l), NOT the linear l*E - mv
        e, mv = 33730.51, 3033.52
        assert T.cash_funded_room(0.12, mv, e, True) == pytest.approx((0.12 * e - mv) / 0.88, abs=0.01)
        assert T.cash_funded_room(0.12, mv, e, True) > 0.12 * e - mv
        assert T.cash_funded_room(0.12, mv, e, False) == pytest.approx(0.12 * e - mv, abs=0.01)   # total book: linear
        assert T.cash_funded_room(0.12, 99999.0, e, True) == 0.0                                    # already over: zero, never negative

    def test_ai_capex_at_100_percent_of_invested_equity_cannot_bind_a_cash_funded_buy(self):
        # 95.76% of equity today: the LINEAR figure would be $1,430 for the whole run and would
        # silently choke every AI buy; a cash-funded buy raises numerator and denominator together
        # so a 100% cap is unreachable and the clamp is honestly non-binding
        assert T.cash_funded_room(1.0, 0.9576 * 33730.51, 33730.51, True) is None
        assert T.cash_funded_room(1.0, 0.9576 * 33730.51, 33730.51, False) == pytest.approx(1430.5, abs=1.0)
        assert T.cash_funded_room(None, 1.0, 1.0, True) is None and T.cash_funded_room(0.1, 1.0, 0, True) is None

    def test_allocator_applies_single_position_and_names_it(self):
        b = budget_for()
        d = T.allocate_heat([single("x", 50, 1000, ticker="X")], b,
                            rooms={"single_position_usd": {"X": 400.0}})["decisions"]["x"]
        assert d["size_usd"] == 400.0 and d["clamped_by"] == "single_position" and d["status"] == "clamped"

    def test_two_buys_of_one_name_share_one_room(self):
        b = budget_for()
        res = T.allocate_heat([single("a", 90, 300, ticker="X"), single("b", 80, 300, ticker="X")], b,
                              rooms={"single_position_usd": {"X": 500.0}})["decisions"]
        assert res["a"]["size_usd"] == 300 and res["b"]["size_usd"] == 200.0 and res["b"]["clamped_by"] == "single_position"

    def test_ai_capex_applies_only_to_ai_names_and_pools_across_them(self):
        b = budget_for()
        rooms = {"ai_capex_usd": 500.0}
        res = T.allocate_heat([single("ai1", 90, 400, is_ai=True), single("ai2", 80, 400, is_ai=True),
                               single("non", 70, 400, is_ai=False)], b, rooms=rooms)["decisions"]
        assert res["ai1"]["size_usd"] == 400 and res["ai2"]["size_usd"] == 100.0
        assert res["ai2"]["clamped_by"] == "ai_capex"
        assert res["non"]["size_usd"] == 400 and res["non"]["clamped_by"] is None

    def test_ai_swap_credits_back_what_it_sells(self):
        b = budget_for()
        p = pair("p", 90, 700, 5.0, freed=40.0, is_ai=True, sell_is_ai=True, sell_size=500.0)
        assert T.allocate_heat([p], b, rooms={"ai_capex_usd": 300.0})["decisions"]["p"]["size_usd"] == 700   # 300 + 500 >= 700
        assert T.allocate_heat([p], b, rooms={"ai_capex_usd": 100.0})["decisions"]["p"]["size_usd"] == 600.0

    def test_cluster_risk_budget_shrinks_in_risk_space(self):
        b = budget_for()
        d = T.allocate_heat([single("a", 50, 4000, stop=5.0, cluster="C")], b,
                            rooms={"cluster_risk_usd": {"C": 60.0}})["decisions"]["a"]
        assert d["size_usd"] == pytest.approx(1200.0) and d["clamped_by"] == "cluster_risk_budget"
        assert d["risk_usd"] == pytest.approx(60.0)

    def test_same_cluster_swap_is_credited_the_risk_it_frees(self):
        b = budget_for()
        p = pair("p", 50, 1000, 5.0, freed=50.0, cluster="C", sell_cluster="C")
        assert T.allocate_heat([p], b, rooms={"cluster_risk_usd": {"C": 0.0}})["decisions"]["p"]["status"] == "fit"

    def test_cluster_risk_max_uses_the_basis_the_policy_tested_the_ceiling_on(self):
        h, tb, e = 3742.42, 42541.95, 33730.51
        eq = T.cluster_risk_max_usd(h, 33, "invested_equity", tb, e)
        tbk = T.cluster_risk_max_usd(h, 33, "total_book", tb, e)
        assert eq == pytest.approx(h * 0.33, abs=0.01)
        assert tbk == pytest.approx(h * 0.33 * tb / e, abs=0.01) and tbk > eq
        assert T.cluster_risk_max_usd(h, None, "total_book", tb, e) is None
        assert T.cluster_risk_max_usd(h, 90, "total_book", tb, e) == round(h, 2)     # capped at the whole budget


# ---------------------------------------------------------------------------
# the adapter: rows in, rows out (smith_math._apply_heat_budget)
# ---------------------------------------------------------------------------
def _risk(h=H_LIVE, cap=10, positions=None):
    return {"total_book_usd": BOOK, "aggregate_open_risk_usd": h, "aggregate_open_risk_cap_pct": cap,
            "positions": positions if positions is not None else []}


def _drift(cluster_rows=None, ai_pct=None):
    return {"invested_equity_usd": 33730.51, "ai_capex_pct_of_equity": ai_pct,
            "ai_capex_pct_of_total_book": None if ai_pct is None else ai_pct * 0.79,
            "cluster_table": cluster_rows or []}


def _sizing(stops):
    return T.sizing_context(BOOK, POLICY, stops)


def _buy(fam, ticker, score, size, cluster="AI Semis/Fabs", vote="live"):
    return {"ticker": ticker, "trigger_type": fam, "direction": "BUY", "vote": vote, "cluster": cluster,
            "conviction_score": score, "suggested_size_usd": size, "size_wanted_usd": size,
            "clamped_by": None, "blockers": [], "price_usd": 100.0}


def _sell(fam, ticker, risk_removed, vote="live", action="trim"):
    return {"ticker": ticker, "trigger_type": fam, "direction": "TRIM", "vote": vote, "sell_action": action,
            "risk_removed_usd": risk_removed, "suggested_size_usd": 500.0, "blockers": []}


def _pair(kind, sell_t, buy_t, sell_risk, buy_size, vote="live", score=30.0, cluster="AI Semis/Fabs"):
    return {"pair_id": f"{kind}-{sell_t}-{buy_t}", "trigger_type": kind, "vote": vote, "blockers": [],
            "sell_leg": {"ticker": sell_t, "direction": "SELL", "suggested_size_usd": 600.0,
                         "risk_removed_usd": sell_risk, "cluster": cluster},
            "buy_leg": {"ticker": buy_t, "direction": "BUY", "suggested_size_usd": buy_size,
                        "clamped_by": None, "conviction_score": score, "cluster": cluster},
            "rotation_risk": {"r_freed_usd": sell_risk, "buy_size_final_usd": buy_size,
                              "buy_risk_final_usd": 0.0, "heat_delta_final_usd": 0.0}}


def _run(fams=None, pairs=None, sells=None, risk=None, drift=None, corr=None, policy=None, stops=None,
         positions=None, sector_map=None):
    dq = []
    pol = dict(POLICY, ai_capex_clusters=["AI Semis/Fabs"], **(policy or {}))
    risk = risk or _risk(positions=positions)
    block = smith_math._apply_heat_budget(
        fams or {}, pairs or {}, sells or {}, risk, drift or _drift(), pol,
        fresh_corr(0.401) if corr is None else corr, TODAY, _sizing(stops or {}), sector_map or {}, dq, {}, {})
    return block, dq


STOPS = {"AAA": 5.0, "BBB": 5.0, "CCC": 5.0, "SELL1": 10.0, "SELL2": 10.0}


class TestAdapter:
    def test_live_book_is_non_binding_and_rows_keep_their_sizes(self):
        rows = [_buy("trend_entry", "AAA", 30, 500.0), _buy("conviction_average", "BBB", 20, 400.0)]
        block, dq = _run({"trend_entry": rows[:1], "conviction_average": rows[1:]}, stops=STOPS)
        assert block["enabled"] and not block["over_cap"] and block["deferred"] == []
        assert [r["suggested_size_usd"] for r in rows] == [500.0, 400.0]
        for r in rows:
            assert r["risk_usd"] == pytest.approx(r["suggested_size_usd"] * 0.05)
            assert r["book_heat_after_usd"] == pytest.approx(r["book_heat_before_usd"] + r["risk_usd"])
            assert set(T_FIELDS) <= set(r)
        assert any("heat_budget is UNCONFIRMED" in x for x in dq)

    def test_over_cap_book_defers_every_buy_with_vote_reason_and_would_be_size(self):
        rows = [_buy("trend_entry", "AAA", 30, 500.0)]
        block, dq = _run({"trend_entry": rows}, risk=_risk(h=0.09 * BOOK), stops=STOPS)
        r = rows[0]
        assert block["over_cap"] and r["vote"] == "deferred" and r["deferred_by"] == "portfolio heat budget"
        assert r["would_be_size_usd"] == 500.0 and "exceeds the correlation-adjusted budget" in r["deferred_reason"]
        assert any("exceeds the correlation-adjusted budget" in b for b in r["blockers"])
        assert any(x.startswith("DEFERRED by the portfolio heat budget") for x in dq)

    def test_over_cap_book_still_emits_a_risk_neutral_rotation(self):
        pr = _pair("profit_rotation", "SELL1", "AAA", sell_risk=40.0, buy_size=800.0)   # buy risk 40 = freed 40
        buy = _buy("trend_entry", "BBB", 30, 500.0)
        _run({"trend_entry": [buy]}, {"profit_rotation": [pr]}, risk=_risk(h=0.09 * BOOK), stops=STOPS)
        assert pr["vote"] == "live" and pr["buy_leg"]["suggested_size_usd"] == 800.0
        assert buy["vote"] == "deferred"

    def test_a_proposed_standalone_sell_frees_no_heat_by_default(self):
        """A proposed sell has not freed anything: the user decided 2026-09-20 that even an accepted
        proposal is agreement, never an order. Crediting it lets buys spend risk that was never freed."""
        assert smith_core.STANDALONE_SELL_CREDIT_ENABLED is False
        rows = {"catalyst_threat": [_sell("catalyst_threat", "SELL1", 90.0)]}
        block, _ = _run(sells=rows, positions=[{"ticker": "SELL1", "position_open_risk_usd": 120.0, "cluster": "X"}],
                        stops=STOPS)
        assert block["sell_credit_usd"] == 0.0 and block["sell_credit_from"] == []

    def test_below_materiality_and_shadow_sells_do_not_free_heat(self, monkeypatch):
        # these exercise the credit MECHANISM, which is off by default (see the default-off test)
        monkeypatch.setattr(smith_math, "STANDALONE_SELL_CREDIT_ENABLED", True)
        # R_free is ~$0 here; one live sell would free $100, two junk sells claim $500 each
        h = 3742.42
        live = _sell("catalyst_threat", "SELL1", 100.0)
        junk = [_sell("catalyst_threat", "SELL2", 500.0, vote="below_materiality"),
                _sell("overbought_distribution", "CCC", 500.0, vote="shadow")]
        pos = [{"ticker": t, "position_open_risk_usd": 1000.0, "cluster": "X"} for t in ("SELL1", "SELL2", "CCC")]
        buy = _buy("trend_entry", "AAA", 30, 4000.0)                       # $200 of risk wanted
        block, _ = _run({"trend_entry": [buy]}, sells={"catalyst_threat": [live, junk[0]],
                                                       "overbought_distribution": [junk[1]]},
                        risk=_risk(h=h, positions=pos), stops=STOPS)
        assert block["sell_credit_usd"] == 100.0                            # ONLY the live one
        assert buy["clamped_by"] == "heat_room" and buy["risk_usd"] == pytest.approx(100.0)

    def test_a_deferred_pair_does_not_free_its_sell_leg_either(self):
        # a net-positive pair too big for the room is deferred WHOLE; its $80 sell frees nothing
        pr = _pair("cluster_rotation", "SELL1", "AAA", sell_risk=80.0, buy_size=100000.0)
        buy = _buy("trend_entry", "BBB", 30, 2000.0)                       # $100 of risk
        block, _ = _run({"trend_entry": [buy]}, {"cluster_rotation": [pr]},
                        risk=_risk(h=3742.42 - 30.0), stops=STOPS)          # R_free = 30 -> $600, above the floor
        assert pr["vote"] == "deferred" and pr["deferred_by"] == "portfolio heat budget"
        assert pr["would_be_size_usd"] == 100000.0
        assert buy["clamped_by"] == "heat_room" and buy["risk_usd"] == pytest.approx(30.0)   # not 30 + 80

    def test_a_pair_that_is_not_live_is_never_a_candidate(self):
        pr = _pair("profit_rotation", "SELL1", "AAA", sell_risk=80.0, buy_size=0.0, vote="below_materiality")
        block, _ = _run(pairs={"profit_rotation": [pr]}, stops=STOPS)
        assert pr["vote"] == "below_materiality" and pr["buy_leg"]["heat_status"].startswith("not_allocated")
        assert block["allocated"] == [] and block["deferred"] == []

    def test_credit_per_ticker_is_capped_at_the_position_own_open_risk(self, monkeypatch):
        # these exercise the credit MECHANISM, which is off by default (see the default-off test)
        monkeypatch.setattr(smith_math, "STANDALONE_SELL_CREDIT_ENABLED", True)
        # two live sell rows on one name cannot free more than the position carries
        rows = {"catalyst_threat": [_sell("catalyst_threat", "SELL1", 90.0)],
                "overbought_distribution": [_sell("overbought_distribution", "SELL1", 90.0)]}
        block, _ = _run(sells=rows, positions=[{"ticker": "SELL1", "position_open_risk_usd": 120.0, "cluster": "X"}],
                        stops=STOPS)
        assert block["sell_credit_usd"] == 120.0

    def test_single_position_clamp_shrinks_a_buy_and_names_itself(self):
        # AAA already 11% of invested equity -> a 12% cap leaves ~$400 of room
        e = 33730.51
        pos = [{"ticker": "AAA", "market_value_usd": 0.11 * e, "position_open_risk_usd": 100.0, "cluster": "X"}]
        buy = _buy("trend_entry", "AAA", 30, 2000.0)
        _run({"trend_entry": [buy]}, positions=pos, stops=STOPS, policy={"max_single_position_pct": 12})
        room = (0.12 * e - 0.11 * e) / 0.88
        assert buy["suggested_size_usd"] == pytest.approx(room, abs=0.01)
        assert buy["clamped_by"] == "single_position" and buy["size_pre_heat_usd"] == 2000.0

    def test_ai_capex_clamp_only_when_the_cap_can_bind(self):
        buy = _buy("trend_entry", "AAA", 30, 5000.0)
        # cap 100% of invested equity: unbindable by a cash-funded buy -> no shrink (live behaviour)
        _run({"trend_entry": [buy]}, drift=_drift(ai_pct=95.76), stops=STOPS,
             policy={"max_ai_capex_factor_pct": 100, "ai_capex_denominator": "invested_equity"})
        assert buy["suggested_size_usd"] == 5000.0 and buy["clamped_by"] is None
        # a 96% cap at 95.76% does bind, and shrinks
        buy2 = _buy("trend_entry", "AAA", 30, 5000.0)
        _run({"trend_entry": [buy2]}, drift=_drift(ai_pct=95.76), stops=STOPS,
             policy={"max_ai_capex_factor_pct": 96, "ai_capex_denominator": "invested_equity"})
        assert buy2["clamped_by"] == "ai_capex" and buy2["suggested_size_usd"] < 5000.0
        # a non-AI cluster is untouched by the same cap
        buy3 = _buy("bench_diversifier", "AAA", 30, 5000.0, cluster="Enterprise Software")
        _run({"bench_diversifier": [buy3]}, drift=_drift(ai_pct=95.76), stops=STOPS,
             policy={"max_ai_capex_factor_pct": 96, "ai_capex_denominator": "invested_equity"})
        assert buy3["suggested_size_usd"] == 5000.0

    def _cluster_case(self, sub_budget):
        rows = [{"cluster": "AI Semis/Fabs", "band_pct": [23, 33], "ceiling_tested_on": "invested_equity"}]
        pos = [{"ticker": "OWN", "market_value_usd": 5000.0, "position_open_risk_usd": 1230.0,
                "cluster": "AI Semis/Fabs"}]
        buy = _buy("trend_entry", "AAA", 30, 4000.0)                         # $200 of risk
        policy = {"heat_budget": {"heat_floor_at_full_correlation": 0.7, "cluster_sub_budget": sub_budget,
                                  "confirmed": False}}
        block, _ = _run({"trend_entry": [buy]}, drift=_drift(rows), positions=pos, stops=STOPS, policy=policy)
        return buy, block

    def test_cluster_sub_budget_on_clamps_in_risk_space(self):
        buy, block = self._cluster_case(True)
        cap = 3742.42 * 0.33                                                 # ~$1,235
        assert block["rooms"]["cluster_risk_max_usd"]["AI Semis/Fabs"] == pytest.approx(cap, abs=0.05)
        assert buy["clamped_by"] == "cluster_risk_budget"
        assert buy["risk_usd"] == pytest.approx(cap - 1230.0, abs=0.05)

    def test_cluster_sub_budget_off_leaves_the_buy_alone(self):
        buy, block = self._cluster_case(False)
        assert buy["suggested_size_usd"] == 4000.0 and buy["clamped_by"] is None
        assert block["rooms"]["cluster_risk_max_usd"] == {}

    def test_missing_correlation_is_disclosed_in_dq_and_block(self):
        block, dq = _run({"trend_entry": [_buy("trend_entry", "AAA", 30, 500.0)]}, corr={}, stops=STOPS)
        assert not block["rho_measured"] and block["cap_factor"] == 0.7 and "CONSERVATIVE BOUND" in block["rho_basis"]
        assert any("CONSERVATIVE bound" in x for x in dq)

    def test_no_aggregate_cap_disables_the_pass_and_touches_no_row(self):
        buy = _buy("trend_entry", "AAA", 30, 500.0)
        block, dq = _run({"trend_entry": [buy]}, risk=_risk(cap=None), stops=STOPS)
        assert block["enabled"] is False and "risk_usd" not in buy and any("DISABLED" in x for x in dq)

    def test_unallocated_rows_still_carry_their_risk(self):
        shadow = _buy("entry_setup", "AAA", 30, 500.0, vote="shadow")
        _run({"entry_setup": [shadow]}, stops=STOPS)
        assert shadow["risk_usd"] == 25.0 and shadow["heat_status"] == "not_allocated (shadow)"
        assert shadow["vote"] == "shadow"


T_FIELDS = ("risk_usd", "book_heat_before_usd", "book_heat_after_usd", "heat_room_remaining_usd")


# ---------------------------------------------------------------------------
# end to end on the golden fixtures: conservative-bound + over-cap, and measured
# ---------------------------------------------------------------------------
def _run_triggers(fixture, tmp_path, mutate=None):
    dst = tmp_path / fixture
    shutil.copytree(os.path.join(ROOT, "tests", "fixtures", fixture), dst)
    if mutate:
        mutate(dst)
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "smith_math.py"), "triggers", "--base-dir",
                        str(dst / "base"), "--run-dir", str(dst / "rundir"), "--today", "2026-09-01"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


class TestFixtureBooks:
    def test_case1_has_no_correlation_file_so_it_runs_on_the_conservative_bound_and_is_over_cap(self, tmp_path):
        out = _run_triggers("triggers_case1", tmp_path)
        h = out["heat_budget"]
        assert not h["rho_measured"] and "compute_correlation.json absent" in h["rho_basis"]
        assert h["over_cap"] and h["h_usd"] > h["h_eff_max_usd"]
        live_buys = [r for f in ("trend_entry", "conviction_average", "reentry", "entry_setup", "bench_diversifier",
                                 "oversold_reversion") for r in out[f] if r.get("vote") == "live"]
        # nothing that ADDS risk survives as live; whatever is left carries no size
        assert all((r.get("risk_usd") or 0) == 0 for r in live_buys)
        deferred = [r for f in ("conviction_average", "reentry", "trend_entry") for r in out[f] if r["vote"] == "deferred"]
        assert deferred and all(r["deferred_by"] == "portfolio heat budget" and r["would_be_size_usd"] for r in deferred)
        assert out["deferred_counts"]

    def test_case1_risk_neutral_rotation_still_emits_when_over_cap(self, tmp_path):
        out = _run_triggers("triggers_case1", tmp_path)
        rot = [r for f in ("cluster_rotation", "profit_rotation") for r in out[f] if r["vote"] == "live"]
        assert rot and all(r["buy_leg"]["risk_usd"] <= (r["rotation_risk"]["r_freed_usd"] + 0.01) for r in rot)

    def test_case2_measured_correlation_gives_room_and_a_greedy_split(self, tmp_path):
        out = _run_triggers("triggers_case2_ladder", tmp_path)
        h = out["heat_budget"]
        assert h["rho_measured"] and h["rho"] == 0.3 and not h["over_cap"] and h["r_free_usd"] > 0
        assert h["book_heat_after_allocation_usd"] <= h["h_eff_max_usd"] + 0.05
        spent = sum(a["net_risk_usd"] for a in h["allocated"])
        assert spent <= h["r_available_usd"] + 0.05

    def test_fixture_stale_correlation_falls_back_to_conservative(self, tmp_path):
        def stale(dst):
            c = json.load(open(dst / "rundir" / "compute_correlation.json"))
            c["window"]["to"] = "2026-06-01"
            json.dump(c, open(dst / "rundir" / "compute_correlation.json", "w"))
        out = _run_triggers("triggers_case2_ladder", tmp_path, stale)
        assert not out["heat_budget"]["rho_measured"] and out["heat_budget"]["over_cap"]

    def test_thresholds_publish_the_rule(self, tmp_path):
        out = _run_triggers("triggers_case2_ladder", tmp_path)
        hb = out["thresholds"]["sizing"]["heat_budget"]
        assert hb["static_clamps"] == ["single_position", "ai_capex", "cluster_risk_budget"] and hb["heat_floor"] == 0.7


# ---------------------------------------------------------------------------
# policy.heat_budget + validate
# ---------------------------------------------------------------------------
class TestPolicy:
    def test_live_policy_block_is_unconfirmed_and_valid(self):
        import smith_memory
        pol = json.load(open(os.path.join(ROOT, "policy.json")))
        hb = pol["heat_budget"]
        assert hb["confirmed"] is False and hb["heat_floor_at_full_correlation"] == 0.70 and hb["cluster_sub_budget"] is True
        assert smith_memory.validate_heat_budget(pol) == []

    def test_validate_rejects_bad_blocks_and_accepts_absence(self):
        import smith_memory as M
        assert M.validate_heat_budget({}) == []
        good = {"heat_floor_at_full_correlation": 0.7, "cluster_sub_budget": True, "confirmed": False}
        assert M.validate_heat_budget({"heat_budget": good}) == []
        assert M.validate_heat_budget({"heat_budget": dict(good, heat_floor_at_full_correlation=1.4)})
        assert M.validate_heat_budget({"heat_budget": dict(good, heat_floor_at_full_correlation=True)})
        assert M.validate_heat_budget({"heat_budget": dict(good, cluster_sub_budget="yes")})
        assert M.validate_heat_budget({"heat_budget": dict(good, confirmed=True)})            # no stamp
        assert M.validate_heat_budget({"heat_budget": dict(good, confirmed=True, confirmed_by_user="2026-09-21")}) == []
        assert M.validate_heat_budget({"heat_budget": []})


# ---------------------------------------------------------------------------
# learned_stop: reachable, advisory, never operative
# ---------------------------------------------------------------------------
class TestLearnedStop:
    STORE = {"parameters": {"stops.atr_multiple.mid": {"state": "active", "current": 2.249, "measured": 2.249}}}

    def test_only_an_active_parameter_on_a_mid_tier_name(self):
        f = smith_risk.learned_stop_multiple_for
        assert f(4.28, self.STORE) == 2.249
        assert f(2.0, self.STORE) is None and f(6.0, self.STORE) is None and f(None, self.STORE) is None   # measured on mid only
        assert f(3.0, self.STORE) == 2.249 and f(5.49, self.STORE) == 2.249 and f(5.5, self.STORE) is None
        for state in ("shadow", "escalated", "default"):
            store = {"parameters": {"stops.atr_multiple.mid": {"state": state, "current": 2.249}}}
            assert f(4.28, store) is None
        assert f(4.28, {}) is None and f(4.28, None) is None

    def test_the_mid_tier_range_matches_lifecycle_vol_tiers(self):
        import smith_lifecycle
        tiers = dict(smith_lifecycle.VOL_TIERS)
        assert smith_core.STOP_LEARNED_MID_ATR_RANGE == (tiers["low"], tiers["mid"])

    def test_it_never_changes_the_operative_stop_or_size(self):
        pol = {"stop_loss_framework": {"risk_per_position_pct_of_book": 0.5}}
        plain = smith_risk.stop_and_cap(4.28, 100.0, 10, BOOK, pol)
        learned = smith_risk.stop_and_cap(4.28, 100.0, 10, BOOK, pol, learned_multiple=2.249)
        assert "learned_stop" not in plain and learned["learned_stop"]["stop_distance_pct"] == pytest.approx(9.626, abs=0.001)
        assert {k: v for k, v in learned.items() if k != "learned_stop"} == plain

    def test_policy_max_position_forwards_it_without_touching_the_size(self):
        pol = {"stop_loss_framework": {"risk_per_position_pct_of_book": 0.5}}
        a = smith_conviction.policy_max_position_usd(4.28, 100.0, BOOK, pol)
        b = smith_conviction.policy_max_position_usd(4.28, 100.0, BOOK, pol, learned_multiple=2.249)
        assert "learned_stop" in b and a["max_position_usd"] == b["max_position_usd"] and a["stop_price_usd"] == b["stop_price_usd"]

    def test_learned_stop_is_surfaced_on_buy_rows_only_for_mid_names(self):
        buy = _buy("trend_entry", "AAA", 30, 500.0)
        smith_math._apply_heat_budget({"trend_entry": [buy]}, {}, {}, _risk(), _drift(), POLICY, fresh_corr(0.4), TODAY,
                                      _sizing(STOPS), {}, [], {"AAA": 4.28}, self.STORE)
        assert buy["learned_stop"]["atr_multiple"] == 2.249 and "advisory" in buy["learned_stop"]["status"]
        hi = _buy("trend_entry", "AAA", 30, 500.0)
        smith_math._apply_heat_budget({"trend_entry": [hi]}, {}, {}, _risk(), _drift(), POLICY, fresh_corr(0.4), TODAY,
                                      _sizing(STOPS), {}, [], {"AAA": 8.0}, self.STORE)
        assert "learned_stop" not in hi


# ---------------------------------------------------------------------------
# pipeline order: the budget reads correlation, so correlation must run first
# ---------------------------------------------------------------------------
def test_correlation_stage_precedes_triggers():
    src = open(os.path.join(SCRIPTS, "smith_math.py")).read()
    assert src.index('("correlation", ["compute_risk.json"') < src.index('("triggers",    ["compute_risk.json"')

"""Phase 2 of the proposal-engine rebuild (2026-09-20): sells and rotation buys sized in RISK
DOLLARS (smith_ticket.py), a materiality floor, the exit-or-hold rule, SEVERITY_R replacing every
market-value sell fraction, real cluster room at every buy site, and candidate prices for
entry_setup. The motivating incident throughout: a $56.37 SKHY->CIEN rotation on a $42.5K book,
where a correct 10-point call earns $5.64.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tokenize

import pytest

import smith_core
import smith_math
import smith_ticket as T

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "scripts")

BOOK = 42541.95                      # the live 2026-09-20 book
POLICY = {"stop_loss_framework": {"risk_per_position_pct_of_book": 0.5}}
R_BASE = T.r_base_usd(BOOK, POLICY)  # $212.71


def ctx(book=BOOK, stops=None):
    return T.sizing_context(book, POLICY, stops or {})


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------
class TestPrimitives:
    def test_r_base_is_half_a_percent_of_book(self):
        assert R_BASE == pytest.approx(212.71, abs=0.01)

    def test_size_from_risk(self):
        assert T.size_from_risk(212.71, 12.0) == pytest.approx(1772.58, abs=0.01)
        assert T.size_from_risk(None, 12.0) is None and T.size_from_risk(10.0, 0) is None

    def test_stop_rule_matches_smith_risk(self):
        import smith_risk
        for atr in (1.0, 1.5, 3.9, 6.0, 12.0):
            assert T.stop_pct_from_atr(atr) == smith_risk.stop_and_cap(atr, 100.0, 1, BOOK, POLICY)["stop_distance_pct"]
        assert T.stop_pct_from_atr(None) is None


# ---------------------------------------------------------------------------
# THE PROPERTY: size x stop/100 == severity x R_base, or clamped by mv with a named reason
# ---------------------------------------------------------------------------
class TestSellSizeProperty:
    ATRS = (1.2, 1.5, 2.29, 3.0, 3.92, 4.6, 6.0, 8.5, 12.0)
    MVS = (2.98, 150.0, 187.9, 800.0, 2035.87, 6000.0, 30000.0)
    SEVS = (0.1, 0.25, 0.5, 1.0, 2.0)

    def test_risk_removed_equals_severity_or_clamped_by_mv(self):
        checked = clamped = 0
        for atr in self.ATRS:
            stop = T.stop_pct_from_atr(atr)
            for mv in self.MVS:
                for sev in self.SEVS:
                    r = T.sell_size_from_risk(sev, R_BASE, stop, mv)
                    if r["clamped_by_mv"]:
                        clamped += 1
                        assert r["size_usd"] == pytest.approx(mv, abs=0.005)
                        assert r["unclamped_usd"] >= mv - 0.005          # and it names WHY
                    else:
                        checked += 1
                        # size is rounded to a cent, so the risk it carries is exact to a cent x stop
                        assert r["size_usd"] * stop / 100 == pytest.approx(sev * R_BASE, abs=0.005 * stop / 100 + 1e-9)
                    assert r["size_usd"] <= mv + 1e-9
        assert checked > 50 and clamped > 20      # the grid actually exercises both branches

    def test_open_risk_property_size_x_stop_equals_severity_x_R_open(self):
        """risk_removed == severity * R_open(t), R_open = mv * stop/100 (the unit SEVERITY_R uses)."""
        for atr in self.ATRS:
            stop = T.stop_pct_from_atr(atr)
            for mv in self.MVS:
                for sev in (0.2, 0.25, 0.3, 0.4, 0.5, 1.0):
                    r = T.sell_size_from_open_risk(sev, mv, stop)
                    r_open = mv * stop / 100
                    if sev >= 1.0:
                        assert r["clamped_by_mv"] and r["size_usd"] == pytest.approx(mv, abs=0.005)
                    else:
                        assert not r["clamped_by_mv"]
                        assert r["size_usd"] * stop / 100 == pytest.approx(sev * r_open, abs=0.005 * stop / 100 + 1e-9)
                        assert r["risk_removed_usd"] == pytest.approx(sev * r_open, abs=0.01)

    def test_same_severity_removes_the_same_fraction_of_every_position(self):
        """Severity is relative to the position, so a 3%-ATR and a 12%-ATR name of equal size lose
        the same dollars but the volatile one sheds proportionally more absolute risk."""
        calm = T.sell_size_from_open_risk(0.2, 3000.0, T.stop_pct_from_atr(3.0))
        loud = T.sell_size_from_open_risk(0.2, 3000.0, T.stop_pct_from_atr(12.0))
        assert calm["size_usd"] == loud["size_usd"] == 600.0
        assert loud["risk_removed_usd"] > calm["risk_removed_usd"]

    def test_r_base_units_are_still_available_for_trim_risk_cap(self):
        assert T.sell_size_from_risk(0.5, R_BASE, 12.0, 100000.0)["size_usd"] == pytest.approx(886.29, abs=0.01)

    def test_low_atr_name_gets_larger_dollar_trim_for_same_severity(self):
        calm = T.sell_size_from_risk(0.5, R_BASE, T.stop_pct_from_atr(3.0), 100000.0)["size_usd"]
        loud = T.sell_size_from_risk(0.5, R_BASE, T.stop_pct_from_atr(12.0), 100000.0)["size_usd"]
        assert calm > loud
        assert calm * T.stop_pct_from_atr(3.0) == pytest.approx(loud * T.stop_pct_from_atr(12.0), rel=1e-3)  # equal RISK

    def test_missing_inputs_are_never_estimated(self):
        assert T.sell_size_from_risk(0.5, R_BASE, None, 1000.0)["size_usd"] is None
        leg = T.size_sell_leg(0.5, 1000.0, None, ctx())
        assert leg["size_usd"] is None and leg["vote_hint"] == T.UNSIZED


class TestTrimRiskCap:
    def test_trims_exactly_back_to_the_cap_and_never_past_it(self):
        for atr in (2.29, 3.92, 6.0, 12.0):
            stop = T.stop_pct_from_atr(atr)
            max_pos = R_BASE / (stop / 100)
            for over in (1.05, 1.3, 2.0):
                mv = max_pos * over
                sev = T.trim_risk_cap_severity(mv * stop / 100, R_BASE)
                assert sev == pytest.approx(over - 1.0, abs=1e-9)
                size = T.sell_size_from_risk(sev, R_BASE, stop, mv)["size_usd"]
                assert size == pytest.approx(mv - max_pos, abs=0.01)             # exactly the excess
                assert (mv - size) <= max_pos + 0.01                              # lands on the cap...
                assert (mv - size) >= max_pos - 0.01                              # ...not below it

    def test_at_or_under_cap_has_nothing_to_trim(self):
        assert T.trim_risk_cap_severity(100.0, R_BASE) == 0.0


# ---------------------------------------------------------------------------
# rotation legs: risk-conserving
# ---------------------------------------------------------------------------
class TestRotationLegs:
    def test_the_worked_example_from_the_live_run(self):
        """Selling $610.76 of MU (12% stop) frees $73.30 of risk; AMAT (7.84% stop) buys $935 on it."""
        legs = T.rotation_legs(610.76, 12.0, None, 7.84)
        assert legs["r_freed_usd"] == pytest.approx(73.29, abs=0.01)
        assert legs["buy_size_usd"] == pytest.approx(934.8, abs=0.5)
        assert legs["bound_by"] == "r_freed" and legs["heat_delta_usd"] == 0.0

    def test_heat_after_equals_heat_before_within_5pct(self):
        """A rotation must leave aggregate open risk where it was (fixture pair, no clamp binding)."""
        sell, sell_stop, buy_stop = 1500.0, 9.0, 4.6
        legs = T.rotation_legs(sell, sell_stop, buy_r_ticket=None, buy_stop_pct=buy_stop)
        heat_out = sell * sell_stop / 100
        heat_in = legs["buy_size_usd"] * buy_stop / 100
        assert abs(heat_in - heat_out) <= 0.05 * heat_out

    def test_buy_is_capped_by_its_own_ticket_and_the_bound_is_named(self):
        legs = T.rotation_legs(610.76, 12.0, buy_r_ticket=39.55, buy_stop_pct=7.84)
        assert legs["bound_by"] == "buy_r_ticket"
        assert legs["buy_size_usd"] == pytest.approx(504.5, abs=0.5)     # the $504.51 tranche
        assert legs["heat_delta_usd"] < 0                                  # ...so it is NOT flat: honest

    def test_no_sell_leg_no_buy(self):
        assert T.rotation_legs(0.0, 12.0, None, 7.84)["buy_size_usd"] == 0.0

    def test_rotation_buy_names_the_binding_clamp(self):
        conv = {"headroom_usd": 300.0}
        size, by, legs = smith_math._rotation_buy_leg(610.76, "MU", "AMAT", conv, None, None,
                                                      ctx(stops={"MU": 12.0, "AMAT": 7.84}))
        assert size == 300.0 and by == "ATR headroom"                     # an existing clamp binds
        size, by, _ = smith_math._rotation_buy_leg(610.76, "MU", "AMAT", {"headroom_usd": 5000.0}, None, 150.0,
                                                   ctx(stops={"MU": 12.0, "AMAT": 7.84}))
        assert size == 150.0 and by == "cluster ceiling room"
        size, by, _ = smith_math._rotation_buy_leg(610.76, "MU", "AMAT", {"headroom_usd": 5000.0}, 39.55, None,
                                                   ctx(stops={"MU": 12.0, "AMAT": 7.84}))
        assert by == "buy R_ticket (its own conviction tranche)"


# ---------------------------------------------------------------------------
# materiality
# ---------------------------------------------------------------------------
class TestMateriality:
    def test_the_skhy_56_dollar_rotation_is_below_materiality(self):
        m = T.materiality(56.37, 14.0, BOOK, R_BASE, 56.37 * 0.003, None)
        assert m["ok"] is False and m["shortfall_usd"] > 190
        # at MIN_TICKET_R 0.10 the dollar floor is what binds a $56 ticket on a 14% stop
        assert m["binding_term"] == "min_ticket_usd"
        assert m["floor_usd"] >= 250

    def test_floor_is_the_max_of_the_terms(self):
        m = T.materiality(10000.0, 12.0, BOOK, R_BASE, 30.0, None)
        assert m["floor_usd"] == max(m["terms"].values())
        assert m["terms"]["min_ticket_usd"] == 250.0
        assert m["terms"]["pct_of_book"] == pytest.approx(BOOK * 0.004, abs=0.01)
        assert m["terms"]["min_ticket_r"] == pytest.approx(0.1 * R_BASE / 0.12, abs=0.01)

    def test_low_vol_names_have_higher_floors(self):
        lo = T.materiality(1.0, 4.58, BOOK, R_BASE, 0.0, None)["floor_usd"]
        hi = T.materiality(1.0, 12.0, BOOK, R_BASE, 0.0, None)["floor_usd"]
        assert lo > hi

    def test_a_ticket_exactly_at_the_floor_passes(self):
        floor = T.materiality(1.0, 8.0, BOOK, R_BASE, 0.0, None)["floor_usd"]
        assert T.materiality(floor, 8.0, BOOK, R_BASE, 0.0, None)["ok"]
        assert not T.materiality(floor - 0.01, 8.0, BOOK, R_BASE, 0.0, None)["ok"]

    def test_policy_floors_override_defaults(self):
        m = T.materiality(300.0, 8.0, BOOK, R_BASE, 0.0, {"min_ticket_usd": 900})
        assert not m["ok"] and m["binding_term"] == "min_ticket_usd"

    def test_fee_term_is_inert_under_a_proportional_fee_but_binds_on_a_fixed_one(self):
        # 0.30% of size x 25 = 7.5% of size: never above the size itself...
        for size in (100.0, 1000.0, 50000.0):
            m = T.materiality(size, 8.0, BOOK, R_BASE, size * 0.003, None)
            assert m["terms"]["fee_cover"] < size
        # ...but a fixed $30 per-order fee would set a $750 floor.
        assert T.materiality(500.0, 8.0, BOOK, R_BASE, 30.0, {"min_ticket_r": 0.0001})["binding_term"] == "fee_cover"

    def test_sub_floor_sell_emits_below_materiality_not_shrunk_not_dropped(self):
        # a tiny severity on a big position: a genuine partial trim that is too small to matter
        leg = T.size_sell_leg(0.01, 20000.0, 10.0, ctx())
        assert leg["action"] == "trim" and leg["vote_hint"] == "below_materiality"
        assert leg["size_usd"] == pytest.approx(0.01 * 20000.0, abs=0.01)             # NOT lifted to the floor
        assert leg["materiality"]["shortfall_usd"] > 0

    def test_full_exit_below_the_floor_is_still_permitted(self):
        leg = T.size_sell_leg(1.0, 187.9, 14.0, ctx())           # a severity of 1.0 asks for everything
        assert leg["action"] == "full_exit" and leg["size_usd"] == 187.9
        assert leg["vote_hint"] == "ok" and leg["materiality"]["exempt"] == "full_exit"
        assert leg["materiality"]["floor_usd"] > 187.9         # it IS below the floor, and is allowed anyway


# ---------------------------------------------------------------------------
# exit-or-hold and stubs
# ---------------------------------------------------------------------------
class TestExitOrHold:
    MIN = smith_core.DUST_USD_DEFAULT

    def test_plain_trim_passes_through(self):
        r = T.exit_or_hold(2000.0, 500.0, self.MIN)
        assert r == {"action": "trim", "size_usd": 500.0, "reason": None}

    def test_residual_under_the_minimum_becomes_a_full_exit(self):
        r = T.exit_or_hold(600.0, 300.0, self.MIN)              # would leave $300 < $400
        assert r["action"] == "full_exit" and r["size_usd"] == 600.0 and "minimum position" in r["reason"]

    def test_more_than_60pct_becomes_a_full_exit_and_says_so(self):
        r = T.exit_or_hold(2000.0, 1300.0, self.MIN)            # 65%, residual $700 is fine
        assert r["action"] == "full_exit" and "65%" in r["reason"]
        assert T.exit_or_hold(2000.0, 1200.0, self.MIN)["action"] == "trim"     # exactly 60% is not "more than"

    def test_stubs_are_never_partially_trimmed(self):
        for mv in (2.98, 37.58, 187.9, 399.99):
            for trim in [t for t in (0.5, 10.0, 56.37, mv * 0.5, mv * 0.99) if t < mv]:
                r = T.exit_or_hold(mv, trim, self.MIN)
                assert r["action"] == "hold" and r["size_usd"] == 0.0, (mv, trim)
            assert T.exit_or_hold(mv, mv, self.MIN)["action"] == "full_exit"    # ...but may be exited whole

    def test_skhy_and_cien_absurdities_stop_at_the_source(self):
        """$37.58 SKHY / $2.98 CIEN 'trims' can no longer be produced: full exit or nothing."""
        skhy = T.size_sell_leg(0.5, 187.9, 14.0, ctx())
        assert skhy["size_usd"] in (0.0, 187.9) and skhy["action"] in ("hold", "full_exit")
        cien = T.size_sell_leg(0.5, 2.98, 8.0, ctx())
        assert cien["size_usd"] in (0.0, 2.98)

    def test_one_dust_number_not_two(self):
        """MIN_POSITION_USD must BE smith_core.DUST_USD_DEFAULT, not a second constant that can
        drift from the one cmd_derisk and smith_lifecycle already use."""
        assert ctx()["min_position_usd"] == smith_core.DUST_USD_DEFAULT
        assert smith_core.dust_usd({}) == smith_core.DUST_USD_DEFAULT
        assert smith_core.dust_usd({"mandate": {"dust_position_usd": 250}}) == 250      # the existing override still wins
        for mod in ("smith_core.py", "smith_ticket.py"):
            src = open(os.path.join(SCRIPTS, mod)).read()
            assert "MIN_POSITION_USD =" not in src and "MIN_POSITION_USD=" not in src


# ---------------------------------------------------------------------------
# SEVERITY_R replaces every sell fraction
# ---------------------------------------------------------------------------
class TestSeverityTable:
    def test_table_is_fractions_of_the_positions_own_open_risk(self):
        """The first table (0.5/1.0/2.0 in R_base units) turned 20% catalyst trims into 100%
        liquidations. The unit is now the position's own open risk, at the legacy magnitudes."""
        assert smith_core.SEVERITY_R == {
            "overbought_distribution": 0.25, "catalyst_threat": 0.20, "scale_out_ladder": 1.0 / 3.0,
            "profit_rotation": 0.30, "cluster_rotation": 0.30, "cluster_bench_rotation": 0.30,
            "trend_breakdown": 0.30, "thesis_break": 0.40, "conviction_exit": 0.50}
        assert all(0 < v < 1 for v in smith_core.SEVERITY_R.values())    # a trim, never a liquidation

    def test_unclamped_sells_agree_with_the_legacy_numbers(self):
        for fam, sev in smith_core.SEVERITY_R.items():
            assert sev == pytest.approx(smith_core.LEGACY_SELL_FRACTION[fam])

    def test_no_uncapped_catalyst_trim_exceeds_40pct_of_the_position(self):
        """REGRESSION GUARD. At the ATR cap (where this book's positions sit) a catalyst_threat
        trim must stay a ~20% trim across volatilities and position sizes -- never the 50-100%
        liquidation the R_base-unit table produced on the live 2026-09-20 run."""
        for atr in (1.5, 2.29, 3.92, 6.0, 8.56, 12.0):
            stop = T.stop_pct_from_atr(atr)
            max_pos = R_BASE / (stop / 100)                       # a position sitting exactly at its cap
            for mult in (1.0, 1.15):
                mv = max_pos * mult
                if mv < 2 * smith_core.DUST_USD_DEFAULT:
                    continue                                       # sub-scale positions may legitimately exit
                leg = T.size_sell_leg(smith_core.SEVERITY_R["catalyst_threat"], mv, stop, ctx())
                assert leg["action"] == "trim", (atr, mult, leg["sizing_note"])
                assert leg["size_usd"] <= 0.40 * mv
                assert leg["size_usd"] == pytest.approx(0.20 * mv, abs=0.01)

    def test_the_old_fraction_constants_are_gone(self):
        for name in ("OVERBOUGHT_TRIM_FRACTION", "CATALYST_THREAT_TRIM_FRACTION",
                     "THESIS_BREAK_TRIM_FRACTION", "LADDER_FRACTION"):
            assert not hasattr(smith_core, name), name
            for root in ("scripts", "skill", "tests/unit"):
                for dirpath, _, files in os.walk(os.path.join(ROOT, root)):
                    for f in files:
                        if f.endswith((".py", ".md", ".sh")) and f != "test_smith_ticket_sizing.py":
                            assert name not in open(os.path.join(dirpath, f)).read(), (name, dirpath, f)

    def test_every_sell_family_has_a_severity_and_a_legacy_number(self):
        for fam in smith_core.SEVERITY_R:
            assert fam in smith_core.LEGACY_SELL_FRACTION

    def test_no_bare_sell_fraction_literal_survives_in_the_trigger_code(self):
        """Grep-style guard: 0.20/0.25/0.30/0.40/0.50 (and 1/3) must not reappear as a NUMBER token
        anywhere in the trigger functions or cmd_triggers. Comments and docstrings are ignored --
        only executable numbers count -- so the rationale can still quote the old fractions."""
        path = os.path.join(SCRIPTS, "smith_math.py")
        src = open(path).read()
        lines = src.splitlines()
        start = next(i for i, l in enumerate(lines, 1) if l.startswith("# RISK-SIZED SELLS (Phase 2"))
        end = next(i for i, l in enumerate(lines, 1) if l.startswith("def _draft_leg_spec"))
        # cmd_buckets (0.30 is a RANK cutoff there, not a sell fraction) sits inside this range: skip it
        skip_from = next(i for i, l in enumerate(lines, 1) if l.startswith("def cmd_buckets"))
        skip_to = next(i for i, l in enumerate(lines, 1) if l.startswith("def _bucket_expectancy_r"))
        banned = {0.2, 0.25, 0.3, 0.4, 0.5}
        hits = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            ln = tok.start[0]
            if tok.type == tokenize.NUMBER and start <= ln <= end and not (skip_from <= ln < skip_to):
                try:
                    val = float(tok.string)
                except ValueError:
                    continue
                if val in banned or tok.string.replace(" ", "") in ("1/3",):
                    hits.append((ln, tok.string, lines[ln - 1].strip()))
        assert not hits, f"bare sell-fraction literal(s) crept back in: {hits}"

    def test_guard_actually_detects_a_literal(self):
        """The guard must be able to fail -- prove it on a synthetic snippet."""
        toks = [t.string for t in tokenize.generate_tokens(io.StringIO("size = mv * 0.30\n").readline)
                if t.type == tokenize.NUMBER]
        assert toks == ["0.30"] and float(toks[0]) in {0.2, 0.25, 0.3, 0.4, 0.5}


# ---------------------------------------------------------------------------
# wired into the trigger functions
# ---------------------------------------------------------------------------
def _base(ticker="AAA", mv=1000.0):
    from conftest import make_base
    return make_base(ticker=ticker, market_value_usd=mv)


class TestWiredTriggers:
    def sizing(self, book=10000.0, stops=None):
        return T.sizing_context(book, POLICY, stops or {"AAA": 8.0})

    def test_overbought_row_carries_the_full_audit_trail(self):
        out = []
        smith_math._trigger_overbought_distribution(
            _base(), "AAA", True, 80.0, True, 12.0, 1000.0, {}, {}, {}, {}, {}, out, self.sizing())
        row = out[0]
        for k in ("severity_r", "stop_pct", "risk_removed_usd", "sell_action", "legacy_size_usd",
                  "sizing_note", "materiality", "trim_fraction"):
            assert k in row, k
        assert row["legacy_size_usd"] == 250.0 and row["vote"] == "live"

    def test_stub_catalyst_threat_is_a_full_exit_never_a_37_dollar_trim(self):
        out = []
        cats = {"SKHY": [{"headline": "x", "date": "2026-09-01", "magnitude": "m", "source": "s"}]}
        smith_math._trigger_catalyst_threat(
            _base("SKHY", 187.9), "SKHY", 187.9, cats, {}, "watch", out, self.sizing(BOOK, {"SKHY": 14.0}))
        row = out[0]
        # 20% of a $187.90 stub is the old $37.58 -- and a stub is never partially trimmed
        assert row["legacy_size_usd"] == 37.58 and row["suggested_size_usd"] == 0.0
        assert row["sell_action"] == "hold" and row["vote"] == "below_materiality"

    def test_sub_floor_live_sell_is_demoted_but_still_emitted(self):
        out = []
        cats = {"AAA": [{"headline": "x", "date": "2026-09-01", "magnitude": "m", "source": "s"}]}
        # a $1,000 position: 20% = $200, a genuine partial trim (residual $800) but under the $250 floor
        smith_math._trigger_catalyst_threat(_base(mv=1000.0), "AAA", 1000.0, cats, {}, "intact", out, self.sizing())
        row = out[0]
        assert row["vote"] == "below_materiality" and row["materiality_shortfall_usd"] == 50.0
        assert row["suggested_size_usd"] == 200.0 and row["sell_action"] == "trim"   # not lifted to the floor
        assert any("below materiality" in b for b in row["blockers"])

    def test_no_stop_means_no_size_and_a_blocker(self):
        out = []
        smith_math._trigger_thesis_break(_base(), "AAA", "broken", 1000.0,
                                         {"AAA": {"status": "broken", "evidence_against": [{"claim": "c"}],
                                                  "evidence_for": [], "verified": "primary"}},
                                         out, T.sizing_context(10000.0, POLICY, {}))
        assert out[0]["suggested_size_usd"] is None
        assert any("never estimated" in b for b in out[0]["blockers"])

    def test_ladder_rungs_are_risk_sized_with_legacy_slice_kept(self):
        ratchet, ladder, dq = [], [], []
        smith_math._trigger_ratchet_and_ladder(
            _base(mv=1300.0), "AAA", {"stop_price_usd": 100.0}, 1300.0, 130.0, 55.0,
            {"AAA": [{"qty": 10, "price_usd": 100.0}]}, set(), ratchet, ladder, dq, self.sizing())
        t0 = ladder[0]["tiers"][0]
        assert t0["slice_usd"] == t0["legacy_slice_usd"] == round(1300 / 3, 2)

    def test_profit_rotation_skhy_cien_is_below_materiality_with_the_stub_never_partially_trimmed(self):
        out = []
        conv = {
            "SKHY": {"market_value_usd": 187.9, "cluster": "Mem", "rel_pp": 10.0, "over_cap": False,
                     "headroom_usd": 1000.0, "conviction_tier": "medium", "conviction_score": 50.0,
                     "conviction_tier_pct": 0.6, "atr_pct": 7.0, "price": 50.0},
            "CIEN": {"market_value_usd": 2.98, "cluster": "Opt", "rel_pp": -8.0, "over_cap": False,
                     "headroom_usd": 900.0, "conviction_tier": "medium", "conviction_score": 50.0,
                     "conviction_tier_pct": 0.6, "atr_pct": 4.0, "price": 100.0}}
        smith_math._trigger_profit_rotation(
            {"SKHY"}, conv, {"SKHY": "x|watch", "CIEN": "y|strengthening"}, BOOK, POLICY, out)
        pair = out[0]
        assert pair["sell_leg"]["legacy_size_usd"] == 56.37
        # 30% of a $187.90 stub is the old $56.37 -- it is now NO partial trim of a stub at all
        assert pair["sell_leg"]["sell_action"] == "hold"
        assert pair["sell_leg"]["suggested_size_usd"] == 0.0 and pair["buy_leg"]["suggested_size_usd"] == 0.0
        assert pair["vote"] == "below_materiality" and "sell" in pair["materiality_legs_below"]

    def test_live_counts_exclude_below_materiality_rows(self, tmp_path):
        out = _run_triggers("triggers_case1", tmp_path)
        assert out["live_counts"]["profit_rotation"] == 0
        assert out["below_materiality_counts"]["profit_rotation"] == 2
        assert all(r["vote"] == "below_materiality" for r in out["profit_rotation"])

    def test_thresholds_publish_the_sizing_parameters(self, tmp_path):
        s = _run_triggers("triggers_case1", tmp_path)["thresholds"]["sizing"]
        assert s["currency"] == "risk_dollars" and s["severity_r"] == smith_core.SEVERITY_R
        assert s["materiality"]["confirmed"] is False and s["exit_or_hold"]["min_position_usd"] == 400.0
        assert s["r_base_usd"] > 0 and "trim_risk_cap" in s["severity_r_computed"]


def _run_triggers(fixture, tmp_path, mutate=None):
    src = os.path.join(ROOT, "tests", "fixtures", fixture)
    dst = tmp_path / fixture
    shutil.copytree(src, dst)
    if mutate:
        mutate(dst)
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "smith_math.py"), "triggers", "--base-dir",
                        str(dst / "base"), "--run-dir", str(dst / "rundir"), "--today", "2026-09-01"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ---------------------------------------------------------------------------
# cluster_room is REAL at every buy site (was None at four of six)
# ---------------------------------------------------------------------------
class TestClusterRoomIsReal:
    def _held(self, cluster_rows, **kw):
        from test_smith_math_triggers import _ctx_builder, POLICY as P
        te, tb, ca, ce, dq = [], [], [], [], []
        thesis = {"AAA": "strengthening thesis|strengthening"}
        smith_math._trigger_conviction_held(
            _base(), "AAA", {"cluster": "Compute"}, mv=1000.0, price=100.0, rsi=50.0, rel_pp=5.0,
            rsi_usable=True, healthy=True, over_cap=False, headroom=5000.0, thesis=thesis,
            signal_history={"AAA": ["BREAKOUT"]}, atr_vals={"AAA": 8.0}, total_book=100000.0, policy=P,
            deployable_for_ideas=10000.0, build_ctx=_ctx_builder(thesis), conviction_by_ticker={},
            catalyst_threats_by_ticker={}, lots={}, trend_entry=te, trend_breakdown=tb,
            conviction_average=ca, conviction_exit=ce, dq=dq, cluster_rows=cluster_rows)
        return te

    def test_trend_entry_is_clamped_by_cluster_ceiling_room(self):
        te = self._held({"Compute": {"cluster_room_usd": 25.0}})
        assert te[0]["suggested_size_usd"] == 25.0 and te[0]["clamped_by"] == "cluster ceiling room"

    def test_unknown_cluster_room_stays_non_binding(self):
        te = self._held({})
        assert te[0]["clamped_by"] != "cluster ceiling room" and te[0]["suggested_size_usd"] > 25.0

    def test_room_helper_returns_none_when_unknown(self):
        assert smith_math._cluster_room_for({}, "X") is None
        assert smith_math._cluster_room_for({"X": {"cluster_room_usd": None}}, "X") is None
        assert smith_math._cluster_room_for({"X": {"cluster_room_usd": 5.0}}, "X") == 5.0
        assert smith_math._cluster_room_for({"X": {"cluster_room_usd": 5.0}}, None) is None

    def test_no_buy_site_passes_a_literal_none_cluster_room_any_more(self):
        """clamp_size(..., None, ...) as the cluster argument is the bug this replaces."""
        src = open(os.path.join(SCRIPTS, "smith_math.py")).read()
        import re
        bad = re.findall(r"clamp_size\([^)]*?,\s*None\s*,\s*None\s*,\s*deployable", src)
        bad += re.findall(r"clamp_size\(wanted,\s*headroom,\s*None,", src)
        assert not bad, bad


# ---------------------------------------------------------------------------
# prerequisite: candidate prices for entry_setup, fetched not derived
# ---------------------------------------------------------------------------
class TestCandidatePrices:
    ROW = {"ticker": "ZZZ", "type": "oversold_bounce", "upside_pct": 30.0, "pos": 0.15}

    def _scan(self, prices, atr=None, thesis=True):
        from test_smith_math_triggers import POLICY as P
        out = []
        smith_math._trigger_entry_setup_scan(
            [dict(self.ROW)], {}, {}, {}, ({"ZZZ": "ok|strengthening"} if thesis else {}), [], {}, {},
            lambda b: None, ({"ZZZ": atr} if atr else {}), {}, out, 100000.0, P, 5000.0,
            market_prices=prices)
        return out[0]

    def test_price_comes_from_a_fetched_quote_when_the_row_has_none(self):
        row = self._scan({"ZZZ": {"price": 12.5, "source": "live_quotes.json"}}, atr=6.0)
        assert row["price_usd"] == 12.5 and row["price_source"] == "live_quotes.json"
        assert row["suggested_size_usd"] and row["suggested_size_usd"] > 0

    def test_no_fetched_price_means_no_size_never_a_back_derived_one(self):
        row = self._scan({}, atr=6.0)
        assert row["price_usd"] is None and row["suggested_size_usd"] is None
        assert any("no price_usd" in b for b in row["blockers"])

    def test_end_to_end_via_cmd_triggers(self, tmp_path):
        def add(dst):
            st = json.load(open(dst / "base" / "state.json"))
            st.setdefault("data_cache", {}).setdefault("atr20", {}).setdefault("values_pct", {})["CORZ"] = 7.0
            st.setdefault("thesis", {})["CORZ"] = "AI hosting|strengthening"
            json.dump(st, open(dst / "base" / "state.json", "w"))
            json.dump({"CORZ": {"price": 15.25}}, open(dst / "rundir" / "live_quotes.json", "w"))
            # the fixture book is over its correlation-adjusted heat cap on the conservative bound
            # (Phase 3), which would defer any new buy; this test is about prices, so give it a
            # measured, uncorrelated book with room.
            json.dump({"as_of": "2026-09-01", "window": {"to": "2026-08-28"},
                       "stop_risk": {"avg_pairwise_correlation": 0.0}},
                      open(dst / "rundir" / "compute_correlation.json", "w"))
        out = _run_triggers("triggers_case1", tmp_path, add)
        row = next(r for r in out["entry_setup"] if r["ticker"] == "CORZ")
        assert row["price_usd"] == 15.25 and row["price_source"] == "live_quotes.json"
        assert row["suggested_size_usd"] and row["vote"] == "live"

    def test_bars_last_close_is_the_fallback(self, tmp_path):
        def add(dst):
            st = json.load(open(dst / "base" / "state.json"))
            st.setdefault("data_cache", {}).setdefault("atr20", {}).setdefault("values_pct", {})["CORZ"] = 7.0
            json.dump(st, open(dst / "base" / "state.json", "w"))
            json.dump({"CORZ": [{"d": "2026-08-31", "c": 14.0}, {"d": "2026-09-01", "c": 14.5}]},
                      open(dst / "rundir" / "bars.json", "w"))
        row = next(r for r in _run_triggers("triggers_case1", tmp_path, add)["entry_setup"]
                   if r["ticker"] == "CORZ")
        assert row["price_usd"] == 14.5 and row["price_source"] == "bars.json last close"


class TestFetchCandidates:
    def test_candidate_tickers_from_all_three_sources(self):
        import smith_fetch as sf
        st = {"watchlist_setups": [{"ticker": "ionq"}, {"ticker": "BABA"}],
              "diversifier_candidates": {"VST": {}, "UNH": {}},
              "cluster_ladders": {"A": {"bench": [{"ticker": "AMKR"}, {"ticker": "LRCX"}]},
                                  "B": {"bench": [{"ticker": "IONQ"}]}}}
        assert sf.candidate_tickers(st) == ["AMKR", "BABA", "IONQ", "LRCX", "UNH", "VST"]
        assert sf.candidate_tickers({}) == []

    def test_fixture_fetch_writes_candidates_to_both_files_and_still_exits_zero(self, tmp_path):
        import smith_fetch as sf
        from test_smith_marketdata import _hist, _series
        fx = tmp_path / "fx"
        fx.mkdir()
        h = _hist()
        h["MU"] = _series([50.0 + i for i in range(260)])
        h["IONQ"] = _series([20.0 + i * 0.1 for i in range(260)])          # BABA deliberately absent
        (fx / "history.json").write_text(json.dumps(h))
        (fx / "minute.json").write_text(json.dumps({
            "MU": [{"d": "2026-09-14T14:00:00Z", "c": 320.0}], "IONQ": [{"d": "2026-09-14T14:00:00Z", "c": 45.5}]}))
        (tmp_path / "state.json").write_text(json.dumps({
            "holdings": [{"ticker": "MU"}], "peer_map": {},
            "watchlist_setups": [{"ticker": "IONQ"}, {"ticker": "BABA"}]}))
        env = dict(os.environ, SMITH_NO_SHARED_CACHE="1")
        out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "smith_fetch.py"), "all", "--base-dir",
                              str(tmp_path), "--run-dir", str(tmp_path / "r"), "--fixtures", str(fx)],
                             capture_output=True, text=True, env=env)
        rep = json.loads(out.stdout)
        assert out.returncode == 0 and rep["ok"], rep
        assert {"MU", "SMH", "IONQ"} <= set(json.load(open(tmp_path / "r" / "bars.json")))
        q = json.load(open(tmp_path / "r" / "live_quotes.json"))
        assert q["IONQ"]["price"] == 45.5 and "BABA" not in q
        # a missing CANDIDATE degrades that name only -- reported, never a fallback_needed section
        assert "BABA" in rep["errors"]["candidate_quotes_partial"] and rep["fallback_needed"] == []

    def test_corrupt_candidate_state_never_blocks_the_held_book(self, tmp_path):
        from test_smith_marketdata import _hist, _series
        fx = tmp_path / "fx"
        fx.mkdir()
        h = _hist()
        h["MU"] = _series([50.0 + i for i in range(260)])
        (fx / "history.json").write_text(json.dumps(h))
        (fx / "minute.json").write_text(json.dumps({"MU": [{"d": "2026-09-14T14:00:00Z", "c": 320.0}]}))
        (tmp_path / "state.json").write_text(json.dumps({
            "holdings": [{"ticker": "MU"}], "watchlist_setups": "garbage", "cluster_ladders": [1, 2]}))
        env = dict(os.environ, SMITH_NO_SHARED_CACHE="1")
        out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "smith_fetch.py"), "all", "--base-dir",
                              str(tmp_path), "--run-dir", str(tmp_path / "r"), "--fixtures", str(fx)],
                             capture_output=True, text=True, env=env)
        assert out.returncode == 0 and json.loads(out.stdout)["sections"]["quotes"] == "ok"


# ---------------------------------------------------------------------------
# policy
# ---------------------------------------------------------------------------
class TestPolicyBlock:
    def _policy(self):
        return json.load(open(os.path.join(ROOT, "policy.json")))

    def test_block_present_unconfirmed_and_complete(self):
        tm = self._policy()["trade_materiality"]
        assert tm["confirmed"] is False
        for k in ("min_ticket_usd", "min_ticket_pct_of_book", "min_ticket_r", "fee_cover_mult", "min_position_usd"):
            assert tm[k] > 0
        assert tm["min_position_usd"] == smith_core.DUST_USD_DEFAULT

    def test_block_matches_the_engine_defaults(self):
        pol = T.materiality_policy(self._policy()["trade_materiality"])
        assert (pol["min_ticket_usd"], pol["min_ticket_pct_of_book"], pol["min_ticket_r"], pol["fee_cover_mult"]) == (
            smith_core.MIN_TICKET_USD, smith_core.MIN_TICKET_PCT_OF_BOOK, smith_core.MIN_TICKET_R, smith_core.FEE_COVER_MULT)

    def test_validator_accepts_the_shipped_block_and_flags_bad_ones(self):
        import smith_memory
        assert smith_memory.validate_trade_materiality(self._policy()) == []
        assert smith_memory.validate_trade_materiality({}) == []                       # absent is fine
        bad = smith_memory.validate_trade_materiality({"trade_materiality": {
            "confirmed": True, "min_ticket_usd": -1, "min_position_usd": 999}})
        joined = " | ".join(bad)
        assert "min_ticket_usd" in joined and "confirmed_by_user" in joined and "DUST_USD_DEFAULT" in joined

    def test_validate_policy_still_accepts_the_real_policy(self):
        import smith_memory
        assert not [d for d in smith_memory.validate_policy(self._policy()) if "trade_materiality" in d]

    def test_confirmed_values_untouched(self):
        pol = self._policy()
        assert pol["stop_loss_framework"]["risk_per_position_pct_of_book"] == 0.5
        assert pol["stop_loss_framework"]["confirmed_by_user"] == "2026-07-27"
        assert pol["confirmed"] is True


class TestUnconfirmedIsDisclosed:
    def test_dq_says_the_floors_are_unconfirmed(self, tmp_path):
        out = _run_triggers("triggers_case1", tmp_path)
        assert any("UNCONFIRMED" in d and "trade_materiality" in d for d in out["data_quality"])

    def test_dq_carries_the_legacy_vs_new_table(self, tmp_path):
        out = _run_triggers("triggers_case1", tmp_path)
        line = next(d for d in out["data_quality"] if d.startswith("risk-sized sell legs"))
        assert "catalyst_threat" in line and "->" in line

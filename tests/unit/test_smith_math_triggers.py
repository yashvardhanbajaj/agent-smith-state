"""Unit tests for the 12 functions extracted from cmd_triggers (smith_math.py) in the
2026-09 god-function refactor. Each covers: the gate firing, the gate NOT firing, and at
least one edge case (funding blocked, stale cache, boundary value) specific to that trigger.
"""
from conftest import make_base

import smith_math
import smith_core


# ---------------------------------------------------------------------------
# A. oversold_reversion
# ---------------------------------------------------------------------------

class TestOversoldReversion:
    def test_fires_when_oversold_healthy_and_funded(self, base):
        oversold, dq = [], []
        smith_math._trigger_oversold_reversion(
            base, "AAA", "intact", healthy=True, rsi_usable=True, rsi=30.0, over_cap=False,
            headroom=500.0, max_single=200.0, fundamental_headwind=False, oversold=oversold, dq=dq)
        assert len(oversold) == 1
        row = oversold[0]
        assert row["trigger_type"] == "oversold_reversion"
        assert row["direction"] == "BUY" and row["vote"] == "live"
        assert row["suggested_size_usd"] == 200.0  # min(headroom, max_single)
        assert row["blockers"] == []
        assert dq == []

    def test_funding_blocked_still_fires_with_blocker(self, base):
        oversold, dq = [], []
        smith_math._trigger_oversold_reversion(
            base, "AAA", "intact", healthy=True, rsi_usable=True, rsi=30.0, over_cap=False,
            headroom=500.0, max_single=0.0, fundamental_headwind=False, oversold=oversold, dq=dq)
        assert len(oversold) == 1
        assert oversold[0]["suggested_size_usd"] == 0.0
        assert "no deployable cash" in oversold[0]["blockers"][0]

    def test_unhealthy_thesis_logs_dq_not_a_bounce(self, base):
        oversold, dq = [], []
        smith_math._trigger_oversold_reversion(
            base, "AAA", "watch", healthy=False, rsi_usable=True, rsi=30.0, over_cap=False,
            headroom=500.0, max_single=200.0, fundamental_headwind=False, oversold=oversold, dq=dq)
        assert oversold == []
        assert len(dq) == 1 and "falling knife" in dq[0]

    def test_over_cap_suppresses_even_when_oversold_and_healthy(self, base):
        oversold, dq = [], []
        smith_math._trigger_oversold_reversion(
            base, "AAA", "intact", healthy=True, rsi_usable=True, rsi=30.0, over_cap=True,
            headroom=500.0, max_single=200.0, fundamental_headwind=False, oversold=oversold, dq=dq)
        assert oversold == [] and dq == []

    def test_stale_rsi_cache_does_nothing(self, base):
        oversold, dq = [], []
        smith_math._trigger_oversold_reversion(
            base, "AAA", "intact", healthy=True, rsi_usable=False, rsi=None, over_cap=False,
            headroom=500.0, max_single=200.0, fundamental_headwind=False, oversold=oversold, dq=dq)
        assert oversold == [] and dq == []


# ---------------------------------------------------------------------------
# B. overbought_distribution
# ---------------------------------------------------------------------------

class TestOverboughtDistribution:
    def test_fires_when_overbought_and_genuinely_up(self, base):
        overbought = []
        smith_math._trigger_overbought_distribution(
            base, "AAA", rsi_usable=True, rsi=80.0, rel_usable=True, abs_pct=12.0, mv=1000.0,
            sector_map={}, cluster_rows={}, rel_vals={}, risk_by_ticker={}, thesis={},
            overbought=overbought)
        assert len(overbought) == 1
        row = overbought[0]
        assert row["direction"] == "TRIM" and row["over_cap_independent"] is True
        assert row["suggested_size_usd"] == 1000.0 * smith_core.OVERBOUGHT_TRIM_FRACTION
        assert row["cluster_tension"] is False

    def test_suppressed_when_rel_usable_but_not_genuinely_up(self, base):
        overbought = []
        smith_math._trigger_overbought_distribution(
            base, "AAA", rsi_usable=True, rsi=80.0, rel_usable=True, abs_pct=-3.0, mv=1000.0,
            sector_map={}, cluster_rows={}, rel_vals={}, risk_by_ticker={}, thesis={},
            overbought=overbought)
        assert overbought == []

    def test_stale_rel_cache_still_fires_with_blocker(self, base):
        overbought = []
        smith_math._trigger_overbought_distribution(
            base, "AAA", rsi_usable=True, rsi=80.0, rel_usable=False, abs_pct=None, mv=1000.0,
            sector_map={}, cluster_rows={}, rel_vals={}, risk_by_ticker={}, thesis={},
            overbought=overbought)
        assert len(overbought) == 1
        assert any("1m return unavailable" in b for b in overbought[0]["blockers"])

    def test_cluster_tension_names_rotation_target(self, base):
        overbought = []
        sector_map = {"AAA": "Compute", "BBB": "Compute"}
        cluster_rows = {"Compute": {"drift_pt": -5.0}}
        rel_vals = {"BBB": -2.0}
        risk_by_ticker = {"BBB": {"over_cap": False}}
        thesis = {"BBB": "intact"}
        smith_math._trigger_overbought_distribution(
            base, "AAA", rsi_usable=True, rsi=80.0, rel_usable=True, abs_pct=12.0, mv=1000.0,
            sector_map=sector_map, cluster_rows=cluster_rows, rel_vals=rel_vals,
            risk_by_ticker=risk_by_ticker, thesis=thesis, overbought=overbought)
        row = overbought[0]
        assert row["cluster_tension"] is True
        assert row["rotation_targets"][0]["ticker"] == "BBB"
        assert "INTRA-CLUSTER ROTATION" in row["blockers"][0]

    def test_not_overbought_does_nothing(self, base):
        overbought = []
        smith_math._trigger_overbought_distribution(
            base, "AAA", rsi_usable=True, rsi=55.0, rel_usable=True, abs_pct=5.0, mv=1000.0,
            sector_map={}, cluster_rows={}, rel_vals={}, risk_by_ticker={}, thesis={},
            overbought=overbought)
        assert overbought == []


# ---------------------------------------------------------------------------
# C. laggard_rotation
# ---------------------------------------------------------------------------

class TestLaggardRotation:
    def test_fires_when_laggard_healthy_and_funded(self, base):
        laggard = []
        smith_math._trigger_laggard_rotation(
            base, "AAA", rel_usable=True, laggard_set={"AAA"}, healthy=True, over_cap=False,
            headroom=500.0, status="intact", rel_pp=-15.0, rel_cache={"benchmark": "SMH"},
            max_single=200.0, fundamental_headwind=False, laggard=laggard)
        assert len(laggard) == 1
        assert laggard[0]["vote"] == "shadow"
        assert laggard[0]["suggested_size_usd"] == 200.0

    def test_not_in_laggard_set_does_nothing(self, base):
        laggard = []
        smith_math._trigger_laggard_rotation(
            base, "AAA", rel_usable=True, laggard_set={"ZZZ"}, healthy=True, over_cap=False,
            headroom=500.0, status="intact", rel_pp=-15.0, rel_cache={},
            max_single=200.0, fundamental_headwind=False, laggard=laggard)
        assert laggard == []

    def test_no_funding_still_fires_with_honest_blocker(self, base):
        laggard = []
        smith_math._trigger_laggard_rotation(
            base, "AAA", rel_usable=True, laggard_set={"AAA"}, healthy=True, over_cap=False,
            headroom=500.0, status="intact", rel_pp=-15.0, rel_cache={},
            max_single=0.0, fundamental_headwind=False, laggard=laggard)
        assert len(laggard) == 1
        assert laggard[0]["suggested_size_usd"] == 0.0
        assert "fund it from a sell leg" in laggard[0]["blockers"][0]


# ---------------------------------------------------------------------------
# F. catalyst_threat
# ---------------------------------------------------------------------------

class TestCatalystThreat:
    def test_fires_on_a_named_catalyst(self, base):
        catalyst_threat = []
        cats = {"AAA": [{"headline": "Supply glut", "date": "2026-08-01",
                          "magnitude": "large", "source": "reuters"}]}
        smith_math._trigger_catalyst_threat(
            base, "AAA", mv=1000.0, catalyst_threats_by_ticker=cats, rotation_by_ticker={},
            status="intact", catalyst_threat=catalyst_threat)
        assert len(catalyst_threat) == 1
        row = catalyst_threat[0]
        assert row["direction"] == "TRIM" and row["over_cap_independent"] is True
        assert row["suggested_size_usd"] == 1000.0 * smith_core.CATALYST_THREAT_TRIM_FRACTION

    def test_no_catalyst_does_nothing(self, base):
        catalyst_threat = []
        smith_math._trigger_catalyst_threat(
            base, "AAA", mv=1000.0, catalyst_threats_by_ticker={}, rotation_by_ticker={},
            status="intact", catalyst_threat=catalyst_threat)
        assert catalyst_threat == []

    def test_flags_tension_with_accumulate_rotation(self, base):
        catalyst_threat = []
        cats = {"AAA": [{"headline": "x", "date": "2026-08-01", "magnitude": "m", "source": "s"}]}
        rotation = {"AAA": {"bucket": "accumulate"}}
        smith_math._trigger_catalyst_threat(
            base, "AAA", mv=1000.0, catalyst_threats_by_ticker=cats, rotation_by_ticker=rotation,
            status="strengthening", catalyst_threat=catalyst_threat)
        assert any("simultaneously in rotation" in b for b in catalyst_threat[0]["blockers"])


# ---------------------------------------------------------------------------
# G. thesis_break
# ---------------------------------------------------------------------------

class TestThesisBreak:
    def test_fires_when_broken(self, base):
        thesis_break = []
        thesis = {"AAA": {"status": "broken", "thesis": "Losing share",
                           "evidence_against": [{"claim": "share loss", "date": "2026-08-01", "source": "10-Q"}],
                           "evidence_for": [], "verified": "primary"}}
        smith_math._trigger_thesis_break(base, "AAA", "broken", 1000.0, thesis, thesis_break)
        assert len(thesis_break) == 1
        row = thesis_break[0]
        assert row["direction"] == "TRIM" and row["evidence_verified"] == "primary"
        assert row["suggested_size_usd"] == 1000.0 * smith_core.THESIS_BREAK_TRIM_FRACTION

    def test_not_broken_does_nothing(self, base):
        thesis_break = []
        smith_math._trigger_thesis_break(base, "AAA", "watch", 1000.0, {}, thesis_break)
        assert thesis_break == []

    def test_broken_with_no_evidence_against_flags_backfill(self, base):
        thesis_break = []
        thesis = {"AAA": {"status": "broken", "thesis": "", "evidence_against": [],
                           "evidence_for": [], "verified": "unverified"}}
        smith_math._trigger_thesis_break(base, "AAA", "broken", 1000.0, thesis, thesis_break)
        assert "backfill the evidence" in thesis_break[0]["blockers"][0]


# ---------------------------------------------------------------------------
# D/E. profit_ratchet + scale_out_ladder
# ---------------------------------------------------------------------------

class TestRatchetAndLadder:
    def test_ratchet_fires_when_gain_and_stop_below_cost(self, base):
        ratchet, ladder, dq = [], [], []
        lots = {"AAA": [{"qty": 10, "price_usd": 100.0}]}
        r = {"stop_price_usd": 95.0}
        smith_math._trigger_ratchet_and_ladder(
            base, "AAA", r, mv=1200.0, price=120.0, rsi=55.0, lots=lots, laggard_set=set(),
            ratchet=ratchet, ladder=ladder, dq=dq)
        assert len(ratchet) == 1
        assert ratchet[0]["suggested_stop_usd"] == 100.0
        assert ratchet[0]["gain_pct"] == 20.0

    def test_ladder_fires_at_25pct_rung(self, base):
        ratchet, ladder, dq = [], [], []
        lots = {"AAA": [{"qty": 10, "price_usd": 100.0}]}
        r = {"stop_price_usd": 100.0}  # already at breakeven -> ratchet won't fire
        smith_math._trigger_ratchet_and_ladder(
            base, "AAA", r, mv=1300.0, price=130.0, rsi=55.0, lots=lots, laggard_set=set(),
            ratchet=ratchet, ladder=ladder, dq=dq)
        assert ratchet == []
        assert len(ladder) == 1
        assert ladder[0]["tiers"][0]["triggered"] is True   # 25% rung
        assert ladder[0]["tiers"][1]["triggered"] is False  # 50% rung not yet

    def test_below_gain_threshold_fires_neither(self, base):
        ratchet, ladder, dq = [], [], []
        lots = {"AAA": [{"qty": 10, "price_usd": 100.0}]}
        r = {"stop_price_usd": 95.0}
        smith_math._trigger_ratchet_and_ladder(
            base, "AAA", r, mv=1050.0, price=105.0, rsi=55.0, lots=lots, laggard_set=set(),
            ratchet=ratchet, ladder=ladder, dq=dq)
        assert ratchet == [] and ladder == [] and dq == []

    def test_missing_lots_entry_logs_dq_when_relevant(self, base):
        ratchet, ladder, dq = [], [], []
        smith_math._trigger_ratchet_and_ladder(
            base, "AAA", {}, mv=1000.0, price=100.0, rsi=80.0, lots={}, laggard_set=set(),
            ratchet=ratchet, ladder=ladder, dq=dq)
        assert ratchet == [] and ladder == []
        assert len(dq) == 1 and "no lots.json entry" in dq[0]

    def test_missing_lots_entry_silent_when_not_relevant(self, base):
        ratchet, ladder, dq = [], [], []
        smith_math._trigger_ratchet_and_ladder(
            base, "AAA", {}, mv=1000.0, price=100.0, rsi=50.0, lots={}, laggard_set=set(),
            ratchet=ratchet, ladder=ladder, dq=dq)
        assert dq == []


# ---------------------------------------------------------------------------
# H/I/J/K. conviction_held (trend_entry, trend_breakdown, conviction_average, conviction_exit)
# ---------------------------------------------------------------------------

def _ctx_builder(thesis_entry_map):
    """A stub build_ctx matching cmd_triggers' real closure signature: builds the ctx dict
    smith_conviction.score_conviction expects, without needing the full orchestrator state."""
    def build_ctx(ticker, thesis_entry, buckets, price, rsi_val, rel_val, earnings_fact_ticker):
        return {"ticker": ticker, "thesis_entry": thesis_entry, "factor_catalysts": [],
                "buckets": buckets, "upside_pct": None, "earnings_fact": None,
                "rsi": rsi_val, "rsi_usable": True, "rel_pp": rel_val, "rel_usable": True,
                "mention_count": 0, "track_record": None}
    return build_ctx


POLICY = {"stop_loss_framework": {"risk_per_position_pct_of_book": 0.5}}


class TestConvictionHeld:
    def test_trend_entry_fires_on_breakout_with_strong_thesis(self, base):
        trend_entry, trend_breakdown, conviction_average, conviction_exit, dq = [], [], [], [], []
        conviction_by_ticker = {}
        thesis = {"AAA": "strengthening thesis|strengthening"}
        r = {"cluster": "Compute"}
        smith_math._trigger_conviction_held(
            base, "AAA", r, mv=1000.0, price=100.0, rsi=50.0, rel_pp=5.0, rsi_usable=True,
            healthy=True, over_cap=False, headroom=500.0, thesis=thesis,
            signal_history={"AAA": ["BREAKOUT"]}, atr_vals={"AAA": 8.0}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, build_ctx=_ctx_builder(thesis),
            conviction_by_ticker=conviction_by_ticker, catalyst_threats_by_ticker={}, lots={},
            trend_entry=trend_entry, trend_breakdown=trend_breakdown,
            conviction_average=conviction_average, conviction_exit=conviction_exit, dq=dq)
        assert "AAA" in conviction_by_ticker  # always populated regardless of firing
        assert len(trend_entry) == 1
        assert trend_entry[0]["direction"] == "BUY"
        assert trend_breakdown == [] and conviction_average == [] and conviction_exit == []

    def test_trend_breakdown_fires_on_weak_thesis_and_breakdown_bucket(self, base):
        trend_entry, trend_breakdown, conviction_average, conviction_exit, dq = [], [], [], [], []
        thesis = {"AAA": "losing momentum|watch"}
        r = {"cluster": "Compute"}
        smith_math._trigger_conviction_held(
            base, "AAA", r, mv=1000.0, price=100.0, rsi=50.0, rel_pp=-5.0, rsi_usable=True,
            healthy=False, over_cap=False, headroom=500.0, thesis=thesis,
            signal_history={"AAA": ["BREAKDOWN"]}, atr_vals={"AAA": 8.0}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, build_ctx=_ctx_builder(thesis),
            conviction_by_ticker={}, catalyst_threats_by_ticker={}, lots={},
            trend_entry=trend_entry, trend_breakdown=trend_breakdown,
            conviction_average=conviction_average, conviction_exit=conviction_exit, dq=dq)
        assert len(trend_breakdown) == 1
        assert trend_breakdown[0]["direction"] == "TRIM"

    def test_conviction_exit_fires_on_convergence_of_three_negatives(self, base):
        trend_entry, trend_breakdown, conviction_average, conviction_exit, dq = [], [], [], [], []
        thesis = {"AAA": "under pressure|watch"}
        r = {"cluster": "Compute"}
        catalyst_threats = {"AAA": [{"headline": "x"}]}
        smith_math._trigger_conviction_held(
            base, "AAA", r, mv=1000.0, price=100.0, rsi=80.0, rel_pp=-5.0, rsi_usable=True,
            healthy=False, over_cap=False, headroom=500.0, thesis=thesis,
            signal_history={"AAA": ["BREAKDOWN"]}, atr_vals={"AAA": 8.0}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, build_ctx=_ctx_builder(thesis),
            conviction_by_ticker={}, catalyst_threats_by_ticker=catalyst_threats, lots={},
            trend_entry=trend_entry, trend_breakdown=trend_breakdown,
            conviction_average=conviction_average, conviction_exit=conviction_exit, dq=dq)
        # watch thesis + catalyst threat + net-bearish polarity + overbought-while-not-bullish
        # = 4 independent negatives, clears convergence_exit_score's default min_negatives=3
        assert len(conviction_exit) == 1
        assert conviction_exit[0]["direction"] == "SELL"
        assert conviction_exit[0]["negative_signal_count"] >= 3

    def test_over_cap_suppresses_trend_entry(self, base):
        trend_entry, trend_breakdown, conviction_average, conviction_exit, dq = [], [], [], [], []
        thesis = {"AAA": "strengthening thesis|strengthening"}
        r = {"cluster": "Compute"}
        smith_math._trigger_conviction_held(
            base, "AAA", r, mv=1000.0, price=100.0, rsi=50.0, rel_pp=5.0, rsi_usable=True,
            healthy=True, over_cap=True, headroom=-200.0, thesis=thesis,
            signal_history={"AAA": ["BREAKOUT"]}, atr_vals={"AAA": 8.0}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, build_ctx=_ctx_builder(thesis),
            conviction_by_ticker={}, catalyst_threats_by_ticker={}, lots={},
            trend_entry=trend_entry, trend_breakdown=trend_breakdown,
            conviction_average=conviction_average, conviction_exit=conviction_exit, dq=dq)
        assert trend_entry == []


# ---------------------------------------------------------------------------
# L. entry_setup (watchlist scan)
# ---------------------------------------------------------------------------

class TestEntrySetupScan:
    def _track_record_for(self, buckets):
        return None

    def test_fires_for_unheld_ticker_with_conviction(self):
        entry_setup = []
        watchlist_setups = [{"ticker": "ZZZ", "pos": 0.1, "type": "breakout", "upside_pct": 20.0}]
        thesis = {"ZZZ": "strengthening thesis|strengthening"}
        smith_math._trigger_entry_setup_scan(
            watchlist_setups, risk_by_ticker={}, state={}, signal_history={}, thesis=thesis,
            factor_catalysts=[], earnings_facts={}, mention_counts={},
            track_record_for=self._track_record_for, atr_vals={}, sector_map={},
            entry_setup=entry_setup)
        assert len(entry_setup) == 1
        assert entry_setup[0]["ticker"] == "ZZZ"
        assert "no live price/ATR" in entry_setup[0]["blockers"][0]

    def test_already_held_ticker_is_skipped(self):
        entry_setup = []
        watchlist_setups = [{"ticker": "ZZZ", "pos": 0.1}]
        smith_math._trigger_entry_setup_scan(
            watchlist_setups, risk_by_ticker={"ZZZ": {}}, state={}, signal_history={}, thesis={},
            factor_catalysts=[], earnings_facts={}, mention_counts={},
            track_record_for=self._track_record_for, atr_vals={}, sector_map={},
            entry_setup=entry_setup)
        assert entry_setup == []

    def test_no_conviction_is_skipped(self):
        entry_setup = []
        watchlist_setups = [{"ticker": "ZZZ", "pos": None}]
        smith_math._trigger_entry_setup_scan(
            watchlist_setups, risk_by_ticker={}, state={}, signal_history={}, thesis={},
            factor_catalysts=[], earnings_facts={}, mention_counts={},
            track_record_for=self._track_record_for, atr_vals={}, sector_map={},
            entry_setup=entry_setup)
        assert entry_setup == []


# ---------------------------------------------------------------------------
# M. reentry
# ---------------------------------------------------------------------------

class TestReentryScan:
    def _upside_pct_for(self, ticker, price):
        return None

    def _track_record_for(self, buckets):
        return None

    def test_fires_for_alumnus_with_intact_thesis(self):
        reentry, no_thesis, judged_out = [], [], []
        from datetime import date
        trades = {"trades": [{"ticker": "ZZZ", "date": "2026-07-01", "price_at_trade": 50.0}]}
        recently_exited = {"ZZZ": date(2026, 7, 1)}
        thesis = {"ZZZ": "strengthening thesis|strengthening"}
        smith_math._trigger_reentry_scan(
            trades, recently_exited, signal_history={}, thesis=thesis, factor_catalysts=[],
            earnings_facts={}, upside_pct_for=self._upside_pct_for, rsi_vals={}, rsi_usable=True,
            rel_vals={}, rel_usable=True, mention_counts={},
            track_record_for=self._track_record_for, atr_vals={}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, sector_map={}, reentry=reentry,
            reentry_no_thesis=no_thesis, reentry_judged_out=judged_out)
        assert len(reentry) == 1
        assert reentry[0]["ticker"] == "ZZZ"
        assert reentry[0]["price_usd"] == 50.0
        assert no_thesis == [] and judged_out == []

    def test_no_thesis_entry_counted_separately_from_judged_out(self):
        reentry, no_thesis, judged_out = [], [], []
        from datetime import date
        trades = {"trades": []}
        recently_exited = {"ZZZ": date(2026, 7, 1)}
        smith_math._trigger_reentry_scan(
            trades, recently_exited, signal_history={}, thesis={}, factor_catalysts=[],
            earnings_facts={}, upside_pct_for=self._upside_pct_for, rsi_vals={}, rsi_usable=True,
            rel_vals={}, rel_usable=True, mention_counts={},
            track_record_for=self._track_record_for, atr_vals={}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, sector_map={}, reentry=reentry,
            reentry_no_thesis=no_thesis, reentry_judged_out=judged_out)
        assert reentry == []
        assert no_thesis == ["ZZZ"]
        assert judged_out == []

    def test_judged_and_rejected_counted_separately(self):
        reentry, no_thesis, judged_out = [], [], []
        from datetime import date
        trades = {"trades": []}
        recently_exited = {"ZZZ": date(2026, 7, 1)}
        thesis = {"ZZZ": "still weak|watch"}
        smith_math._trigger_reentry_scan(
            trades, recently_exited, signal_history={}, thesis=thesis, factor_catalysts=[],
            earnings_facts={}, upside_pct_for=self._upside_pct_for, rsi_vals={}, rsi_usable=True,
            rel_vals={}, rel_usable=True, mention_counts={},
            track_record_for=self._track_record_for, atr_vals={}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, sector_map={}, reentry=reentry,
            reentry_no_thesis=no_thesis, reentry_judged_out=judged_out)
        assert reentry == []
        assert no_thesis == []
        assert judged_out == ["ZZZ"]


# ---------------------------------------------------------------------------
# N. bench_diversifier
# ---------------------------------------------------------------------------

class TestBenchDiversifierScan:
    def _track_record_for(self, buckets):
        return None

    def test_fires_for_clean_diversifier_with_upside(self):
        # Diversifier candidates carry no thesis, so valuation (capped at WEIGHTS['valuation']=14)
        # alone can never clear the 20-point "low" conviction floor -- corroboration (mention
        # counts) has to do the rest, same as the real engine's honest-limit note for this trigger.
        bench_diversifier = []
        divs = {"ZZZ": {"clean_diversifier": True, "status": "active", "price_usd": 40.0,
                        "upside_pct": 60.0}}
        smith_math._trigger_bench_diversifier_scan(
            divs, risk_by_ticker={}, state={}, mention_counts={"ZZZ": 3},
            track_record_for=self._track_record_for, atr_vals={}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, bench_diversifier=bench_diversifier)
        assert len(bench_diversifier) == 1
        assert bench_diversifier[0]["ticker"] == "ZZZ"

    def test_already_held_ticker_is_skipped(self):
        bench_diversifier = []
        divs = {"ZZZ": {"clean_diversifier": True, "status": "active", "price_usd": 40.0,
                        "upside_pct": 35.0}}
        smith_math._trigger_bench_diversifier_scan(
            divs, risk_by_ticker={"ZZZ": {}}, state={}, mention_counts={},
            track_record_for=self._track_record_for, atr_vals={}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, bench_diversifier=bench_diversifier)
        assert bench_diversifier == []

    def test_stale_candidate_is_skipped(self):
        bench_diversifier = []
        divs = {"ZZZ": {"clean_diversifier": True, "status": "stale", "price_usd": 40.0,
                        "upside_pct": 35.0}}
        smith_math._trigger_bench_diversifier_scan(
            divs, risk_by_ticker={}, state={}, mention_counts={},
            track_record_for=self._track_record_for, atr_vals={}, total_book=100000.0,
            policy=POLICY, deployable_for_ideas=10000.0, bench_diversifier=bench_diversifier)
        assert bench_diversifier == []


# ---------------------------------------------------------------------------
# O/P. profit_rotation + cluster_rotation
# ---------------------------------------------------------------------------

def _conv_row(mv, cluster, rel_pp, over_cap=False, tier="medium", score=50.0, atr_pct=8.0, price=100.0):
    return {"market_value_usd": mv, "cluster": cluster, "rel_pp": rel_pp, "over_cap": over_cap,
            "headroom_usd": 5000.0, "conviction_tier": tier, "conviction_score": score,
            "conviction_tier_pct": 0.6, "atr_pct": atr_pct, "price": price}


class TestProfitRotation:
    def test_pairs_a_stretched_sell_with_a_laggard_buy(self):
        profit_rotation = []
        conviction_by_ticker = {
            "SELL_ME": _conv_row(2000.0, "Compute", rel_pp=10.0),
            "BUY_ME": _conv_row(500.0, "Networking", rel_pp=-8.0),
        }
        thesis = {"SELL_ME": "extended|watch", "BUY_ME": "cheap now|strengthening"}
        smith_math._trigger_profit_rotation(
            names_stretched={"SELL_ME"}, conviction_by_ticker=conviction_by_ticker,
            thesis=thesis, total_book=100000.0, policy=POLICY, profit_rotation=profit_rotation)
        assert len(profit_rotation) == 1
        pair = profit_rotation[0]
        assert pair["sell_leg"]["ticker"] == "SELL_ME"
        assert pair["buy_leg"]["ticker"] == "BUY_ME"

    def test_no_stretched_names_produces_no_pairs(self):
        profit_rotation = []
        smith_math._trigger_profit_rotation(
            names_stretched=set(), conviction_by_ticker={}, thesis={}, total_book=100000.0,
            policy=POLICY, profit_rotation=profit_rotation)
        assert profit_rotation == []


class TestClusterRotation:
    def test_pairs_cluster_laggard_with_cluster_performer(self):
        cluster_rotation = []
        conviction_by_ticker = {
            "LAG": _conv_row(1000.0, "Compute", rel_pp=-5.0),
            "PERF": _conv_row(1000.0, "Compute", rel_pp=5.0),
        }
        thesis = {"LAG": "stuck|watch", "PERF": "running|strengthening"}
        smith_math._trigger_cluster_rotation(conviction_by_ticker, thesis, cluster_rotation)
        assert len(cluster_rotation) == 1
        pair = cluster_rotation[0]
        assert pair["sell_leg"]["ticker"] == "LAG"
        assert pair["buy_leg"]["ticker"] == "PERF"

    def test_single_member_cluster_produces_no_pair(self):
        cluster_rotation = []
        conviction_by_ticker = {"ONLY": _conv_row(1000.0, "Compute", rel_pp=-5.0)}
        smith_math._trigger_cluster_rotation(conviction_by_ticker, {"ONLY": "watch"}, cluster_rotation)
        assert cluster_rotation == []


# ---------------------------------------------------------------------------
# cmd_buckets helpers (added 2026-09-06) -- the deterministic half of smith-signals
# ---------------------------------------------------------------------------

class TestBucketArithmetic:
    """Moved out of smith-signals, which cost 144,878 tokens on 2026-09-06 largely to re-derive
    these. Thresholds are smith-signals.md task 10's, unchanged -- this pins that the move was a
    relocation, not a redefinition."""

    def test_strong_move_threshold_scales_with_atr(self):
        assert smith_math._strong_move_threshold(4.0) == 6.0          # 1.5 x ATR

    def test_threshold_floor_stops_a_quiet_name_flagging_on_noise(self):
        assert smith_math._strong_move_threshold(0.5) == 2.0

    def test_threshold_ceiling_keeps_a_loud_name_flaggable(self):
        assert smith_math._strong_move_threshold(15.6) == 12.0

    def test_rel_sigma_uses_the_2_3x_atr_denominator(self):
        assert round(smith_math._rel_sigma(6.34, 4.36), 3) == round(6.34 / (2.3 * 4.36), 3)

    def test_rel_sigma_denominator_has_a_5pp_floor(self):
        """A very low-ATR name must not get an artificially tiny denominator that turns an
        ordinary move into a multi-sigma event."""
        assert smith_math._rel_sigma(5.0, 0.1) == 1.0                 # max(0.23, 5.0) -> 5.0

    def test_high_atr_name_needs_a_far_bigger_gap_to_lead(self):
        """The whole point of normalizing: SNDK at 15.6% ATR moving -25.9pp is inside its own
        noise (-0.72 sigma), while a 2.89% ATR name moving the same -25.9pp is a real signal."""
        loud = smith_math._rel_sigma(-25.9, 15.6)
        quiet = smith_math._rel_sigma(-25.9, 2.89)
        assert -1.0 < loud < 0            # not flagged
        assert quiet <= -1.0              # flagged

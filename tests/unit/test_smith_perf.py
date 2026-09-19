"""Position-level realized-return reconstruction (smith_perf.py, added 2026-09-19).

Each test here pins one of the three corrections that a naive reconstruction gets wrong. All
three were found by an implausible OUTPUT rather than by reading the code, so a regression would
be equally silent: the series would still be produced, still look like a return series, and still
be wrong. The fourth test pins the survivorship property that is the whole reason the module
exists -- an exited position must keep contributing to the record after it is gone.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_perf as sp


def bars(**series):
    """{'AAA': {'2026-01-02': 100.0, ...}} from kwargs of {date: close}."""
    return {t: dict(rows) for t, rows in series.items()}


SESSIONS = ["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07"]


def flat_bench(price=100.0):
    return {d: price for d in SESSIONS}


class TestAdjustmentRowsAreFlowNotReturn:
    """A `ca_type: adjustment` row changes quantity with no cash and an unknown basis. Counted
    as free shares it manufactures return -- the real 2026-02-02 GOOG/NVDA pair read as +13.87%
    in a single session."""

    def test_pure_adjustment_session_returns_zero(self):
        b = bars(AAA={d: 50.0 for d in SESSIONS}, SMH=flat_bench())
        trades = [
            {"date": "2026-01-02", "ticker": "AAA", "qty_change": 10, "amount_usd": 500.0},
            {"date": "2026-01-06", "ticker": "AAA", "qty_change": 4, "ca_type": "adjustment"},
        ]
        out = sp.reconstruct(trades, b)
        by_day = {r["d"]: r for r in out["series"]}
        assert round(by_day["2026-01-06"]["ret"], 10) == 0.0
        # the shares still arrive -- an adjustment corrects the position, it just isn't performance
        assert out["positions_final"]["AAA"] == 14
        assert out["adjustment_flow_usd"] == 200.0

    def test_adjustment_is_priced_at_that_sessions_close(self):
        b = bars(AAA={"2026-01-02": 50.0, "2026-01-05": 50.0, "2026-01-06": 80.0,
                      "2026-01-07": 80.0}, SMH=flat_bench())
        trades = [
            {"date": "2026-01-02", "ticker": "AAA", "qty_change": 10, "amount_usd": 500.0},
            {"date": "2026-01-06", "ticker": "AAA", "qty_change": 1, "ca_type": "adjustment"},
        ]
        out = sp.reconstruct(trades, b)
        by_day = {r["d"]: r for r in out["series"]}
        # the 80.0 close, not the 50.0 entry price: flow must cancel the value the share adds
        assert by_day["2026-01-06"]["flow_usd"] == 80.0


class TestMaterialityFloor:
    """A $1,000 deposit against a $103 book produced -41.88% on 2025-05-07. Sessions whose PRIOR
    value is below the floor are excluded rather than allowed to dominate the chain."""

    def test_sessions_below_floor_are_skipped_not_chained(self):
        b = bars(AAA={d: 1.0 for d in SESSIONS}, SMH=flat_bench())
        trades = [
            {"date": "2026-01-02", "ticker": "AAA", "qty_change": 100, "amount_usd": 100.0},
            {"date": "2026-01-05", "ticker": "AAA", "qty_change": 5000, "amount_usd": 5000.0},
        ]
        out = sp.reconstruct(trades, b, min_book_usd=500.0)
        assert out["skipped_below_floor"] >= 1
        assert all(r["d"] > "2026-01-05" for r in out["series"])

    def test_floor_of_zero_keeps_everything(self):
        b = bars(AAA={d: 1.0 for d in SESSIONS}, SMH=flat_bench())
        trades = [{"date": "2026-01-02", "ticker": "AAA", "qty_change": 100, "amount_usd": 100.0}]
        out = sp.reconstruct(trades, b, min_book_usd=0.0)
        assert out["skipped_below_floor"] == 0


class TestNonTradingDateRollForward:
    """5 of 1003 real trades are dated on non-trading days (the 2026-08-15 Saturday
    reconciliation batch, 2025-12-25). Matching the market calendar on date equality dropped
    them silently and lost $2.8K of position."""

    def test_weekend_trade_lands_on_the_next_session(self):
        b = bars(AAA={d: 10.0 for d in SESSIONS}, SMH=flat_bench())
        trades = [
            {"date": "2026-01-02", "ticker": "AAA", "qty_change": 10, "amount_usd": 100.0},
            {"date": "2026-01-03", "ticker": "AAA", "qty_change": 5, "amount_usd": 50.0},  # Saturday
        ]
        out = sp.reconstruct(trades, b, min_book_usd=0.0)
        by_day = {r["d"]: r for r in out["series"]}
        assert out["positions_final"]["AAA"] == 15
        assert by_day["2026-01-05"]["flow_usd"] == 50.0   # rolled to Monday, not dropped

    def test_trade_after_the_last_session_is_not_silently_lost(self):
        b = bars(AAA={d: 10.0 for d in SESSIONS}, SMH=flat_bench())
        trades = [{"date": "2026-01-02", "ticker": "AAA", "qty_change": 10, "amount_usd": 100.0},
                  {"date": "2030-01-01", "ticker": "AAA", "qty_change": 99, "amount_usd": 990.0}]
        out = sp.reconstruct(trades, b, min_book_usd=0.0)
        # it cannot be placed on a session, so it must not appear in the priced book either
        assert out["positions_final"]["AAA"] == 10


class TestSurvivorship:
    """The property the whole module exists for: a name that was held and sold still counts."""

    def test_a_losing_position_that_was_exited_still_drags_the_record(self):
        b = bars(LOSER={"2026-01-02": 100.0, "2026-01-05": 50.0, "2026-01-06": 50.0,
                        "2026-01-07": 50.0},
                 WINNER={d: 100.0 for d in SESSIONS}, SMH=flat_bench())
        trades = [
            {"date": "2026-01-02", "ticker": "LOSER", "qty_change": 100, "amount_usd": 10000.0},
            {"date": "2026-01-06", "ticker": "LOSER", "qty_change": -100, "amount_usd": 5000.0},
            {"date": "2026-01-06", "ticker": "WINNER", "qty_change": 50, "amount_usd": 5000.0},
        ]
        out = sp.reconstruct(trades, b, min_book_usd=0.0)
        stats = sp.chain(out["series"], b)
        assert "LOSER" not in out["positions_final"]          # gone from the book
        assert stats["twr_pct"] < -40                          # but not gone from the record

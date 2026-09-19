"""Realised correlation (smith_correlation.py, added 2026-09-19).

Two of these pin mistakes made while writing the module, because both were the kind that produce
a plausible number rather than an error: listwise-complete alignment (one new ticker silently cut
27 names to 50 shared sessions) and the diversification-credit direction (the first draft claimed
the desk's stop sum understated risk, when summing every stop distance IS the all-fire case).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_correlation as sc


def ramp(start, steps, per):
    """A price path with a fixed per-session return, as OHLC-ish rows."""
    out, px = [], start
    for i in range(steps):
        out.append({"d": f"2026-{1 + i // 21:02d}-{1 + i % 21:02d}", "c": round(px, 4)})
        px *= (1 + per)
    return out


def wiggle(steps, seed, scale=0.02, start=100.0):
    """Deterministic pseudo-random walk -- no numpy, no test-order dependence."""
    out, px, x = [], start, seed
    for i in range(steps):
        x = (1103515245 * x + 12345) % 2147483648
        out.append({"d": f"2026-{1 + i // 21:02d}-{1 + i % 21:02d}", "c": round(px, 4)})
        px *= (1 + ((x / 2147483648) - 0.5) * 2 * scale)
    return out


class TestPairwiseCompleteAlignment:
    """One recently-bought name must not truncate everybody else's history."""

    def test_a_short_series_does_not_shorten_the_others(self):
        bars = {"OLD1": wiggle(200, 7), "OLD2": wiggle(200, 11), "NEW": wiggle(10, 13)}
        rets, dates, dropped = sc.daily_returns(bars, ["OLD1", "OLD2", "NEW"])
        assert len(rets["OLD1"]) == 199          # full history retained
        assert len(rets["NEW"]) == 9
        corr, obs = sc.matrix(rets, min_obs=40)
        assert obs["OLD1"]["OLD2"] == 199        # the long pair keeps its long overlap
        assert corr["OLD1"]["OLD2"] is not None

    def test_a_pair_with_too_few_shared_sessions_scores_none_not_a_number(self):
        bars = {"OLD": wiggle(200, 7), "NEW": wiggle(10, 13)}
        rets, _, _ = sc.daily_returns(bars, ["OLD", "NEW"])
        corr, obs = sc.matrix(rets, min_obs=40)
        assert obs["OLD"]["NEW"] < 40
        assert corr["OLD"]["NEW"] is None        # abstains rather than reporting noise


class TestDiversification:
    def test_identical_assets_are_one_bet(self):
        # same path at a different scale: perfectly correlated, non-zero variance
        a = wiggle(150, 5)
        b = [{"d": r["d"], "c": round(r["c"] * 3, 4)} for r in a]
        rets, _, _ = sc.daily_returns({"A": a, "B": b}, ["A", "B"])
        corr, _ = sc.matrix(rets, min_obs=10)
        assert round(corr["A"]["B"], 3) == 1.0
        d = sc.diversification({"A": 50.0, "B": 50.0}, rets, corr)
        assert round(d["diversification_ratio"], 3) == 1.0
        assert round(d["effective_bets"], 2) == 1.0

    def test_an_unmeasurable_pair_is_imputed_not_assumed_independent(self):
        # a None correlation must NOT read as 0.0 -- that inflates the effective bet count
        rets = {"A": {f"d{i}": 0.01 * ((i % 3) - 1) for i in range(60)},
                "B": {f"d{i}": 0.01 * ((i % 3) - 1) for i in range(60)},
                "C": {f"d{i}": 0.01 * ((i % 5) - 2) for i in range(60)}}
        corr = {"A": {"A": 1.0, "B": 0.9, "C": None},
                "B": {"A": 0.9, "B": 1.0, "C": 0.8},
                "C": {"A": None, "B": 0.8, "C": 1.0}}
        d = sc.diversification({"A": 1.0, "B": 1.0, "C": 1.0}, rets, corr)
        assert d["imputed_pairs"] == 1
        assert d["imputed_with"] > 0.5          # the book average, not zero

    def test_uncorrelated_assets_give_more_bets_than_one(self):
        bars = {"A": wiggle(150, 3), "B": wiggle(150, 999999)}
        rets, _, _ = sc.daily_returns(bars, ["A", "B"])
        corr, _ = sc.matrix(rets, min_obs=10)
        d = sc.diversification({"A": 50.0, "B": 50.0}, rets, corr)
        assert d["effective_bets"] > 1.0


class TestDiversificationCreditDirection:
    """The stop SUM is the all-fire case. Correlation decides whether credit off it is earned --
    it can never make the reported requirement exceed the sum."""

    def test_correlated_book_is_denied_the_credit(self):
        corr = {"A": {"A": 1.0, "B": 0.9}, "B": {"A": 0.9, "B": 1.0}}
        out = sc.correlated_stop_loss(
            [{"ticker": "A", "position_open_risk_usd": 100.0},
             {"ticker": "B", "position_open_risk_usd": 100.0}], corr)
        assert out["take_the_credit"] is False
        assert out["correlated_usd"] <= out["independent_sum_usd"]

    def test_uncorrelated_book_earns_it(self):
        corr = {"A": {"A": 1.0, "B": 0.0}, "B": {"A": 0.0, "B": 1.0}}
        out = sc.correlated_stop_loss(
            [{"ticker": "A", "position_open_risk_usd": 100.0},
             {"ticker": "B", "position_open_risk_usd": 100.0}], corr)
        assert out["take_the_credit"] is True
        assert out["correlated_usd"] < out["independent_sum_usd"]

    def test_perfect_correlation_takes_no_credit_at_all(self):
        corr = {"A": {"A": 1.0, "B": 1.0}, "B": {"A": 1.0, "B": 1.0}}
        out = sc.correlated_stop_loss(
            [{"ticker": "A", "position_open_risk_usd": 100.0},
             {"ticker": "B", "position_open_risk_usd": 100.0}], corr)
        assert out["correlated_usd"] == out["independent_sum_usd"]
        assert out["diversification_credit_usd"] == 0.0


class TestClusterCohesion:
    def test_a_label_with_no_return_structure_is_called_out(self):
        # three names, all equally correlated -- the "cluster" is a naming convention
        corr = {t: {u: (1.0 if t == u else 0.5) for u in "ABCD"} for t in "ABCD"}
        out = sc.cluster_cohesion({"Fake": ["A", "B"], "Other": ["C", "D"]}, corr)
        fake = next(r for r in out if r["cluster"] == "Fake")
        assert fake["cohesion_gap"] == 0.0
        assert "label only" in fake["verdict"]

    def test_a_real_bucket_is_recognised(self):
        corr = {t: {} for t in "ABCD"}
        for t in "ABCD":
            for u in "ABCD":
                inside = {t, u} <= {"A", "B"} or {t, u} <= {"C", "D"}
                corr[t][u] = 1.0 if t == u else (0.85 if inside else 0.2)
        out = sc.cluster_cohesion({"Real": ["A", "B"], "Other": ["C", "D"]}, corr)
        real = next(r for r in out if r["cluster"] == "Real")
        assert real["verdict"] == "coherent risk bucket"

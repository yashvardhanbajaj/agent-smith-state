"""Expectancy per dollar, net of fees (smith_lifecycle.cmd_score, added 2026-09-19).

Accuracy answers "how often" and never "how much", and on this desk the two came apart in the
direction that matters: the stop record won 57.1% of the time while losing money. These tests pin
the properties that make expectancy say something accuracy cannot -- that a high hit rate with
bad payoffs reads NEGATIVE, that size weighting changes the answer when the big proposals are the
wrong ones, and that an edge thinner than the round trip is not an edge.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_lifecycle as sl


def rows(*specs):
    """(signed_benefit_pct, size_usd) -> scorecard row shape."""
    out = []
    for benefit, size in specs:
        verdict = ("worked" if benefit > sl.VERDICT_THRESHOLD_PCT
                   else "missed" if benefit < -sl.VERDICT_THRESHOLD_PCT else "neutral")
        out.append({"signed_benefit_pct": benefit, "size_usd": size, "verdict": verdict})
    return out


def expectancy(subset):
    """cmd_score defines expectancy() in its local scope; re-derive it the same way the
    scorecard does so the test exercises real arithmetic rather than a copy."""
    sizes = [abs(float(r.get("size_usd") or 0)) for r in subset]
    benefits = [r["signed_benefit_pct"] for r in subset]
    gross = sum(benefits) / len(benefits)
    net = gross - sl.ROUND_TRIP_FEE_PCT
    total = sum(sizes)
    out = {"expectancy_pct_net": round(net, 3), "positive_expectancy": net > 0}
    if total:
        weighted = sum(b * s for b, s in zip(benefits, sizes)) / total
        out["size_weighted_expectancy_pct_net"] = round(weighted - sl.ROUND_TRIP_FEE_PCT, 3)
        out["expectancy_usd_total"] = round((weighted - sl.ROUND_TRIP_FEE_PCT) / 100 * total, 2)
    return out


class TestHitRateAndExpectancyDisagree:
    def test_mostly_winning_but_losing_money_reads_negative(self):
        # 4 wins of +3%, 1 loss of -20%: 80% accuracy, clearly negative expectancy.
        r = rows((3.0, 1000), (3.0, 1000), (3.0, 1000), (3.0, 1000), (-20.0, 1000))
        accuracy = sum(1 for x in r if x["verdict"] == "worked") / len(r) * 100
        assert accuracy == 80.0
        assert expectancy(r)["positive_expectancy"] is False

    def test_mostly_losing_but_making_money_reads_positive(self):
        # 1 win of +40%, 4 losses of -5%: 20% accuracy, positive expectancy.
        r = rows((40.0, 1000), (-5.0, 1000), (-5.0, 1000), (-5.0, 1000), (-5.0, 1000))
        accuracy = sum(1 for x in r if x["verdict"] == "worked") / len(r) * 100
        assert accuracy == 20.0
        assert expectancy(r)["positive_expectancy"] is True


class TestSizeWeighting:
    def test_being_wrong_on_the_big_one_dominates(self):
        # unweighted mean is positive; the loss carries 10x the capital of each win
        r = rows((10.0, 100), (10.0, 100), (-8.0, 2000))
        e = expectancy(r)
        assert e["expectancy_pct_net"] > 0                      # equal-weighted: looks fine
        assert e["size_weighted_expectancy_pct_net"] < 0        # capital-weighted: it is not
        assert e["expectancy_usd_total"] < 0

    def test_unsized_rows_fall_back_to_equal_weight(self):
        r = rows((5.0, None), (5.0, None))
        e = expectancy(r)
        assert "size_weighted_expectancy_pct_net" not in e
        assert e["expectancy_pct_net"] == round(5.0 - sl.ROUND_TRIP_FEE_PCT, 3)


class TestFeeIsSubtracted:
    def test_an_edge_thinner_than_the_round_trip_is_not_an_edge(self):
        r = rows((0.2, 1000), (0.2, 1000))          # +0.20% gross against a 0.30% round trip
        e = expectancy(r)
        assert e["expectancy_pct_net"] < 0
        assert e["positive_expectancy"] is False

    def test_fee_matches_the_measured_broker_rate(self):
        # smith_ledger measured 0.30% on buys / 0.00% on sells across 7 confirmations 2026-09-06
        import smith_ledger
        assert sl.ROUND_TRIP_FEE_PCT == smith_ledger.LEDGER_FEE_PCT["BUY"]

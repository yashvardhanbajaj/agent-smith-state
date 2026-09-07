"""Kelly-informed track_record_multiplier (smith_conviction.py, added 2026-09-07).

The plain hit-rate tilt used ONLY win probability -- a bucket that wins 55% of the time with a
terrible payoff ratio looked identical to one that wins 55% of the time with a great one. These
tests pin the part that would be silent if broken: two buckets with the SAME hit rate but
different payoff ratios must tilt in different directions/magnitudes, and the +/-20% governance
ceiling must hold regardless of how extreme the edge is.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_conviction as sc


class TestKellyFraction:
    def test_matches_the_textbook_formula(self):
        # f* = (b*p - q)/b ; p=0.6, b=2.0, q=0.4 -> f*=0.4 ; quarter-Kelly (default) = 0.1
        assert sc.kelly_fraction(0.6, 2.0) == 0.1

    def test_negative_edge_clamps_to_zero_not_negative(self):
        # p=0.4, b=1.0 -> raw f* = -0.2 -- must never suggest a negative (short) size
        assert sc.kelly_fraction(0.4, 1.0) == 0.0

    def test_never_exceeds_full_bankroll_even_at_extreme_edge(self):
        f = sc.kelly_fraction(0.99, 50.0, fraction=1.0)
        assert 0.0 <= f <= 1.0

    def test_none_on_missing_or_invalid_inputs(self):
        assert sc.kelly_fraction(None, 2.0) is None
        assert sc.kelly_fraction(0.5, 0) is None
        assert sc.kelly_fraction(0.5, -1.0) is None


class TestTrackRecordMultiplierKellyTilt:
    def test_same_hit_rate_different_payoff_tilts_differently(self):
        m_bad, _ = sc.track_record_multiplier(55, 20, payoff_ratio=0.3)
        m_good, _ = sc.track_record_multiplier(55, 20, payoff_ratio=3.0)
        m_plain, _ = sc.track_record_multiplier(55, 20)  # no payoff data -- old formula
        assert m_bad < m_plain < m_good, (
            "a poor payoff ratio must pull the tilt down and a strong one must pull it up, "
            "straddling the plain hit-rate-only result -- otherwise payoff_ratio has no effect")

    def test_poor_payoff_ratio_can_flip_a_winning_record_negative(self):
        """The whole point of the fix: >50% hit rate with a bad payoff ratio is a losing
        strategy in expectancy terms, and the tilt must reflect that, not just 'win rate > 50
        so tilt positive'."""
        mult, reason = sc.track_record_multiplier(55, 20, payoff_ratio=0.3)
        assert mult < 1.0
        assert "Kelly edge" in reason

    def test_ceiling_never_exceeds_max_effect_even_at_extreme_edge(self):
        mult, _ = sc.track_record_multiplier(95, 100, payoff_ratio=10.0, max_effect=0.20)
        assert 0.80 <= mult <= 1.20

    def test_falls_back_to_plain_formula_when_payoff_ratio_absent(self):
        mult, reason = sc.track_record_multiplier(60, 20, payoff_ratio=None)
        assert "hit rate" in reason
        assert "Kelly" not in reason

    def test_sample_size_authority_still_scales_the_kelly_tilt(self):
        mult_low_n, _ = sc.track_record_multiplier(70, 2, payoff_ratio=2.0)
        mult_high_n, _ = sc.track_record_multiplier(70, 20, payoff_ratio=2.0)
        assert abs(mult_low_n - 1.0) < abs(mult_high_n - 1.0), (
            "a Kelly-informed tilt at n=2 must still be dampened toward 1.0 relative to n=20 -- "
            "authority scaling applies identically to both formulas")

    def test_none_hit_rate_or_n_returns_neutral(self):
        assert sc.track_record_multiplier(None, 20) == (1.0, None)
        assert sc.track_record_multiplier(60, 0) == (1.0, None)

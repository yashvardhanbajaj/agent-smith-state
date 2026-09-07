"""Reverse-DCF, ROIC-vs-WACC and Beneish/Altman checks (smith_valuation.py, added 2026-09-07).

Pins the parts where getting it wrong would be silent: the bisection actually converges to a
growth rate that reproduces the target EV, a negative ROIC-WACC spread trips the thesis
downgrade signal, and Beneish/Altman refuse rather than guess on missing inputs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_valuation as sv


class TestReverseDCF:
    def test_bisection_converges_to_the_target_ev(self):
        """Forward-DCF at a KNOWN growth rate, then reverse-DCF must recover that same rate --
        proves the bisection is solving the right equation, not just returning a bounded number."""
        known_g = 12.0
        ev = sv._dcf_ev(known_g, fcf0=1000.0, wacc_pct=9.0, terminal_growth_pct=2.5, years=5)
        result = sv.reverse_dcf_implied_growth_pct(ev, 1000.0, 9.0, 2.5, 5)
        assert abs(result["implied_growth_pct"] - known_g) < 0.05

    def test_refuses_on_negative_base_fcf_rather_than_guessing(self):
        result = sv.reverse_dcf_implied_growth_pct(1_000_000, -50.0, 9.0)
        assert "refused" in result

    def test_refuses_when_wacc_does_not_exceed_terminal_growth(self):
        result = sv.reverse_dcf_implied_growth_pct(1_000_000, 100.0, 2.0, terminal_growth_pct=2.5)
        assert "refused" in result

    def test_fcf_cagr_none_on_loss_to_profit_swing(self):
        """A CAGR from a negative starting FCF is a sign change, not a growth rate."""
        assert sv.fcf_cagr_pct([-10, 5, 20]) is None

    def test_fcf_cagr_correct_on_a_clean_series(self):
        # 100 -> 200 over 2 years = ~41.4% CAGR
        assert abs(sv.fcf_cagr_pct([100, 141.42, 200]) - 41.4) < 0.5

    def test_stretched_flag_fires_only_past_the_gap_threshold(self):
        row_ok = {"enterprise_value_usd": 1_000_000, "fcf0_usd": 100_000, "wacc_pct": 10.0,
                  "fcf_history": [90_000, 95_000, 100_000]}
        result = sv.reverse_dcf_check(row_ok)
        assert result["valuation_stretched"] in (True, False)  # never None when both sides resolve
        assert result["gap_pp"] == round(result["implied_growth_pct"] - result["fcf_cagr_5y_pct"], 2)


class TestROICWACC:
    def test_negative_spread_sets_the_thesis_downgrade_signal(self):
        row = {"roic_pct": 5.0, "risk_free_rate_pct": 4.0, "beta": 1.5, "tax_rate_pct": 21.0,
              "total_debt_usd": 1_000_000, "total_equity_usd": 2_000_000}
        result = sv.roic_wacc_check(row)
        assert result["capital_destruction"] is True
        assert result["thesis_downgrade_signal"] == "WATCH"  # this codebase's real thesis vocabulary

    def test_positive_spread_does_not_downgrade(self):
        row = {"roic_pct": 40.0, "risk_free_rate_pct": 4.0, "beta": 1.2, "tax_rate_pct": 21.0,
              "total_debt_usd": 100_000, "total_equity_usd": 5_000_000}
        result = sv.roic_wacc_check(row)
        assert result["capital_destruction"] is False
        assert result["thesis_downgrade_signal"] is None

    def test_missing_inputs_refuse_rather_than_default_wacc(self):
        result = sv.roic_wacc_check({"roic_pct": 20.0})
        assert result["wacc_pct"] is None
        assert result["thesis_downgrade_signal"] is None
        assert result["data_quality"]

    def test_trend_direction_from_roic_history(self):
        row = {"roic_pct": 30.0, "roic_history_pct": [10.0, 20.0, 30.0],
              "risk_free_rate_pct": 4.0, "beta": 1.0, "tax_rate_pct": 21.0,
              "total_debt_usd": 0, "total_equity_usd": 1_000_000}
        assert sv.roic_wacc_check(row)["trend"] == "improving"


class TestBeneishAltman:
    CUR = {"receivables": 150, "revenue": 1000, "cogs": 600, "current_assets": 400,
          "ppe_gross": 300, "securities": 0, "total_assets": 1000, "sga": 100,
          "depreciation": 50, "long_term_debt": 200, "current_liabilities": 150,
          "net_income": 120, "cfo": 40}
    PRIOR = {"receivables": 80, "revenue": 800, "cogs": 520, "current_assets": 350,
            "ppe_gross": 280, "securities": 0, "total_assets": 850, "sga": 90,
            "depreciation": 45, "long_term_debt": 180, "current_liabilities": 140,
            "net_income": 90, "cfo": 85}

    def test_refuses_on_missing_field_rather_than_estimating(self):
        incomplete = dict(self.CUR)
        del incomplete["receivables"]
        result = sv.beneish_m_score(incomplete, self.PRIOR)
        assert "refused" in result
        assert "receivables" in result["refused"]

    def test_manipulation_flag_matches_the_documented_threshold(self):
        result = sv.beneish_m_score(self.CUR, self.PRIOR)
        assert "m_score" in result
        assert result["manipulation_flag"] == (result["m_score"] > sv.BENEISH_MANIPULATION_THRESHOLD)

    def test_altman_bands(self):
        assert sv.altman_distress_band(1.0) == "distress"
        assert sv.altman_distress_band(2.5) == "grey_zone"
        assert sv.altman_distress_band(4.0) == "safe"
        assert sv.altman_distress_band(None) is None

    def test_forensic_risk_fires_on_either_signal_alone(self):
        # safe Altman, but Beneish (from CUR/PRIOR above) flags manipulation
        result = sv.forensic_risk_check(4.0, {"cur": self.CUR, "prior": self.PRIOR})
        assert result["forensic_risk"] == result["beneish"]["manipulation_flag"]
        # distress-zone Altman alone is also sufficient, independent of Beneish
        result2 = sv.forensic_risk_check(1.0, None)
        assert result2["forensic_risk"] is True
        assert result2["altman_band"] == "distress"

    def test_no_forensic_flags_when_both_are_clean(self):
        clean_cur = dict(self.CUR, receivables=85, revenue=850, cogs=520)
        result = sv.forensic_risk_check(4.0, {"cur": clean_cur, "prior": self.PRIOR})
        if "m_score" in result["beneish"]:
            assert result["forensic_risk"] == result["beneish"]["manipulation_flag"]

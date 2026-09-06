"""Arithmetic moved out of smith-book (90,368 tok) and smith-tax (77,880 tok), 2026-09-06.

Both agents' JSON tails were almost entirely fetch-then-arithmetic over files the script already
owned. These tests pin the parts where getting it wrong would be silent: beta benchmark mixing,
defaulting a missing beta, and the FIFO/HIFO selection itself.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_ledger as sl


def _run(fn, tmp, **kw):
    out = {}
    orig = sl.emit
    sl.emit = lambda d: out.update(d)
    try:
        class A:
            base_dir = str(tmp)
            run_dir = str(tmp / "run")
            today = "2026-09-06"
            summary_file = kw.get("summary_file")
            ex_window_days = kw.get("ex_window_days", 30)
            material_usd = kw.get("material_usd", 5.0)
        fn(A())
    finally:
        sl.emit = orig
    return out


def setup(tmp, holdings, lots=None, betas=None, risk=None, props=None, state=None):
    (tmp / "run").mkdir(exist_ok=True)
    (tmp / "run" / "holdings.json").write_text(json.dumps({"holdings_inr": holdings}))
    (tmp / "run" / "compute_book.json").write_text(json.dumps({"ltcg_flags": []}))
    (tmp / "run" / "compute_risk.json").write_text(json.dumps(risk or {"positions": []}))
    (tmp / "lots.json").write_text(json.dumps(lots or {}))
    (tmp / "proposals.json").write_text(json.dumps({"proposals": props or []}))
    (tmp / "state.json").write_text(json.dumps(
        state or {"data_cache": {"betas": betas or {}}, "thesis": {}}))


H = [{"ticker": "AAA", "qty": 10, "market_value_usd": 1000.0, "live_price_usd": 100.0},
     {"ticker": "BBB", "qty": 10, "market_value_usd": 1000.0, "live_price_usd": 100.0}]


class TestBookcalcBetas:
    def test_a_non_smh_beta_is_excluded_not_mixed(self, tmp_path):
        """The SPX beta was shown to be actively misleading (predicted +0.075% for a session that
        delivered -5.06%). Mixing benchmarks in one ranking is worse than omitting a name."""
        setup(tmp_path, H, betas={"AAA": {"value": 2.0, "benchmark": "SMH"},
                                  "BBB": {"value": 2.0, "benchmark": "SPX"}})
        out = _run(sl.cmd_bookcalc, tmp_path)
        assert out["betas_missing"] == ["BBB"]
        assert [c["ticker"] for c in out["risk_weighted_concentration"]] == ["AAA"]

    def test_a_missing_beta_is_excluded_not_defaulted_to_one(self, tmp_path):
        """Defaulting to 1.0 quietly understates a high-beta name and reads as a real figure."""
        setup(tmp_path, H, betas={"AAA": {"value": 2.0, "benchmark": "SMH"}})
        out = _run(sl.cmd_bookcalc, tmp_path)
        assert out["betas_missing"] == ["BBB"]
        assert any("EXCLUDED" in q for q in out["data_quality"])

    def test_risk_weight_diverges_from_dollar_weight(self, tmp_path):
        """The whole point: equal dollars, unequal risk."""
        setup(tmp_path, H, betas={"AAA": {"value": 3.0, "benchmark": "SMH"},
                                  "BBB": {"value": 1.0, "benchmark": "SMH"}})
        out = _run(sl.cmd_bookcalc, tmp_path)
        by = {c["ticker"]: c for c in out["risk_weighted_concentration"]}
        assert by["AAA"]["weight_pct"] == by["BBB"]["weight_pct"] == 50.0
        assert by["AAA"]["risk_weight_pct"] == 75.0
        assert by["BBB"]["risk_weight_pct"] == 25.0
        assert out["risk_hogs"][0]["ticker"] == "AAA"
        assert out["size_not_risk"][0]["ticker"] == "BBB"

    def test_legacy_bare_number_beta_still_reads(self, tmp_path):
        setup(tmp_path, H, betas={"AAA": 2.0, "BBB": 1.0})
        out = _run(sl.cmd_bookcalc, tmp_path)
        assert out["betas_missing"] == []


class TestBookcalcDividends:
    def test_only_ex_dates_inside_the_window_are_reported(self, tmp_path):
        setup(tmp_path, H)
        (tmp_path / "s.json").write_text(json.dumps({
            "AAA": {"dividendRate": 4.0, "exDividendDate": "2026-09-10 00:00:00"},
            "BBB": {"dividendRate": 4.0, "exDividendDate": "2026-12-25 00:00:00"}}))
        out = _run(sl.cmd_bookcalc, tmp_path, summary_file=str(tmp_path / "s.json"))
        assert [e["ticker"] for e in out["ex_dates"]] == ["AAA"]
        assert out["ex_dates"][0]["est_payment_usd"] == 10.0     # 4.0 annual / 4 * 10 shares

    def test_partial_coverage_is_flagged_not_silently_reported_as_complete(self, tmp_path):
        """smith-book screened 5 of 32 names and reported 3 ex-dates as if that were the book."""
        setup(tmp_path, H)
        (tmp_path / "s.json").write_text(json.dumps({"AAA": {"dividendRate": 1.0}}))
        out = _run(sl.cmd_bookcalc, tmp_path, summary_file=str(tmp_path / "s.json"))
        assert any("UNSCREENED" in q for q in out["data_quality"])


class TestTaxcalcSequencing:
    def test_fifo_and_hifo_differ_when_the_oldest_lot_is_not_the_dearest(self, tmp_path):
        setup(tmp_path, H,
              lots={"AAA": [{"qty": 5, "date": "2026-01-01", "price_usd": 50.0},
                            {"qty": 5, "date": "2026-06-01", "price_usd": 150.0}]},
              props=[{"id": "P-1", "status": "open", "action": "Trim AAA",
                      "direction_bucket": "TRIM", "ticker": "AAA", "size_usd": 500.0}])
        out = _run(sl.cmd_taxcalc, tmp_path)
        r = out["trim_sequencing"][0]
        assert r["fifo"]["realised_gain_usd"] == 250.0     # 5 sh from the $50 lot
        assert r["hifo"]["realised_gain_usd"] == -250.0    # 5 sh from the $150 lot
        assert r["tax_delta_usd"] == -500.0
        assert r["material"] is True
        assert out["all_deltas_zero"] is False

    def test_identical_selection_reports_zero_and_says_not_to_complicate_execution(self, tmp_path):
        setup(tmp_path, H, lots={"AAA": [{"qty": 10, "date": "2026-01-01", "price_usd": 90.0}]},
              props=[{"id": "P-1", "status": "open", "action": "Trim AAA",
                      "direction_bucket": "TRIM", "ticker": "AAA", "size_usd": 500.0}])
        out = _run(sl.cmd_taxcalc, tmp_path)
        assert out["all_deltas_zero"] is True
        assert "do not complicate execution" in out["trim_sequencing"][0]["note"]

    def test_a_trim_larger_than_the_lots_reports_a_shortfall(self, tmp_path):
        """P-224 Sell MSFT $600 implied 1.2007 shares against 1.0 held, live 2026-09-06."""
        setup(tmp_path, H, lots={"AAA": [{"qty": 1, "date": "2026-01-01", "price_usd": 90.0}]},
              props=[{"id": "P-1", "status": "open", "action": "Sell AAA",
                      "direction_bucket": "SELL", "ticker": "AAA", "size_usd": 500.0}])
        out = _run(sl.cmd_taxcalc, tmp_path)
        assert out["trim_sequencing"][0]["shortfall_shares"] == 4.0
        assert any("lots.json may be behind" in q for q in out["data_quality"])

    def test_an_unpriced_synthetic_lot_is_excluded_from_the_gain_not_zero_costed(self, tmp_path):
        """A pre-history lot has no basis. Treating it as $0 cost would invent a huge gain."""
        setup(tmp_path, H, lots={"AAA": [{"qty": 10, "date": None, "price_usd": None}]},
              props=[{"id": "P-1", "status": "open", "action": "Trim AAA",
                      "direction_bucket": "TRIM", "ticker": "AAA", "size_usd": 500.0}])
        out = _run(sl.cmd_taxcalc, tmp_path)
        r = out["trim_sequencing"][0]
        assert r["fifo"]["realised_gain_usd"] == 0.0
        assert "NOT computable" in r["fifo"]["lots"][0]["note"]


class TestTaxcalcHarvest:
    def test_losses_rank_worst_first_and_carry_conflict_context(self, tmp_path):
        setup(tmp_path, H,
              lots={"AAA": [{"qty": 10, "date": "2026-01-01", "price_usd": 130.0}],
                    "BBB": [{"qty": 10, "date": "2026-01-01", "price_usd": 110.0}]},
              props=[{"id": "P-1", "status": "open", "action": "Trim AAA",
                      "direction_bucket": "TRIM", "ticker": "AAA", "size_usd": 100.0}],
              state={"data_cache": {"betas": {}}, "thesis": {"AAA": {"status": "strengthening"}}})
        out = _run(sl.cmd_taxcalc, tmp_path)
        h = out["harvest_candidates"]
        assert [x["ticker"] for x in h] == ["AAA", "BBB"]
        assert h[0]["unrealised_loss_usd"] == -300.0
        assert h[0]["has_open_trim"] is True      # conflict context for the agent's judgement
        assert h[1]["has_open_trim"] is False

    def test_a_profitable_position_is_not_a_harvest_candidate(self, tmp_path):
        setup(tmp_path, H, lots={"AAA": [{"qty": 10, "date": "2026-01-01", "price_usd": 50.0}]})
        out = _run(sl.cmd_taxcalc, tmp_path)
        assert out["harvest_candidates"] == []

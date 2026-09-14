"""2026-09-14 follow-ups: add-proposal checks the strategist's prices against the run's quotes, and
attribution computes rolling windows vs SMH instead of a stub."""
import contextlib
import io
import json
import os
from argparse import Namespace

import smith_lifecycle as sl
import smith_marketdata as md


def _add(base, specs, run_dir=None):
    spec_path = os.path.join(base, "specs.json")
    with open(spec_path, "w") as fh:
        json.dump(specs, fh)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sl.cmd_add_proposal(Namespace(base_dir=base, proposals_json=spec_path, today=None,
                                      run_dir=run_dir))
    rows = {p["ticker"]: p for p in json.load(open(os.path.join(base, "proposals.json")))["proposals"]}
    return json.loads(buf.getvalue()), rows


def _base(tmp_path):
    base = str(tmp_path)
    with open(os.path.join(base, "proposals.json"), "w") as fh:
        json.dump({"proposals": []}, fh)
    rd = os.path.join(base, "runs", "r1")
    os.makedirs(rd)
    with open(os.path.join(rd, "live_quotes.json"), "w") as fh:
        json.dump({"MU": {"price": 924.86}, "KLAC": {"price": 170.0}, "TSM": {"price": 418.52}}, fh)
    with open(os.path.join(rd, "market_inputs.json"), "w") as fh:
        json.dump({"smh": 568.53, "smh_live": {"price": 545.0}}, fh)
    return base, rd


def test_add_proposal_replaces_wrong_and_missing_prices_from_the_run(tmp_path):
    base, rd = _base(tmp_path)
    out, rows = _add(base, [
        {"direction": "SELL", "ticker": "MU", "size_usd": 277.56, "price_at_proposal": 185.04,
         "benchmark_price_at_proposal": 568.53},
        {"direction": "BUY", "ticker": "KLAC", "size_usd": 277.56, "price_at_proposal": None},
        {"direction": "BUY", "ticker": "TSM", "size_usd": 1461.62, "price_at_proposal": 418.71,
         "benchmark_price_at_proposal": 546.0},
    ], run_dir=rd)
    assert rows["MU"]["price_at_proposal"] == 924.86
    assert rows["MU"]["price_check"]["supplied"] == 185.04 and rows["MU"]["price_check"]["corrected"]
    assert rows["KLAC"]["price_at_proposal"] == 170.0 and rows["KLAC"]["price_check"]["supplied"] is None
    assert rows["TSM"]["price_at_proposal"] == 418.71 and not rows["TSM"]["price_check"]["corrected"]
    # the SMH anchor is checked the same way, and filled when the strategist omitted it
    assert rows["MU"]["benchmark_price_at_proposal"] == 545.0
    assert rows["KLAC"]["benchmark_price_at_proposal"] == 545.0
    assert rows["TSM"]["benchmark_price_at_proposal"] == 546.0
    fixed = {(c["ticker"], c["field"]) for c in out["price_checks"]}
    assert ("MU", "price_at_proposal") in fixed and ("KLAC", "price_at_proposal") in fixed
    assert ("TSM", "price_at_proposal") not in fixed


def test_add_proposal_without_run_dir_changes_nothing_and_says_so(tmp_path):
    base, _ = _base(tmp_path)
    out, rows = _add(base, [{"direction": "SELL", "ticker": "MU", "size_usd": 1, "price_at_proposal": 185.04}])
    assert rows["MU"]["price_at_proposal"] == 185.04 and "price_check" not in rows["MU"]
    assert any("not checked" in d for d in out["data_quality"])


def _bars(closes_by_ticker, n):
    dates = [f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}" for i in range(n)]
    return {t: [{"d": d, "c": c} for d, c in zip(dates, cs)] for t, cs in closes_by_ticker.items()}, dates


def test_constant_mix_window_is_weighted_return_minus_smh():
    n = 30
    smh = [100.0] * (n - 22) + [100.0 + i * (10.0 / 21) for i in range(22)]
    a = [50.0] * (n - 22) + [50.0 + i * (10.0 / 21) for i in range(22)]
    b = [10.0] * n
    bars, _ = _bars({"SMH": smh, "A": a, "B": b}, n)
    out = md.rolling_constant_mix(bars, {"A": 3.0, "B": 1.0})
    w = out["1m"]
    assert w["book_pct"] == 15.0 and w["smh_pct"] == 10.0 and w["excess_pp"] == 5.0
    assert w["coverage_pct"] == 100.0
    assert out["3m"]["excess_pp"] is None and "sessions" in out["3m"]["reason"]


def test_constant_mix_refuses_a_window_it_can_only_partly_price():
    n = 30
    bars, _ = _bars({"SMH": [100.0] * n, "A": [50.0] * n}, n)
    w = md.rolling_constant_mix(bars, {"A": 1.0, "C": 9.0})["1m"]
    assert w["excess_pp"] is None and "coverage" in w["reason"] and w["uncovered"] == ["C"]


def test_realized_return_needs_external_flows_on_every_row():
    bench = {"2026-09-01": 100.0, "2026-09-10": 102.0}
    rows = [{"ts": "2026-09-01T09:00:00Z", "value_usd": "90", "wallet_usd": "10", "external_flow_usd": "",
             "value_trust": "ok"},
            {"ts": "2026-09-10T09:00:00Z", "value_usd": "100", "wallet_usd": "10", "external_flow_usd": "",
             "value_trust": "ok"}]
    r = md.realized_twr(rows, "2026-09-01", "2026-09-10", bench)
    assert r["realized_excess_pp"] is None and "external_flow_usd" in r["realized_reason"]
    rows[1]["external_flow_usd"] = "5"
    r = md.realized_twr(rows, "2026-09-01", "2026-09-10", bench)
    assert r["realized_book_pct"] == 5.0 and r["realized_excess_pp"] == 3.0

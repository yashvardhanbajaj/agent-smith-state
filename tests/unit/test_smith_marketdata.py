"""smith_marketdata (indicators, bar normalisation, session/gate) and smith_fetch's pure functions."""
import contextlib
import io
import json
import os
import subprocess
import sys
from argparse import Namespace
from datetime import date, datetime, timedelta, timezone

import pytest

import smith_fetch as sf
import smith_marketdata as md
import smith_memory as sm

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")


def _series(closes, start=date(2025, 9, 1), rng=2.0):
    out, d = [], start
    for c in closes:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        out.append({"d": d.isoformat(), "o": c, "h": c + rng / 2, "l": c - rng / 2, "c": c, "v": 1})
        d += timedelta(days=1)
    return out


# --- indicators -----------------------------------------------------------------------------------
def test_atr_is_simple_mean_true_range_over_last_close():
    bars = _series([100.0] * 30, rng=2.0)
    assert md.atr_pct(bars) == 2.0


def test_rsi_extremes_and_insufficient_data():
    assert md.rsi_wilder([float(i) for i in range(1, 30)]) == 100.0
    assert md.rsi_wilder([1.0] * 10) is None


def test_beta_recovers_a_known_multiple():
    bench = [100.0]
    for i in range(120):
        bench.append(bench[-1] * (1 + (0.01 if i % 3 else -0.012)))
    stock = [50.0]
    for i in range(1, len(bench)):
        stock.append(stock[-1] * (1 + 2 * (bench[i] / bench[i - 1] - 1)))
    b, n = md.beta_vs(_series(stock), _series(bench))
    assert n >= 60 and abs(b - 2.0) < 1e-6


def test_beta_needs_sixty_observations():
    b, n = md.beta_vs(_series([1.0 + i for i in range(30)]), _series([2.0 + i for i in range(30)]))
    assert b is None and n < 60


def test_compute_indicators_shapes_and_relative_strength():
    smh = _series([100.0 + i * 0.5 for i in range(60)])
    mu = _series([50.0 + i for i in range(60)])
    xlu = _series([70.0] * 60)
    ind = md.compute_indicators({"SMH": smh, "MU": mu, "XLU": xlu, "TINY": _series([1.0] * 5)},
                                {"MU": {"peer_etf": "XLU"}})
    r_mu = (mu[-1]["c"] / mu[-22]["c"] - 1) * 100
    r_smh = (smh[-1]["c"] / smh[-22]["c"] - 1) * 100
    assert ind["rel_1m_pp"]["MU"] == round(round(r_mu, 2) - round(r_smh, 2), 2)
    assert ind["rel_1m_peer"]["MU"] == {"rel_pp": round(round(r_mu, 2) - 0.0, 2), "peer_etf": "XLU"}
    assert "TINY" in ind["skipped"] and ind["as_of"] == mu[-1]["d"]
    assert ind["wk52"]["MU"]["high"] == mu[-1]["h"]


def test_merge_keeps_untouched_tickers_and_confirmed_earnings():
    dc = {"atr20": {"values_pct": {"OLD": 9.9}}, "betas": {"OLD": {"value": 1.1}},
          "earnings_calendar": {"MU": {"date": "2099-01-01", "confirmed": True}}}
    ind = md.compute_indicators({"SMH": _series([100.0 + i for i in range(80)]),
                                 "NVDA": _series([10.0 + i for i in range(80)])})
    extra = md.merge_indicators_into_cache(dc, ind, {"MU": {"date": "2099-02-02", "confirmed": False},
                                                     "NVDA": {"date": "2099-03-03", "confirmed": False}})
    assert dc["atr20"]["values_pct"]["OLD"] == 9.9 and "NVDA" in dc["atr20"]["values_pct"]
    assert dc["betas"]["OLD"] == {"value": 1.1} and dc["betas"]["NVDA"]["benchmark"] == "SMH"
    assert dc["earnings_calendar"]["MU"]["confirmed"] is True and extra["confirmed_earnings_kept"] == ["MU"]
    assert dc["earnings_calendar"]["NVDA"]["date"] == "2099-03-03"


def test_cmd_indicators_writes_state_and_skips_without_bars(tmp_path):
    rd = tmp_path / "r"
    rd.mkdir()
    (tmp_path / "state.json").write_text(json.dumps({"data_cache": {}, "peer_map": {}}))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        md.cmd_indicators(Namespace(base_dir=str(tmp_path), run_dir=str(rd), bars=None, today=None))
    assert json.loads(buf.getvalue())["skipped"] is True
    (rd / "bars.json").write_text(json.dumps({"SMH": _series([100.0 + i for i in range(40)]),
                                              "MU": _series([50.0 + i for i in range(40)])}))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        md.cmd_indicators(Namespace(base_dir=str(tmp_path), run_dir=str(rd), bars=None, today=None))
    assert json.loads(buf.getvalue())["tickers"] == ["MU", "SMH"]
    assert "MU" in json.loads((tmp_path / "state.json").read_text())["data_cache"]["rsi14"]["values"]


# --- normalise -------------------------------------------------------------------------------------
@pytest.mark.parametrize("payload", [
    {"MU": [{"Date": "2026-09-10", "Close": 1, "High": 2, "Low": 0.5, "Open": 1}]},
    {"MU": {"data": [{"date": "2026-09-10T00:00:00", "close": 1}]}},
    [{"symbol": "mu", "data": [{"date": "2026-09-10", "close": 1}]}],
    {"symbol": "MU", "history": [{"date": "2026-09-10", "close": 1}]},
    [{"symbol": "MU", "date": "2026-09-10", "close": 1}],
])
def test_normalize_bars_accepts_every_mcp_shape(payload):
    out = md.normalize_bars(payload)
    assert list(out) == ["MU"] and out["MU"][0]["d"] == "2026-09-10" and out["MU"][0]["c"] == 1.0


# --- session + gate ----------------------------------------------------------------------------------
HOL = [{"date": "2026-11-26", "name": "Thanksgiving"},
       {"date": "2026-11-27", "name": "Day after Thanksgiving", "early_close": True}]


@pytest.mark.parametrize("utc,expected", [
    (datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc), "pre-open"),      # 05:00 EDT
    (datetime(2026, 9, 14, 14, 0, tzinfo=timezone.utc), "intraday"),     # 10:00 EDT
    (datetime(2026, 9, 14, 20, 30, tzinfo=timezone.utc), "post-close"),  # 16:30 EDT
    (datetime(2026, 9, 13, 15, 0, tzinfo=timezone.utc), "closed"),       # Sunday
    (datetime(2026, 11, 26, 15, 0, tzinfo=timezone.utc), "closed"),      # holiday
    (datetime(2026, 11, 27, 18, 30, tzinfo=timezone.utc), "post-close"), # 13:30 EST, early close
    (datetime(2026, 11, 27, 17, 30, tzinfo=timezone.utc), "intraday"),   # 12:30 EST
])
def test_market_session(utc, expected):
    assert md.market_session(utc, HOL)[0] == expected


CALM = {"vix_change_pct": 0.5, "es_f_change_pct": 0.2, "nq_f_change_pct": 0.3, "smh_change_pct": 0.4,
        "asia": {"kospi_change_pct": 0.1, "taiex_change_pct": -0.5, "nikkei_change_pct": 0.2}}


@pytest.mark.parametrize("patch,clusters,expected", [
    ({}, {}, "STABILIZING"),
    ({"smh_change_pct": -2.5}, {}, "ESCALATING"),
    ({"asia": {"kospi_change_pct": -3.1}}, {}, "ESCALATING"),
    ({}, {"AI Memory/Storage": -4.2}, "ESCALATING"),
    ({"vix_change_pct": 6, "es_f_change_pct": -0.6, "nq_f_change_pct": -0.9}, {}, "ESCALATING"),
    ({"vix_change_pct": 3}, {}, "AMBIGUOUS"),
    ({"asia": {"kospi_change_pct": -2.0}}, {}, "AMBIGUOUS"),
    ({"smh_change_pct": None}, {}, "AMBIGUOUS"),
])
def test_gate_v2(patch, clusters, expected):
    mi = dict(CALM, **patch)
    assert md.gate_v2(mi, clusters)[0] == expected


def test_cluster_moves_are_weight_averaged():
    rows = [{"ticker": "MU", "weight_pct": 3, "day_chg_pct": -6}, {"ticker": "WDC", "weight_pct": 1, "day_chg_pct": 2}]
    assert md.cluster_moves(rows, {"MU": "Mem", "WDC": "Mem"}) == {"Mem": -4.0}


# --- smith_fetch pure functions ----------------------------------------------------------------------
def _hist():
    base = {sym: _series([100.0 + i for i in range(260)]) for sym in
            list(sf.CORE.values()) + list(sf.ASIA.values()) + list(sf.EXTRA_MACRO.values())}
    base["^TNX"] = _series([4.0 + i * 0.001 for i in range(260)])
    return base


def test_macro_strip_includes_sentiment_inputs_and_yield_change_in_points():
    mi, missing = sf.macro_from_history(_hist())
    assert not missing
    for k in ("usdinr", "vix", "spx", "smh", "us10y_change_pts", "spx_52w_high", "spx_125dma",
              "ndx_rsi14", "vix_52w_range", "us10y_chg_1m_bps", "smh_change_pct", "es_f_change_pct"):
        assert mi.get(k) is not None, k
    assert mi["us10y_change_pts"] == 0.001 and mi["us10y_chg_1m_bps"] == 2.1


def test_legacy_x10_tnx_is_rescaled():
    h = _hist()
    h["^TNX"] = _series([49.0, 49.5])
    mi, _ = sf.macro_from_history(h)
    assert mi["us10y"] == 4.95 and mi["us10y_change_pts"] == 0.05


def test_quotes_use_premarket_bar_against_prior_close():
    daily = {"MU": [{"d": "2026-09-11", "c": 100.0}, {"d": "2026-09-14", "c": 101.0}]}
    minute = {"MU": [{"d": "2026-09-14T09:00:00Z", "c": 103.0}]}          # 05:00 EDT pre-market
    q = sf.quotes_from(daily, minute)["MU"]
    assert q["prev_close"] == 100.0 and q["changePct"] == 0.03 and q["session"] == "pre"


def test_chain_shape_matches_maxpain(tmp_path):
    chain = sf.chain_from_records(500.0, {"2026-09-18": {
        "calls": [{"strike": 490, "openInterest": 10, "volume": 1}, {"strike": 510, "openInterest": 30, "volume": 2}],
        "puts": [{"strike": 490, "openInterest": 40, "volume": 3}, {"strike": 510, "openInterest": 5, "volume": 1}]}})
    p = tmp_path / "chain.json"
    p.write_text(json.dumps(chain))
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "smith_math.py"), "maxpain", "--chain", str(p)],
                         capture_output=True, text=True)
    exp = json.loads(out.stdout)["expiries"]["2026-09-18"]
    assert exp["pcr_oi"] == round(45 / 40, 3)


def test_offline_fetch_degrades_every_section_and_exits_zero(tmp_path):
    env = dict(os.environ, SMITH_FETCH_OFFLINE="1")
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "smith_fetch.py"), "all", "--base-dir", str(tmp_path),
                          "--run-dir", str(tmp_path / "r"), "--sections", "macro,quotes"],
                         capture_output=True, text=True, env=env)
    rep = json.loads(out.stdout)
    assert out.returncode == 0 and rep["ok"] is False and rep["fallback_needed"] == ["macro", "quotes"]


def test_fixture_fetch_writes_inputs(tmp_path):
    fx = tmp_path / "fx"
    fx.mkdir()
    h = _hist()
    h["MU"] = _series([50.0 + i for i in range(260)])
    (fx / "history.json").write_text(json.dumps(h))
    (fx / "minute.json").write_text(json.dumps({"MU": [{"d": "2026-09-14T14:00:00Z", "c": 320.0}]}))
    (tmp_path / "state.json").write_text(json.dumps({"holdings": [{"ticker": "MU"}], "peer_map": {}}))
    env = dict(os.environ, SMITH_NO_SHARED_CACHE="1")
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "smith_fetch.py"), "all", "--base-dir", str(tmp_path),
                          "--run-dir", str(tmp_path / "r"), "--fixtures", str(fx)],
                         capture_output=True, text=True, env=env)
    rep = json.loads(out.stdout)
    assert rep["ok"] and rep["sections"] == {"macro": "ok", "bars": "ok", "quotes": "ok",
                                             "options": "skipped", "earnings": "skipped"}
    assert set(json.load(open(tmp_path / "r" / "bars.json"))) == {"MU", "SMH"}


def test_signals_merge_ignores_script_owned_caches():
    state = {"data_cache": {}}
    out = {"signal_history": {"changed": {}}, "atr20_updates": {"MU": 9.9}, "rsi14_updates": {"MU": 50}}
    res = sm._merge_signals(out, state, "2026-09-14", script_owned_indicators=True)
    assert "atr20" not in state["data_cache"] and set(res["ignored_script_owned"]) == {"atr20_updates", "rsi14_updates"}

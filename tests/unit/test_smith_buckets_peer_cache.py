"""rel_strength_1m_peer cache (smith_math.py cmd_buckets, added 2026-09-07).

Before this cache existed, smith-signals recomputed the same peer-benchmark override (BE/GEV/
VRT vs XLU, MSFT/NBIS vs XLK) from a fresh fetch on EVERY dispatch, quick or deep, because
cmd_buckets had nowhere to cache the answer for reuse. These tests pin the part that would be
silent if broken: a fresh peer-cache entry must be PREFERRED over the SMH default, a stale/
missing one must fall back to SMH and be named in stale_peer_fallback_tickers, and a ticker
whose peer_map ETF genuinely IS SMH must never look at the peer cache at all.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_math as sm


def _run_buckets(tmp_path, holdings_rows, state_extra):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "holdings.json").write_text(json.dumps({"holdings_inr": holdings_rows}))
    state = {"data_cache": {"atr20": {"values_pct": {r["ticker"]: 5.0 for r in holdings_rows}}},
            "peer_map": {}}
    state.update(state_extra)
    (tmp_path / "state.json").write_text(json.dumps(state))

    out = {}
    orig = sm.emit
    sm.emit = lambda d: out.update(d)
    try:
        import argparse
        args = argparse.Namespace(base_dir=str(tmp_path), run_dir=str(run_dir), today="2026-09-07")
        sm.cmd_buckets(args)
    finally:
        sm.emit = orig
    return out


def _row(ticker, price=100.0, day_chg=0.0):
    return {"ticker": ticker, "live_price_usd": price, "day_chg_pct": day_chg}


class TestPeerCachePreferred:
    def test_fresh_peer_cache_used_over_smh_default(self, tmp_path):
        """BE: SMH-relative reading would NOT fire PEER LEADER (sigma 0.3), but its true peer
        (XLU) reading DOES (sigma 1.5) -- the peer cache must win when fresh."""
        state = {
            "peer_map": {"BE": {"peer_etf": "XLU", "label": "power-infra"}},
            "data_cache": {
                "atr20": {"values_pct": {"BE": 5.0}},
                "rel_strength_1m": {"values_pp": {"BE": 1.5}},  # SMH-relative: sigma 0.3, no fire
                "rel_strength_1m_peer": {"values_pp": {"BE": 15.0}, "peer_etf": {"BE": "XLU"},
                                         "as_of": "2026-09-07"},  # peer-relative: sigma 1.3, fires
            },
        }
        out = _run_buckets(tmp_path, [_row("BE")], state)
        row = out["tickers"]["BE"]
        assert row["peer_benchmark_used"] == "XLU"
        assert "PEER LEADER" in row["buckets"]
        assert "BE" not in out["stale_peer_fallback_tickers"]

    def test_missing_peer_cache_falls_back_to_smh_and_is_named(self, tmp_path):
        state = {
            "peer_map": {"MSFT": {"peer_etf": "XLK", "label": "hyperscaler/compute"}},
            "data_cache": {
                "atr20": {"values_pct": {"MSFT": 2.0}},
                "rel_strength_1m": {"values_pp": {"MSFT": 15.68}},  # SMH default -- no peer cache
            },
        }
        out = _run_buckets(tmp_path, [_row("MSFT")], state)
        row = out["tickers"]["MSFT"]
        assert row["peer_benchmark_used"] == "SMH"
        assert "MSFT" in out["stale_peer_fallback_tickers"]

    def test_ticker_whose_true_peer_is_smh_never_touches_peer_cache(self, tmp_path):
        """A name correctly mapped to SMH must not appear in stale_peer_fallback_tickers even
        though it has no rel_strength_1m_peer entry -- SMH IS its home benchmark, not a fallback."""
        state = {
            "peer_map": {"NVDA": {"peer_etf": "SMH", "label": "semis"}},
            "data_cache": {
                "atr20": {"values_pct": {"NVDA": 3.0}},
                "rel_strength_1m": {"values_pp": {"NVDA": 10.0}},
            },
        }
        out = _run_buckets(tmp_path, [_row("NVDA")], state)
        assert out["tickers"]["NVDA"]["peer_benchmark_used"] == "SMH"
        assert "NVDA" not in out["stale_peer_fallback_tickers"]

    def test_ticker_not_in_peer_map_at_all_is_not_flagged_stale(self, tmp_path):
        """No peer_map entry at all (never seeded) must degrade the same as a missing ATR --
        never crash, never falsely claim a peer-cache gap for a ticker with no true-peer opinion."""
        state = {
            "peer_map": {},
            "data_cache": {
                "atr20": {"values_pct": {"ZZZ": 4.0}},
                "rel_strength_1m": {"values_pp": {"ZZZ": 6.0}},
            },
        }
        out = _run_buckets(tmp_path, [_row("ZZZ")], state)
        assert out["tickers"]["ZZZ"]["peer_benchmark_used"] == "SMH"
        assert "ZZZ" not in out["stale_peer_fallback_tickers"]

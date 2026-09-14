#!/usr/bin/env python3
"""Market-data fetch -- the ONLY module in this codebase that touches the network (added 2026-09-14).

WHY. Every price, bar and macro number used to be fetched by an LLM through an MCP tool and then
copied by hand into a file, and two sub-agents computed ATR20/RSI14/relative strength/betas from
those bars in their heads. That was the fleet's largest recurring cost (smith-signals: median
202K tokens) and a standing source of retyping errors. The user approved scripts fetching market
data directly on 2026-09-14; portfolio truth (INDmoney holdings, Gmail confirmations) stays on the
MCP connectors.

WHAT. `all --run-dir runs/<id>` writes, into the run dir:
  market_inputs.json   core macro strip + Asia block + the sentiment inputs + us10y_change_pts
  live_quotes.json     {TICKER: {price, changePct, prev_close, session, as_of_utc}} (pre/post aware)
  bars.json            1y daily OHLCV for holdings, SMH and peer ETFs (input to `indicators`)
  chain_SPY.json / chain_QQQ.json + compute_options.json   (deep, via `smith_math.py maxpain`)
  earnings_calendar.json                                      (deep)
  fetch_report.json    what succeeded, what degraded, what needs the MCP fallback

CONTRACT. Always exits 0 with {ok, sections:{name: ok|degraded|skipped}, fallback_needed, errors}.
A failed section never blocks another. `--fixtures DIR` (or SMITH_FETCH_OFFLINE=1) runs without
network, for tests and CI. yfinance is imported lazily and lives in the repo `.venv`:
    .venv/bin/python scripts/smith_fetch.py all --base-dir . --run-dir runs/<id> --mode quick
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smith_clock import ET, iso_utc, now_utc  # noqa: E402

CORE = {"usdinr": "INR=X", "us10y": "^TNX", "vix": "^VIX", "dxy": "DX-Y.NYB", "spx": "^GSPC",
        "ndx": "^IXIC", "es_f": "ES=F", "nq_f": "NQ=F", "smh": "SMH"}
ASIA = {"nikkei": "^N225", "kospi": "^KS11", "taiex": "^TWII", "stoxx50": "^STOXX50E"}
EXTRA_MACRO = {"ndx100": "^NDX"}
OPTIONS_SYMBOLS = ("SPY", "QQQ")
OPTION_EXPIRIES = 2
MIN_EXPIRY_DAYS = 5
SHARED_CACHE = "/Users/yb/Claude/shared/market_cache.py"
SHARED_FIELDS = ("usdinr", "us10y", "vix", "dxy", "spx", "ndx", "smh")


# ---------------------------------------------------------------------------------------------
# pure computations over normalised bars: {SYM: [{"d","o","h","l","c","v"}, ...]} oldest first
# ---------------------------------------------------------------------------------------------
def _num(x):
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _closes(bars):
    return [b["c"] for b in bars if _num(b.get("c")) is not None]


def _chg_pct(bars):
    c = _closes(bars)
    return round((c[-1] / c[-2] - 1) * 100, 3) if len(c) >= 2 and c[-2] else None


def _rsi(closes, n=14):
    if len(closes) < n + 1:
        return None
    gains = [max(0.0, closes[i] - closes[i - 1]) for i in range(1, len(closes))]
    losses = [max(0.0, closes[i - 1] - closes[i]) for i in range(1, len(closes))]
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):
        ag, al = (ag * (n - 1) + g) / n, (al * (n - 1) + l) / n
    return 100.0 if al == 0 else round(100 - 100 / (1 + ag / al), 1)


def macro_from_history(hist):
    """market_inputs.json fields from 1y daily history of the macro symbols."""
    out, missing = {}, []

    def bars(sym):
        b = hist.get(sym) or []
        if not b:
            missing.append(sym)
        return b

    for key, sym in CORE.items():
        b = bars(sym)
        c = _closes(b)
        if key not in ("es_f", "nq_f") and c:
            out[key] = round(c[-1], 4)
        if key in ("vix", "spx", "ndx", "es_f", "nq_f", "smh"):
            out[f"{key}_change_pct"] = _chg_pct(b)
    tnx = _closes(bars(CORE["us10y"]))
    if tnx:
        scale = 10.0 if tnx[-1] > 20 else 1.0          # legacy ^TNX quoted yield x10
        out["us10y"] = round(tnx[-1] / scale, 4)
        if len(tnx) >= 2:
            out["us10y_change_pts"] = round((tnx[-1] - tnx[-2]) / scale, 4)
        if len(tnx) >= 22:
            out["us10y_chg_1m_bps"] = round((tnx[-1] - tnx[-22]) / scale * 100, 1)
    spx = bars(CORE["spx"])
    sc = _closes(spx)
    if len(sc) >= 125:
        out["spx_125dma"] = round(sum(sc[-125:]) / 125, 2)
    highs = [b["h"] for b in spx[-252:] if _num(b.get("h")) is not None]
    if highs:
        out["spx_52w_high"] = round(max(highs), 2)
    vc = _closes(bars(CORE["vix"]))[-252:]
    if len(vc) >= 20:
        out["vix_52w_range"] = [round(min(vc), 2), round(max(vc), 2)]
    rsi = _rsi(_closes(hist.get(EXTRA_MACRO["ndx100"]) or hist.get(CORE["ndx"]) or []))
    if rsi is not None:
        out["ndx_rsi14"] = rsi
    out["asia"] = {f"{k}_change_pct": _chg_pct(hist.get(sym) or []) for k, sym in ASIA.items()}
    out["bar_dates"] = {k: ((hist.get(sym) or [{}])[-1].get("d")) for k, sym in CORE.items()}
    return out, sorted(set(missing))


def _et_session(dt_utc):
    t = dt_utc.astimezone(ET).time()
    if (t.hour, t.minute) < (9, 30):
        return "pre"
    if (t.hour, t.minute) < (16, 0):
        return "regular"
    return "post"


def quotes_from(daily, minute):
    """live_quotes.json: the newest 1-minute bar (pre/post-market included) against the last
    daily close strictly before that bar's ET date. changePct is a FRACTION, matching the
    shape build-holdings has always read."""
    out = {}
    for sym, mbars in minute.items():
        mbars = [b for b in mbars if _num(b.get("c")) is not None]
        if not mbars:
            continue
        last = mbars[-1]
        ts = datetime.fromisoformat(str(last["d"]).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        et_day = ts.astimezone(ET).date().isoformat()
        prior = [b for b in (daily.get(sym) or []) if str(b.get("d"))[:10] < et_day
                 and _num(b.get("c")) is not None]
        prev_close = prior[-1]["c"] if prior else None
        price = float(last["c"])
        out[sym] = {"price": round(price, 4),
                    "changePct": (round(price / prev_close - 1, 6) if prev_close else None),
                    "prev_close": prev_close, "session": _et_session(ts),
                    "as_of_utc": iso_utc(ts)}
    return out


def chain_from_records(spot, expiries):
    """{expiry: {"calls": [...], "puts": [...]}} -> the exact input shape cmd_maxpain reads."""
    data = {}
    for exp, legs in expiries.items():
        data[exp] = {side: [{"strike": _num(r.get("strike")),
                             "openInterest": int(_num(r.get("openInterest")) or 0),
                             "volume": int(_num(r.get("volume")) or 0)}
                            for r in (legs.get(side) or []) if _num(r.get("strike")) is not None]
                     for side in ("calls", "puts")}
    return {"underlyingPrice": spot, "data": data}


# ---------------------------------------------------------------------------------------------
# sources: live yfinance, or fixtures
# ---------------------------------------------------------------------------------------------
class FixtureSource:
    def __init__(self, d):
        self.d = d

    def _load(self, name):
        p = os.path.join(self.d, name)
        if not os.path.exists(p):
            raise FileNotFoundError(f"fixture {name} absent")
        with open(p) as fh:
            return json.load(fh)

    def history(self, symbols, period="1y"):
        h = self._load("history.json")
        return {s: h[s] for s in symbols if s in h}

    def minute(self, symbols):
        m = self._load("minute.json")
        return {s: m[s] for s in symbols if s in m}

    def option_chain(self, sym):
        return self._load("chains.json")[sym]

    def earnings(self, symbols):
        e = self._load("earnings.json")
        return {s: e[s] for s in symbols if s in e}


class YFinanceSource:
    def __init__(self, timeout=20):
        import yfinance  # lazy: only live runs need it
        self.yf = yfinance
        self.timeout = timeout

    @staticmethod
    def _frame_to_bars(df, with_time=False):
        bars = []
        if df is None or getattr(df, "empty", True):
            return bars
        for idx, row in df.iterrows():
            c = _num(row.get("Close"))
            if c is None:
                continue
            d = idx.isoformat() if with_time else str(idx.date() if hasattr(idx, "date") else idx)[:10]
            bars.append({"d": d, "o": _num(row.get("Open")), "h": _num(row.get("High")),
                         "l": _num(row.get("Low")), "c": c, "v": _num(row.get("Volume"))})
        return bars

    def _download(self, symbols, with_time=False, **kw):
        symbols = sorted(set(symbols))
        if not symbols:
            return {}
        df = self.yf.download(tickers=symbols, group_by="ticker", auto_adjust=False,
                              progress=False, threads=True, timeout=self.timeout, **kw)
        out = {}
        cols = getattr(df, "columns", None)
        multi = cols is not None and getattr(cols, "nlevels", 1) > 1
        for s in symbols:
            try:
                sub = df[s] if multi else df
            except KeyError:
                continue
            out[s] = self._frame_to_bars(sub.dropna(how="all"), with_time=with_time)
        return {s: b for s, b in out.items() if b}

    def history(self, symbols, period="1y"):
        return self._download(symbols, period=period, interval="1d")

    def minute(self, symbols):
        out = self._download(symbols, with_time=True, period="1d", interval="1m", prepost=True)
        for s, bars in out.items():
            for b in bars:
                dt = datetime.fromisoformat(b["d"])
                b["d"] = iso_utc(dt if dt.tzinfo else dt.replace(tzinfo=ET))
        return out

    def option_chain(self, sym):
        t = self.yf.Ticker(sym)
        spot = None
        try:
            spot = _num(t.fast_info.last_price)
        except Exception:  # noqa: BLE001
            pass
        if spot is None:
            h = self._download([sym], period="5d", interval="1d").get(sym) or []
            spot = h[-1]["c"] if h else None
        # Skip expiries inside MIN_EXPIRY_DAYS: same-day/next-day chains carry no settled open
        # interest, so max-pain on them is always null (seen live 2026-09-14).
        cutoff = (now_utc().astimezone(ET).date()).toordinal() + MIN_EXPIRY_DAYS
        usable = [e for e in (t.options or []) if datetime.fromisoformat(e).date().toordinal() >= cutoff]
        expiries = {}
        for exp in usable[:OPTION_EXPIRIES]:
            oc = t.option_chain(exp)
            expiries[exp] = {"calls": oc.calls.to_dict("records"), "puts": oc.puts.to_dict("records")}
        return chain_from_records(spot, expiries)

    def earnings(self, symbols):
        out = {}
        for s in symbols:
            try:
                cal = self.yf.Ticker(s).calendar
            except Exception:  # noqa: BLE001 -- one bad ticker must not sink the section
                continue
            dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
            dates = [d for d in (dates or []) if d]
            if dates:
                out[s] = {"date": str(dates[0])[:10], "confirmed": len(dates) == 1,
                          "source": "yfinance"}
        return out


# ---------------------------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------------------------
def _load_json(path, default=None):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _write_json(path, obj):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _tickers(base_dir, snapshot_json, extra):
    state = _load_json(os.path.join(base_dir, "state.json"), {}) or {}
    held = {h.get("ticker") for h in (state.get("holdings") or []) if h.get("ticker")}
    if snapshot_json:
        snap = _load_json(snapshot_json, {}) or {}
        held |= {h.get("investment_code") for h in (snap.get("holdings") or [])
                 if h.get("investment_code")}
    held |= {t.strip().upper() for t in (extra or "").split(",") if t.strip()}
    peers = {v.get("peer_etf") for v in (state.get("peer_map") or {}).values()
             if isinstance(v, dict) and v.get("peer_etf")}
    return sorted(held), sorted(peers | {"SMH"})


def run_all(args, source):
    started = time.monotonic()
    rd = args.run_dir
    os.makedirs(rd, exist_ok=True)
    sections = [s.strip() for s in (args.sections or "").split(",") if s.strip()] or (
        ["macro", "quotes", "bars"] + (["options", "earnings"] if args.mode == "deep" else []))
    report = {"ok": True, "mode": args.mode, "sections": {}, "fallback_needed": [], "errors": {},
              "written": [], "started_utc": iso_utc()}
    held, peers = _tickers(args.base_dir, args.snapshot_json, args.tickers)
    hist = {}

    def over_budget():
        return time.monotonic() - started > args.budget_seconds

    def section(name, fn):
        if name not in sections:
            report["sections"][name] = "skipped"
            return
        if over_budget():
            report["sections"][name] = "degraded"
            report["errors"][name] = f"time budget {args.budget_seconds}s exhausted"
            report["fallback_needed"].append(name)
            return
        try:
            fn()
            report["sections"][name] = "ok"
        except Exception as e:  # noqa: BLE001 -- every section degrades independently
            report["sections"][name] = "degraded"
            report["errors"][name] = f"{type(e).__name__}: {e}"[:300]
            report["fallback_needed"].append(name)

    def need_history():
        want = set(CORE.values()) | set(ASIA.values()) | set(EXTRA_MACRO.values())
        if "bars" in sections or "quotes" in sections:
            want |= set(held) | set(peers)
        missing = sorted(want - set(hist))
        if missing:
            hist.update(source.history(missing, period="1y"))

    def do_macro():
        need_history()
        mi, missing = macro_from_history(hist)
        if not {"vix", "spx", "smh"} <= set(mi):
            raise RuntimeError(f"core macro symbols missing from history: {missing}")
        path = os.path.join(rd, "market_inputs.json")
        merged = _load_json(path, {}) or {}
        merged.update(mi)
        merged.update({"source": "smith_fetch/yfinance", "fetched_at_utc": iso_utc(),
                       "missing_symbols": missing})
        _write_json(path, merged)
        report["written"].append("market_inputs.json")
        if missing:
            report["errors"]["macro_partial"] = f"no history for {missing}"
        if not os.environ.get("SMITH_NO_SHARED_CACHE") and os.path.exists(SHARED_CACHE):
            payload = {k: mi[k] for k in SHARED_FIELDS if k in mi}
            subprocess.run([sys.executable, SHARED_CACHE, "write", "--source-skill", "agent-smith",
                            "--data", json.dumps(payload)], capture_output=True, timeout=20)

    def do_bars():
        need_history()
        bars = {s: hist[s] for s in sorted(set(held) | set(peers)) if s in hist}
        absent = sorted((set(held) | set(peers)) - set(bars))
        _write_json(os.path.join(rd, "bars.json"), bars)
        report["written"].append("bars.json")
        if absent:
            report["errors"]["bars_partial"] = f"no daily bars for {absent}"

    def do_quotes():
        need_history()
        minute = source.minute(held)
        q = quotes_from(hist, minute)
        absent = sorted(set(held) - set(q))
        _write_json(os.path.join(rd, "live_quotes.json"), q)
        report["written"].append("live_quotes.json")
        if absent:
            report["errors"]["quotes_partial"] = f"no live quote for {absent}"
        if held and not q:
            raise RuntimeError("no quotes at all")

    def do_options():
        summary = {}
        for sym in OPTIONS_SYMBOLS:
            chain = source.option_chain(sym)
            p = os.path.join(rd, f"chain_{sym}.json")
            _write_json(p, chain)
            proc = subprocess.run([sys.executable, os.path.join(HERE, "smith_math.py"), "maxpain",
                                   "--chain", p, "--symbol", sym], capture_output=True, text=True,
                                  timeout=60)
            summary[sym] = json.loads(proc.stdout) if proc.stdout.strip() else {"error": proc.stderr[-200:]}
        summary["as_of_utc"] = iso_utc()
        _write_json(os.path.join(rd, "compute_options.json"), summary)
        report["written"].append("compute_options.json")

    def do_earnings():
        cal = source.earnings(held)
        _write_json(os.path.join(rd, "earnings_calendar.json"), cal)
        report["written"].append("earnings_calendar.json")

    section("macro", do_macro)
    section("bars", do_bars)
    section("quotes", do_quotes)
    section("options", do_options)
    section("earnings", do_earnings)
    report["ok"] = not report["fallback_needed"]
    report["elapsed_s"] = round(time.monotonic() - started, 1)
    _write_json(os.path.join(rd, "fetch_report.json"), report)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("all", help="fetch every section this mode needs into the run dir")
    sp.add_argument("--base-dir", default=os.environ.get("SMITH_BASE_DIR", "/Users/yb/Claude/AgentSmith"))
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--mode", choices=("quick", "deep"), default="quick")
    sp.add_argument("--sections", default=None, help="comma-separated subset: macro,quotes,bars,options,earnings")
    sp.add_argument("--snapshot-json", default=None, help="raw networth_holdings dump (adds new tickers)")
    sp.add_argument("--tickers", default=None, help="extra comma-separated tickers")
    sp.add_argument("--fixtures", default=None, help="offline: read normalised fixtures from this dir")
    sp.add_argument("--budget-seconds", type=float, default=120.0)
    args = ap.parse_args()

    if args.fixtures:
        source = FixtureSource(args.fixtures)
    elif os.environ.get("SMITH_FETCH_OFFLINE"):
        source = None
    else:
        try:
            source = YFinanceSource()
        except ImportError as e:
            source, import_error = None, str(e)
    if source is None:
        sections = [s for s in (args.sections or "macro,quotes,bars,options,earnings").split(",") if s]
        report = {"ok": False, "mode": args.mode, "sections": {s: "degraded" for s in sections},
                  "fallback_needed": sections,
                  "errors": {"source": ("SMITH_FETCH_OFFLINE set" if os.environ.get("SMITH_FETCH_OFFLINE")
                                        else f"yfinance unavailable: {locals().get('import_error')}")},
                  "written": []}
        os.makedirs(args.run_dir, exist_ok=True)
        _write_json(os.path.join(args.run_dir, "fetch_report.json"), report)
        print(json.dumps(report))
        return
    print(json.dumps(run_all(args, source)))


if __name__ == "__main__":
    main()

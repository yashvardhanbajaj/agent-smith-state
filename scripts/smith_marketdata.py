"""Deterministic market-data math (added 2026-09-14). Stdlib only, no network.

  indicators     ATR20 %, RSI14, ret_5d, 1-month relative strength vs SMH and vs a peer ETF,
                 52-week range and beta vs SMH, from the daily bars smith_fetch.py wrote. Merged
                 into state.data_cache in the SAME shapes the triggers/buckets/derisk stages
                 already read -- previously an LLM (smith-signals, smith-book) did this arithmetic.
  normalize-bars converts saved yfinance-MCP history output (the fallback path) to bars.json, so
                 both paths feed one computation.
  session-gate   market_session (DST, holidays, early close) and GATE v2 -- rules that lived in
                 SKILL.md prose and were evaluated by eye every run.

Indicator conventions deliberately match the caches the desk has been calibrated on (e.g.
smith-signals' k=2.3 rel_sigma scaling assumed simple-mean ATR20), so no threshold moves:
ATR20 = simple mean of the last 20 true ranges / last close; RSI14 = Wilder; 1-month = 21 sessions.
"""
import math
import os
from datetime import time as dtime

from smith_core import *  # noqa: F401,F403

BENCHMARK = "SMH"
BETA_MIN_OBS, BETA_MAX_OBS = 60, 252


# ---------------------------------------------------------------------------------------------
# bars
# ---------------------------------------------------------------------------------------------
_FIELD_NAMES = {"d": ("d", "date", "Date", "datetime", "Datetime", "timestamp", "time"),
                "o": ("o", "open", "Open"), "h": ("h", "high", "High"), "l": ("l", "low", "Low"),
                "c": ("c", "close", "Close"), "v": ("v", "volume", "Volume")}


def _num(x):
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _norm_record(r):
    if not isinstance(r, dict):
        return None
    out = {}
    for k, names in _FIELD_NAMES.items():
        for n in names:
            if r.get(n) is not None:
                out[k] = r[n]
                break
    if "d" not in out or _num(out.get("c")) is None:
        return None
    out["d"] = str(out["d"])[:10]
    for k in "ohlcv":
        if k in out:
            out[k] = _num(out[k])
    return out


def normalize_bars(payload):
    """Accepts every history shape the MCP path has produced: {SYM: [records]},
    {SYM: {"data"|"history": [...]}}, [{"symbol": S, "data": [...]}, ...],
    {"symbol": S, "data": [...]}, or flat records carrying a symbol field."""
    result = {}

    def add(sym, recs):
        if not sym or not isinstance(recs, list):
            return
        rows = [n for n in (_norm_record(r) for r in recs) if n]
        merged = {b["d"]: b for b in result.get(str(sym).upper(), [])}
        merged.update({b["d"]: b for b in rows})
        if merged:
            result[str(sym).upper()] = [merged[d] for d in sorted(merged)]

    def walk(obj):
        if isinstance(obj, list):
            if obj and all(isinstance(r, dict) and (r.get("symbol") or r.get("ticker")) and
                           not isinstance(r.get("data") or r.get("history"), list) for r in obj):
                by = {}
                for r in obj:
                    by.setdefault(r.get("symbol") or r.get("ticker"), []).append(r)
                for s, recs in by.items():
                    add(s, recs)
            else:
                for item in obj:
                    walk(item)
        elif isinstance(obj, dict):
            recs = obj.get("data") or obj.get("history") or obj.get("bars")
            sym = obj.get("symbol") or obj.get("ticker")
            if sym and isinstance(recs, list):
                add(sym, recs)
                return
            for k, v in obj.items():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    add(k, v)
                elif isinstance(v, dict) and isinstance(v.get("data") or v.get("history"), list):
                    add(k, v.get("data") or v.get("history"))
    walk(payload)
    return result


def cmd_normalize_bars(args):
    out = {}
    for path in args.mcp_files:
        for sym, bars in normalize_bars(load_json(path, default={})).items():
            merged = {b["d"]: b for b in out.get(sym, [])}
            merged.update({b["d"]: b for b in bars})
            out[sym] = [merged[d] for d in sorted(merged)]
    dest = args.out or os.path.join(args.run_dir, "bars.json")
    existing = load_json(dest, default={}) or {}
    existing.update(out)
    atomic_write_json(dest, existing)
    emit({"written": dest, "symbols": len(out), "bars": {s: len(b) for s, b in out.items()}})


# ---------------------------------------------------------------------------------------------
# indicators
# ---------------------------------------------------------------------------------------------
def atr_pct(bars, n=20):
    rows = [b for b in bars if None not in (_num(b.get("h")), _num(b.get("l")), _num(b.get("c")))]
    if len(rows) < n + 1:
        return None
    trs = [max(cur["h"] - cur["l"], abs(cur["h"] - prev["c"]), abs(cur["l"] - prev["c"]))
           for prev, cur in zip(rows[:-1], rows[1:])]
    last = rows[-1]["c"]
    return round(sum(trs[-n:]) / n / last * 100, 2) if last else None


def rsi_wilder(closes, n=14):
    if len(closes) < n + 1:
        return None
    gains = [max(0.0, closes[i] - closes[i - 1]) for i in range(1, len(closes))]
    losses = [max(0.0, closes[i - 1] - closes[i]) for i in range(1, len(closes))]
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):
        ag, al = (ag * (n - 1) + g) / n, (al * (n - 1) + l) / n
    return 100.0 if al == 0 else round(100 - 100 / (1 + ag / al), 1)


def pct_return(closes, k):
    return (round((closes[-1] / closes[-1 - k] - 1) * 100, 2)
            if len(closes) > k and closes[-1 - k] else None)


ROLLING_WINDOWS = (("1m", 21), ("3m", 63), ("6m", 126), ("12m", 250))
ROLLING_MIN_COVERAGE_PCT = 80.0


def rolling_constant_mix(bars, weights, bench=BENCHMARK, windows=ROLLING_WINDOWS):
    """Trailing-window return of TODAY's holdings at TODAY's weights vs the benchmark.

    Flow-free by construction: it prices the book you hold now through each window, so deposits,
    wallet cash and trades cannot leak in (the ledger's `external_flow_usd` has never been
    recorded, so a realized return would mix deposits with returns). It is NOT your realized
    return, and callers must label it so. A window is refused, not guessed, when fewer than
    ROLLING_MIN_COVERAGE_PCT of the weight has a close on both end dates."""
    b = [x for x in (bars.get(bench) or []) if _num(x.get("c"))]
    if len(b) < 2:
        return {key: {"excess_pp": None, "sessions": k, "reason": f"no {bench} bars"} for key, k in windows}
    dates = [str(x["d"])[:10] for x in b]
    bc = {str(x["d"])[:10]: float(x["c"]) for x in b}
    closes = {t: {str(x["d"])[:10]: float(x["c"]) for x in rows if _num(x.get("c"))}
              for t, rows in bars.items()}
    live = {t: float(w) for t, w in weights.items() if _num(w) and w > 0}
    total = sum(live.values())
    out = {}
    for key, k in windows:
        if len(dates) <= k:
            out[key] = {"excess_pp": None, "sessions": k,
                        "reason": f"only {len(dates)} {bench} sessions, need {k + 1}"}
            continue
        d0, d1 = dates[-1 - k], dates[-1]
        acc = cov = 0.0
        missing = []
        for t, w in live.items():
            c = closes.get(t) or {}
            if c.get(d0) and c.get(d1):
                acc += w * (c[d1] / c[d0] - 1)
                cov += w
            else:
                missing.append(t)
        cov_pct = round(100.0 * cov / total, 1) if total else 0.0
        smh = round((bc[d1] / bc[d0] - 1) * 100, 2)
        row = {"from": d0, "to": d1, "sessions": k, "coverage_pct": cov_pct,
               "uncovered": sorted(missing), "smh_pct": smh}
        if not cov or cov_pct < ROLLING_MIN_COVERAGE_PCT:
            row.update({"excess_pp": None, "book_pct": None,
                        "reason": f"coverage {cov_pct}% of weight is below {ROLLING_MIN_COVERAGE_PCT:.0f}%"})
        else:
            book = round(100.0 * acc / cov, 2)
            row.update({"book_pct": book, "excess_pp": round(book - smh, 2)})
        out[key] = row
    return out


def realized_twr(rows, d0, d1, bench_closes):
    """Time-weighted realized return from ledger rows dated d0..d1 (value + wallet, net of
    `external_flow_usd`), against the benchmark over the same dates. Refused unless every row after
    the first records its external flow and every row is trusted: an unrecorded deposit would
    read as performance."""
    sel = [r for r in rows if d0 <= str(r.get("ts") or "")[:10] <= d1]
    if len(sel) < 2:
        return {"realized_excess_pp": None, "realized_reason": "fewer than 2 ledger rows in the window"}
    if any((r.get("value_trust") or "ok") != "ok" for r in sel):
        return {"realized_excess_pp": None, "realized_reason": "a ledger row in the window is not value_trust=ok"}
    if any(str(r.get("external_flow_usd") or "").strip() == "" for r in sel[1:]):
        return {"realized_excess_pp": None,
                "realized_reason": "external_flow_usd is not recorded on every ledger row in the window, "
                                   "so a deposit would read as return"}

    def total(r):
        return float(r.get("value_usd") or 0) + float(r.get("wallet_usd") or 0)

    growth = 1.0
    for prev, cur in zip(sel, sel[1:]):
        if total(prev) <= 0:
            return {"realized_excess_pp": None, "realized_reason": "zero book value in the window"}
        growth *= (total(cur) - float(cur.get("external_flow_usd"))) / total(prev)
    bdates = sorted(bench_closes)

    def close_on(d):
        prior = [x for x in bdates if x <= d]
        return bench_closes[prior[-1]] if prior else None

    s0, s1 = close_on(str(sel[0]["ts"])[:10]), close_on(str(sel[-1]["ts"])[:10])
    book = round((growth - 1) * 100, 2)
    if not (s0 and s1):
        return {"realized_book_pct": book, "realized_excess_pp": None,
                "realized_reason": "no benchmark close at the window's ledger dates"}
    smh = round((s1 / s0 - 1) * 100, 2)
    return {"realized_book_pct": book, "realized_smh_pct": smh,
            "realized_excess_pp": round(book - smh, 2), "realized_rows": len(sel)}


def beta_vs(bars, bench):
    b_close = {x["d"]: x["c"] for x in bench if _num(x.get("c"))}
    s = [(x["d"], x["c"]) for x in bars if _num(x.get("c")) and x["d"] in b_close]
    rs, rb = [], []
    for (d0, c0), (d1, c1) in zip(s[:-1], s[1:]):
        if c0 and b_close[d0]:
            rs.append(c1 / c0 - 1)
            rb.append(b_close[d1] / b_close[d0] - 1)
    rs, rb = rs[-BETA_MAX_OBS:], rb[-BETA_MAX_OBS:]
    if len(rs) < BETA_MIN_OBS:
        return None, len(rs)
    mb, ms = sum(rb) / len(rb), sum(rs) / len(rs)
    var = sum((x - mb) ** 2 for x in rb)
    if not var:
        return None, len(rs)
    cov = sum((x - mb) * (y - ms) for x, y in zip(rb, rs))
    return round(cov / var, 3), len(rs)


def compute_indicators(bars, peer_map=None, benchmark=BENCHMARK):
    bench = bars.get(benchmark) or []
    bc = [b["c"] for b in bench if _num(b.get("c"))]
    bench_1m, bench_5d = pct_return(bc, 21), pct_return(bc, 5)
    out = {"atr20_pct": {}, "rsi14": {}, "ret_5d_pct": {}, "ret_1m_abs_pct": {}, "rel_1m_pp": {},
           "rel_1m_peer": {}, "wk52": {}, "beta": {}, "beta_obs": {}, "skipped": {},
           "benchmark": benchmark, "benchmark_return_1m_pct": bench_1m,
           "benchmark_return_5d_pct": bench_5d}
    peer_ret = {s: pct_return([b["c"] for b in v if _num(b.get("c"))], 21) for s, v in bars.items()}
    last_dates = []
    for sym, rows in bars.items():
        closes = [b["c"] for b in rows if _num(b.get("c"))]
        if len(closes) < 22:
            out["skipped"][sym] = f"{len(closes)} closes (<22)"
            continue
        last_dates.append(rows[-1]["d"])
        out["atr20_pct"][sym] = atr_pct(rows)
        out["rsi14"][sym] = rsi_wilder(closes)
        out["ret_5d_pct"][sym] = pct_return(closes, 5)
        r1m = pct_return(closes, 21)
        out["ret_1m_abs_pct"][sym] = r1m
        if r1m is not None and bench_1m is not None:
            out["rel_1m_pp"][sym] = round(r1m - bench_1m, 2)
        peer = ((peer_map or {}).get(sym) or {}).get("peer_etf")
        if peer and peer != benchmark and peer_ret.get(peer) is not None and r1m is not None:
            out["rel_1m_peer"][sym] = {"rel_pp": round(r1m - peer_ret[peer], 2), "peer_etf": peer}
        window = rows[-252:]
        lows = [b["l"] for b in window if _num(b.get("l"))]
        highs = [b["h"] for b in window if _num(b.get("h"))]
        if lows and highs:
            out["wk52"][sym] = {"low": round(min(lows), 4), "high": round(max(highs), 4)}
        if sym != benchmark and bench:
            b, n = beta_vs(rows, bench)
            out["beta_obs"][sym] = n
            if b is not None:
                out["beta"][sym] = b
    out["as_of"] = max(last_dates) if last_dates else None
    out["tickers"] = sorted(out["atr20_pct"])
    return out


def merge_indicators_into_cache(dc, ind, earnings=None):
    """Per-ticker updates into the existing cache shapes. Tickers without bars keep their entry."""
    as_of = ind["as_of"]
    src = "smith_math.py indicators (script) from smith_fetch daily bars"
    clean = lambda m: {k: v for k, v in m.items() if v is not None}  # noqa: E731
    c = dc.setdefault("atr20", {})
    c.setdefault("values_pct", {}).update(clean(ind["atr20_pct"]))
    c.update({"as_of": as_of, "source": src, "method": "simple mean of the last 20 true ranges / last close"})
    c = dc.setdefault("rsi14", {})
    c.setdefault("values", {}).update(clean(ind["rsi14"]))
    c.update({"as_of": as_of, "period": 14, "method": "Wilder RSI14 on daily closes (script)"})
    c = dc.setdefault("rel_strength_1m", {})
    c.setdefault("values_pp", {}).update(clean(ind["rel_1m_pp"]))
    c.setdefault("values_abs_pct", {}).update(clean(ind["ret_1m_abs_pct"]))
    c.update({"as_of": as_of, "benchmark": ind["benchmark"], "window": "21 sessions",
              "benchmark_return_1m_pct": ind["benchmark_return_1m_pct"]})
    if ind["rel_1m_peer"]:
        c = dc.setdefault("rel_strength_1m_peer", {})
        c.setdefault("values_pp", {}).update({k: v["rel_pp"] for k, v in ind["rel_1m_peer"].items()})
        c.setdefault("peer_etf", {}).update({k: v["peer_etf"] for k, v in ind["rel_1m_peer"].items()})
        c["as_of"] = as_of
    c = dc.setdefault("ret_5d", {})
    c.setdefault("values_pct", {}).update(clean(ind["ret_5d_pct"]))
    c.update({"as_of": as_of, "benchmark": ind["benchmark"],
              "benchmark_return_pct": ind["benchmark_return_5d_pct"]})
    dc.setdefault("wk52", {}).update(ind["wk52"])
    betas = dc.setdefault("betas", {})
    for t, b in ind["beta"].items():
        betas[t] = {"value": b, "as_of": as_of, "benchmark": ind["benchmark"],
                    "obs": ind["beta_obs"].get(t), "source": "script"}
    if ind["beta"]:
        betas["as_of"] = as_of
    confirmed_kept = []
    for t, e in (earnings or {}).items():
        cur = (dc.setdefault("earnings_calendar", {})).get(t)
        if isinstance(cur, dict) and cur.get("confirmed") and not e.get("confirmed") \
                and str(cur.get("date", "")) >= str(as_of or ""):
            confirmed_kept.append(t)          # a fetch never overwrites a confirmed, upcoming date
            continue
        dc["earnings_calendar"][t] = e
    return {"confirmed_earnings_kept": confirmed_kept}


def cmd_indicators(args):
    path = args.bars or os.path.join(args.run_dir, "bars.json")
    if not os.path.exists(path):
        emit({"skipped": True, "tickers": None,
              "reason": "no bars.json in the run dir (smith_fetch did not run or bars degraded) -- "
                        "caches left as they were; freshness will say how old they are"})
        return
    bars = normalize_bars(load_json(path, default={}))
    base = args.base_dir
    earnings = load_json(os.path.join(args.run_dir, "earnings_calendar.json"), default=None)
    with locked_json(os.path.join(base, "state.json"), default={}) as box:
        state = box["obj"]
        ind = compute_indicators(bars, state.get("peer_map") or {})
        # Market facts, not run decisions: written straight to state.json (under the write lock)
        # so the later pipeline stages in this same run -- book, risk, buckets, triggers, ladder --
        # read them. A run that dies afterwards leaves only a fresher, still-true cache behind.
        extra = merge_indicators_into_cache(state.setdefault("data_cache", {}), ind, earnings)
    ind.update(extra)
    emit(ind)


# ---------------------------------------------------------------------------------------------
# session + GATE v2
# ---------------------------------------------------------------------------------------------
def market_session(now, holidays):
    et = now.astimezone(ET)
    if et.weekday() >= 5:
        return "closed", "weekend"
    hol = {h.get("date"): h for h in (holidays or []) if isinstance(h, dict)}
    h = hol.get(et.date().isoformat())
    if h and not h.get("early_close"):
        return "closed", f"holiday: {h.get('name')}"
    close = dtime(13, 0) if h and h.get("early_close") else dtime(16, 0)
    t = et.time()
    if t < dtime(9, 30):
        return "pre-open", f"{t.strftime('%H:%M')} ET"
    if t < close:
        return "intraday", f"{t.strftime('%H:%M')} ET" + (" (early close 13:00)" if close.hour == 13 else "")
    return "post-close", f"{t.strftime('%H:%M')} ET"


def cluster_moves(rows, sector_map):
    acc = {}
    for r in rows or []:
        cl, w, chg = (sector_map or {}).get(r.get("ticker")), _num(r.get("weight_pct")), _num(r.get("day_chg_pct"))
        if cl and w and chg is not None:
            a = acc.setdefault(cl, [0.0, 0.0])
            a[0] += w * chg
            a[1] += w
    return {cl: round(s / w, 2) for cl, (s, w) in acc.items() if w}


def gate_v2(mi, clusters):
    """GATE v2 exactly as SKILL.md states it (revised 2026-07-28)."""
    asia = mi.get("asia") or {}
    asia_vals = [v for v in (asia.get("kospi_change_pct", mi.get("kospi_change_pct")),
                             asia.get("taiex_change_pct", mi.get("taiex_change_pct")),
                             asia.get("nikkei_change_pct", mi.get("nikkei_change_pct")))
                 if _num(v) is not None]
    vix, es, nq, smh = (_num(mi.get(k)) for k in ("vix_change_pct", "es_f_change_pct",
                                                  "nq_f_change_pct", "smh_change_pct"))
    worst_asia = min(asia_vals) if asia_vals else None
    worst_cluster = min(clusters.values()) if clusters else None
    esc = []
    if None not in (vix, es, nq) and vix >= 5 and es <= -0.5 and nq <= -0.5:
        esc.append(f"VIX {vix:+.1f}% with ES {es:+.2f}% / NQ {nq:+.2f}%")
    if worst_asia is not None and worst_asia <= -3:
        esc.append(f"worst Asia index {worst_asia:+.2f}%")
    if smh is not None and smh <= -2.5:
        esc.append(f"SMH {smh:+.2f}%")
    if worst_cluster is not None and worst_cluster <= -4:
        esc.append(f"cluster {min(clusters, key=clusters.get)} {worst_cluster:+.2f}%")
    if esc:
        return "ESCALATING", "; ".join(esc)
    missing = [k for k, v in (("vix_change_pct", vix), ("es/nq", es if nq is not None else None),
                              ("smh_change_pct", smh)) if v is None]
    if missing:
        return "AMBIGUOUS", f"inputs missing: {', '.join(missing)}"
    if vix <= 2 and max(es, nq) >= 0 and (worst_asia is None or worst_asia > -2) and smh >= -1:
        return "STABILIZING", (f"VIX {vix:+.1f}%, ES/NQ best {max(es, nq):+.2f}%, SMH {smh:+.2f}%"
                               + (f", worst Asia {worst_asia:+.2f}%" if worst_asia is not None else ""))
    return "AMBIGUOUS", f"VIX {vix:+.1f}%, ES {es:+.2f}%, NQ {nq:+.2f}%, SMH {smh:+.2f}%"


def cmd_session_gate(args):
    now = parse_any(args.now) if args.now else now_utc()
    state = load_json(os.path.join(args.base_dir, "state.json"), default={}) or {}
    mi = load_json(os.path.join(args.run_dir, "market_inputs.json"), default={}) or {}
    hpath = os.path.join(args.run_dir, "holdings.json")
    holdings = load_json(hpath, default=None)
    session, why = market_session(now, state.get("us_market_holidays"))
    clusters = cluster_moves((holdings or {}).get("holdings_inr"), state.get("sector_map"))
    gate, reason = gate_v2(mi, clusters)
    out = {"now_utc": iso_utc(now), "market_session": session, "session_reason": why,
           "gate_classification": gate, "gate_reason": reason, "cluster_moves_pct": clusters,
           "market_inputs_present": bool(mi)}
    atomic_write_json(os.path.join(args.run_dir, "compute_session.json"), out)
    if args.write_holdings and isinstance(holdings, dict):
        holdings.update({"market_session": session, "gate_classification": gate,
                         "gate_reason": reason})
        atomic_write_json(hpath, holdings)
        out["holdings_updated"] = True
    emit(out)

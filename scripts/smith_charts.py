#!/usr/bin/env python3
"""
Agent Smith chart layer -- deterministic inline-SVG generation from state files.

Same principle as smith_math.py: the LLM does not hand-draw charts any more than it
hand-computes weights. This script reads ledger.csv / policy.json / state.json and
emits self-contained SVG (no external libs -- the artifact CSP blocks CDNs).

Palette is the validated dataviz reference instance. Categorical roles used here
(blue #2a78d6 equity, yellow #eda100 cash, red #d03b3b critical) passed the six
checks in both light and dark; the light-mode yellow sits below 3:1 on surface, so
the relief rule applies and the cash series is ALWAYS direct-labeled.

Usage:
  smith_charts.py all       --base-dir DIR            # every chart, JSON keyed by name
  smith_charts.py bookvalue --base-dir DIR
  smith_charts.py relative  --base-dir DIR
  smith_charts.py drawdown  --base-dir DIR
  smith_charts.py weights   --base-dir DIR
  smith_charts.py treemap   --base-dir DIR
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smith_risk

DEFAULT_BASE = "/Users/yb/Claude/AgentSmith"

# Cluster name (policy.json's cluster_targets keys) -> CSS custom property.
# Colors for the 6 clusters with historical nonzero weight are carried from the
# archived 2026-07-28 reference render (visually reasonable, already seen live);
# the 2 currently-zero-weight clusters (diversified/software) and ALL 8 dark-mode
# variants are new and have NOT been run through the dataviz skill's six-check
# contrast validation yet -- flagged here rather than silently shipped as final.
CLUSTER_COLOR_VAR = {
    "AI Semis/Fabs": "--cl-semis",
    "AI Memory/Storage": "--cl-memory",
    "AI Networking/Optics": "--cl-networking",
    "AI Power/Cooling/DC Infra": "--cl-power",
    "Compute/Hyperscaler OEM": "--cl-compute-oem",
    "Compute/Hyperscaler": "--cl-hyperscaler",
    "Diversified/Regional ETF": "--cl-diversified",
    "Enterprise Software": "--cl-software",
}

# --- validated palette roles (see module docstring) -------------------------
# Emitted as CSS vars so light/dark swap in one place and marks reference roles.
PALETTE_CSS = """
.viz{ --surface-1:#ffffff; --grid:#e8eaea; --axis:#c8cdce;
      --ink-1:#14181c; --ink-2:#4a5157; --ink-3:#7c8389;
      --equity:#2a78d6; --cash:#eda100; --pos:#2a78d6; --neg:#d03b3b;
      --good:#0ca30c; --warning:#fab219; --serious:#ec835a; --critical:#d03b3b;
      --muted:#b6bbbd;
      --cl-semis:#5b8fa8; --cl-memory:#b8862b; --cl-networking:#7a6ca8;
      --cl-power:#3f8f6b; --cl-compute-oem:#a86f5b; --cl-hyperscaler:#4a6fa5;
      --cl-diversified:#6b7c8f; --cl-software:#8a8a4a; }
@media (prefers-color-scheme: dark){ :root:where(:not([data-theme="light"])) .viz{
      --surface-1:#171a1d; --grid:#262a2e; --axis:#3a4045;
      --ink-1:#e8eaec; --ink-2:#a7adb2; --ink-3:#71787d;
      --equity:#3987e5; --cash:#c98500; --pos:#3987e5; --neg:#d03b3b;
      --muted:#4d5457;
      --cl-semis:#7fb0c9; --cl-memory:#d9a34f; --cl-networking:#9a8cc8;
      --cl-power:#5fb08b; --cl-compute-oem:#c98f7b; --cl-hyperscaler:#6a8fc5;
      --cl-diversified:#8b9cad; --cl-software:#aaaa6a; } }
:root[data-theme="dark"] .viz{
      --surface-1:#171a1d; --grid:#262a2e; --axis:#3a4045;
      --ink-1:#e8eaec; --ink-2:#a7adb2; --ink-3:#71787d;
      --equity:#3987e5; --cash:#c98500; --pos:#3987e5; --neg:#d03b3b;
      --muted:#4d5457;
      --cl-semis:#7fb0c9; --cl-memory:#d9a34f; --cl-networking:#9a8cc8;
      --cl-power:#5fb08b; --cl-compute-oem:#c98f7b; --cl-hyperscaler:#6a8fc5;
      --cl-diversified:#8b9cad; --cl-software:#aaaa6a; }
.viz text{ font-family:ui-monospace,"SF Mono",Consolas,monospace; }
.viz .lbl{ font-family:-apple-system,"Segoe UI",Inter,Roboto,sans-serif; }
.viz .mark{ transition:opacity .12s; }
.viz .mark:hover{ opacity:.72; }
.viz-legend{ display:flex; gap:16px; flex-wrap:wrap; align-items:center;
      font-size:12px; color:var(--ink-2); margin:2px 0 10px;
      font-family:-apple-system,"Segoe UI",Inter,Roboto,sans-serif; }
.viz-legend i{ width:10px; height:10px; border-radius:2px; display:inline-block;
      margin-right:6px; vertical-align:-1px; }
.viz-note{ font-size:11.5px; color:var(--ink-3); line-height:1.5; margin-top:8px;
      font-family:-apple-system,"Segoe UI",Inter,Roboto,sans-serif; }
"""


def load_ledger(base):
    p = os.path.join(base, "ledger.csv")
    if not os.path.exists(p):
        return []
    rows = []
    for r in csv.DictReader(open(p)):
        def f(k):
            v = (r.get(k) or "").strip()
            try:
                return float(v)
            except ValueError:
                return None
        rows.append({
            "ts": r["ts"], "date": r["ts"][:10], "hm": r["ts"][11:16],
            "mode": r.get("mode", ""),
            "equity": f("value_usd") or 0.0, "cash": f("wallet_usd") or 0.0,
            "total": (f("value_usd") or 0.0) + (f("wallet_usd") or 0.0),
            "smh": f("smh"),
            "trust": (r.get("value_trust") or "ok").strip() or "ok",
            "ext_flow": f("external_flow_usd"),
        })
    return rows


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def nice_ceil(x):
    """Round an axis max up to a readable step."""
    if x <= 0:
        return 1.0
    import math
    mag = 10 ** math.floor(math.log10(x))
    for m in (1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10):
        if x <= m * mag:
            return m * mag
    return 10 * mag


# ---------------------------------------------------------------------------
# 1. BOOK VALUE -- stacked area, equity + cash. One axis (dollars). The stack
#    shows total book AND the cash proportion without a second scale, which is
#    why it beats a dual-axis value/cash% chart.
# ---------------------------------------------------------------------------
def load_stops_by_date(base):
    """date -> [ticker,...] for every scored stop-loss fill, from stops_analysis.json (see
    smith_math.py cmd_stops). Added 2026-08-06 so the book-value chart can mark the session a
    stop cascade fired -- seeing several stops cluster on one candle is worth more than reading
    it off a table."""
    p = os.path.join(base, "stops_analysis.json")
    if not os.path.exists(p):
        return {}
    try:
        d = json.load(open(p))
    except (json.JSONDecodeError, OSError):
        return {}
    by_date = {}
    for r in d.get("stops", []):
        if r.get("date"):
            by_date.setdefault(r["date"], []).append(r["ticker"])
    return by_date


def chart_bookvalue(base):
    rows = load_ledger(base)
    if len(rows) < 2:
        return {"svg": "", "note": "ledger has <2 rows -- no time series yet"}
    stops_by_date = load_stops_by_date(base)

    W, H = 720, 260
    ML, MR, MT, MB = 62, 76, 16, 34
    pw, ph = W - ML - MR, H - MT - MB
    n = len(rows)
    ymax = nice_ceil(max(r["total"] for r in rows) * 1.08)

    def X(i):
        return ML + (pw * i / (n - 1))

    def Y(v):
        return MT + ph - (ph * v / ymax)

    eq = [(X(i), Y(r["equity"])) for i, r in enumerate(rows)]
    tot = [(X(i), Y(r["total"])) for i, r in enumerate(rows)]
    base_y = Y(0)

    def path(pts, close_to=None):
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        if close_to is not None:
            d += f" L{pts[-1][0]:.1f},{close_to:.1f} L{pts[0][0]:.1f},{close_to:.1f} Z"
        return d

    # cash band = between equity line and total line
    cash_area = ("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in tot)
                 + " L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in reversed(eq)) + " Z")

    s = [f'<svg class="viz-svg" viewBox="0 0 {W} {H}" width="100%" '
         f'preserveAspectRatio="xMidYMid meet" role="img" '
         f'aria-label="Total book value over time, split into equity and cash">']

    # recessive gridlines + y axis
    for g in range(5):
        v = ymax * g / 4
        y = Y(v)
        s.append(f'<line x1="{ML}" y1="{y:.1f}" x2="{ML+pw}" y2="{y:.1f}" '
                 f'stroke="var(--grid)" stroke-width="1"/>')
        s.append(f'<text x="{ML-8}" y="{y+3.5:.1f}" text-anchor="end" font-size="10" '
                 f'fill="var(--ink-3)">${v/1000:.0f}k</text>')

    s.append(f'<path d="{path(eq, base_y)}" fill="var(--equity)" fill-opacity="0.88"/>')
    # 2px surface gap between the two fills (skill: spacer between stacked segments)
    s.append(f'<path d="{path(eq)}" fill="none" stroke="var(--surface-1)" stroke-width="2"/>')
    s.append(f'<path d="{cash_area}" fill="var(--cash)" fill-opacity="0.9"/>')
    s.append(f'<path d="{path(tot)}" fill="none" stroke="var(--ink-1)" stroke-width="2" '
             f'stroke-opacity="0.55"/>')

    # suspect-data markers -- honesty about which points are corrupt
    for i, r in enumerate(rows):
        if r["trust"] != "ok":
            x, y = X(i), Y(r["total"])
            s.append(f'<line x1="{x:.1f}" y1="{MT}" x2="{x:.1f}" y2="{MT+ph}" '
                     f'stroke="var(--neg)" stroke-width="1" stroke-dasharray="2 3" '
                     f'stroke-opacity="0.65"/>')
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="var(--surface-1)" '
                     f'stroke="var(--neg)" stroke-width="2"><title>'
                     f'{esc(r["date"])} ${r["total"]:,.0f} - EXCLUDED ({esc(r["trust"])}: '
                     f'price-feed gap, not a real value)</title></circle>')

    # stop-loss markers -- one small triangle above the plot per ledger date that had scored
    # stop-loss fills that day (added 2026-08-06). Triangle count is capped visually at 3 marks
    # (no benefit to drawing 7 overlapping glyphs); the tooltip always lists every ticker.
    for i, r in enumerate(rows):
        tks = stops_by_date.get(r["date"])
        if not tks:
            continue
        x = X(i)
        n_shown = min(len(tks), 3)
        for k in range(n_shown):
            dx = (k - (n_shown - 1) / 2) * 6
            s.append(f'<path d="M{x+dx:.1f},{MT-2} l4,7 l-8,0 Z" fill="var(--neg)" '
                     f'fill-opacity="0.85"/>')
        s.append(f'<rect class="mark" x="{x-10:.1f}" y="{MT-10}" width="20" height="12" '
                 f'fill="transparent"><title>{esc(r["date"])}: {len(tks)} stop-loss fill'
                 f'{"s" if len(tks)!=1 else ""} ({esc(", ".join(sorted(set(tks))))})</title></rect>')

    # hover targets, every point
    for i, r in enumerate(rows):
        x = X(i)
        cpct = r["cash"] / r["total"] * 100 if r["total"] else 0
        s.append(f'<rect class="mark" x="{x-8:.1f}" y="{MT}" width="16" height="{ph}" '
                 f'fill="transparent"><title>{esc(r["date"])} {esc(r["hm"])}  '
                 f'total ${r["total"]:,.0f}  |  equity ${r["equity"]:,.0f}  |  '
                 f'cash ${r["cash"]:,.0f} ({cpct:.1f}%)</title></rect>')

    # direct labels -- REQUIRED relief for the sub-3:1 light-mode cash yellow
    last = rows[-1]
    ly_e = Y(last["equity"] / 2)
    ly_c = Y(last["equity"] + last["cash"] / 2)
    s.append(f'<text x="{ML+pw+8}" y="{ly_e+3.5:.1f}" font-size="11" fill="var(--ink-2)">'
             f'equity</text>')
    s.append(f'<text x="{ML+pw+8}" y="{ly_e+16:.1f}" font-size="11" fill="var(--ink-1)" '
             f'font-weight="600">${last["equity"]/1000:.1f}k</text>')
    s.append(f'<text x="{ML+pw+8}" y="{ly_c+3.5:.1f}" font-size="11" fill="var(--ink-2)">'
             f'cash</text>')
    s.append(f'<text x="{ML+pw+8}" y="{ly_c+16:.1f}" font-size="11" fill="var(--ink-1)" '
             f'font-weight="600">${last["cash"]/1000:.1f}k</text>')

    # x labels, thinned
    step = max(1, n // 7)
    for i in range(0, n, step):
        s.append(f'<text x="{X(i):.1f}" y="{MT+ph+16}" text-anchor="middle" font-size="10" '
                 f'fill="var(--ink-3)">{esc(rows[i]["date"][5:])}</text>')
    s.append(f'<line x1="{ML}" y1="{MT+ph}" x2="{ML+pw}" y2="{MT+ph}" stroke="var(--axis)" '
             f'stroke-width="1"/>')
    s.append("</svg>")

    bad = sum(1 for r in rows if r["trust"] != "ok")
    note = ("Cash is the top band, not a second axis - the stack shows total book and the "
            "cash split on one scale. ")
    if bad:
        note += (f"{bad} reading(s) ringed in red are EXCLUDED as corrupt "
                 f"(self-flagged price-feed gaps); they are drawn so the gap is visible, "
                 f"not silently dropped.")
    return {"svg": "\n".join(s),
            "legend": [("var(--equity)", "Equity"), ("var(--cash)", "Cash")],
            "note": note}


# ---------------------------------------------------------------------------
# 2. RELATIVE vs SMH -- diverging bars, per period. Cumulative is NOT shown:
#    external contributions are unrecorded, so a cumulative book line would be
#    a performance claim the data cannot support.
# ---------------------------------------------------------------------------
def chart_relative(base):
    rows = [r for r in load_ledger(base) if r["smh"]]
    if len(rows) < 2:
        return {"svg": "", "note": "not enough SMH-tagged ledger rows"}

    periods = []
    for a, b in zip(rows, rows[1:]):
        usable = (a["trust"] == "ok" and b["trust"] == "ok")
        bp = (b["total"] - a["total"]) / a["total"] * 100 if a["total"] else 0
        sp = (b["smh"] - a["smh"]) / a["smh"] * 100 if a["smh"] else 0
        periods.append({"label": b["date"][5:], "rel": bp - sp, "book": bp, "smh": sp,
                        "usable": usable, "to": b["date"], "frm": a["date"]})

    W, H = 720, 230
    ML, MR, MT, MB = 46, 16, 14, 40
    pw, ph = W - ML - MR, H - MT - MB
    n = len(periods)
    # Scale off USABLE periods only -- letting an excluded corrupt period (e.g. the
    # 07-18 price-feed spike) set the axis crushes every real bar to invisibility.
    live = [abs(p["rel"]) for p in periods if p["usable"]] or [1.0]
    lim = max(2.0, nice_ceil(max(live)))
    bw = min(30, pw / n * 0.62)
    zero = MT + ph / 2

    def X(i):
        return ML + pw * (i + 0.5) / n

    def hh(v):
        return (ph / 2) * (abs(v) / lim)

    s = [f'<svg class="viz-svg" viewBox="0 0 {W} {H}" width="100%" '
         f'preserveAspectRatio="xMidYMid meet" role="img" '
         f'aria-label="Book return minus SMH return, per period">']
    s.append('<defs><pattern id="hatch" width="5" height="5" patternTransform="rotate(45)" '
             'patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="5" '
             'stroke="var(--muted)" stroke-width="2.5"/></pattern></defs>')

    for g in (-1, -0.5, 0.5, 1):
        y = zero - (ph / 2) * g
        s.append(f'<line x1="{ML}" y1="{y:.1f}" x2="{ML+pw}" y2="{y:.1f}" stroke="var(--grid)" '
                 f'stroke-width="1"/>')
        s.append(f'<text x="{ML-8}" y="{y+3.5:.1f}" text-anchor="end" font-size="10" '
                 f'fill="var(--ink-3)">{lim*g:+.0f}%</text>')

    for i, p in enumerate(periods):
        x, h = X(i) - bw / 2, hh(p["rel"])
        y = zero - h if p["rel"] >= 0 else zero
        if not p["usable"]:
            s.append(f'<rect class="mark" x="{x:.1f}" y="{zero-ph/2*0.16:.1f}" width="{bw:.1f}" '
                     f'height="{ph/2*0.32:.1f}" fill="url(#hatch)" rx="2"><title>'
                     f'{esc(p["frm"])} to {esc(p["to"])} - EXCLUDED, corrupt price feed in '
                     f'this interval</title></rect>')
            continue
        col = "var(--pos)" if p["rel"] >= 0 else "var(--neg)"
        s.append(f'<rect class="mark" x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" '
                 f'height="{max(h,1.5):.1f}" rx="3" fill="{col}"><title>'
                 f'{esc(p["frm"])} to {esc(p["to"])}  book {p["book"]:+.2f}%  '
                 f'SMH {p["smh"]:+.2f}%  =>  {p["rel"]:+.2f}% vs benchmark</title></rect>')

    s.append(f'<line x1="{ML}" y1="{zero:.1f}" x2="{ML+pw}" y2="{zero:.1f}" '
             f'stroke="var(--axis)" stroke-width="1.5"/>')
    step = max(1, round(n / 7))
    for i in range(0, n, step):
        s.append(f'<text x="{X(i):.1f}" y="{MT+ph+16}" text-anchor="middle" font-size="10" '
                 f'fill="var(--ink-3)">{esc(periods[i]["label"])}</text>')
    s.append(f'<text x="{ML}" y="{MT+ph+32}" font-size="10" fill="var(--ink-3)">'
             f'above 0 = beat SMH that period</text>')
    s.append("</svg>")

    ok = [p for p in periods if p["usable"]]
    won = sum(1 for p in ok if p["rel"] > 0)
    note = (f"Per-period only. {won} of {len(ok)} clean periods beat SMH. "
            f"CUMULATIVE performance vs SMH is deliberately NOT shown: external "
            f"contributions are not recorded in the ledger, so a cumulative book line "
            f"would mix deposits with returns and overstate performance. The new "
            f"external_flow_usd column fixes this going forward.")
    hatch_swatch = ("repeating-linear-gradient(45deg,var(--muted) 0 2px,"
                    "transparent 2px 5px)")
    return {"svg": "\n".join(s),
            "legend": [("var(--pos)", "Beat SMH"), ("var(--neg)", "Lagged SMH"),
                       (hatch_swatch, "Excluded (bad data)")],
            "note": note}


# ---------------------------------------------------------------------------
# 3. DRAWDOWN METER -- a single ratio against limits => meter, not a chart.
# ---------------------------------------------------------------------------
def chart_drawdown(base):
    state = json.load(open(os.path.join(base, "state.json")))
    policy = json.load(open(os.path.join(base, "policy.json")))
    us = state.get("us", {})
    peak = us.get("peak_total_book_usd")
    cur = (us.get("value_usd") or 0) + (us.get("wallet_usd") or 0)
    if not peak:
        return {"svg": "", "note": "no peak_total_book_usd in state"}
    dd = (cur - peak) / peak * 100

    ladder = sorted(policy.get("drawdown_trim_ladder", []),
                    key=lambda r: abs(r.get("drawdown_pct", 0)))
    budget = (policy.get("mandate") or {}).get("risk_budget_pct", 25)
    lim = max(budget, max([abs(r["drawdown_pct"]) for r in ladder] or [25])) * 1.12

    W, H = 720, 128
    ML, MR, MT = 16, 16, 40
    pw = W - ML - MR
    TH = 22

    def X(p):
        return ML + pw * (abs(p) / lim)

    fired = None
    for r in ladder:
        if abs(dd) >= abs(r["drawdown_pct"]):
            fired = r
    col = ("var(--good)" if not fired else
           "var(--warning)" if fired["phase"] == "warn" else
           "var(--critical)" if fired["phase"] == "risk_off" else "var(--serious)")

    s = [f'<svg class="viz-svg" viewBox="0 0 {W} {H}" width="100%" '
         f'preserveAspectRatio="xMidYMid meet" role="img" '
         f'aria-label="Current drawdown against the pre-committed trim ladder">']
    s.append(f'<rect x="{ML}" y="{MT}" width="{pw}" height="{TH}" rx="11" '
             f'fill="var(--grid)"/>')
    s.append(f'<rect class="mark" x="{ML}" y="{MT}" width="{max(X(dd)-ML,3):.1f}" '
             f'height="{TH}" rx="11" fill="{col}"><title>drawdown {dd:.2f}% of total book '
             f'(peak ${peak:,.0f} -&gt; now ${cur:,.0f})</title></rect>')

    for r in ladder:
        p = abs(r["drawdown_pct"])
        x = X(p)
        hit = abs(dd) >= p
        s.append(f'<line x1="{x:.1f}" y1="{MT-6}" x2="{x:.1f}" y2="{MT+TH+6}" '
                 f'stroke="var(--ink-1)" stroke-width="{2 if hit else 1}" '
                 f'stroke-opacity="{0.85 if hit else 0.35}"/>')
        s.append(f'<text x="{x:.1f}" y="{MT+TH+20}" text-anchor="middle" font-size="10" '
                 f'fill="{"var(--ink-1)" if hit else "var(--ink-3)"}">-{p:g}%</text>')
        phase = {"warn": "warn", "de-risk_batch_1": "batch 1", "de-risk_batch_2": "batch 2",
                 "risk_off": "risk off"}.get(r["phase"], r["phase"].replace("_", " "))
        s.append(f'<text x="{x:.1f}" y="{MT+TH+32}" text-anchor="middle" font-size="9" '
                 f'class="lbl" fill="var(--ink-3)">{esc(phase)}</text>')

    s.append(f'<text x="{ML}" y="{MT-13}" font-size="26" font-weight="700" fill="{col}">'
             f'{dd:.2f}%</text>')
    s.append(f'<text x="{ML+118}" y="{MT-13}" font-size="11" class="lbl" fill="var(--ink-2)">'
             f'drawdown on total book &#183; peak ${peak:,.0f}</text>')
    status = fired["phase"].replace("_", " ") if fired else "no rung reached"
    s.append(f'<text x="{ML+pw}" y="{MT-14}" text-anchor="end" font-size="11" class="lbl" '
             f'font-weight="600" fill="{col}">{esc(status.upper())}</text>')
    s.append("</svg>")

    return {"svg": "\n".join(s),
            "note": (f"Risk budget is {budget}% (mandate). Rungs are pre-committed: crossing "
                     f"one triggers its action without a fresh judgment call.")}


# ---------------------------------------------------------------------------
# 4. POSITION WEIGHTS vs cap -- magnitude compare => bars, emphasis on breach.
# ---------------------------------------------------------------------------
def chart_weights(base):
    state = json.load(open(os.path.join(base, "state.json")))
    policy = json.load(open(os.path.join(base, "policy.json")))
    cap = policy.get("max_single_position_pct", 12)
    hold = sorted(state.get("holdings", []), key=lambda h: -h.get("weight_pct", 0))[:14]
    if not hold:
        return {"svg": "", "note": "no holdings in state"}

    RH, MT, ML, MR = 21, 12, 58, 54
    W = 720
    H = MT + RH * len(hold) + 26
    pw = W - ML - MR
    lim = nice_ceil(max(max(h["weight_pct"] for h in hold), cap) * 1.15)

    s = [f'<svg class="viz-svg" viewBox="0 0 {W} {H}" width="100%" '
         f'preserveAspectRatio="xMidYMid meet" role="img" '
         f'aria-label="Position weights against the single-position cap">']
    capx = ML + pw * cap / lim
    s.append(f'<rect x="{capx:.1f}" y="{MT-4}" width="{ML+pw-capx:.1f}" '
             f'height="{RH*len(hold)+4}" fill="var(--critical)" fill-opacity="0.06"/>')

    for i, h in enumerate(hold):
        y = MT + i * RH
        w = pw * h["weight_pct"] / lim
        over = h["weight_pct"] > cap
        col = "var(--critical)" if over else "var(--equity)"
        s.append(f'<text x="{ML-8}" y="{y+RH/2+3.5:.1f}" text-anchor="end" font-size="11" '
                 f'font-weight="{700 if over else 400}" fill="var(--ink-1)">'
                 f'{esc(h["ticker"])}</text>')
        s.append(f'<rect class="mark" x="{ML}" y="{y+3:.1f}" width="{max(w,2):.1f}" '
                 f'height="{RH-8}" rx="3" fill="{col}"><title>{esc(h["ticker"])} '
                 f'{h["weight_pct"]:.2f}% of equity'
                 f'{" - BREACHES the " + str(cap) + "% cap" if over else ""}</title></rect>')
        s.append(f'<text x="{ML+max(w,2)+7:.1f}" y="{y+RH/2+3.5:.1f}" font-size="10.5" '
                 f'fill="{"var(--critical)" if over else "var(--ink-2)"}" '
                 f'font-weight="{700 if over else 400}">{h["weight_pct"]:.1f}%</text>')

    s.append(f'<line x1="{capx:.1f}" y1="{MT-4}" x2="{capx:.1f}" y2="{MT+RH*len(hold)}" '
             f'stroke="var(--critical)" stroke-width="1.5" stroke-dasharray="3 3"/>')
    s.append(f'<text x="{capx:.1f}" y="{MT+RH*len(hold)+16}" text-anchor="middle" '
             f'font-size="10" class="lbl" fill="var(--critical)">{cap}% cap</text>')
    s.append("</svg>")

    br = [h["ticker"] for h in hold if h["weight_pct"] > cap]
    return {"svg": "\n".join(s),
            "note": (f"Breaching: {', '.join(br)}." if br else "No position breaches the cap.")}


# ---------------------------------------------------------------------------
# 5. ALLOCATION TREEMAP -- squarified layout (Bruls/Huizing/van Wijk), sized by
#    weight, colored by cluster, red outline where a position is over its ATR
#    risk cap. G34: was hand-authored once with baked-in rect coordinates,
#    never a generator; this is the from-scratch layout algorithm.
# ---------------------------------------------------------------------------
def _squarify_worst(row, length):
    if not row:
        return float("inf")
    s = sum(row)
    row_max, row_min = max(row), min(row)
    side2 = (s / length) ** 2 if length else float("inf")
    if row_min <= 0 or side2 <= 0:
        return float("inf")
    return max(side2 / row_min, row_max / side2)


def _squarify_row_rects(row, x, y, w, h, horizontal):
    row_sum = sum(row)
    rects = []
    if horizontal:
        thickness = row_sum / w if w else 0
        cx = x
        for s in row:
            rw = s / thickness if thickness else 0
            rects.append((cx, y, rw, thickness))
            cx += rw
    else:
        thickness = row_sum / h if h else 0
        cy = y
        for s in row:
            rh = s / thickness if thickness else 0
            rects.append((x, cy, thickness, rh))
            cy += rh
    return rects, thickness


def squarify(sizes, x, y, w, h):
    """sizes: positive floats (already area-normalized to sum(sizes) == w*h,
    sorted descending by caller). Returns rects [(x,y,w,h), ...] in the same
    order as sizes. Standard squarified-treemap algorithm, no dependencies."""
    sizes = list(sizes)
    if not sizes:
        return []
    rects, row = [], []
    rx, ry, rw, rh = x, y, w, h
    i = 0
    while i < len(sizes):
        horizontal = rw >= rh
        length = rw if horizontal else rh
        if not row:
            row = [sizes[i]]
            i += 1
            continue
        candidate = row + [sizes[i]]
        if _squarify_worst(candidate, length) <= _squarify_worst(row, length):
            row = candidate
            i += 1
        else:
            row_rects, thickness = _squarify_row_rects(row, rx, ry, rw, rh, horizontal)
            rects.extend(row_rects)
            if horizontal:
                ry, rh = ry + thickness, rh - thickness
            else:
                rx, rw = rx + thickness, rw - thickness
            row = []
    if row:
        horizontal = rw >= rh
        row_rects, _ = _squarify_row_rects(row, rx, ry, rw, rh, horizontal)
        rects.extend(row_rects)
    return rects


def chart_treemap(base):
    state = json.load(open(os.path.join(base, "state.json")))
    policy = json.load(open(os.path.join(base, "policy.json")))
    us = state.get("us", {})
    value_usd = us.get("value_usd") or 0
    wallet_usd = us.get("wallet_usd") or 0
    total_book_usd = value_usd + wallet_usd
    sector_map = state.get("sector_map", {})
    atr_cache = state.get("data_cache", {}).get("atr20", {}).get("values_pct", {})

    holdings = sorted(state.get("holdings", []), key=lambda h: -(h.get("weight_pct") or 0))
    if not holdings or not value_usd:
        return {"svg": "", "note": "no holdings/equity in state"}

    W, H = 760, 320
    items = []
    for hd in holdings:
        ticker, w_pct, qty = hd["ticker"], hd.get("weight_pct") or 0, hd.get("qty")
        if w_pct <= 0:
            continue
        market_value_usd = w_pct / 100 * value_usd
        price_usd = (market_value_usd / qty) if qty else None
        r = smith_risk.stop_and_cap(atr_cache.get(ticker), price_usd, qty, total_book_usd, policy)
        cluster = sector_map.get(ticker, "Unclassified")
        items.append({"ticker": ticker, "weight_pct": w_pct, "market_value_usd": market_value_usd,
                      "cluster": cluster, "over_cap": r["over_cap"]})

    total_w = sum(it["weight_pct"] for it in items) or 1.0
    areas = [it["weight_pct"] / total_w * (W * H) for it in items]
    rects = squarify(areas, 0, 0, W, H)

    s = [f'<svg class="viz-svg" viewBox="0 0 {W} {H}" width="100%" '
         f'preserveAspectRatio="xMidYMid meet" role="img" '
         f'aria-label="Position allocation treemap, size by weight, color by cluster">']
    clusters_seen = []
    for it, (rx, ry, rw, rh) in zip(items, rects):
        var = CLUSTER_COLOR_VAR.get(it["cluster"], "--muted")
        if it["cluster"] not in clusters_seen:
            clusters_seen.append(it["cluster"])
        stroke = ('stroke="var(--critical)" stroke-width="2.5"' if it["over_cap"]
                  else 'stroke="var(--surface-1)" stroke-width="1.5"')
        cap_note = "  (OVER RISK CAP)" if it["over_cap"] else ""
        s.append(f'<rect class="mark" x="{rx:.1f}" y="{ry:.1f}" width="{max(rw,0):.1f}" '
                 f'height="{max(rh,0):.1f}" fill="var({var})" fill-opacity="0.85" {stroke}>'
                 f'<title>{esc(it["ticker"])} &#8212; {it["weight_pct"]:.2f}% of equity &#8212; '
                 f'${it["market_value_usd"]:,.0f} &#8212; {esc(it["cluster"])}{cap_note}</title></rect>')
        if rw > 34 and rh > 20:
            s.append(f'<text x="{rx+6:.1f}" y="{ry+17:.1f}" font-size="12" font-weight="700" '
                     f'fill="#fff">{esc(it["ticker"])}</text>')
        if rw > 34 and rh > 32:
            s.append(f'<text x="{rx+6:.1f}" y="{ry+32:.1f}" font-size="10" fill="#ffffffcc">'
                     f'{it["weight_pct"]:.1f}%</text>')
    s.append("</svg>")

    legend = [(f"var({CLUSTER_COLOR_VAR.get(c, '--muted')})", c) for c in clusters_seen]
    return {"svg": "\n".join(s), "legend": legend,
            "note": ("Not shown: a correlation heatmap. On a book this concentrated in one factor "
                     "every pair correlates near 1.0 -- it would render as a wall of red saying "
                     "nothing a treemap doesn't already say faster.")}


CHARTS = {"bookvalue": chart_bookvalue, "relative": chart_relative,
          "drawdown": chart_drawdown, "weights": chart_weights,
          "treemap": chart_treemap}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=list(CHARTS) + ["all", "css"])
    ap.add_argument("--base-dir", default=DEFAULT_BASE)
    a = ap.parse_args()
    try:
        if a.cmd == "css":
            print(PALETTE_CSS)
        elif a.cmd == "all":
            print(json.dumps({k: f(a.base_dir) for k, f in CHARTS.items()}))
        else:
            print(json.dumps(CHARTS[a.cmd](a.base_dir)))
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()

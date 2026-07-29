#!/usr/bin/env python3
"""
Agent Smith dashboard builder -- assembles dashboard.html from state files + charts.

G34 (2026-07-29): ported the richer design that had been hand-authored once (never
in scripts/, archived at archive/dashboard_rich_template_2026-07-28.html) into this
generator, so it's produced safely from real data every run instead of by hand.
Everything derivable from state.json / policy.json / ledger.csv / proposals.json /
compute_*.json is rendered here deterministically; the per-run judgment content
(session read) comes from an optional narrative.json the orchestrator writes.

STRUCTURE, top to bottom:
  Masthead + status strip
  Tier DECISIONS   -- open proposals, factor catalysts, rotation analysis, the
                       read + macro strip (always open)
  Sentiment gauge + intraday & international session (side by side)
  The week ahead   -- earnings/FOMC calendar, 6 days forward
  Tier BOOK COMPOSITION -- allocation treemap, clusters, risk-cap breaches,
                            full positions table
  Tier DIAGNOSTICS -- thesis map, signal history, open data gaps (collapsed);
                       "Historical charts" (the 4 original SVG charts, collapsed)

Prose rule: one sentence inline, anything longer goes inside <details>.

Usage:  smith_dashboard.py --base-dir DIR [--out dashboard.html]
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smith_risk

DEFAULT_BASE = "/Users/yb/Claude/AgentSmith"


def load(p, d=None):
    if not os.path.exists(p):
        return d
    with open(p) as f:
        return json.load(f)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def charts(base):
    r = subprocess.run([sys.executable, os.path.join(base, "scripts", "smith_charts.py"),
                        "all", "--base-dir", base], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def chart_css(base):
    r = subprocess.run([sys.executable, os.path.join(base, "scripts", "smith_charts.py"),
                        "css", "--base-dir", base], capture_output=True, text=True)
    return r.stdout


def fig(d, title, sub=""):
    """One chart block: title, legend, svg, note. Rendered as a .panel.viz."""
    if not d or not d.get("svg"):
        return ""
    leg = ""
    if d.get("legend"):
        leg = ('<div class="viz-legend">' + "".join(
            f'<span><i style="background:{c}"></i>{esc(l)}</span>' for c, l in d["legend"])
            + "</div>")
    s = f'<span class="sub">{esc(sub)}</span>' if sub else ""
    return (f'<section class="panel viz"><div class="phead"><h2>{esc(title)}{s}</h2></div>'
            f'<div class="pbody">{leg}{d["svg"]}'
            f'<div class="viz-note">{esc(d.get("note",""))}</div></div></section>')


def trim_lead(text, max_len=180):
    """First sentence (or a word-boundary-safe cut), plus the remainder for a
    <details> expansion. Returns (short, rest_or_empty)."""
    text = (text or "").strip()
    if not text:
        return "", ""
    head = text.split(". ")[0]
    if len(head) > max_len:
        head = head[:max_len].rsplit(" ", 1)[0]
    short = head.rstrip(" ,;:-") + "."
    rest = text[len(head):].strip(" .")
    return short, rest


CSS = """
*{box-sizing:border-box}
/* ============ tokens ============ */
:root{
  --ground:#f2f4f5; --surface:#ffffff; --surface-2:#f7f9f9;
  --ink:#12171b; --ink-2:#48545c; --ink-3:#79868e;
  --line:#dbe1e3; --line-soft:#e9edee;
  --accent:#35586a; --accent-soft:#e4ecef; --accent-line:#b6cbd4;
  --action:#8f5322; --action-soft:#f7ece2; --action-line:#e0bd9c;
  --good:#1f7a4d; --good-soft:#e3f1e9;
  --warn:#9c6f18; --warn-soft:#f8efd9;
  --bad:#a83737;  --bad-soft:#f8e5e5;
  --sans:-apple-system,"Segoe UI",system-ui,sans-serif;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --r:7px; --shadow:0 1px 2px rgba(18,23,27,.05),0 1px 10px rgba(18,23,27,.03);
}
@media (prefers-color-scheme:dark){
  :root:where(:not([data-theme="light"])){
    --ground:#0d1013; --surface:#161b1f; --surface-2:#1b2126;
    --ink:#e6eaec; --ink-2:#a3b0b7; --ink-3:#6f7c84;
    --line:#283036; --line-soft:#212930;
    --accent:#82abbf; --accent-soft:#182831; --accent-line:#2d4653;
    --action:#d1904f; --action-soft:#2b1e12; --action-line:#4d3620;
    --good:#5cb98a; --good-soft:#12251c;
    --warn:#d3a446; --warn-soft:#2a2211;
    --bad:#d97676;  --bad-soft:#2b1717;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 1px 10px rgba(0,0,0,.2);
  }
}
:root[data-theme="dark"]{
  --ground:#0d1013; --surface:#161b1f; --surface-2:#1b2126;
  --ink:#e6eaec; --ink-2:#a3b0b7; --ink-3:#6f7c84;
  --line:#283036; --line-soft:#212930;
  --accent:#82abbf; --accent-soft:#182831; --accent-line:#2d4653;
  --action:#d1904f; --action-soft:#2b1e12; --action-line:#4d3620;
  --good:#5cb98a; --good-soft:#12251c;
  --warn:#d3a446; --warn-soft:#2a2211;
  --bad:#d97676;  --bad-soft:#2b1717;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 1px 10px rgba(0,0,0,.2);
}

body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  -webkit-font-smoothing:antialiased;line-height:1.5;font-size:15px}
.wrap{max-width:1140px;margin:0 auto;padding:26px 20px 80px;display:flex;flex-direction:column;gap:26px}
h1,h2{margin:0;text-wrap:balance;font-weight:640;letter-spacing:-.015em}
p{margin:0}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.voice{font-family:var(--serif);font-size:15.5px;line-height:1.62;color:var(--ink-2)}
.voice em{color:var(--ink);font-style:italic}
.pos{color:var(--good)} .neg{color:var(--bad)}
.col{display:flex;flex-direction:column}

/* ============ masthead ============ */
.mast{display:flex;flex-wrap:wrap;gap:14px;align-items:baseline;justify-content:space-between;
  padding-bottom:16px;border-bottom:2px solid var(--ink)}
.mast h1{font-size:25px}
.mast h1 span{color:var(--accent);font-weight:500}
.stamp{font-family:var(--mono);font-size:11.5px;color:var(--ink-3);text-align:right;line-height:1.65}

/* ============ status strip ============ */
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(146px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.cell{background:var(--surface);padding:12px 14px;display:flex;flex-direction:column;gap:4px}
.cell .k{font-size:10.5px;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:var(--ink-3)}
.cell .v{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:19px;font-weight:600;letter-spacing:-.02em}
.cell .s{font-family:var(--mono);font-size:11.5px;color:var(--ink-3)}
.cell.flag{background:var(--bad-soft)} .cell.flag .v{color:var(--bad)}
.cell.okc .v{color:var(--good)}
.macro{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:16px}
.macro .k{font-size:10.5px;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:var(--ink-3)}
.macro .v{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:18px;font-weight:600;letter-spacing:-.02em}
.macro .s{font-family:var(--mono);font-size:11.5px;color:var(--ink-3)}

/* ============ panels ============ */
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow)}
.phead{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;
  padding:13px 17px;border-bottom:1px solid var(--line-soft)}
.phead h2{font-size:14.5px}
.pbody{padding:17px;display:flex;flex-direction:column;gap:14px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:26px;align-items:start}

.act{border-color:var(--action-line);background:var(--action-soft)}
.act .phead{border-bottom-color:var(--action-line)}
.act .phead h2{color:var(--action)}

.pill{display:inline-flex;align-items:center;font-size:10.5px;font-weight:700;
  letter-spacing:.07em;text-transform:uppercase;padding:3px 9px;border-radius:100px;
  background:var(--accent-soft);color:var(--accent);white-space:nowrap}
.pill.g{background:var(--good-soft);color:var(--good)}
.pill.w{background:var(--warn-soft);color:var(--warn)}
.pill.b{background:var(--bad-soft);color:var(--bad)}
.pill.a{background:var(--surface);color:var(--action);border:1px solid var(--action-line)}
.pills{display:flex;gap:6px;flex-wrap:wrap}

/* ============ tables ============ */
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px}
th{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);
  text-align:right;padding:0 10px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left;padding-left:0}
th:last-child,td:last-child{padding-right:0}
td{padding:8px 10px;text-align:right;border-bottom:1px solid var(--line-soft);white-space:nowrap;
  font-family:var(--mono);font-variant-numeric:tabular-nums}
tbody tr:last-child td{border-bottom:none}
td.name{font-family:var(--sans);font-weight:640;letter-spacing:-.01em}
td.txt{font-family:var(--sans);text-align:left;white-space:normal;color:var(--ink-2);font-size:12px}
tfoot td{font-weight:700;border-top:2px solid var(--line);border-bottom:none;padding-top:10px}
td.blank{color:var(--ink-3)}

/* ============ band meter (clusters) ============ */
.band{position:relative;height:26px;background:var(--surface-2);border-radius:4px;overflow:hidden;min-width:160px}
.band .ok{position:absolute;top:0;bottom:0;background:var(--accent-soft)}
.band .tgt{position:absolute;top:0;bottom:0;width:2px;background:var(--accent-line)}
.band .mk{position:absolute;top:3px;bottom:3px;width:3px;border-radius:2px;background:var(--ink)}
.band .mk.bad{background:var(--bad)}

/* ============ decision/proposal rows ============ */
.pr{display:grid;grid-template-columns:96px 1fr auto;gap:12px;padding:11px 0;border-bottom:1px solid var(--line-soft);align-items:baseline}
.pr:last-child{border-bottom:none}
.pr .act2{font-family:var(--mono);font-size:12px;font-weight:700}
.pr .why{font-size:12.5px;color:var(--ink-2);line-height:1.45}
.pr .amt{font-family:var(--mono);font-weight:700;color:var(--action)}

/* ============ factor catalysts ============ */
.ci{display:grid;grid-template-columns:78px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--line-soft)}
.ci:last-child{border-bottom:none}
.cb{font-size:9.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 6px;border-radius:4px;text-align:center;height:fit-content}
.cb.TAILWIND{background:var(--good-soft);color:var(--good)}
.cb.THREAT{background:var(--bad-soft);color:var(--bad)}
.cb.AMBIGUOUS{background:var(--warn-soft);color:var(--warn)}
.ci .hh{font-size:13.5px;font-weight:640;line-height:1.4}
.ci .mm{font-size:12px;color:var(--ink-3);margin-top:4px;line-height:1.45}
.ci .aa{font-family:var(--mono);font-size:11px;color:var(--accent);margin-top:4px}

/* ============ rotation analysis ============ */
.rgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}
.rcol{display:flex;flex-direction:column;gap:9px}
.rct{font-family:var(--mono);font-size:11px;color:var(--ink-3);font-weight:400;margin-left:auto}
.grp-h{display:flex;align-items:center;gap:7px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);margin-bottom:8px}
.dot-g,.dot-w,.dot-b{width:7px;height:7px;border-radius:50%}
.dot-g{background:var(--good)} .dot-w{background:var(--warn)} .dot-b{background:var(--bad)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.rchip{display:inline-flex;align-items:baseline;gap:5px;padding:5px 9px;border-radius:5px;
  font-size:12.5px;font-weight:700;cursor:help;border:1px solid var(--line)}
.rchip.g{background:var(--good-soft);color:var(--good);border-color:transparent}
.rchip.b{background:var(--bad-soft);color:var(--bad);border-color:transparent}
.rchip.w{background:var(--warn-soft);color:var(--warn);border-color:transparent}
.rchip i{font-style:normal;font-family:var(--mono);font-size:10.5px;opacity:.75}

/* ============ sentiment gauge ============ */
.sg{display:flex;flex-direction:column;gap:10px}
.sg-head{display:flex;justify-content:space-between;align-items:baseline;font-size:11.5px;color:var(--ink-3)}
.sg-head b{font-size:19px;color:var(--ink)}
.sg-track{position:relative;height:14px;border-radius:7px;overflow:hidden;display:flex}
.sg-seg{height:100%}
.sg-seg.xfear{background:#7a3a3a} .sg-seg.fear{background:#a86a4a}
.sg-seg.neu{background:var(--ink-3);opacity:.4} .sg-seg.greed{background:#7a9a5a} .sg-seg.xgreed{background:#4a7a5a}
.sg-marker{position:absolute;top:-5px;width:2px;height:24px;background:var(--ink);transform:translateX(-1px)}
.sg-marker::after{content:"";position:absolute;top:-4px;left:-4px;width:8px;height:8px;border-radius:50%;background:var(--ink)}
.sg-val{position:absolute;top:-24px;left:50%;transform:translateX(-50%);font-family:var(--mono);
  font-size:11px;font-weight:700;white-space:nowrap;color:var(--ink)}
.sg-labels{display:flex;justify-content:space-between;font-size:10px;font-family:var(--mono);color:var(--ink-3)}
.sg-dist{display:flex;gap:6px;flex-wrap:wrap}
.sg-comp{display:flex;gap:12px;flex-wrap:wrap;padding-top:6px;border-top:1px solid var(--line-soft)}
.scc{font-size:11.5px;color:var(--ink-3)} .scc b{font-family:var(--mono);color:var(--ink-2);font-weight:640}

/* ============ intl session ============ */
.kv{display:flex;flex-direction:column;gap:9px}
.kv .row{display:flex;gap:12px;align-items:baseline;justify-content:space-between;
  padding-bottom:9px;border-bottom:1px solid var(--line-soft)}
.kv .row:last-child{border-bottom:none;padding-bottom:0}
.kv .lab{font-size:13px;color:var(--ink-2)}
.kv .val{font-family:var(--mono);font-size:13.5px;font-weight:640;text-align:right;line-height:1.45}
.db{font-family:var(--mono);font-weight:640}
.db.pos{color:var(--good)} .db.neg{color:var(--bad)}
.value-sub{font-size:12.5px;color:var(--ink-2);line-height:1.5;padding-top:8px;border-top:1px solid var(--line-soft)}
.value-sub b{color:var(--ink)}

/* ============ week ahead calendar ============ */
.cal{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:1px;background:var(--line);
  border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.day{background:var(--surface);padding:11px 12px;display:flex;flex-direction:column;gap:7px;min-height:96px}
.day.hot{background:var(--warn-soft)}
.day .d{font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3)}
.day.hot .d{color:var(--warn)}
.ev{font-size:12px;line-height:1.4;color:var(--ink)}
.ev.est{color:var(--ink-3);font-style:italic}

/* ============ diagnostics: chips / ticks ============ */
.chip{display:inline-flex;flex-direction:column;gap:1px;padding:5px 9px;border-radius:5px;background:var(--surface-2);
 border:1px solid var(--line);border-left-width:3px;font-size:12.5px;font-weight:700;cursor:help}
.chip i{font-style:normal;font-size:9.5px;font-weight:500;color:var(--ink-3)}
.tick{font-family:var(--mono);font-size:11.5px;font-weight:700;padding:2px 6px;border-radius:4px;background:var(--surface-2);color:var(--ink-2)}
.tick.g{background:var(--good-soft);color:var(--good)} .tick.b{background:var(--bad-soft);color:var(--bad)}
.tick.gone{opacity:.42;text-decoration:line-through}
.srow{display:grid;grid-template-columns:150px 1fr;gap:11px;align-items:baseline;padding:5px 0}
.slab{font-size:11.5px;color:var(--ink-2)} .sch{display:flex;flex-wrap:wrap;gap:4px}

/* ============ tiers / details (t3) ============ */
.tier{margin-top:6px;display:flex;align-items:center;gap:13px}
.tier h2{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:var(--ink-3);white-space:nowrap}
.tier .ln{flex:1;height:1px;background:var(--line)}
.t3 .panel{padding:0}
details{border-top:1px solid var(--line-soft)}
details:first-of-type{border-top:none}
.t3 details{margin:0;padding:0 20px}
details>summary{cursor:pointer;list-style:none;user-select:none;padding:14px 0;
  font-size:13.5px;font-weight:640;letter-spacing:-.01em;color:var(--ink);font-family:var(--serif)}
details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"▸  ";color:var(--ink-3)}
details[open]>summary::before{content:"▾  "}
details>summary:hover{color:var(--accent)}
details>summary .c{font-family:var(--mono);font-size:11px;color:var(--ink-3);font-weight:400;margin-left:7px}
details .body{padding:2px 0 17px;font-size:12.5px;color:var(--ink-2);line-height:1.6}

/* ============ misc ============ */
.note{font-size:12.5px;color:var(--ink-3);line-height:1.55}
.note b{color:var(--ink-2)}
.rule{height:1px;background:var(--line-soft);border:0;margin:0}
footer{border-top:1px solid var(--line);padding-top:18px;display:flex;flex-direction:column;gap:10px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
"""


def status_strip(us, dd, cash_pct, cash_band, cash_breach, risk, drift):
    ai_capex_pct = drift.get("ai_capex_pct")
    prior_ai = drift.get("ai_capex_pct_prior")  # optional, not always present
    open_risk_pct = risk.get("aggregate_open_risk_pct")
    open_risk_cap = risk.get("aggregate_open_risk_cap_pct")
    open_risk_over = risk.get("aggregate_over_cap")

    cells = []
    cells.append(("", "Total book", f'${(us.get("value_usd",0) or 0)+(us.get("wallet_usd",0) or 0):,.0f}', "equity + wallet"))
    cells.append(("", "Equity", f'${us.get("value_usd",0) or 0:,.0f}', f'{us.get("count","-")} positions'))
    cells.append(("okc" if not cash_breach else "flag", "Cash",
                  f'{cash_pct:.1f}%', f'band [{cash_band[0]},{cash_band[1]}]'))
    cells.append(("flag" if abs(dd) >= 15 else "", "Drawdown", f'{dd:.2f}%',
                  f'{15-abs(dd):.2f}pt to warn' if abs(dd) < 15 else "past warn rung"))
    if open_risk_pct is not None:
        cells.append(("flag" if open_risk_over else "", "Open risk",
                      f'{open_risk_pct:.1f}%', f'cap {open_risk_cap:g}%' + (" · OVER" if open_risk_over else "")))
    if ai_capex_pct is not None:
        cells.append(("flag" if ai_capex_pct >= 90 else "", "AI-capex", f'{ai_capex_pct:.1f}%',
                      "of book" + (f', was {prior_ai:.1f}%' if prior_ai is not None else "")))

    return ('<section class="strip">' + "".join(
        f'<div class="cell {cls}"><span class="k">{esc(k)}</span><span class="v num">{esc(v)}</span>'
        f'<span class="s">{esc(s)}</span></div>' for cls, k, v, s in cells) + '</section>')


def build(base, out):
    state = load(os.path.join(base, "state.json"), {}) or {}
    policy = load(os.path.join(base, "policy.json"), {}) or {}
    props = load(os.path.join(base, "proposals.json"), {}) or {}
    narr = load(os.path.join(base, "narrative.json"), {}) or {}
    ch = charts(base)

    last_run_dir = state.get("last_run_dir", "")

    def run_file(name):
        return load(os.path.join(base, last_run_dir, name), {}) or {} if last_run_dir else {}

    drift = run_file("compute_drift.json")
    market_inputs = run_file("market_inputs.json")
    risk = run_file("compute_risk.json")
    rotation = run_file("compute_rotation.json")
    book_compute = run_file("compute_book.json")

    us = state.get("us", {})
    equity = us.get("value_usd") or 0
    cash = us.get("wallet_usd") or 0
    total = equity + cash
    peak = us.get("peak_total_book_usd") or total
    dd = (total - peak) / peak * 100 if peak else 0
    cash_pct = cash / total * 100 if total else 0
    cash_band = drift.get("cash_band_pct") or policy.get("cash_band_pct", [3, 15])
    cash_breach = drift.get("cash_breach")
    if cash_breach is None:
        cash_breach = cash_pct < cash_band[0] or cash_pct > cash_band[1]
    mandate = policy.get("mandate", {})
    ts = state.get("ts", "")
    sector_map = state.get("sector_map", {})
    held_tickers = {h["ticker"] for h in state.get("holdings", [])}

    H = []
    H.append(f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
             f'<meta name="viewport" content="width=device-width,initial-scale=1">'
             f'<title>Agent Smith - US Book</title><style>{CSS}{chart_css(base)}</style>'
             f'</head><body><div class="wrap">')

    # ---------------- masthead ----------------
    mode_label = "US Deep Review" if state.get("mode") == "deep" else "US"
    H.append(f'<header class="mast"><h1>Agent Smith <span>&middot; {esc(mode_label)}</span></h1>'
             f'<div class="stamp">{esc(ts[:16].replace("T"," "))}'
             f'<br>USD/INR {us.get("usdinr","-")} &middot; stops on ATR20 &middot; betas vs SMH</div></header>')

    # ---------------- status strip ----------------
    H.append(status_strip(us, dd, cash_pct, cash_band, cash_breach, risk, drift))

    # ================= TIER: DECISIONS =================
    H.append('<div class="tier"><h2>Decisions</h2><div class="ln"></div></div>')

    open_props = [p for p in props.get("proposals", []) if p.get("status") == "open"]
    cap = policy.get("max_single_position_pct", 12)
    breaches = []
    for h in state.get("holdings", []):
        if h.get("weight_pct", 0) > cap:
            breaches.append(f'{h["ticker"]} {h["weight_pct"]:.1f}% vs {cap}% position cap')
    if cash_breach:
        breaches.append(f'cash {cash_pct:.1f}% outside the [{cash_band[0]},{cash_band[1]}]% band')

    if open_props or breaches:
        rows = []
        for b in breaches:
            rows.append(f'<div class="pr"><span class="act2">Breach</span>'
                        f'<span class="why">{esc(b)} &mdash; bring it inside the band or record why '
                        f'the breach is accepted.</span><span class="amt">&mdash;</span></div>')
        for p in open_props:
            short, rest = trim_lead(p.get("rationale", ""))
            more = (f'<details><summary>full rationale</summary><div class="body">{esc(rest)}</div></details>'
                    if len(rest) > 40 else "")
            rows.append(f'<div class="pr"><span class="act2">{esc(p.get("action",""))}</span>'
                        f'<span class="why">{esc(short)}{more}</span>'
                        f'<span class="amt">${p.get("size_usd",0):,.0f}</span></div>')
        H.append('<section class="panel act"><div class="phead"><h2>Open proposals</h2>'
                 '<span class="pill a">For review &mdash; never executed</span></div>'
                 f'<div class="pbody"><div>{"".join(rows)}</div></div></section>')

    # -- factor catalysts --
    catalysts = state.get("factor_catalysts", [])
    if catalysts:
        rows = []
        for c in catalysts[:6]:
            dirn = {"threat": "THREAT", "tailwind": "TAILWIND"}.get(c.get("direction", ""), "AMBIGUOUS")
            affects = " &middot; ".join(c.get("affects", []))
            exp = c.get("exposure_pct_equity")
            exp_s = f' &mdash; {exp:.1f}% equity' if isinstance(exp, (int, float)) else ""
            rows.append(f'<div class="ci"><span class="cb {dirn}">{dirn}</span><div>'
                        f'<div class="hh">{esc(c.get("headline",""))}</div>'
                        f'<div class="mm">{esc(c.get("magnitude",""))}</div>'
                        f'<div class="aa">{esc(affects)}{exp_s}</div></div></div>')
        H.append('<section class="panel"><div class="phead"><h2>Factor catalysts</h2></div>'
                 f'<div class="pbody"><div>{"".join(rows)}</div></div></section>')

    # -- rotation analysis --
    rtickers = rotation.get("tickers", {})
    if rtickers:
        groups = {"accumulate": [], "rotate_out": [], "trim_risk_cap": []}
        for tk, v in rtickers.items():
            b = v.get("bucket")
            if b in groups:
                groups[b].append((tk, v))
        for g in groups.values():
            g.sort(key=lambda tv: -tv[1]["net_signal"])

        def rchip(tk, v):
            buckets = v["bullish_buckets"] or v["bearish_buckets"]
            tail = (f'{v["cap_multiple"]:.2f}x over cap' if v.get("over_cap") and v.get("cap_multiple")
                    else (f'${v["headroom_usd"]:,.0f} headroom' if v.get("headroom_usd") is not None else ""))
            title = f'{v.get("cluster","-")} | {v.get("thesis_status") or "-"} | net signal {v["net_signal"]:+d} ({", ".join(buckets) or "none"}) | {tail}'
            cls = "g" if v["net_signal"] > 0 else ("b" if v["net_signal"] < 0 else "w")
            return f'<span class="rchip {cls}" title="{esc(title)}">{esc(tk)}<i>{v["net_signal"]:+d}</i></span>'

        cols = [
            ("dot-g", "Accumulate", groups["accumulate"]),
            ("dot-b", "Rotate out", groups["rotate_out"]),
            ("dot-w", "Trim &mdash; risk cap", groups["trim_risk_cap"]),
        ]
        rgrid = "".join(
            f'<div class="rcol"><div class="grp-h"><span class="{dot}"></span>{label}'
            f'<b class="rct">{len(items)}</b></div><div class="chips">'
            + "".join(rchip(tk, v) for tk, v in items) + '</div></div>'
            for dot, label, items in cols)
        H.append('<section class="panel"><div class="phead"><h2>Rotation analysis</h2>'
                 '<span class="pill">thesis &times; signal history &times; risk headroom</span></div>'
                 '<div class="pbody"><p class="note">Rule-based: <b>Accumulate</b> = strengthening thesis + '
                 'net-bullish signals. <b>Rotate out</b> = watch thesis + net-bearish signals. '
                 '<b>Trim &mdash; risk cap</b> = over its ATR risk cap, regardless of thesis or signal. '
                 'Everything else is unchipped (thesis and signal disagree, or both are flat). '
                 'MOMENTUM+VOLUME and TARGET GAP are excluded from the signal count &mdash; both fire on '
                 'moves in either direction by their own definition, so neither is unambiguously bullish '
                 'or bearish.</p>'
                 f'<div class="rgrid">{rgrid}</div></div></section>')

    # -- the read + macro strip --
    session_text = narr.get("session_read")
    if session_text:
        short, rest = trim_lead(session_text, 400)
        more = (f'<details><summary>more</summary><div class="body">{esc(rest)}</div></details>'
                if len(rest) > 40 else "")
        gate = market_inputs.get("gate_classification")
        gate_pill = (f'<span class="pill {"b" if gate=="ESCALATING" else ("w" if gate=="AMBIGUOUS" else "g")}">'
                     f'Gate {esc(gate.title())}</span>') if gate else ""
        H.append(f'<section class="panel"><div class="phead"><h2>The read</h2>'
                 f'<div class="pills">{gate_pill}</div></div>'
                 f'<div class="pbody"><p class="voice">{esc(short)}</p>{more}')

        macro_cells = []
        if market_inputs:
            us10y = market_inputs.get("us10y")
            if us10y is not None:
                macro_cells.append(("10-yr", f'{us10y:.3f}%', ""))
            vix = market_inputs.get("vix")
            if vix is not None:
                macro_cells.append(("VIX", f'{vix:.2f}', f'{market_inputs.get("vix_chg_pct",0):+.1f}% today'))
            smh_chg = market_inputs.get("smh_chg_pct")
            if smh_chg is not None:
                macro_cells.append(("SMH", f'{smh_chg:+.2f}%', "the benchmark"))
            asia = market_inputs.get("asia_block") or {}
            if asia:
                worst_name, worst = min(asia.items(), key=lambda kv: kv[1].get("chg_pct", 0))
                macro_cells.append((worst_name.upper(), f'{worst.get("chg_pct",0):+.2f}%', "worst Asia index"))
        fomc = state.get("fomc_cache", {})
        if fomc.get("rate_pct") is not None:
            macro_cells.append(("Fed", f'{fomc["rate_pct"]:.2f}%', esc(fomc.get("stance", "")).lower()))
        beta = book_compute.get("primary_benchmark", {}).get("primary_beta")
        if beta is not None:
            macro_cells.append(("Beta vs SMH", f'{beta:.3f}', ""))
        if macro_cells:
            H.append('<hr class="rule"><div class="macro">' + "".join(
                f'<div class="col"><span class="k">{esc(k)}</span><span class="v">{esc(v)}</span>'
                f'<span class="s">{esc(s)}</span></div>' for k, v, s in macro_cells) + '</div>')
        H.append('</div></section>')

    # ================= grid2: sentiment gauge + intraday session =================
    left = right = ""
    sentiment = state.get("sentiment", {})
    if sentiment.get("score") is not None:
        score = sentiment["score"]
        comp = sentiment.get("components", {})
        dist_bits = []
        if score >= 45:
            dist_bits.append(f'<span class="pill">{score-45:.1f} pts above Neutral</span>')
        else:
            dist_bits.append(f'<span class="pill">{45-score:.1f} pts below Neutral</span>')
        if score < 75:
            dist_bits.append(f'<span class="pill w">{75-score:.1f} pts to Extreme Greed</span>')
        left = (
            '<section class="panel"><div class="phead"><h2>Sentiment gauge</h2>'
            '<span class="pill">proxy composite, not CNN\'s index</span></div>'
            '<div class="pbody"><div class="sg" tabindex="0">'
            f'<div class="sg-head"><span>Extreme Fear &mdash; Fear &mdash; Neutral &mdash; Greed &mdash; '
            f'Extreme Greed</span><b class="num">{score:.1f}</b></div>'
            '<div class="sg-track"><div class="sg-seg xfear" style="width:25%"></div>'
            '<div class="sg-seg fear" style="width:20%"></div><div class="sg-seg neu" style="width:10%"></div>'
            '<div class="sg-seg greed" style="width:20%"></div><div class="sg-seg xgreed" style="width:25%"></div>'
            f'<div class="sg-marker" style="left:{max(0,min(100,score)):.1f}%">'
            f'<span class="sg-val">{score:.1f}</span></div></div>'
            '<div class="sg-labels"><span>0</span><span>25</span><span>45</span><span>55</span>'
            '<span>75</span><span>100</span></div>'
            f'<div class="sg-dist">{"".join(dist_bits)}</div>'
            '<div class="sg-comp">' + "".join(
                f'<span class="scc">{esc(k)} <b>{v}</b></span>' for k, v in comp.items())
            + '</div></div></div></section>')

    if market_inputs:
        es = market_inputs.get("es_f_chg_pct")
        nq = market_inputs.get("nq_f_chg_pct")
        asia = market_inputs.get("asia_block") or {}
        smh_chg = market_inputs.get("smh_chg_pct")
        gate = market_inputs.get("gate_classification")
        gate_reason = market_inputs.get("gate_reason", "")
        asia_str = " &middot; ".join(
            f'{name.upper()} <span class="db {"pos" if v.get("chg_pct",0)>=0 else "neg"}">{v.get("chg_pct",0):+.2f}%</span>'
            for name, v in asia.items())
        rows = []
        if es is not None or nq is not None:
            rows.append(f'<div class="row"><span class="lab">US futures (ES / NQ)</span><span class="val">'
                        f'<span class="db {"pos" if (es or 0)>=0 else "neg"}">{es:+.2f}%</span> / '
                        f'<span class="db {"pos" if (nq or 0)>=0 else "neg"}">{nq:+.2f}%</span></span></div>')
        if asia:
            rows.append(f'<div class="row"><span class="lab">Asia session (overnight)</span>'
                        f'<span class="val" style="font-size:12px">{asia_str}</span></div>')
        if smh_chg is not None:
            rows.append(f'<div class="row"><span class="lab">Book benchmark (SMH)</span><span class="val">'
                        f'<span class="db {"pos" if smh_chg>=0 else "neg"}">{smh_chg:+.2f}%</span></span></div>')
        sub = (f'<div class="value-sub">Gate: <b>{esc(gate)}</b> &mdash; {esc(gate_reason)}</div>'
               if gate else "")
        right = ('<section class="panel"><div class="phead"><h2>Intraday &amp; international session</h2></div>'
                 f'<div class="pbody"><div class="kv">{"".join(rows)}</div>{sub}</div></section>')

    if left or right:
        H.append(f'<div class="grid2">{left}{right}</div>')

    # ================= the week ahead =================
    earnings_cal = state.get("data_cache", {}).get("earnings_calendar", {})
    fomc = state.get("fomc_cache", {})
    try:
        today = datetime.strptime(ts[:10], "%Y-%m-%d").date() if ts else datetime.now().date()
    except ValueError:
        today = datetime.now().date()
    by_date = {}
    for tk, e in earnings_cal.items():
        by_date.setdefault(e.get("date"), []).append((tk, e.get("confirmed", False)))
    fomc_date = fomc.get("next_check_date")

    days = []
    for i in range(6):
        d = today + timedelta(days=i)
        ds = d.isoformat()
        events = []
        hot = False
        for tk, confirmed in by_date.get(ds, []):
            cls = "" if confirmed else " est"
            events.append(f'<span class="ev{cls}">{esc(tk)}{"" if confirmed else " (est.)"}</span>')
            hot = True
        if ds == fomc_date:
            events.insert(0, '<span class="ev">FOMC decision</span>')
            hot = True
        label = "Today" if i == 0 else d.strftime("%a %-d")
        days.append(f'<div class="day{" hot" if hot else ""}"><span class="d">{esc(label)}</span>'
                    + "".join(events) + '</div>')
    H.append('<section class="panel"><div class="phead"><h2>The week ahead</h2></div>'
             f'<div class="pbody"><div class="cal">{"".join(days)}</div></div></section>')

    # ================= TIER: BOOK COMPOSITION =================
    H.append('<div class="tier"><h2>Book composition</h2><div class="ln"></div></div>')

    H.append(fig(ch.get("treemap"), "Allocation treemap",
                 "size = weight &middot; color = cluster &middot; red outline = over risk cap"))

    cluster_table = drift.get("cluster_table", [])
    clusters_html = ""
    if cluster_table:
        rows = []
        for c in sorted(cluster_table, key=lambda r: -r.get("actual_pct_of_equity", r.get("actual_pct", 0))):
            band_c = c.get("band_pct") or [0, 100]
            lo, hi = band_c[0] or 0, band_c[1] or 100
            actual = c.get("actual_pct_of_equity", c.get("actual_pct", 0))
            tgt = c.get("target_pct") or 0
            scale = max(hi, actual, tgt, 1) * 1.15
            pc = lambda v: max(0, min(100, v / scale * 100))
            breach = c.get("breach")
            rows.append(
                f'<tr><td class="name">{esc(c.get("cluster",""))}</td>'
                f'<td>{actual:.2f}%</td>'
                f'<td class="{"neg" if breach else "pos"}">{c.get("actual_pct_of_total_book",0):.2f}%</td>'
                f'<td class="blank">[{lo:g},{hi:g}]</td>'
                f'<td><div class="band"><div class="ok" style="left:{pc(lo):.1f}%;width:{pc(hi)-pc(lo):.1f}%"></div>'
                f'<div class="tgt" style="left:{pc(tgt):.1f}%"></div>'
                f'<div class="mk{" bad" if breach else ""}" style="left:{pc(actual):.1f}%"></div></div></td></tr>')
        clusters_html = ('<section class="panel"><div class="phead"><h2>Clusters</h2>'
                         '<span class="pill">ceiling on book &middot; floor on equity</span></div>'
                         '<div class="pbody"><div class="scroll"><table><thead><tr><th>Cluster</th>'
                         '<th>Equity</th><th>Book</th><th>Band</th><th style="width:150px"></th></tr></thead>'
                         f'<tbody>{"".join(rows)}</tbody></table></div></div></section>')

    risk_rows = sorted([r for r in risk.get("positions", []) if r.get("over_cap")],
                       key=lambda r: (r.get("headroom_usd") or 0))
    riskcap_html = ""
    if risk_rows:
        rows = "".join(
            f'<tr><td class="name">{esc(r["ticker"])}</td><td>${r.get("market_value_usd",0):,.0f}</td>'
            f'<td class="blank">${r.get("max_position_usd",0):,.0f}</td>'
            f'<td class="neg">{r.get("cap_multiple",0):.2f}x</td>'
            f'<td class="neg" style="font-weight:640">${abs(r.get("headroom_usd",0)):,.0f}</td></tr>'
            for r in risk_rows)
        riskcap_html = (f'<section class="panel"><div class="phead"><h2>Risk-cap breaches</h2>'
                        f'<span class="pill w">{len(risk_rows)} names</span></div>'
                        '<div class="pbody"><div class="scroll"><table><thead><tr><th>Name</th><th>Held</th>'
                        '<th>Cap</th><th>&times;</th><th>Excess</th></tr></thead>'
                        f'<tbody>{rows}</tbody></table></div>'
                        '<p class="note">Cap = 0.5% of book &divide; that name\'s 2&times;ATR20 stop.</p>'
                        '</div></section>')

    if clusters_html or riskcap_html:
        H.append(f'<div class="grid2">{clusters_html}{riskcap_html}</div>')

    risk_by_ticker = {r["ticker"]: r for r in risk.get("positions", [])}
    holdings = sorted(state.get("holdings", []), key=lambda h: -(h.get("weight_pct") or 0))
    if holdings:
        tot_value = sum((risk_by_ticker.get(h["ticker"], {}).get("market_value_usd") or 0) for h in holdings)
        tot_weight = sum(h.get("weight_pct", 0) for h in holdings)
        rows = []
        for h in holdings:
            tk, qty = h["ticker"], h.get("qty", 0)
            r = risk_by_ticker.get(tk, {})
            mv = r.get("market_value_usd")
            price = (mv / qty) if (mv and qty) else None
            atr = r.get("atr20_pct")
            beta = r.get("beta")
            stop_pct = r.get("stop_distance_pct")
            stop_px = r.get("stop_price_usd")
            capv = r.get("max_position_usd")
            head = r.get("headroom_usd")
            beta_cls = "neg" if (beta is not None and beta >= 1.5) else ("pos" if (beta is not None and beta <= 0.6) else "")
            head_cls = "neg" if (head is not None and head < 0) else "pos"
            c_price = f'{price:.2f}' if price is not None else "&mdash;"
            c_value = f'${mv:,.0f}' if mv is not None else "&mdash;"
            c_atr = f'{atr:.2f}%' if atr is not None else "&mdash;"
            c_beta = f'{beta:.3f}' if beta is not None else "&mdash;"
            c_stop = f'{stop_pct:.1f}%' if stop_pct is not None else "&mdash;"
            c_stoppx = f'{stop_px:.2f}' if stop_px is not None else "&mdash;"
            c_cap = f'${capv:,.0f}' if capv is not None else "&mdash;"
            c_head = f'{"&minus;" if (head is not None and head<0) else ""}${abs(head):,.0f}' if head is not None else "&mdash;"
            c_weight = f'{h.get("weight_pct",0):.2f}%'
            rows.append(
                f'<tr><td class="name">{esc(tk)}</td><td class="txt">{esc(sector_map.get(tk,"-"))}</td>'
                f'<td>{qty:g}</td><td>{c_price}</td><td>{c_value}</td><td class="blank">{c_weight}</td>'
                f'<td class="blank">{c_atr}</td><td class="{beta_cls}">{c_beta}</td>'
                f'<td>{c_stop}</td><td>{c_stoppx}</td><td class="blank">{c_cap}</td>'
                f'<td class="{head_cls}" style="font-weight:640">{c_head}</td></tr>')

        agg_risk_pct = risk.get("aggregate_open_risk_pct")
        beta_book = book_compute.get("beta") or book_compute.get("primary_benchmark", {}).get("primary_beta")
        c_beta_book = f'<td class="pos">{beta_book:.3f}</td>' if beta_book is not None else '<td></td>'
        c_risk_foot = (f'<td colspan="3" class="blank" style="text-align:right">aggregate open risk</td>'
                      f'<td class="neg">{agg_risk_pct:.1f}%</td>' if agg_risk_pct is not None
                      else '<td colspan="4"></td>')
        foot = (f'<tfoot><tr><td class="name">Book</td><td class="txt"></td><td></td><td></td>'
               f'<td>${tot_value:,.0f}</td><td class="blank">{tot_weight:.1f}%</td><td class="blank"></td>'
               f'{c_beta_book}{c_risk_foot}</tr></tfoot>')

        H.append(f'<section class="panel"><div class="phead"><h2>Positions<span class="sub">'
                 f'{len(holdings)}</span></h2></div><div class="pbody"><div class="scroll"><table>'
                 '<thead><tr><th>Name</th><th>Cluster</th><th>Qty</th><th>Price</th><th>Value</th><th>Wt</th>'
                 '<th>ATR20</th><th>&beta;</th><th>Stop</th><th>Stop px</th><th>Cap</th><th>Headroom</th></tr></thead>'
                 f'<tbody>{"".join(rows)}</tbody>{foot}</table></div></div></section>')

    # ================= TIER: DIAGNOSTICS =================
    H.append('<div class="tier"><h2>Diagnostics</h2><div class="ln"></div></div>')
    H.append('<div class="t3">')

    # -- thesis map, grouped by status --
    thesis = state.get("thesis", {})
    if thesis:
        groups = {"strengthening": [], "watch": [], "broken": []}
        other = []
        for tk, txt in thesis.items():
            body, _, status = txt.rpartition("|")
            st = status.strip().lower() if status else ""
            (groups.get(st) or other).append((tk, body.strip()))
        dotcls = {"strengthening": "dot-g", "watch": "dot-w", "broken": "dot-b"}
        blocks = []
        for st in ("strengthening", "watch", "broken"):
            items = groups[st]
            if not items:
                continue
            chips = "".join(
                f'<span class="chip" title="{esc(body[:220])}">{esc(tk)}<i>{esc(sector_map.get(tk,"-"))}</i></span>'
                for tk, body in sorted(items))
            blocks.append(f'<div class="grp-h"><span class="{dotcls[st]}"></span>{st.title()}</div>'
                          f'<div class="chips" style="margin-bottom:12px">{chips}</div>')
        H.append(f'<details><summary>Thesis map<span class="c">{len(thesis)} held</span></summary>'
                 f'<div class="body">{"".join(blocks)}'
                 f'<p class="note" style="margin-top:8px">Hover any ticker for its thesis.</p></div></details>')

    # -- signal history, grouped bullish/bearish --
    signal_history = {k: v for k, v in (state.get("signal_history") or {}).items() if v}
    if signal_history:
        by_bucket = {}
        for tk, buckets in signal_history.items():
            for b in buckets:
                by_bucket.setdefault(b, []).append(tk)
        bull_rows, bear_rows = [], []
        for bucket in sorted(smith_risk.SIGNAL_POLARITY["bullish"]):
            tks = by_bucket.get(bucket)
            if not tks:
                continue
            ticks = "".join(f'<span class="tick g{" gone" if tk not in held_tickers else ""}">{esc(tk)}</span>'
                            for tk in sorted(tks))
            bull_rows.append(f'<div class="srow"><span class="slab">{bucket.title()}</span>'
                             f'<span class="sch">{ticks}</span></div>')
        for bucket in sorted(smith_risk.SIGNAL_POLARITY["bearish"]):
            tks = by_bucket.get(bucket)
            if not tks:
                continue
            ticks = "".join(f'<span class="tick b{" gone" if tk not in held_tickers else ""}">{esc(tk)}</span>'
                            for tk in sorted(tks))
            bear_rows.append(f'<div class="srow"><span class="slab">{bucket.title()}</span>'
                             f'<span class="sch">{ticks}</span></div>')
        body = ""
        if bull_rows:
            body += f'<div class="grp-h"><span class="dot-g"></span>Bullish</div>{"".join(bull_rows)}'
        if bear_rows:
            body += f'<div class="grp-h" style="margin-top:14px"><span class="dot-b"></span>Bearish</div>{"".join(bear_rows)}'
        body += '<p class="note" style="margin-top:10px">Struck-through tickers are no longer held.</p>'
        H.append(f'<details><summary>Signal history<span class="c">bullish / bearish</span></summary>'
                 f'<div class="body">{body}</div></details>')

    # -- open (non-closed) data gaps --
    gaps = [g for g in state.get("known_gaps", []) if g.get("status") not in ("closed", "wont_fix")]
    if gaps:
        rows = "".join(f'<div class="srow"><span class="slab"><b>{esc(g.get("id",""))}</b></span>'
                       f'<span style="font-size:12.5px;color:var(--ink-2)">{esc(g.get("description",""))[:280]}</span></div>'
                       for g in gaps)
        H.append(f'<details><summary>Open data gaps<span class="c">{len(gaps)} open</span></summary>'
                 f'<div class="body">{rows}</div></details>')

    H.append('</div>')  # /t3

    # -- historical charts, separate collapsed panel --
    hist_charts = "".join([
        fig(ch.get("bookvalue"), "Book value & cash", "every ledger row"),
        fig(ch.get("drawdown"), "Drawdown vs trim ladder", "pre-committed rungs"),
        fig(ch.get("relative"), "Book vs SMH", "per period, clean data only"),
        fig(ch.get("weights"), "Position weights", f"against the {cap}% cap"),
    ])
    if hist_charts:
        H.append('<section class="panel"><div class="pbody" style="gap:0">'
                 '<details><summary>Historical charts<span class="c">ledger &middot; drawdown &middot; '
                 'benchmark &middot; weights</span></summary>'
                 f'<div class="body" style="display:flex;flex-direction:column;gap:26px">{hist_charts}</div>'
                 '</details></div></section>')

    # ---------------- footer ----------------
    confirm_flags = [f for f in state.get("open_flags", [])
                     if "RISK-CAP" not in f.get("ticker", "").upper()
                     and "risk cap" not in f.get("flag", "").lower()]
    hz = mandate.get("horizon_years", "-")
    hz = f'{hz[0]}-{hz[1]}' if isinstance(hz, list) and len(hz) == 2 else str(hz)
    H.append('<footer>')
    H.append('<p class="note"><b>Everything here is a proposal for your review.</b> No trade has been or '
             'will be placed by this desk, and none of it is licensed investment advice.</p>')
    if confirm_flags:
        bits = "; ".join(f'<b>{esc(f.get("ticker",""))}</b> &mdash; {esc(f.get("flag",""))[:200]}' for f in confirm_flags[:3])
        H.append(f'<p class="note">Needs confirmation: {bits}</p>')
    H.append(f'<p class="note">Mandate: {esc(str(mandate.get("objective","-")).replace("_"," "))} &middot; '
             f'horizon {esc(hz)}y &middot; benchmark {esc(mandate.get("benchmark","-"))} &middot; '
             f'risk budget {esc(str(mandate.get("risk_budget_pct","-")))}%.</p>')
    H.append('</footer>')

    H.append('</div></body></html>')

    html = "\n".join(H)
    with open(out, "w") as f:
        f.write(html)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=DEFAULT_BASE)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(a.base_dir, "dashboard.html")
    html = build(a.base_dir, out)
    print(json.dumps({"written": out, "bytes": len(html)}))


if __name__ == "__main__":
    main()

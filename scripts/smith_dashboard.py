#!/usr/bin/env python3
"""
Agent Smith dashboard builder -- assembles dashboard.html from state files + charts.

Replaces hand-writing 66KB of HTML per run. Everything derivable from state.json /
policy.json / ledger.csv / proposals.json is rendered here deterministically; the
per-run judgment content (headline, session read, signal one-liners) comes from an
optional narrative.json the orchestrator writes.

STRUCTURE -- three tiers, decision-first (the old layout was 16 flat sections at
equal weight with proposals buried at #11):
  TIER 1  DECISIONS   what needs a call, always open
  TIER 2  BOOK STATE  the charts, always open
  TIER 3  DIAGNOSTICS thesis / signals / gaps, collapsed by default

Prose rule: one sentence inline, anything longer goes inside <details>. The chat
briefing is the place for narrative; this page is for scanning.

Usage:  smith_dashboard.py --base-dir DIR [--out dashboard.html]
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime

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
    """One chart block: title, legend, svg, note."""
    if not d or not d.get("svg"):
        return ""
    leg = ""
    if d.get("legend"):
        leg = ('<div class="viz-legend">' + "".join(
            f'<span><i style="background:{c}"></i>{esc(l)}</span>' for c, l in d["legend"])
            + "</div>")
    s = f'<span class="sub">{esc(sub)}</span>' if sub else ""
    return (f'<section class="card viz"><h2>{esc(title)}{s}</h2>{leg}{d["svg"]}'
            f'<div class="viz-note">{esc(d.get("note",""))}</div></section>')


CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
     -webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:32px 24px 72px}
:root{--bg:#f4f5f3;--panel:#fff;--ink:#14181c;--ink-2:#4a5157;--ink-3:#7c8389;
  --line:#dde1e2;--line-soft:#e8eaea;--accent:#3a5a6b;--accent-soft:#e6edef;
  --good:#0ca30c;--warn:#fab219;--bad:#d03b3b;--good-bg:#e5f2e9;--warn-bg:#fbf0dd;--bad-bg:#f7e6e6;
  --mono:ui-monospace,"SF Mono",Consolas,monospace;
  --serif:"Iowan Old Style",Palatino,Georgia,serif;
  --sans:-apple-system,"Segoe UI",Inter,Roboto,sans-serif}
@media(prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){
  --bg:#0f1113;--panel:#171a1d;--ink:#e8eaec;--ink-2:#a7adb2;--ink-3:#71787d;
  --line:#2a2e32;--line-soft:#232629;--accent:#7fa8bd;--accent-soft:#1b2a30;
  --good-bg:#16261c;--warn-bg:#2c2410;--bad-bg:#2c1717}}
:root[data-theme="dark"]{--bg:#0f1113;--panel:#171a1d;--ink:#e8eaec;--ink-2:#a7adb2;
  --ink-3:#71787d;--line:#2a2e32;--line-soft:#232629;--accent:#7fa8bd;
  --accent-soft:#1b2a30;--good-bg:#16261c;--warn-bg:#2c2410;--bad-bg:#2c1717}

.masthead{display:flex;justify-content:space-between;align-items:baseline;gap:16px;
  border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:22px;flex-wrap:wrap}
.masthead h1{font-family:var(--serif);font-weight:500;font-size:25px;margin:0}
.masthead .meta{text-align:right;color:var(--ink-2);font-size:12.5px;line-height:1.6}
.masthead .meta b{color:var(--ink)}

.statusstrip{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}

.tier{margin:30px 0 12px;display:flex;align-items:center;gap:12px}
.tier h2{font-family:var(--serif);font-size:13px;font-weight:600;margin:0;
  text-transform:uppercase;letter-spacing:1.4px;color:var(--ink-3);white-space:nowrap}
.tier .rule{flex:1;height:1px;background:var(--line)}

.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:18px 20px;margin-bottom:14px}
.card h2{font-family:var(--serif);font-weight:500;font-size:14px;margin:0 0 12px;
  text-transform:uppercase;letter-spacing:.6px}
.card h2 .sub{text-transform:none;font-family:var(--sans);font-weight:400;
  letter-spacing:0;color:var(--ink-3);font-size:12px;margin-left:8px}

.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;
  margin-bottom:14px}
.kpi .card{margin:0;padding:15px 17px}
.kpi .k{font-size:11px;color:var(--ink-3);text-transform:uppercase;letter-spacing:.6px}
.kpi .v{font-family:var(--mono);font-size:25px;font-weight:600;margin-top:5px;
  font-variant-numeric:tabular-nums;letter-spacing:-.5px}
.kpi .d{font-size:11.5px;color:var(--ink-2);margin-top:3px}

.pill{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:99px;
  font-size:11.5px;font-weight:600}
.pill::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
.pill.good{background:var(--good-bg);color:var(--good)}
.pill.warn{background:var(--warn-bg);color:var(--warn)}
.pill.bad{background:var(--bad-bg);color:var(--bad)}
.pill.neutral{background:var(--accent-soft);color:var(--accent)}

.decision{display:grid;grid-template-columns:30px 1fr auto;gap:13px;padding:13px 0;
  border-bottom:1px solid var(--line-soft);align-items:start}
.decision:last-child{border-bottom:none}
.decision .n{font-family:var(--mono);font-size:12px;color:var(--ink-3);
  border:1px solid var(--line);border-radius:5px;text-align:center;padding:2px 0}
.decision .t{font-size:13.5px;font-weight:600;line-height:1.45}
.decision .why{font-size:12px;color:var(--ink-2);margin-top:3px;line-height:1.5}
.decision .amt{font-family:var(--mono);font-size:13px;white-space:nowrap;text-align:right}

details{border-top:1px solid var(--line-soft);padding-top:9px;margin-top:9px}
details>summary{cursor:pointer;font-size:12px;color:var(--ink-3);list-style:none;
  user-select:none}
details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"▸ ";color:var(--ink-3)}
details[open]>summary::before{content:"▾ "}
details>summary:hover{color:var(--accent)}
details .body{font-size:12.5px;color:var(--ink-2);line-height:1.6;padding:9px 0 3px}

.t3 .card{padding:0}
.t3 details{border-top:none;margin:0;padding:0}
.t3 details>summary{padding:15px 20px;font-size:13.5px;color:var(--ink);font-weight:600;
  font-family:var(--serif)}
.t3 details[open]>summary{border-bottom:1px solid var(--line-soft)}
.t3 details .body{padding:14px 20px 17px}
.t3 summary .c{font-family:var(--mono);font-size:11px;color:var(--ink-3);font-weight:400;
  margin-left:7px}

table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;
  color:var(--ink-3);font-weight:600;padding:7px 9px;border-bottom:1px solid var(--line)}
td{padding:7px 9px;border-bottom:1px solid var(--line-soft)}
tr:last-child td{border-bottom:none}
td.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
td.tk{font-family:var(--mono);font-weight:700;white-space:nowrap}
.table-wrap{overflow-x:auto}
.foot{margin-top:34px;padding-top:16px;border-top:1px solid var(--line);
  font-size:11.5px;color:var(--ink-3);line-height:1.65}
"""


def build(base, out):
    state = load(os.path.join(base, "state.json"), {}) or {}
    policy = load(os.path.join(base, "policy.json"), {}) or {}
    props = load(os.path.join(base, "proposals.json"), {}) or {}
    narr = load(os.path.join(base, "narrative.json"), {}) or {}
    ch = charts(base)

    # Latest run's compute outputs, if available -- optional, graceful degradation.
    last_run_dir = state.get("last_run_dir", "")
    drift = load(os.path.join(base, last_run_dir, "compute_drift.json"), {}) or {} if last_run_dir else {}
    market_inputs = load(os.path.join(base, last_run_dir, "market_inputs.json"), {}) or {} if last_run_dir else {}

    us = state.get("us", {})
    equity = us.get("value_usd") or 0
    cash = us.get("wallet_usd") or 0
    total = equity + cash
    peak = us.get("peak_total_book_usd") or total
    dd = (total - peak) / peak * 100 if peak else 0
    cash_pct = cash / total * 100 if total else 0
    band = policy.get("cash_band_pct", [3, 15])
    mandate = policy.get("mandate", {})
    ts = state.get("ts", "")

    H = []
    H.append(f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
             f'<meta name="viewport" content="width=device-width,initial-scale=1">'
             f'<title>Agent Smith - US Book</title><style>{CSS}{chart_css(base)}</style>'
             f'</head><body><div class="wrap">')

    # masthead
    H.append(f'<div class="masthead"><div><h1>Agent Smith &mdash; US Book</h1></div>'
             f'<div class="meta"><b>${total:,.0f}</b> total book<br>'
             f'{esc(ts[:16].replace("T"," "))} &middot; {esc(state.get("mode",""))}</div></div>')

    # ---------------- STATUS STRIP ----------------
    sentiment = state.get("sentiment", {})
    gate = market_inputs.get("gate_classification") or drift.get("gate_classification")
    ai_capex_pct = drift.get("ai_capex_pct")
    strip = []
    strip.append(('bad' if abs(dd) >= 15 else ('warn' if abs(dd) >= 10 else 'good'),
                   f'Drawdown {dd:.1f}%'))
    strip.append(('bad' if (cash_pct < band[0] or cash_pct > band[1]) else 'good',
                   f'Cash {cash_pct:.1f}%'))
    if gate:
        strip.append(({'ESCALATING': 'bad', 'AMBIGUOUS': 'warn', 'STABILIZING': 'good'}.get(gate, 'neutral'),
                       f'Gate {gate.title()}'))
    if sentiment.get("band"):
        strip.append(('neutral', f'Sentiment {esc(sentiment.get("band",""))} ({sentiment.get("score","-")})'))
    if ai_capex_pct is not None:
        strip.append(('warn' if ai_capex_pct >= 90 else 'neutral', f'AI-capex {ai_capex_pct:.0f}% of equity'))
    if strip:
        H.append('<div class="statusstrip">' + "".join(
            f'<span class="pill {cls}">{esc(txt)}</span>' for cls, txt in strip) + '</div>')

    # ---------------- TIER 1 : DECISIONS ----------------
    H.append('<div class="tier"><h2>Decisions</h2><div class="rule"></div></div>')

    open_props = [p for p in props.get("proposals", []) if p.get("status") == "open"]
    breaches = []
    cap = policy.get("max_single_position_pct", 12)
    for h in state.get("holdings", []):
        if h.get("weight_pct", 0) > cap:
            breaches.append(f'{h["ticker"]} {h["weight_pct"]:.1f}% vs {cap}% cap')
    if cash_pct > band[1]:
        breaches.append(f'cash {cash_pct:.1f}% over the {band[1]}% ceiling')
    elif cash_pct < band[0]:
        breaches.append(f'cash {cash_pct:.1f}% under the {band[0]}% floor')

    H.append('<section class="card">')
    if not open_props and not breaches:
        H.append('<div style="font-size:13px;color:var(--ink-2)">'
                 'Nothing requires a decision this run.</div>')
    n = 0
    for b in breaches:
        n += 1
        H.append(f'<div class="decision"><div class="n">{n}</div><div>'
                 f'<div class="t">Breach &mdash; {esc(b)}</div>'
                 f'<div class="why">Policy limit exceeded. Either bring it inside the band '
                 f'or record why the breach is accepted.</div></div>'
                 f'<div class="amt"><span class="pill bad">breach</span></div></div>')
    for p in open_props:
        n += 1
        why = (p.get("rationale") or "").strip()
        # first sentence, but never mid-clause: trim back to a word boundary and
        # strip any dangling punctuation before adding the period.
        head = why.split(". ")[0]
        if len(head) > 150:
            head = head[:150].rsplit(" ", 1)[0]
        short = head.rstrip(" ,;:-") + ("." if why else "")
        rest = why[len(head):].strip(" .")
        more = (f'<details><summary>full rationale</summary><div class="body">'
                f'{esc(rest)}</div></details>') if len(rest) > 40 else ""
        H.append(f'<div class="decision"><div class="n">{n}</div><div>'
                 f'<div class="t">{esc(p.get("action",""))}</div>'
                 f'<div class="why">{esc(short)}</div>{more}</div>'
                 f'<div class="amt">${p.get("size_usd",0):,.0f}</div></div>')
    H.append('<div class="viz-note">Proposals are for review &mdash; nothing is ever '
             'executed automatically.</div></section>')

    # the read -- session narrative, always open, one sentence visible per the prose rule
    for key, label in (("session_read", "The read"), ("macro", "Macro")):
        text = narr.get(key)
        if not text:
            continue
        head = text.split(". ")[0]
        if len(head) > 180:
            head = head[:180].rsplit(" ", 1)[0]
        short = head.rstrip(" ,;:-") + "."
        rest = text[len(head):].strip(" .")
        more = (f'<details><summary>more</summary><div class="body">{esc(rest)}</div></details>'
                if len(rest) > 40 else "")
        H.append(f'<section class="card"><h2>{esc(label)}</h2>'
                 f'<div style="font-size:13px;color:var(--ink-2);line-height:1.55">{esc(short)}</div>'
                 f'{more}</section>')

    # factor catalysts -- named, dated, sourced events affecting the book's factor
    catalysts = state.get("factor_catalysts", [])
    if catalysts:
        rows = []
        for c in catalysts[:6]:
            dirn = c.get("direction", "")
            cls = {"threat": "bad", "tailwind": "good"}.get(dirn, "neutral")
            affects = ", ".join(c.get("affects", []))
            exp = c.get("exposure_pct_equity")
            exp_s = f'{exp:.1f}% equity' if isinstance(exp, (int, float)) else ""
            rows.append(f'<div class="decision"><div class="n" style="border:none">'
                        f'<span class="pill {cls}" style="width:100%">{esc(dirn or "-")}</span></div>'
                        f'<div><div class="t">{esc(c.get("headline",""))}</div>'
                        f'<div class="why">{esc(c.get("magnitude",""))} &mdash; affects {esc(affects)}'
                        f'{" (" + exp_s + ")" if exp_s else ""}</div></div>'
                        f'<div class="amt" style="font-size:11px;color:var(--ink-3)">{esc(c.get("date",""))}</div></div>')
        H.append('<section class="card"><h2>Factor catalysts</h2>' + "".join(rows) + '</section>')

    # ---------------- TIER 2 : BOOK STATE ----------------
    H.append('<div class="tier"><h2>Book state</h2><div class="rule"></div></div>')

    ddcls = "good" if abs(dd) < 15 else ("warn" if abs(dd) < 25 else "bad")
    cashcls = "bad" if (cash_pct < band[0] or cash_pct > band[1]) else "good"
    H.append('<div class="kpi">')
    H.append(f'<div class="card"><div class="k">Total book</div>'
             f'<div class="v">${total/1000:,.1f}k</div>'
             f'<div class="d">equity ${equity/1000:,.1f}k + cash ${cash/1000:,.1f}k</div></div>')
    H.append(f'<div class="card"><div class="k">Drawdown</div>'
             f'<div class="v" style="color:var(--{ddcls})">{dd:.2f}%</div>'
             f'<div class="d">vs peak ${peak:,.0f} &middot; budget {mandate.get("risk_budget_pct","-")}%</div></div>')
    H.append(f'<div class="card"><div class="k">Cash</div>'
             f'<div class="v" style="color:var(--{cashcls})">{cash_pct:.1f}%</div>'
             f'<div class="d">band [{band[0]},{band[1]}]% of total book</div></div>')
    H.append(f'<div class="card"><div class="k">Benchmark</div>'
             f'<div class="v" style="font-size:21px">{esc(mandate.get("benchmark","-"))}</div>'
             f'<div class="d">mandate: beat it on total return</div></div>')
    H.append('</div>')

    H.append(fig(ch.get("bookvalue"), "Book value & cash", "every ledger row"))
    H.append(fig(ch.get("drawdown"), "Drawdown vs trim ladder", "pre-committed rungs"))
    H.append(fig(ch.get("relative"), "Book vs SMH", "per period, clean data only"))
    H.append(fig(ch.get("weights"), "Position weights", f"against the {cap}% cap"))

    # clusters -- equity% and book% side by side, vs policy target/band
    cluster_table = drift.get("cluster_table", [])
    if cluster_table:
        rows = []
        for c in sorted(cluster_table, key=lambda r: -r.get("actual_pct_of_equity", r.get("actual_pct", 0))):
            breach = c.get("breach")
            cls = "bad" if breach else "good"
            band_c = c.get("band_pct", ["-", "-"])
            rows.append(f'<tr><td class="tk">{esc(c.get("cluster",""))}</td>'
                        f'<td class="num">{c.get("actual_pct_of_equity", c.get("actual_pct",0)):.1f}%</td>'
                        f'<td class="num">{c.get("actual_pct_of_total_book", 0):.1f}%</td>'
                        f'<td class="num">{c.get("target_pct",0):.0f}%</td>'
                        f'<td class="num" style="color:var(--ink-3)">[{band_c[0]},{band_c[1]}]%</td>'
                        f'<td><span class="pill {cls}">{"breach" if breach else "ok"}</span></td></tr>')
        H.append('<section class="card"><h2>Clusters</h2><div class="table-wrap"><table>'
                 '<thead><tr><th>Cluster</th><th>% equity</th><th>% book</th><th>Target</th>'
                 '<th>Band</th><th>Status</th></tr></thead><tbody>' + "".join(rows)
                 + '</tbody></table></div></section>')

    # risk-cap breaches -- qualitative flag from open_flags (structured ATR-based caps
    # require live ATR20, refreshed on deep runs only; rendered as-flagged, not recomputed)
    risk_flags = [f for f in state.get("open_flags", [])
                  if "RISK-CAP" in f.get("ticker", "").upper() or "risk cap" in f.get("flag", "").lower()]
    if risk_flags:
        rows = "".join(f'<tr><td class="tk">{esc(f.get("ticker",""))}</td>'
                       f'<td>{esc(f.get("flag",""))}</td>'
                       f'<td style="color:var(--ink-3);font-size:11px;white-space:nowrap">{esc(f.get("opened",""))}</td></tr>'
                       for f in risk_flags)
        H.append('<section class="card"><h2>Risk-cap breaches</h2><div class="table-wrap"><table>'
                 '<tbody>' + rows + '</tbody></table></div></section>')

    # full positions table
    holdings = sorted(state.get("holdings", []), key=lambda h: -h.get("weight_pct", 0))
    if holdings:
        rows = "".join(f'<tr><td class="tk">{esc(h.get("ticker",""))}</td>'
                       f'<td class="num">{h.get("qty",0):g}</td>'
                       f'<td class="num">{h.get("weight_pct",0):.2f}%</td></tr>'
                       for h in holdings)
        H.append('<section class="card"><h2>Positions<span class="sub">'
                 f'{len(holdings)} names</span></h2><div class="table-wrap"><table>'
                 '<thead><tr><th>Ticker</th><th>Qty</th><th>Weight</th></tr></thead>'
                 '<tbody>' + rows + '</tbody></table></div></section>')

    # ---------------- TIER 3 : DIAGNOSTICS ----------------
    H.append('<div class="tier"><h2>Diagnostics</h2><div class="rule"></div></div>')
    H.append('<div class="t3">')

    # thesis
    thesis = state.get("thesis", {})
    smap = state.get("sector_map", {})
    if thesis:
        rows = []
        for tk, txt in sorted(thesis.items(), key=lambda kv: smap.get(kv[0], "zz")):
            body, _, status = txt.rpartition("|")
            st = status.strip().lower()
            cls = {"strengthening": "good", "broken": "bad", "watch": "warn"}.get(st, "neutral")
            rows.append(f'<tr><td class="tk">{esc(tk)}</td>'
                        f'<td style="color:var(--ink-3);font-size:11.5px">'
                        f'{esc(smap.get(tk,"-"))}</td>'
                        f'<td>{esc(body.strip()[:110])}</td>'
                        f'<td><span class="pill {cls}">{esc(st)}</span></td></tr>')
        H.append(f'<section class="card"><details><summary>Thesis map'
                 f'<span class="c">{len(thesis)} held</span></summary><div class="body">'
                 f'<div class="table-wrap"><table><thead><tr><th>Ticker</th><th>Cluster</th>'
                 f'<th>Thesis</th><th>Status</th></tr></thead><tbody>'
                 + "".join(rows) + '</tbody></table></div></div></details></section>')

    # signals
    sig = {k: v for k, v in (state.get("signal_history") or {}).items() if v}
    if sig:
        items = "".join(
            f'<tr><td class="tk">{esc(k)}</td><td>{esc(", ".join(v))}</td></tr>'
            for k, v in sorted(sig.items()))
        H.append(f'<section class="card"><details><summary>Signal history'
                 f'<span class="c">{len(sig)} names</span></summary><div class="body">'
                 f'<div class="table-wrap"><table><tbody>{items}</tbody></table></div>'
                 f'</div></details></section>')

    # gaps
    gaps = state.get("known_gaps", [])
    if gaps:
        gi = "".join(f'<tr><td class="tk">{esc(g.get("id",""))}</td>'
                     f'<td>{esc(g.get("description",""))}</td></tr>' for g in gaps)
        H.append(f'<section class="card"><details><summary>Open data gaps'
                 f'<span class="c">{len(gaps)}</span></summary><div class="body">'
                 f'<div class="table-wrap"><table><tbody>{gi}</tbody></table></div>'
                 f'</div></details></section>')

    H.append('</div>')  # /t3

    hz = mandate.get("horizon_years", "-")
    hz = f'{hz[0]}-{hz[1]}' if isinstance(hz, list) and len(hz) == 2 else str(hz)
    H.append(f'<div class="foot">Mandate: '
             f'{esc(str(mandate.get("objective","-")).replace("_"," "))} &middot; '
             f'horizon {esc(hz)}y &middot; '
             f'benchmark {esc(mandate.get("benchmark","-"))} &middot; '
             f'risk budget {esc(str(mandate.get("risk_budget_pct","-")))}%.<br>'
             f'Analysis only &mdash; Agent Smith never places trades. '
             f'Not investment advice.</div>')
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

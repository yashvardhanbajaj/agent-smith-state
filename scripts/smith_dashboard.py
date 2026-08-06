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
.pr{display:grid;grid-template-columns:76px 1fr auto;gap:12px;padding:11px 0;border-bottom:1px solid var(--line-soft);align-items:baseline}
.pr:last-child{border-bottom:none}
.pr .act2{font-family:var(--mono);font-size:12px;font-weight:700;display:flex;flex-direction:column;gap:4px;align-items:flex-start}
.pr .why{font-size:12.5px;color:var(--ink-2);line-height:1.45}
.pr .amt{font-family:var(--mono);font-weight:700;color:var(--action)}
.pr .meta{display:block;font-family:var(--mono);font-size:10.5px;font-weight:400;color:var(--ink-3);margin-top:5px}
.pr .meta .pid{margin-left:8px}
/* direction badge -- same visual language as the factor-catalyst .cb badges below */
.dirb{font-size:9.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:2px 6px;border-radius:4px}
.dirb.BUY{background:var(--good-soft);color:var(--good)}
.dirb.SELL{background:var(--bad-soft);color:var(--bad)}
.dirb.TRIM{background:var(--warn-soft);color:var(--warn)}
.dirb.HOLD{background:var(--surface-2);color:var(--ink-3)}
.pr .amt.BUY{color:var(--good)} .pr .amt.SELL{color:var(--bad)} .pr .amt.TRIM{color:var(--warn)}
/* priority groups -- collapsible, reusing the details/summary idiom used elsewhere on this
   dashboard (see "tiers / details" above) rather than inventing a second expand pattern */
details.pgrp{border-top:1px solid var(--line-soft)}
details.pgrp:first-of-type{border-top:none}
details.pgrp>summary{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;padding:12px 0}
details.pgrp.HIGH>summary{color:var(--bad)}
details.pgrp.MEDIUM>summary{color:var(--warn)}
details.pgrp.LOW>summary{color:var(--ink-3)}
details.pgrp>summary .n{background:var(--surface-2);color:var(--ink-2);border-radius:10px;padding:1px 8px;
  font-family:var(--mono);margin-left:8px;text-transform:none;letter-spacing:normal;font-weight:400}
details.pgrp>.body{padding:0 0 4px}
.pr .clus{font-family:var(--sans);font-size:10px;color:var(--ink-3);font-weight:500}
/* live re-justification -- recomputed every run, visually distinct from the frozen rationale
   above it so "why this is still here TODAY" never reads as part of the original prose */
.pr .lives{display:flex;flex-direction:column;gap:3px;margin-top:7px}
.pr .lv{font-family:var(--mono);font-size:11px;color:var(--good);line-height:1.4}
.pr .lv::before{content:"live ";color:var(--ink-3);font-weight:700;letter-spacing:.06em}
.pr .rvf{display:block;font-family:var(--mono);font-size:11px;color:var(--warn);
  line-height:1.4;margin-top:5px}
.pr .rtw{display:block;font-family:var(--mono);font-size:10.5px;color:var(--ink-3);
  line-height:1.4;margin-top:5px;font-style:italic}

/* ============ stop-loss efficacy ============ */
.stops-sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:var(--r);overflow:hidden;margin-bottom:4px}
.stops-sum .c{background:var(--surface);padding:10px 12px;display:flex;flex-direction:column;gap:3px}
.stops-sum .c .k{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3)}
.stops-sum .c .v{font-family:var(--mono);font-size:16px;font-weight:640}
.stops-sum .c .v.pos{color:var(--good)} .stops-sum .c .v.neg{color:var(--bad)}
.cohort-row{display:flex;gap:18px;flex-wrap:wrap;padding:9px 0;border-bottom:1px solid var(--line-soft);
  font-size:12.5px;align-items:baseline}
.cohort-row:last-child{border-bottom:none}
.cohort-row b{font-family:var(--mono);text-transform:uppercase;font-size:11px;letter-spacing:.06em;
  color:var(--ink-2);min-width:82px;display:inline-block}
.cohort-row .m{color:var(--ink-3)}
td.verd-hurt{color:var(--bad);font-weight:640} td.verd-saved{color:var(--good);font-weight:640}
td.verd-flat{color:var(--ink-3)}
.cohort-tag{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
  padding:1px 5px;border-radius:3px;background:var(--surface-2);color:var(--ink-3)}
.cohort-tag.cascade{background:var(--bad-soft);color:var(--bad)}

/* ============ execution log ============ */
.exec-row{display:grid;grid-template-columns:78px 46px 1fr auto;gap:10px;padding:7px 0;
  border-bottom:1px solid var(--line-soft);align-items:baseline;font-size:12px}
.exec-row:last-child{border-bottom:none}
.exec-row .d{font-family:var(--mono);color:var(--ink-3);font-size:11px}
.exec-row .t{font-family:var(--mono);font-weight:700}
.exec-row .rsn{color:var(--ink-2)}
.exec-row .px{font-family:var(--mono);text-align:right}
.exec-row .px.buy{color:var(--good)} .exec-row .px.sell{color:var(--bad)}

/* ============ LTCG watch ============ */
.ltcg-row{display:flex;justify-content:space-between;gap:12px;padding:7px 0;
  border-bottom:1px solid var(--line-soft);font-size:12.5px;align-items:baseline}
.ltcg-row:last-child{border-bottom:none}
.ltcg-row .past{color:var(--bad);font-weight:640}
.ltcg-row .soon{color:var(--warn);font-weight:640}

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

/* ============ de-risk queue meters ============ */
.mbar{display:inline-block;width:52px;height:6px;border-radius:3px;background:var(--grid);
  vertical-align:middle;overflow:hidden}
.mbar i{display:block;height:100%;border-radius:3px}
.mbar i.f{background:var(--critical)}
.mbar i.s{background:var(--warning)}
.mbar i.x{background:var(--ink-3)}
.pill.warn{color:var(--warning);border-color:var(--warning)}
.pill.bad{color:var(--critical);border-color:var(--critical)}
.pill.good{color:var(--good);border-color:var(--good)}

/* ============ misc ============ */
.note{font-size:12.5px;color:var(--ink-3);line-height:1.55}
.note b{color:var(--ink-2)}
.rule{height:1px;background:var(--line-soft);border:0;margin:0}
footer{border-top:1px solid var(--line);padding-top:18px;display:flex;flex-direction:column;gap:10px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
"""


def status_strip(us, dd, cash_pct, cash_band, cash_breach, risk, drift, book_compute):
    ai_capex_pct = drift.get("ai_capex_pct")
    prior_ai = drift.get("ai_capex_pct_prior")  # optional, not always present
    open_risk_pct = risk.get("aggregate_open_risk_pct")
    open_risk_cap = risk.get("aggregate_open_risk_cap_pct")
    open_risk_over = risk.get("aggregate_over_cap")

    cells = []
    cells.append(("", "Total book", f'${(us.get("value_usd",0) or 0)+(us.get("wallet_usd",0) or 0):,.0f}', "equity + wallet"))
    cells.append(("", "Equity", f'${us.get("value_usd",0) or 0:,.0f}', f'{us.get("count","-")} positions'))
    # P&L / day-change (added 2026-08-06, dashboard feature review: the status strip had six
    # cells and NONE of them was return -- book/cash/drawdown/risk/AI-capex all describe the
    # book's shape, nothing said how it's doing). pnl_pct is INDmoney's own invested-vs-current
    # aggregate (compute_book.json, already computed, never rendered). day_chg_pct_weighted is
    # optional -- only present when the run's holdings.json carried a day_chg_pct per position
    # (a live-quote overlay, not always fetched) -- so this cell simply doesn't render rather
    # than showing a stale or fabricated number when that data wasn't gathered this run.
    pnl_pct = book_compute.get("pnl_pct")
    if pnl_pct is not None:
        cells.append(("okc" if pnl_pct >= 0 else "flag", "P&L",
                      f'{pnl_pct:+.2f}%', "vs invested"))
    day_chg = book_compute.get("day_chg_pct_weighted")
    if day_chg is not None:
        cells.append(("okc" if day_chg >= 0 else "flag", "Today",
                      f'{day_chg:+.2f}%', "book-weighted"))
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
    stops_data = load(os.path.join(base, "stops_analysis.json"), {}) or {}
    trades_data = load(os.path.join(base, "trades.json"), {}) or {}
    ch = charts(base)

    last_run_dir = state.get("last_run_dir", "")

    def run_file(name):
        return load(os.path.join(base, last_run_dir, name), {}) or {} if last_run_dir else {}

    drift = run_file("compute_drift.json")
    market_inputs = run_file("market_inputs.json")
    risk = run_file("compute_risk.json")
    rotation = run_file("compute_rotation.json")
    derisk = run_file("compute_derisk.json")
    book_compute = run_file("compute_book.json")

    us = state.get("us", {})
    equity = us.get("value_usd") or 0
    cash = us.get("wallet_usd") or 0
    total = equity + cash
    # peak_total_book_usd/drawdown_pct are computed fresh each run in compute_book.json /
    # compute_drift.json -- state["us"] only ever carries peak_value_usd (equity peak, not
    # total-book peak), so falling back to that key here silently zeroed drawdown out.
    peak = (drift.get("peak_total_book_usd") or book_compute.get("peak_total_book_usd")
            or us.get("peak_value_usd") or total)
    dd = drift.get("drawdown_pct")
    if dd is None:
        dd = book_compute.get("drawdown_pct")
    if dd is None:
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
    H.append(status_strip(us, dd, cash_pct, cash_band, cash_breach, risk, drift, book_compute))

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

        def prop_row(p):
            short, rest = trim_lead(p.get("rationale", ""))
            more = (f'<details><summary>full rationale</summary><div class="body">{esc(rest)}</div></details>'
                    if len(rest) > 40 else "")
            bucket = p.get("direction_bucket", "HOLD")
            pid = p.get("id", "")
            rc = p.get("repeat_count", 1)
            rep = (f'recommended {rc}&times;'
                   + (f' since {esc(str(p["history"][0].get("date",""))[:10])}' if p.get("history") else "")) \
                  if rc > 1 else ""
            pid_s = f'<span class="pid">{esc(pid)}</span>' if pid else ""
            # rep/id live with the rationale (middle column), not the left label column --
            # stacking them under the badge made that column taller than the row needed.
            meta = f'<span class="meta">{rep}{pid_s}</span>' if (rep or pid_s) else ""
            clus_s = f'<span class="clus">{esc(p["cluster"])}</span>' if p.get("cluster") else ""
            # LIVE re-justification (added 2026-08-06). `rationale` is the sentence written the
            # day the proposal was made and never changes; `still_valid_because` is recomputed
            # every run by smith_math.py's proposals pass from today's risk caps, cluster bands
            # and cash position. Showing both, clearly separated, is the difference between a
            # panel that reads as an archive and one that reads as live: the reader can see at a
            # glance that a 6-day-old trim is still on the list because the cap is STILL breached
            # today, not merely because nobody cleaned up. `review_flags` carries the judgement
            # calls the engine deliberately refuses to auto-action (chiefly: price has moved far
            # enough since proposal that the dollar size needs redoing before acting).
            live = p.get("still_valid_because") or []
            live_s = ("".join(f'<span class="lv">{esc(x)}</span>' for x in live)
                      and f'<span class="lives">{"".join(f"<span class=\"lv\">{esc(x)}</span>" for x in live)}</span>')
            flags = p.get("review_flags") or []
            flag_s = "".join(f'<span class="rvf">&#9888;&#65039; {esc(x)}</span>' for x in flags)
            # forward-looking retirement condition (added 2026-08-06, same change) -- the
            # inverse of still_valid_because: what specifically has to happen for this row to
            # auto-retire on a future run. Makes the automation legible, not just present.
            retires = p.get("retires_when")
            retires_s = f'<span class="rtw">retires when: {esc(retires)}</span>' if retires else ""
            return (f'<div class="pr"><span class="act2"><span class="dirb {bucket}">{bucket}</span>'
                    f'{esc(p.get("action",""))}{clus_s}</span>'
                    f'<span class="why">{esc(short)}{more}{live_s}{flag_s}{retires_s}{meta}</span>'
                    f'<span class="amt {bucket}">${p.get("size_usd",0):,.0f}</span></div>')

        # -- grouped by priority (HIGH first), computed by smith_math.py's `proposals`
        # lifecycle pass from live risk-cap/cluster-breach/repeat-count data, not a guess.
        # Anything predating that field (or if the compute step didn't run this cycle)
        # falls back to LOW rather than disappearing or crashing the build. Each tier is
        # a native <details> so it collapses -- HIGH starts open (it's the one that needs
        # eyes every run), MEDIUM/LOW start closed.
        by_priority = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for p in open_props:
            by_priority.setdefault(p.get("priority", "LOW"), by_priority["LOW"]).append(p)
        for tier in ("HIGH", "MEDIUM", "LOW"):
            items = sorted(by_priority[tier], key=lambda p: -p.get("priority_score", 0))
            if not items:
                continue
            open_attr = " open" if tier == "HIGH" else ""
            rows.append(f'<details class="pgrp {tier}"{open_attr}><summary>{tier} PRIORITY'
                        f'<span class="n">{len(items)}</span></summary>'
                        f'<div class="body">{"".join(prop_row(p) for p in items)}</div></details>')

        H.append('<section class="panel act"><div class="phead"><h2>Open proposals</h2>'
                 '<span class="pill a">For review &mdash; never executed</span></div>'
                 f'<div class="pbody"><div>{"".join(rows)}</div>'
                 '<p class="note">To drop a proposal you don\'t want to act on, just tell '
                 'Agent Smith &mdash; e.g. "dismiss P-014" &mdash; citing the id shown under '
                 'its action. It will not be re-proposed.</p></div></section>')

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

    # -- factor themes (added 2026-08-06, dashboard feature review). Standing structural view,
    # companion to Factor catalysts above: catalysts are event-driven (this week's news),
    # themes are the persistent watch list each catalyst gets checked against. state.factor_themes
    # was populated and updated every run by smith-catalyst and rendered nowhere.
    themes = (state.get("factor_themes") or {}).get("themes", [])
    if themes:
        rows = []
        for th in themes[:8]:
            maps = " &middot; ".join(th.get("maps_to", [])[:10])
            live_keys = sorted([k for k in th if k.startswith("live_")], reverse=True)
            latest_live = th.get(live_keys[0]) if live_keys else None
            live_s = (f'<div class="mm">{esc(latest_live)}</div>' if latest_live else "")
            rows.append(f'<div class="ci"><span class="cb AMBIGUOUS">WATCH</span><div>'
                        f'<div class="hh">{esc(th.get("name",""))}</div>'
                        f'<div class="mm" style="font-style:italic">{esc(th.get("watch",""))}</div>'
                        f'{live_s}<div class="aa">{esc(maps)}</div></div></div>')
        H.append('<section class="panel"><div class="phead"><h2>Factor themes'
                 '<span class="sub">the standing watch list catalysts get checked against</span></h2></div>'
                 f'<div class="pbody"><div>{"".join(rows)}</div></div></section>')

    # -- diversifier bench (added 2026-08-06, dashboard feature review). smith-scout's bench of
    # non-AI-capex candidates, priced every run, rendered nowhere -- for a book whose mandate is
    # explicitly a concentrated single-factor bet, the list of what a genuine hedge would even
    # look like is directly relevant, not a footnote.
    divs = {k: v for k, v in (state.get("diversifier_candidates") or {}).items()
            if v.get("status") == "active"}
    if divs:
        rows = sorted(divs.items(), key=lambda kv: -(kv[1].get("upside_pct") or 0))
        chips = "".join(
            f'<span class="rchip {"g" if v.get("clean_diversifier") else "w"}" '
            f'title="{esc(v.get("thesis",""))} | target ${v.get("target_usd","-")} '
            f'({v.get("upside_pct","-")}% upside)">{esc(tk)}<i>{v.get("upside_pct","-")}%</i></span>'
            for tk, v in rows)
        H.append('<section class="panel"><div class="phead"><h2>Diversifier bench'
                 '<span class="sub">non-AI-capex candidates, not held</span></h2>'
                 '<span class="pill">green = clean diversifier &middot; amber = has AI-adjacent overlap</span>'
                 f'</div><div class="pbody"><div class="chips">{chips}</div>'
                 '<p class="note">Priced by smith-scout each deep run; not a proposal to buy, a bench '
                 'of what a genuine hedge to this book\'s single-factor concentration would look like.</p>'
                 '</div></section>')

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

    # -- de-risk queue --
    if derisk and derisk.get("queue"):
        q = derisk["queue"]
        st = derisk.get("queue_state")
        st_cls = {"broad_stretch": "bad", "narrow_stretch": "warn", "no_stretch": "good"}.get(st, "")
        st_lbl = {"broad_stretch": "BROAD STRETCH", "narrow_stretch": "NARROW STRETCH",
                  "no_stretch": "NO STRETCH"}.get(st, (st or "").upper())
        shown = [r for r in q if r.get("derisk_score") is not None][:10]

        def bar(v, cls):
            w = max(0.0, min(100.0, v or 0.0))
            return f'<span class="mbar"><i class="{cls}" style="width:{w:.0f}%"></i></span>'

        body = "".join(
            f'<tr><td class="num">{r["rank"]}</td><td><b>{esc(r["ticker"])}</b></td>'
            f'<td class="num"><b>{r["derisk_score"]:.0f}</b></td>'
            f'<td>{bar(r.get("fragility_score"), "f")}</td>'
            f'<td>{bar(r.get("stretch_score"), "s")}</td>'
            f'<td>{bar(r.get("friction_score"), "x")}</td>'
            f'<td class="num">{(f"{r["abs_return_1m_pct"]:+.1f}%" if r.get("abs_return_1m_pct") is not None else "&mdash;")}</td>'
            f'<td class="num">{(f"{r["rel_strength_1m_pp"]:+.1f}" if r.get("rel_strength_1m_pp") is not None else "&mdash;")}</td>'
            f'<td class="num">{(f"{r["cap_multiple"]:.2f}x" if r.get("cap_multiple") else "&mdash;")}</td>'
            f'<td class="num">${r["market_value_usd"]:,.0f}</td>'
            f'<td class="sub">{esc("; ".join(r.get("friction_reasons") or []) or "-")}</td></tr>'
            for r in shown)

        H.append(
            '<section class="panel"><div class="phead"><h2>De-risk queue'
            '<span class="sub">ranked by damage-if-a-drawdown-comes, not by prediction</span></h2>'
            f'<span class="pill {st_cls}">{esc(st_lbl)}</span></div><div class="pbody">'
            f'<p class="note">{esc(derisk.get("headline",""))}</p>'
            '<div class="tw"><table class="tbl"><thead><tr><th>#</th><th>Name</th><th>Score</th>'
            '<th>Fragility</th><th>Stretch</th><th>Friction</th><th>1m abs</th><th>vs SMH</th>'
            '<th>cap</th><th>Value</th><th>Friction reason</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>'
            '<details><summary>How this is scored</summary><div class="body">'
            '<b>Fragility</b> &mdash; share of the book&rsquo;s total open risk (already embeds ATR &times; '
            'position size) multiplied by how far the position sits over its own 2&times;ATR cap. '
            'This is <i>how hard it hits</i>, and it is the dominant term.<br>'
            '<b>Stretch</b> &mdash; 1-month return relative to SMH, but <i>only counted when the name is '
            'also up in absolute terms</i>. Beating a benchmark that is itself falling means the name '
            'merely fell less; there is no gain to give back, so it is not a trim candidate. '
            'Relative rather than absolute deliberately: in a ~100% single-factor book an absolute '
            'RSI/52-week screen flags all-or-nothing.<br>'
            '<b>Friction</b> &mdash; cost of acting: proximity to the 24-month LTCG boundary (from '
            'lots.json), unknown lot dates, and a dust-position discount. Higher friction pushes a '
            'name down the queue.<br>'
            '<b>Sentiment</b> is an urgency dial on the whole queue '
            f'(band <b>{esc(derisk.get("sentiment_band","-"))}</b> &rarr; &times;'
            f'{derisk.get("urgency_multiplier","-")}), never a trigger. It cannot manufacture stretch '
            'that does not exist per name.<br><br>'
            '<b>This queue is shadow-scored and does not drive proposals.</b> Each deep run logs its '
            'top names to derisk_journal.json and scores them at 30/90d. It earns a vote in sizing '
            'decisions only once it has a real hit rate.'
            '</div></details></div></section>')

    # -- stop-loss efficacy (added 2026-08-06, dashboard feature review) --
    # trades.json had 24 stop-loss fills with exact prices and was referenced by this generator
    # zero times. The computation (smith_math.py cmd_stops, writes stops_analysis.json) measures
    # whether each stop helped or hurt vs simply holding through, split into "cascade" (3+ stops
    # firing within a 5-minute window -- typically a market-open liquidity gap) vs "deliberate"
    # (isolated, mid-session) cohorts. First real finding from this: cascade-fired stops in this
    # book have recovered on average, deliberate ones have on average correctly avoided further
    # downside -- exactly the kind of pattern that stays invisible without a standing panel.
    overall = stops_data.get("overall")
    if overall:
        by_cohort = stops_data.get("by_cohort") or {}
        rows_s = stops_data.get("stops") or []

        def cohort_line(name, label):
            c = by_cohort.get(name)
            if not c:
                return ""
            sign = "pos" if c["net_dollar_impact"] <= 0 else "neg"  # negative $ impact = stop SAVED money
            return (f'<div class="cohort-row"><b>{esc(label)}</b>'
                    f'<span>{c["count"]} stops, avg {c["avg_move_pct"]:+.1f}% since fill</span>'
                    f'<span class="{sign}">${c["net_dollar_impact"]:+,.0f} net</span>'
                    f'<span class="m">{c["saved"]} saved &middot; {c["hurt"]} hurt'
                    + (f' &middot; {c["flat"]} flat' if c.get("flat") else "") + '</span></div>')

        net_cls = "pos" if overall["net_dollar_impact"] <= 0 else "neg"
        summary_cells = (
            f'<div class="stops-sum">'
            f'<div class="c"><span class="k">Scored</span><span class="v">{overall["count"]}</span></div>'
            f'<div class="c"><span class="k">Win rate</span><span class="v">'
            f'{overall["win_rate_pct"]:.0f}%</span></div>' if overall.get("win_rate_pct") is not None else
            f'<div class="stops-sum"><div class="c"><span class="k">Scored</span><span class="v">{overall["count"]}</span></div>')
        summary_cells += (f'<div class="c"><span class="k">Net impact</span>'
                          f'<span class="v {net_cls}">${overall["net_dollar_impact"]:+,.0f}</span></div>'
                          f'<div class="c"><span class="k">Avg move</span>'
                          f'<span class="v">{overall["avg_move_pct"]:+.1f}%</span></div></div>')

        cohort_rows = (cohort_line("cascade", "Cascade") + cohort_line("deliberate", "Deliberate")
                      + cohort_line("unknown", "Untimed"))

        recent_rows = "".join(
            f'<tr><td class="name">{esc(r["ticker"])}</td><td class="blank">{esc(r["date"])}</td>'
            f'<td>${r["fill_price"]:,.2f}</td><td>${r["price_now"]:,.2f}</td>'
            f'<td class="{"pos" if r["move_pct"]>=0 else "neg"}">{r["move_pct"]:+.1f}%</td>'
            f'<td class="verd-{r["verdict"]}">{r["verdict"].upper()}</td>'
            f'<td><span class="cohort-tag {r["cohort"]}">{esc(r["cohort"])}</span></td></tr>'
            for r in rows_s[:12])

        dq_s = ("".join(f'<p class="note">{esc(x)}</p>' for x in (stops_data.get("data_quality") or [])))

        H.append(
            '<section class="panel"><div class="phead"><h2>Stop-loss efficacy'
            '<span class="sub">did the stop help or hurt, vs simply holding through</span></h2>'
            f'<span class="pill">as of {esc(stops_data.get("as_of",""))}</span></div>'
            f'<div class="pbody">{summary_cells}<div>{cohort_rows}</div>'
            '<div class="scroll"><table><thead><tr><th>Name</th><th>Date</th><th>Fill</th>'
            '<th>Now</th><th>Move</th><th>Verdict</th><th>Cohort</th></tr></thead>'
            f'<tbody>{recent_rows}</tbody></table></div>'
            '<p class="note"><b>Cascade</b> = 3+ stops fired within a 5-minute window (typically '
            'a market-open liquidity gap). <b>Deliberate</b> = an isolated, mid-session stop. '
            '<b>Verdict</b>: HURT means the price is now above the fill (holding through would '
            'have been worth more); SAVED means it fell further after the stop fired.</p>'
            f'{dq_s}</div></section>')

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

    # -- LTCG watch (added 2026-08-06, dashboard feature review). compute_book.json computes
    # ltcg_flags every run from lots.json (now fully populated with email-confirmed dates) and
    # renders nowhere, despite `friction` in the De-risk queue already consuming it internally.
    # Only lots within 6 months of the 24-month LTCG boundary are flagged by the compute step,
    # so an empty list here is a real, positive statement ("nothing near the boundary"), not a
    # missing feature -- rendered as such rather than the section silently vanishing.
    ltcg_flags = book_compute.get("ltcg_flags", [])
    ltcg_months = load(os.path.join(base, "policy.json"), {}).get("ltcg_boundary_months", 24)
    if ltcg_flags:
        rows = "".join(
            f'<div class="ltcg-row"><span>{esc(f["ticker"])} &middot; {f.get("qty","-")}sh</span>'
            f'<span class="{"past" if f["months_to_ltcg"]<=0 else "soon"}">'
            f'{("past boundary by " + str(abs(f["months_to_ltcg"])) + "mo") if f["months_to_ltcg"]<=0 else (str(f["months_to_ltcg"]) + "mo to go")}'
            f'</span></div>'
            for f in sorted(ltcg_flags, key=lambda f: f["months_to_ltcg"]))
        H.append(f'<section class="panel"><div class="phead"><h2>LTCG watch'
                 f'<span class="sub">lots within 6mo of the {ltcg_months}-month boundary</span></h2>'
                 f'<span class="pill w">{len(ltcg_flags)} lots</span></div>'
                 f'<div class="pbody">{rows}</div></section>')
    elif os.path.exists(os.path.join(base, "lots.json")):
        H.append(f'<section class="panel"><div class="phead"><h2>LTCG watch'
                 f'<span class="sub">lots within 6mo of the {ltcg_months}-month boundary</span></h2>'
                 '<span class="pill g">clear</span></div>'
                 '<div class="pbody"><p class="note">No lot sits within 6 months of the '
                 f'{ltcg_months}-month LTCG boundary right now.</p></div></section>')

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
    # FIXED 2026-08-06 (dashboard feature review, user-reported): thesis carries entries for
    # every ticker EVER analysed, including names exited long ago (the panel was captioned
    # "36 held" while the book held 28 -- eight of those theses were for EWY/COHR/ARM/GOOG/
    # NBIS/IREN/GLW/QBTS, several exited that very morning). Filter to currently-held tickers
    # so the count and the map are both actually true; stale entries simply age out of view
    # here rather than needing manual pruning from state.json (they stay there for history).
    thesis = {tk: v for tk, v in (state.get("thesis") or {}).items() if tk in held_tickers}
    if thesis:
        groups = {"strengthening": [], "watch": [], "broken": []}
        other = []
        for tk, txt in thesis.items():
            body, _, status = txt.rpartition("|")
            # status is usually a bare keyword but sometimes carries a bracketed note
            # (e.g. "strengthening [position closed ...]") -- match by prefix, not equality,
            # membership-check the dict (not `groups.get(st) or other` -- an empty list is
            # falsy, so that pattern silently sent every ticker to `other` on every run).
            st_raw = status.strip().lower() if status else ""
            st = next((k for k in groups if st_raw.startswith(k)), None)
            target = groups[st] if st else other
            target.append((tk, body.strip()))
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
        if other:
            chips = "".join(
                f'<span class="chip" title="{esc(body[:220])}">{esc(tk)}<i>{esc(sector_map.get(tk,"-"))}</i></span>'
                for tk, body in sorted(other))
            blocks.append(f'<div class="grp-h">Other</div>'
                          f'<div class="chips" style="margin-bottom:12px">{chips}</div>')
        H.append(f'<details><summary>Thesis map<span class="c">{len(thesis)} of {len(held_tickers)} held</span></summary>'
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

    # -- execution log (added 2026-08-06, dashboard feature review). trades.json holds 61
    # trades with captured rationale ("why", not just "what") and had never been rendered.
    exec_trades = sorted(trades_data.get("trades", []), key=lambda t: t.get("date") or "", reverse=True)
    if exec_trades:
        rows = []
        for t in exec_trades[:25]:
            act = (t.get("action") or "").upper()
            side = "sell" if act in ("EXIT", "TRIM", "SELL") else "buy"
            price = t.get("price_at_trade")
            price_s = f'${price:,.2f}' if price is not None else "&mdash;"
            qty = t.get("qty_change")
            qty_s = f'{qty:+g}sh' if qty is not None else ""
            rows.append(f'<div class="exec-row"><span class="d">{esc(t.get("date",""))}</span>'
                        f'<span class="t">{esc(act)}</span>'
                        f'<span class="rsn"><b>{esc(t.get("ticker",""))}</b> {qty_s} &middot; '
                        f'{esc((t.get("reason") or "").replace("-"," "))}</span>'
                        f'<span class="px {side}">{price_s}</span></div>')
        H.append(f'<details><summary>Execution log<span class="c">{len(exec_trades)} trades, '
                 f'most recent 25 shown</span></summary><div class="body">{"".join(rows)}'
                 '<p class="note" style="margin-top:8px">Every entry carries the rationale '
                 'captured at the time -- hover the notes in trades.json for the full text.</p>'
                 '</div></details>')

    # -- data quality (added 2026-08-06, dashboard feature review). Every compute step already
    # self-reports its own caveats (stale feeds, defaulted betas, missing coverage) into
    # data_quality arrays that were computed and never surfaced -- a dashboard that hides its
    # own uncertainty invites more trust in a number than the number earns.
    dq_all = list(state.get("data_quality") or [])
    for src in (book_compute, risk, drift, derisk):
        dq_all.extend(src.get("data_quality") or [])
    if dq_all:
        rows = "".join(f'<div class="srow"><span class="slab"></span>'
                       f'<span style="font-size:12.5px;color:var(--ink-2)">{esc(x)}</span></div>'
                       for x in dq_all)
        H.append(f'<details><summary>Data quality caveats<span class="c">{len(dq_all)} this run</span></summary>'
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

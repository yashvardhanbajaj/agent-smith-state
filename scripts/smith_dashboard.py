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

# Must precede the smith_* imports below: this file is only guaranteed importable when
# invoked as `python3 scripts/smith_dashboard.py` (argv[0]'s directory lands on sys.path
# automatically); importing it as a module from elsewhere -- e.g. a test suite -- needs
# scripts/ on sys.path explicitly first, or `from smith_core import ...` raises ModuleNotFoundError.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smith_core import ticker_rows
import smith_risk
import smith_learning

DEFAULT_BASE = "/Users/yb/Claude/AgentSmith"


def load(p, d=None):
    if not os.path.exists(p):
        return d
    with open(p) as f:
        return json.load(f)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def esc_attr(s):
    """Same as esc() plus quote-escaping -- for values going into an HTML attribute rather
    than text content (e.g. a catalyst headline riding along in a data-* attribute so the
    'priced in' button can carry it without a lookup). esc() alone is safe for the tickers/
    proposal-ids/gap-ids most attributes here carry, but not for arbitrary prose."""
    return esc(s).replace('"', "&quot;").replace("'", "&#39;")


# Buttons per surface -- (decision_key, label, css_class). One table, read by both
# decision_buttons() (server-side render) and the client JS's BUTTON_LABELS mirror below, so
# the two can never drift out of sync with each other.
DECISION_BUTTONS = {
    "proposal": [("accept", "Accept", "b-accept"), ("reject", "Reject", "b-reject"),
                 ("hold", "Hold", "b-hold")],
    "auto_retired_proposal": [("revive", "Revive", "b-revive")],
    "watchlist": [("watch_closely", "Watch closely", "b-watch"),
                  ("not_interested", "Not interested", "b-reject")],
    "diversifier": [("not_interested", "Not interested", "b-reject")],
    "derisk": [("disagree", "Disagree — not fragile", "b-disagree")],
    "gap": [("resolve", "Mark resolved", "b-resolve")],
    "learning_param": [("approve", "Approve", "b-approve"), ("defer", "Defer", "b-hold")],
    "thesis": [("confirm", "Confirm", "b-confirm"), ("override", "Override", "b-override")],
    "catalyst": [("priced_in", "Already priced in", "b-hold")],
}


def held_badge(prop):
    """A visible marker for a proposal the user has already put on Hold.

    Hold was durably captured and synced (SKILL.md 1.7: the proposal stays open and gains
    `held_on`) but NOTHING on the page rendered it -- the row redrew with the same three fresh
    buttons, so a held proposal was indistinguishable from an undecided one and the natural
    next move was to click Hold again. The decision survived; the feedback did not. Added
    2026-08-31 after exactly that happened with P-178.
    """
    held = prop.get("held_on")
    if not held:
        return ""
    when = held[-1] if isinstance(held, list) else held
    why = prop.get("held_reason")
    tail = f" -- {esc(str(why))}" if why else ""
    n = len(held) if isinstance(held, list) else 1
    times = f" (held {n}x)" if n > 1 else ""
    return (f'<span class="held-badge" title="You put this on hold; it stays open until you '
            f'accept or reject it.">HELD {esc(str(when))}{times}{tail}</span>')


def stacks_badge(prop):
    """Show when a proposal stacks with others on the same name and economic side. Written by
    cmd_proposals' stacking guard. Rendered here because the whole failure was that the combined
    number existed nowhere a human would see it: P-164 Sell MSFT $438 accepted and P-201 Sell
    MSFT $306 open were 73% of the position across two rows that never referenced each other.
    A guard that only writes a field repeats the defect it fixes.

    Rebuilt 2026-09-06 alongside the guard (G88): a stack is no longer always "open stacks on
    accepted" -- it can be all-open (AVGO P-212+P-226), and it can merge a Trim with a Sell.
    Both must read correctly here, or the badge quietly misdescribes the row it is warning about."""
    st = prop.get("stacks_on")
    if not isinstance(st, dict):
        return ""
    pct = st.get("combined_pct_of_position")
    pct_s = f" = {pct:.0f}% of the position" if isinstance(pct, (int, float)) else ""
    cls = "stack-badge hi" if st.get("severity") == "high" else "stack-badge"
    others = [i for i in (st.get("member_ids") or []) if i and i != prop.get("id")]
    if not others and st.get("accepted_id"):        # legacy rows written before the rebuild
        others = [st["accepted_id"]]
    accepted = set(st.get("accepted_ids") or ([st["accepted_id"]] if st.get("accepted_id") else []))
    parts = [f'{esc(str(i))} (accepted, not yet filled)' if i in accepted else esc(str(i))
             for i in others]
    lead = "stacks with " + ", ".join(parts) if parts else "stacks"
    merged = st.get("sides_merged") or []
    verb = (f' &middot; {esc(" + ".join(merged))} counted together'
            if len(merged) > 1 else "")
    return (f'<span class="stopline {cls}">{lead} &mdash; '
            f'${st.get("combined_usd", 0):,.0f} combined{pct_s}{verb}</span>')


def decision_buttons(surface, element_id, extra_attrs=""):
    """Renders the standard button-group + optional-reason-input markup for one interactive
    row. `extra_attrs` carries surface-specific data-* attributes the JS needs at click time
    (e.g. a catalyst's headline+date, since 'catalyst' rows are addressed by a synthetic id
    rather than a natural key) -- kept as a raw string the caller assembles, since the shape
    differs per surface and forcing one generic parameter shape here would just move the
    per-surface branching from smith_math.py's sync side into this render function instead.
    The 'thesis' surface additionally needs a new-status <select>, added inline since it's the
    one surface whose Override decision carries a THIRD piece of data (not just decision+reason).
    """
    buttons = DECISION_BUTTONS[surface]
    btn_html = "".join(f'<button type="button" class="{cls}" data-decision="{dk}">{esc(label)}</button>'
                       for dk, label, cls in buttons)
    select_html = ""
    if surface == "thesis":
        opts = "".join(f'<option value="{s}">{s}</option>' for s in
                       ("strengthening", "intact", "watch", "broken"))
        select_html = f'<select class="new-status" aria-label="new thesis status">{opts}</select>'
    return (f'<div class="decide" data-surface="{esc_attr(surface)}" '
           f'data-element-id="{esc_attr(element_id)}"{extra_attrs}>'
           f'{btn_html}{select_html}'
           f'<input class="reason" type="text" placeholder="reason (optional)" maxlength="200">'
           f'</div>')


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
.stack-badge{color:var(--ink-2)}
.stack-badge.hi{color:#b04e72;font-weight:600}
.held-badge{display:inline-block;margin-left:.5rem;padding:.08rem .4rem;border-radius:3px;
  font-size:.72rem;font-weight:600;letter-spacing:.02em;
  background:var(--surface-2);color:var(--ink-2);border:1px solid var(--line)}
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
/* FIXED 2026-08-08 (user-reported: "Factor themesthe standing watch list..." ran together with
   no space) -- .sub was used as a class on <span> throughout (h2 subtitles) AND on <td> (muted
   table-cell text) but never had a CSS rule at all, so h2 subtitles inherited zero spacing and
   ran directly into the heading text. Base rule mutes both contexts; the nested h2 override adds
   the spacing that only makes sense next to a heading, without touching td.sub's table layout. */
.sub{color:var(--ink-3)}
h2 .sub{display:inline-block;margin-left:8px;font-family:var(--sans);font-weight:400;
  font-size:12px;letter-spacing:0;vertical-align:middle}
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
/* FIXED 2026-08-12: `.tw` is the horizontal-scroll wrapper used around every wide table in this
   file (de-risk queue, positions, stop-loss efficacy, trade triggers -- ~16 call sites) and it had
   NEVER been defined, so none of those tables could actually scroll and a wide one pushed the page
   into horizontal overflow instead. Exactly the silent-failure class SKILL.md warns about: an
   undefined class produces no browser warning, and a static tag-balance check cannot see it.
   `.tbl` is also used-but-undefined and is left that way deliberately -- the bare `table`/`th`/`td`
   element selectors below already style it, so it is a genuine no-op rather than a missing rule. */
.tw{overflow-x:auto}
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

/* ============ expandable cluster rows (added 2026-08-08, user-requested: expand a cluster to
   see its member holdings and which are peer leaders/laggards) ============ */
/* FIXED 2026-08-08 (user-reported: rows rendering as unstyled overlapping text with the band
   meter dropping to its own full-width line below). Root cause: `display:grid` set DIRECTLY on
   a <summary> element is unreliable across browsers -- <summary> has special UA-stylesheet/
   marker-box handling per the HTML rendering rules, and several engines silently ignore or only
   partially apply an author `display: grid`/`flex` on it, falling back toward block flow (spans
   collapse to inline-in-block and wrap/overlap; the sibling <div class="band"> forces its own
   line since divs are block-level by default). The fix used throughout the ecosystem for this
   exact quirk: never style <summary> itself as grid/flex -- wrap the row's content in a plain
   child <div> and apply the grid to THAT div instead. <summary> keeps simple default styling
   (cursor, padding, list-style removal), which every engine handles correctly. -->*/
.clus-hdr{display:grid;grid-template-columns:1fr 70px 70px 90px 150px;gap:12px;padding:0 0 8px;
  align-items:baseline}
.clus-hdr .num{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);text-align:right}
details.clus-row{border-top:1px solid var(--line-soft)}
details.clus-row:first-of-type{border-top:none}
details.clus-row>summary{cursor:pointer;list-style:none;list-style-type:none;padding:11px 0;
  font-family:var(--sans)}
details.clus-row>summary::-webkit-details-marker{display:none}
details.clus-row>summary::marker{content:"";display:none}
details.clus-row>summary::before{content:"";}
/* the actual grid lives here, one level in -- see the fix note above */
.clus-summary-grid{display:grid;grid-template-columns:1fr 70px 70px 90px 150px;gap:12px;
  align-items:center}
.clus-summary-grid .name{font-weight:640;letter-spacing:-.01em;display:flex;align-items:baseline;gap:7px}
.clus-summary-grid .name i{font-style:normal;font-family:var(--mono);font-size:11px;font-weight:400;
  color:var(--ink-3)}
.clus-summary-grid .name::before{content:"▸";color:var(--ink-3);font-family:var(--sans);width:10px;
  display:inline-block;flex-shrink:0}
details.clus-row[open] .clus-summary-grid .name::before{content:"▾"}
.clus-summary-grid .num{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right}
.clus-summary-grid .num.blank{color:var(--ink-3)}
.clus-summary-grid .band{min-width:0}
details.clus-row>.body{padding:0 0 14px}
.peer-tag{font-size:9.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  padding:2px 6px;border-radius:4px;white-space:nowrap}
.peer-tag.lead{background:var(--good-soft);color:var(--good)}
.peer-tag.lag{background:var(--bad-soft);color:var(--bad)}

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
.pr .tranche{display:block;font-family:var(--mono);font-size:11px;color:var(--action);
  line-height:1.4;margin-top:5px}

/* ============ rotation ideas (paired trim+buy proposals) ============ */
.rotgrp{border-top:1px solid var(--line-soft);padding-top:2px;margin-bottom:2px}
.rotgrp-h{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--accent);padding:12px 0 8px}
.rotgrp-h .n{background:var(--accent-soft);color:var(--accent);border-radius:10px;padding:1px 8px;
  font-family:var(--mono);margin-left:8px;text-transform:none;letter-spacing:normal;font-weight:400}
.rotcard{display:grid;grid-template-columns:1fr 28px 1fr;gap:4px;align-items:center;
  padding:10px;margin-bottom:10px;border:1px solid var(--accent-line);border-radius:var(--r);
  background:var(--accent-soft)}
.rotleg{background:var(--surface);border-radius:5px;padding:2px 10px}
.rotleg .pr{border-bottom:none;padding:9px 0}
.rotarrow{text-align:center;font-size:18px;color:var(--accent);font-weight:700}
@media (max-width:640px){.rotcard{grid-template-columns:1fr}.rotarrow{transform:rotate(90deg)}}

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
.mbar{display:inline-block;width:52px;height:6px;border-radius:3px;background:var(--line);
  vertical-align:middle;overflow:hidden}
.mbar i{display:block;height:100%;border-radius:3px}
.mbar i.f{background:var(--bad)}
.mbar i.s{background:var(--warn)}
.mbar i.x{background:var(--ink-3)}
.pill.warn{color:var(--warn);border-color:var(--warn)}
.pill.bad{color:var(--bad);border-color:var(--bad)}
.pill.good{color:var(--good);border-color:var(--good)}

/* ============ misc ============ */
.note{font-size:12.5px;color:var(--ink-3);line-height:1.55}
.note b{color:var(--ink-2)}
.rule{height:1px;background:var(--line-soft);border:0;margin:0}
footer{border-top:1px solid var(--line);padding-top:18px;display:flex;flex-direction:column;gap:10px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* ============ interactive decisions (added 2026-08-25) ============ */
.decide{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:6px}
.decide button{font:inherit;font-size:11.5px;padding:3px 9px;border-radius:6px;
  border:1px solid var(--line);background:var(--surface);color:var(--ink-2);cursor:pointer}
.decide button:hover{border-color:var(--accent);color:var(--ink)}
.decide button.b-accept,.decide button.b-approve,.decide button.b-revive,
.decide button.b-confirm,.decide button.b-resolve,.decide button.b-watch{
  border-color:var(--good);color:var(--good)}
.decide button.b-reject,.decide button.b-disagree,.decide button.b-override{
  border-color:var(--bad);color:var(--bad)}
.decide input.reason{font:inherit;font-size:11.5px;padding:3px 7px;border-radius:6px;
  border:1px solid var(--line);background:var(--surface);color:var(--ink-2);flex:1;min-width:140px}
.decide select.new-status{font:inherit;font-size:11.5px;padding:3px 5px;border-radius:6px;
  border:1px solid var(--line);background:var(--surface);color:var(--ink-2)}
.decide .recorded{font-size:11.5px;color:var(--ink-3);font-style:italic}
.decide.readonly{display:none}
"""


# Interactive-decisions client JS (added 2026-08-25). This dashboard was deliberately JS-free
# until now -- every prior interactive need was covered by <details>/<summary>, which has no
# landmine surface. This feature genuinely needs JS: there is no capability that lets a
# published page write to the local filesystem (checked against the real contract before
# designing anything -- only downloads/mcp/self exist), so a click can only persist by having
# the page republish ITSELF via window.claude.self.publish(), with the decision embedded in the
# republished HTML. A future Agent Smith run fetches the live artifact and reconciles what it
# finds (smith_math.py's sync-decisions) -- see plans/clever-watching-hinton.md for the design.
#
# THE PATTERN, per window.claude.self's own contract (self.d.ts): "do not serialize the live
# DOM... instead keep the page's canonical source... and render the replacement from that."
# This captures document.documentElement.outerHTML ONCE, as the very first statement, before
# any click can mutate anything -- that is the pristine, server-authored source, safe to
# republish. Every subsequent publish does a TARGETED STRING REPLACE on that captured pristine
# copy (never on the live, possibly-already-mutated DOM), swapping in the updated decisions
# blob and that one row's "recorded" state.
#
# LANDMINE, stated plainly so a future edit doesn't reintroduce it silently: the string-replace
# anchor is the literal substring `data-surface="X" data-element-id="Y"`, which
# decision_buttons() emits as one contiguous run at the START of each `.decide` div's opening
# tag. If a future edit reorders those two attributes, or inserts something between them, this
# anchor breaks and decisions stop visually marking as recorded (they'd still PERSIST correctly
# -- the blob swap is a separate, independent regex match -- but the optimistic "recorded" UI
# would silently stop working). Keep `data-surface` immediately followed by `data-element-id`
# in decision_buttons() if you touch it.
DASHBOARD_JS = r"""<script>
(function(){
  var PRISTINE = document.documentElement.outerHTML;

  function decisionsFrom(html){
    var m = html.match(/<script type="application\/json" id="smith-decisions">([\s\S]*?)<\/script>/);
    if (!m) return [];
    try { return JSON.parse(m[1]); } catch(e){ return []; }
  }

  function setReadOnly(msg){
    document.querySelectorAll('.decide').forEach(function(el){ el.classList.add('readonly'); });
    var note = document.createElement('p');
    note.className = 'note';
    note.textContent = msg || 'This view is read-only -- decisions cannot be recorded from here.';
    var wrap = document.querySelector('.wrap');
    if (wrap) wrap.insertBefore(note, wrap.firstChild);
  }

  if (!window.claude || !window.claude.self){
    setReadOnly();
    return;
  }

  document.body.addEventListener('click', function(ev){
    var btn = ev.target.closest('.decide button');
    if (!btn) return;
    var group = btn.closest('.decide');
    var surface = group.getAttribute('data-surface');
    var elementId = group.getAttribute('data-element-id');
    var decision = btn.getAttribute('data-decision');
    var reasonInput = group.querySelector('input.reason');
    var reason = (reasonInput && reasonInput.value.trim()) ? reasonInput.value.trim() : null;
    var payload = {surface: surface, element_id: elementId, decision: decision, reason: reason,
                   decided_on: new Date().toISOString().slice(0,10)};

    if (surface === 'thesis' && decision === 'override'){
      var sel = group.querySelector('select.new-status');
      payload.new_status = sel ? sel.value : null;
      if (!reason){ alert('Override needs a reason -- your own read of the company is the point.'); return; }
    }
    if (surface === 'catalyst'){
      payload.headline = group.getAttribute('data-headline');
      payload.date = group.getAttribute('data-date');
    }

    var controls = group.querySelectorAll('button, input, select');
    controls.forEach(function(x){ x.disabled = true; });

    var decisions = decisionsFrom(PRISTINE);
    decisions.push(payload);
    var blobJson = JSON.stringify(decisions);

    var anchor = 'data-surface="' + surface + '" data-element-id="' + elementId + '"';
    var startIdx = PRISTINE.indexOf(anchor);
    var newHtml = PRISTINE;
    if (startIdx !== -1){
      var divStart = PRISTINE.lastIndexOf('<div class="decide"', startIdx);
      var divEnd = PRISTINE.indexOf('</div>', startIdx) + '</div>'.length;
      if (divStart !== -1 && divEnd > divStart){
        var recordedText = 'Recorded: ' + decision + (reason ? ' — ' + reason : '') +
          ' (syncs on the next Agent Smith run)';
        var recorded = '<div class="decide recorded-block"><span class="recorded">' +
          recordedText.replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</span></div>';
        newHtml = PRISTINE.slice(0, divStart) + recorded + PRISTINE.slice(divEnd);
      }
    }
    newHtml = newHtml.replace(
      /<script type="application\/json" id="smith-decisions">[\s\S]*?<\/script>/,
      '<script type="application/json" id="smith-decisions">' + blobJson + '<\/script>'
    );

    window.claude.self.publish('<!doctype html>' + newHtml).catch(function(err){
      var code = err && err.code;
      if (code === 'conflict') return;  // view is already reloading to the winning version
      if (code === 'not_writer' || code === 'not_granted' || code === 'consent_required'){
        setReadOnly();
        return;
      }
      alert('Could not record that decision (' + (code || 'unknown error') +
            '). It was not saved -- try again.');
      controls.forEach(function(x){ x.disabled = false; });
    });
  });
})();
</script>"""


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


def _render_accepted_awaiting_execution(props):
    out = []
    # ---- ACCEPTED, AWAITING EXECUTION (added 2026-08-31) ----------------------------------
    # Accepting a proposal used to make it VANISH from the dashboard. SKILL.md 1.7 is explicit
    # that a click is stated intent and NEVER proof of a trade -- so the moment the user
    # committed to something, the page stopped showing it, and the list of what they had
    # decided to do existed only in chat scrollback. On 2026-08-31 that was six trades.
    # This is the same shape as the invisible Hold badge: the decision persisted correctly and
    # nothing rendered it back. A proposal leaves this panel only when a real fill moves it to
    # executed/fulfilled/filled via the ledger -- never because it was merely acknowledged.
    accepted = [p for p in props.get("proposals", []) if p.get("status") == "accepted_by_user"]
    if accepted:
        # Legacy rows from the hand-written batches predating `add-proposal` carry a BARE
        # DIRECTION WORD as their action ("SELL MSFT", not "Sell MSFT"), which renders as
        # "SELL SELL MSFT" once the direction badge is prepended -- the identical defect that
        # caused add-proposal to be written (it builds `action` from ticker+direction so the
        # shape cannot recur going forward). Those old rows are still on file and this panel is
        # the first surface to render them, so strip a leading direction word that merely
        # repeats the badge. Display-only: the stored action is never rewritten, because
        # editing history to fix a rendering bug is how an audit trail stops being one.
        _DIR_WORDS = {"BUY", "SELL", "TRIM", "HOLD", "ADD", "EXIT", "REDUCE", "REBUILD"}

        def _clean_action(p, bucket):
            act = (p.get("action") or "").strip()
            head, _, tail = act.partition(" ")
            if tail and head.isupper() and head in _DIR_WORDS:
                return tail.strip()
            return act

        def _bucket(p):
            b = (p.get("direction_bucket") or "").upper()
            if b:
                return b
            act = (p.get("action") or "").lower()
            return "SELL" if ("sell" in act or "trim" in act) else "BUY"

        sells = sum(p.get("size_usd") or 0 for p in accepted if _bucket(p) in ("SELL", "TRIM"))
        buys = sum(p.get("size_usd") or 0 for p in accepted if _bucket(p) not in ("SELL", "TRIM"))
        net = sells - buys
        rows = []
        for p in sorted(accepted, key=lambda x: (0 if _bucket(x) in ("SELL", "TRIM") else 1,
                                                 -(x.get("size_usd") or 0))):
            b = _bucket(p)
            pid = p.get("id", "")
            when = p.get("accepted_on") or ""
            pair = p.get("pair_id")
            pair_s = (f'<span class="stopline">paired with the '
                      f'{"buy" if b in ("SELL", "TRIM") else "sell"} leg &mdash; self-funding</span>'
                      if pair else "")
            rows.append(
                f'<div class="pr"><span class="act2"><span class="dirb {b}">{b}</span>'
                f'{esc(_clean_action(p, b))}</span>'
                f'<span class="why">{esc(pid)}{" &middot; accepted " + esc(when) if when else ""}'
                f'{pair_s}</span>'
                f'<span class="amt {b}">${p.get("size_usd", 0):,.0f}</span></div>')
        net_word = "raises cash by" if net >= 0 else "needs cash of"
        out.append(
            '<section class="panel act"><div class="phead"><h2>Accepted &mdash; awaiting execution</h2>'
            f'<span class="pill a">{len(accepted)} decided, not yet filled</span></div>'
            f'<div class="pbody"><div>{"".join(rows)}</div>'
            f'<p class="note"><b>${sells:,.0f}</b> of sells/trims against <b>${buys:,.0f}</b> of buys '
            f'&mdash; net {net_word} <b>${abs(net):,.0f}</b>. '
            'Accepting is a stated intention, not a trade: Agent Smith never places orders. '
            'A row leaves this panel only when the actual fill reaches the ledger.</p></div></section>')

    return out


def _render_ideas_and_housekeeping(props, policy, state, cash_breach, cash_pct, cash_band):
    out = []
    open_props = [p for p in props.get("proposals", []) if p.get("status") == "open"]
    cap = policy.get("max_single_position_pct", 12)
    breaches = []
    for h in state.get("holdings", []):
        if h.get("weight_pct", 0) > cap:
            breaches.append(f'{h["ticker"]} {h["weight_pct"]:.1f}% vs {cap}% position cap')
    if cash_breach:
        breaches.append(f'cash {cash_pct:.1f}% outside the [{cash_band[0]},{cash_band[1]}]% band')

    # Two-panel split (added 2026-08-24, third time the user reported the same defect: the list
    # read as a compliance report because cap/cluster/cash mechanics competed with -- and usually
    # beat, by sheer stacking -- genuine conviction-driven ideas for the top slot). IDEAS is
    # ranked and capped; RISK HOUSEKEEPING is sized/actionable but never ranked against an idea.
    # proposal_class is set by smith_lifecycle.py's cmd_proposals; anything missing the field
    # (legacy proposals) defaults to "idea" there, so nothing silently vanishes into housekeeping.
    idea_props = [p for p in open_props if p.get("proposal_class", "idea") != "housekeeping"]
    housekeeping_props = [p for p in open_props if p.get("proposal_class") == "housekeeping"]

    if idea_props or housekeeping_props or breaches:
        rows = []

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
            # honest sizing (added 2026-08-06, user-reported: sizes looked small vs the breach
            # they claimed to cure). tranche_note only appears when smith_math.py's proposals
            # pass computed a cure_pct under 90% -- a proposal that already cures the bulk of
            # its trigger says nothing extra, this is specifically the "27% of a $1,457 excess"
            # case made visible instead of a bare $400 sitting next to no context.
            tranche = p.get("tranche_note")
            tranche_s = f'<span class="tranche">{esc(tranche)}</span>' if tranche else ""
            # Conviction-driven ideas (added 2026-08-24) carry a stop level, a share count, and
            # clamped_by -- "wanted $1,364, capped to $538 by ATR headroom" -- so a proposal never
            # states a dollar figure without saying what it would take to fill it or what capped
            # it short. Legacy/housekeeping proposals don't carry these fields; render nothing
            # rather than a misleading "$0 shares".
            stop_px = p.get("stop_price_usd")
            price_px = p.get("price_usd")
            shares = None
            if price_px:
                shares = int(p.get("size_usd", 0) / price_px) if price_px else None
            stop_s = f'<span class="stopline">stop ${stop_px:,.2f}</span>' if stop_px else ""
            shares_s = f'<span class="stopline">~{shares} sh</span>' if shares else ""
            clamped = p.get("clamped_by")
            clamped_s = (f'<span class="stopline">wanted ${p.get("size_wanted_usd", 0):,.0f}, '
                        f'capped by {esc(clamped)}</span>') if clamped else ""
            conv = p.get("conviction_score")
            conv_s = (f'<span class="stopline">conviction {conv:.0f} ({esc(p.get("conviction_tier",""))})'
                      f'</span>') if conv is not None else ""
            decide_s = decision_buttons("proposal", pid) if pid else ""
            held_s = held_badge(p)
            stack_s = stacks_badge(p)
            return (f'<div class="pr"><span class="act2"><span class="dirb {bucket}">{bucket}</span>'
                    f'{esc(p.get("action",""))}{clus_s}{held_s}</span>'
                    f'<span class="why">{esc(short)}{more}{live_s}{flag_s}{tranche_s}{retires_s}'
                    f'{conv_s}{stop_s}{shares_s}{clamped_s}{stack_s}{meta}{decide_s}</span>'
                    f'<span class="amt {bucket}">${p.get("size_usd",0):,.0f}</span></div>')

        # -- rotation ideas: paired trim+buy proposals sharing a pair_id (added 2026-08-06,
        # user-reported: proposals were "only ATR risk correction," never capital rotation from
        # a stretched winner toward a name with rally tendency). Pulled OUT of the normal
        # priority-tier grouping below and rendered together, because a pair's two legs can and
        # do land in different tiers (the sell leg is often only MEDIUM while the buy leg scores
        # HIGH on signal conviction) -- splitting them across tiers would visually sever a single
        # rotation idea into two unrelated-looking rows, defeating the entire point of proposing
        # them as a pair. Legs are matched by pair_id and shown side by side with a connecting
        # arrow; a leg whose partner already got dismissed/retired independently (pair_id no
        # longer has 2 open members) falls back to rendering as an ordinary single proposal in
        # its priority tier rather than being silently dropped.
        by_pair = {}
        for p in idea_props:
            if p.get("pair_id"):
                by_pair.setdefault(p["pair_id"], []).append(p)
        complete_pairs = {pid: legs for pid, legs in by_pair.items() if len(legs) == 2}
        paired_ids = {p["id"] for legs in complete_pairs.values() for p in legs}

        def pair_card(legs):
            sell = next((p for p in legs if p.get("pair_role") == "sell"), legs[0])
            buy = next((p for p in legs if p.get("pair_role") == "buy"), legs[1])
            return (f'<div class="rotcard">'
                    f'<div class="rotleg sell">{prop_row(sell)}</div>'
                    f'<div class="rotarrow">&rarr;</div>'
                    f'<div class="rotleg buy">{prop_row(buy)}</div></div>')

        # -- IDEAS panel: ranked by conviction (fallback to priority_score for legacy rows
        # without one), capped at 5. A complete rotation pair counts as ONE slot toward the cap
        # (it's one decision), not two. A minimum bar applies -- show fewer, or zero, rather than
        # pad the list with weak ideas to hit five; "No ideas this week, book within policy" is a
        # legitimate, honest output, not a bug.
        MIN_IDEA_SCORE = 1
        singles = [p for p in idea_props if p["id"] not in paired_ids]

        def idea_rank(p):
            return p.get("conviction_score", p.get("priority_score", 0) * 10)

        ranked_items = ([("pair", legs, max(idea_rank(p) for p in legs)) for legs in complete_pairs.values()]
                        + [("single", p, idea_rank(p)) for p in singles])
        ranked_items = [it for it in ranked_items if it[2] >= MIN_IDEA_SCORE]

        # A HIGH-severity stack is never cut by the cap (added 2026-09-06, G88). The cap ranks by
        # CONVICTION, which is the right axis for choosing what to act on and the wrong one for a
        # safety warning: on the run this was found, FSLR's two open legs (P-214 Trim + P-228
        # Sell, 78.7% of the position combined) both scored below the fold, so a HIGH stack
        # warning that the engine had correctly raised appeared nowhere on the page. That is the
        # v1 defect wearing new clothes -- the guard's own docstring says a guard that only writes
        # a field repeats the defect it fixes, and a badge rendered only on rows that made a
        # conviction cut is a field nobody reads. Force these in; they are bounded (a stack needs
        # two live rows on one name) and they are exactly what the reader must not miss.
        def _has_high_stack(it):
            legs = it[1] if it[0] == "pair" else [it[1]]
            return any((l.get("stacks_on") or {}).get("severity") == "high" for l in legs)

        # Forced rows sit ON TOP OF the cap, they do not consume it. First attempt had them
        # competing for the same five slots, and on this very run all five went to stack
        # warnings -- every actual idea vanished from the Ideas panel. A safety warning and a
        # ranked idea are different things and must not be traded off against each other; the
        # cap exists to stop weak ideas padding the list, not to ration warnings.
        forced = [it for it in ranked_items if _has_high_stack(it)]
        rest = [it for it in ranked_items if not _has_high_stack(it)]
        forced.sort(key=lambda it: -it[2])
        rest.sort(key=lambda it: -it[2])
        ranked_items = forced + rest[:5]

        idea_rows = [pair_card(it[1]) if it[0] == "pair" else prop_row(it[1]) for it in ranked_items]
        if idea_rows:
            out.append('<section class="panel act"><div class="phead"><h2>Ideas</h2>'
                     '<span class="pill a">Ranked by conviction &mdash; for review, never executed</span></div>'
                     f'<div class="pbody"><div>{"".join(idea_rows)}</div>'
                     '<p class="note">To drop an idea you don\'t want to act on, just tell '
                     'Agent Smith &mdash; e.g. "dismiss P-014" &mdash; citing the id shown under '
                     'its action. It will not be re-proposed.</p></div></section>')
        else:
            out.append('<section class="panel act"><div class="phead"><h2>Ideas</h2>'
                     '<span class="pill a">Ranked by conviction</span></div>'
                     '<div class="pbody"><p class="note">No ideas this week &mdash; book within '
                     'policy, nothing cleared the conviction bar.</p></div></section>')

        # -- RISK HOUSEKEEPING panel: cap breaches, stop-raises, band drift. Sized and actionable,
        # but never ranked against an idea and never capped at 5 -- this is a maintenance queue,
        # not a competition for the top slot. Grouped by priority tier same as before.
        hrows = []
        for b in breaches:
            hrows.append(f'<div class="pr"><span class="act2">Breach</span>'
                         f'<span class="why">{esc(b)} &mdash; bring it inside the band or record why '
                         f'the breach is accepted.</span><span class="amt">&mdash;</span></div>')
        by_priority = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for p in housekeeping_props:
            by_priority.setdefault(p.get("priority", "LOW"), by_priority["LOW"]).append(p)
        for tier in ("HIGH", "MEDIUM", "LOW"):
            items = sorted(by_priority[tier], key=lambda p: -p.get("priority_score", 0))
            if not items:
                continue
            open_attr = " open" if tier == "HIGH" else ""
            hrows.append(f'<details class="pgrp {tier}"{open_attr}><summary>{tier} PRIORITY'
                        f'<span class="n">{len(items)}</span></summary>'
                        f'<div class="body">{"".join(prop_row(p) for p in items)}</div></details>')
        if hrows:
            out.append('<section class="panel act"><div class="phead"><h2>Risk housekeeping</h2>'
                     '<span class="pill a">Sized &amp; actionable &mdash; not ranked against ideas</span></div>'
                     f'<div class="pbody"><div>{"".join(hrows)}</div></div></section>')

    return out


def _render_factor_catalysts(state):
    out = []
    # -- factor catalysts --
    catalysts = [c for c in state.get("factor_catalysts", [])
                if not smith_risk.catalyst_is_suppressed(state, c.get("headline"), c.get("date"))]
    if catalysts:
        rows = []
        for i, c in enumerate(catalysts[:6]):
            dirn = {"threat": "THREAT", "tailwind": "TAILWIND"}.get(c.get("direction", ""), "AMBIGUOUS")
            # FIXED 2026-08-08 (user-reported: "&middot" rendering as literal text): affects was
            # joined with the RAW "&middot;" entity, then the whole joined string was passed
            # through esc(), which escapes the "&" a second time into "&amp;middot;" -- browsers
            # render that as the literal text "&middot;", not a dot. Escape each ticker
            # individually first, THEN join with the raw (already-safe) entity separator, same
            # fix applied to `maps` below.
            affects = " &middot; ".join(esc(x) for x in c.get("affects", []))
            exp = c.get("exposure_pct_equity")
            exp_s = f' &mdash; {exp:.1f}% equity' if isinstance(exp, (int, float)) else ""
            # "catalyst" has no natural stable id (headline+date is the real key) -- synthesize
            # one for the button's data-element-id and carry the real key along as extra data-*
            # attributes, which sync-decisions reads directly rather than looking anything up.
            extra = (f' data-headline="{esc_attr(c.get("headline",""))}" '
                    f'data-date="{esc_attr(c.get("date",""))}"')
            decide_s = decision_buttons("catalyst", f"c{i}", extra)
            rows.append(f'<div class="ci"><span class="cb {dirn}">{dirn}</span><div>'
                        f'<div class="hh">{esc(c.get("headline",""))}</div>'
                        f'<div class="mm">{esc(c.get("magnitude",""))}</div>'
                        f'<div class="aa">{affects}{exp_s}</div>{decide_s}</div></div>')
        out.append('<section class="panel"><div class="phead"><h2>Factor catalysts</h2></div>'
                 f'<div class="pbody"><div>{"".join(rows)}</div></div></section>')

    return out


def _render_trade_triggers(triggers):
    out = []
    # -- trade triggers (added 2026-08-12, user-reported: "still most of the proposals are based on
    # ATR risk-cap... I prefer oversold/overbought proposals to catch a bounce back for the good
    # stocks... book profit if something had a good enough run and put my money of another stock
    # which is yet to run"). These are compute_triggers.json's five deterministic candidate screens
    # -- the raw material the strategist turns into proposals, shown here so the reader can see WHAT
    # was available this run, not only what got proposed. A trigger firing is not a proposal.
    if triggers and (triggers.get("live_counts") or triggers.get("shadow_counts")):
        TRIG_META = {
            "oversold_reversion":      ("OVERSOLD &rarr; BUY", "b", "RSI14 &lt; 35, thesis intact/strengthening, inside ATR cap, no fundamental headwind"),
            "overbought_distribution": ("OVERBOUGHT &rarr; TRIM", "a", "RSI14 &gt; 70 and genuinely up on the month &mdash; deliberately independent of the ATR risk cap"),
            "laggard_rotation":        ("LAGGARD &rarr; BUY", "b", "bottom-quartile 1m relative strength with a healthy thesis &mdash; the &ldquo;yet to run&rdquo; destination leg"),
            "profit_ratchet":          ("RATCHET STOP", "g", "up enough that the stop should be raised to at least breakeven"),
            "scale_out_ladder":        ("SCALE OUT", "g", "gain has reached a scale-out rung"),
        }
        blocks = []
        for key, (label, cls, how) in TRIG_META.items():
            rows_t = triggers.get(key) or []
            if not rows_t:
                continue
            vote = (rows_t[0].get("vote") or "live").upper()
            vote_cls = "" if vote == "LIVE" else "warn"
            trs = []
            for c in rows_t:
                if key == "profit_ratchet":
                    amt = (f'${c["current_stop_usd"]:,.2f} &rarr; <b>${c["suggested_stop_usd"]:,.2f}</b>')
                else:
                    sz = c.get("suggested_size_usd")
                    amt = f'<b>${sz:,.0f}</b>' if sz else "&mdash;"
                rsi = c.get("rsi14")
                gain = c.get("gain_pct")
                secondary = (f"{gain:+.1f}% vs basis" if gain is not None
                             else (f"{c['abs_return_1m_pct']:+.1f}% 1m" if c.get("abs_return_1m_pct") is not None else "&mdash;"))
                # esc() each item BEFORE joining with an entity separator -- joining first and then
                # escaping turns "&middot;" into the literal visible text "&middot;" (see SKILL §6).
                why = " &middot; ".join(esc(r) for r in (c.get("reasons") or []))
                blk = "".join(f'<div class="note">! {esc(b)}</div>' for b in (c.get("blockers") or []))
                trs.append(f'<tr><td><b>{esc(c["ticker"])}</b></td>'
                           f'<td class="sub">{esc(c.get("cluster") or "-")}</td>'
                           f'<td class="num">{(f"{rsi:.1f}" if rsi is not None else "&mdash;")}</td>'
                           f'<td class="num">{secondary}</td>'
                           f'<td class="num">{amt}</td>'
                           f'<td class="sub">{why}{blk}</td></tr>')
            blocks.append(
                f'<div class="phead" style="border:0;padding:10px 0 4px"><h2 style="font-size:.82rem">'
                f'{label}<span class="sub">{how}</span></h2>'
                f'<span class="pill {vote_cls}">{esc(vote)}</span></div>'
                '<div class="tw"><table class="tbl"><thead><tr><th>Name</th><th>Cluster</th>'
                '<th>RSI14</th><th>Move</th><th>Size</th><th>Why</th></tr></thead>'
                f'<tbody>{"".join(trs)}</tbody></table></div>')
        if blocks:
            stale = (not triggers.get("rsi_usable")) or (not triggers.get("rel_usable"))
            hdr_pill = ('<span class="pill bad">STALE INPUTS</span>' if stale else
                        f'<span class="pill good">RSI {triggers.get("rsi_as_of","-")}</span>')
            dq = "".join(f'<li>{esc(x)}</li>' for x in (triggers.get("data_quality") or []))
            out.append(
                '<section class="panel act"><div class="phead"><h2>Trade triggers'
                '<span class="sub">non-ATR candidate screens &mdash; what was available, not what was proposed</span></h2>'
                f'{hdr_pill}</div><div class="pbody">'
                + "".join(blocks) +
                '<details><summary>How to read this / why it exists</summary><div class="body">'
                'Until 2026-08-12 essentially every proposal this desk produced was an <b>ATR risk-cap '
                'trim</b>. Five compounding causes: the scorer weighted <code>over_cap</code> highest '
                'and <i>penalised</i> a buy with no breach; the relative-strength cache was 12 days '
                'stale with a benchmark return <b>18.6pp wrong</b>, starving the only profit-take '
                'trigger; per-name RSI did not exist at all, so <code>OVERBOUGHT PULLBACK</code> had '
                'fired <b>once in 69</b> journal entries; the book ran on its two weakest signals '
                'while <code>OVERSOLD BOUNCE</code> (100% interim 7d, n=4) sat dormant; and '
                '<code>repeat_count</code> promoted proposals that had in effect been declined.<br><br>'
                '<b>LIVE</b> triggers may be sized into proposals now. <b>SHADOW</b> triggers are '
                'logged to trigger_journal.json with a flag price and scored at 7/30d first &mdash; '
                'they contribute <b>zero</b> to proposal priority until they earn a measured hit '
                'rate, the same rule the de-risk queue runs under.<br><br>'
                '<b>Overbought&rarr;trim is deliberately cap-independent.</b> A name comfortably '
                'inside its risk cap is still a valid profit-take; gating profit-taking on a breach '
                'is exactly what made every trim an ATR trim.<br>'
                '<b>Thresholds use hysteresis</b> &mdash; oversold fires below 35 and retires above '
                '50, overbought fires above 70 and retires below 60 &mdash; so a name hovering at a '
                'threshold does not flip between open and retired on noise.<br>'
                '<b>The quality gate for a dip-buy is the thesis, not the signal.</b> Requiring '
                'net-bullish signals would disqualify every oversold name by definition. Only a '
                'fundamental negative disqualifies.'
                + (f'<br><br><b>Data quality this run:</b><ul>{dq}</ul>' if dq else "")
                + '</div></details></div></section>')

    return out


def _render_factor_themes(state):
    out = []
    # -- factor themes (added 2026-08-06, dashboard feature review). Standing structural view,
    # companion to Factor catalysts above: catalysts are event-driven (this week's news),
    # themes are the persistent watch list each catalyst gets checked against. state.factor_themes
    # was populated and updated every run by smith-catalyst and rendered nowhere.
    themes = (state.get("factor_themes") or {}).get("themes", [])
    if themes:
        rows = []
        for th in themes[:8]:
            # same double-escape fix as `affects` above
            maps = " &middot; ".join(esc(x) for x in th.get("maps_to", [])[:10])
            live_keys = sorted([k for k in th if k.startswith("live_")], reverse=True)
            latest_live = th.get(live_keys[0]) if live_keys else None
            live_s = (f'<div class="mm">{esc(latest_live)}</div>' if latest_live else "")
            rows.append(f'<div class="ci"><span class="cb AMBIGUOUS">WATCH</span><div>'
                        f'<div class="hh">{esc(th.get("name",""))}</div>'
                        f'<div class="mm" style="font-style:italic">{esc(th.get("watch",""))}</div>'
                        f'{live_s}<div class="aa">{maps}</div></div></div>')
        out.append('<section class="panel"><div class="phead"><h2>Factor themes'
                 '<span class="sub">the standing watch list catalysts get checked against</span></h2></div>'
                 f'<div class="pbody"><div>{"".join(rows)}</div></div></section>')

    return out


def _render_diversifier_bench(state):
    out = []
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
        # Buttons render as a compact separate list rather than inside the chips themselves --
        # decision_buttons() emits a <div>, which doesn't nest inside the existing <span> chip
        # markup without breaking it, and the chips stay the at-a-glance view either way.
        decide_rows = "".join(
            f'<div class="srow"><span class="slab">{esc(tk)}</span>'
            f'<span>{decision_buttons("diversifier", tk)}</span></div>' for tk, v in rows)
        out.append('<section class="panel"><div class="phead"><h2>Diversifier bench'
                 '<span class="sub">non-AI-capex candidates, not held</span></h2>'
                 '<span class="pill">green = clean diversifier &middot; amber = has AI-adjacent overlap</span>'
                 f'</div><div class="pbody"><div class="chips">{chips}</div>'
                 '<p class="note">Priced by smith-scout each deep run; not a proposal to buy, a bench '
                 'of what a genuine hedge to this book\'s single-factor concentration would look like.</p>'
                 f'<details><summary>Not interested in one of these?</summary><div class="body">{decide_rows}</div></details>'
                 '</div></section>')

    return out


def _render_rotation_analysis(rotation):
    out = []
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
        out.append('<section class="panel"><div class="phead"><h2>Rotation analysis</h2>'
                 '<span class="pill">thesis &times; signal history &times; risk headroom</span></div>'
                 '<div class="pbody"><p class="note">Rule-based: <b>Accumulate</b> = strengthening thesis + '
                 'net-bullish signals. <b>Rotate out</b> = watch thesis + net-bearish signals. '
                 '<b>Trim &mdash; risk cap</b> = over its ATR risk cap, regardless of thesis or signal. '
                 'Everything else is unchipped (thesis and signal disagree, or both are flat). '
                 'MOMENTUM+VOLUME and TARGET GAP are excluded from the signal count &mdash; both fire on '
                 'moves in either direction by their own definition, so neither is unambiguously bullish '
                 'or bearish.</p>'
                 f'<div class="rgrid">{rgrid}</div></div></section>')

    return out


def _render_clusters(drift, state, held_tickers, risk_by_ticker, thesis_status, sector_map):
    out = []
    # -- clusters (moved 2026-08-07: swapped position with de-risk queue, per user request --
    # user wanted Clusters surfaced as a decision-relevant section, not buried after the
    # composition treemap) --
    cluster_table = drift.get("cluster_table", [])
    if cluster_table:
        # -- per-cluster member holdings (added 2026-08-08, user-requested: "make modification
        # so that I can open/expand a particular cluster and see the stock in that cluster and
        # some relevant info of these stocks. May be add which stock is peer leader and
        # otherwise"). Cluster -> held tickers, from sector_map (the same source of truth the
        # thesis map and risk pipeline already use, not a re-derivation). sector_map is a
        # superset that also retains exited/tracked-only tickers (2026-08-07: rendered as
        # struck-through "no longer held" chips per member table, reusing the .tick.gone
        # convention from the Signal History section).
        holdings_by_ticker = {h["ticker"]: h for h in state.get("holdings", [])}
        cluster_members = {}
        cluster_ghosts = {}
        for tk, cl in sector_map.items():
            if not cl:
                continue
            (cluster_members if tk in held_tickers else cluster_ghosts).setdefault(cl, []).append(tk)
        signal_history = state.get("signal_history") or {}
        thesis = state.get("thesis") or {}
        thesis_dot = {"strengthening": "dot-g", "watch": "dot-w", "broken": "dot-b"}

        def member_rows(cluster_name):
            members = cluster_members.get(cluster_name, [])
            members = sorted(members, key=lambda tk: -(holdings_by_ticker.get(tk, {}).get("weight_pct") or 0))
            out = []
            for tk in members:
                h = holdings_by_ticker.get(tk, {})
                rpos = risk_by_ticker.get(tk, {})
                qty, mv = h.get("qty"), rpos.get("market_value_usd")
                price = (mv / qty) if (mv and qty) else None
                st = thesis_status(thesis.get(tk))
                st_s = (f'<span class="{thesis_dot.get(st,"dot-w")}" style="display:inline-block;'
                       f'width:7px;height:7px;border-radius:50%;margin-right:5px"></span>{esc(st)}'
                       if st else '<span style="color:var(--ink-3)">&mdash;</span>')
                buckets = signal_history.get(tk) or []
                peer_s = ""
                if "PEER LEADER" in buckets:
                    peer_s = '<span class="peer-tag lead">PEER LEADER</span>'
                elif "PEER LAGGARD" in buckets:
                    peer_s = '<span class="peer-tag lag">PEER LAGGARD</span>'
                other_tags = "".join(
                    f'<span class="tick {"g" if b in smith_risk.SIGNAL_POLARITY["bullish"] else "b" if b in smith_risk.SIGNAL_POLARITY["bearish"] else ""}" '
                    f'style="margin-left:4px">{esc(b)}</span>'
                    for b in buckets if b not in ("PEER LEADER", "PEER LAGGARD"))
                cap_s = (f'<span class="neg" title="{rpos.get("cap_multiple",0):.2f}x its ATR risk cap">&#9888;&#65039;</span>'
                        if rpos.get("over_cap") else "")
                out.append(
                    f'<tr><td class="name">{esc(tk)}</td>'
                    f'<td>{h.get("weight_pct",0):.2f}%</td>'
                    f'<td>{f"${price:,.2f}" if price is not None else "&mdash;"}</td>'
                    f'<td class="txt">{st_s}</td>'
                    f'<td class="txt">{peer_s}{other_tags}</td>'
                    f'<td>{cap_s}</td></tr>')
            return "".join(out)

        rows = []
        for c in sorted(cluster_table, key=lambda r: -r.get("actual_pct_of_equity", r.get("actual_pct", 0))):
            cname = c.get("cluster", "")
            band_c = c.get("band_pct") or [0, 100]
            lo, hi = band_c[0] or 0, band_c[1] or 100
            actual = c.get("actual_pct_of_equity", c.get("actual_pct", 0))
            tgt = c.get("target_pct") or 0
            scale = max(hi, actual, tgt, 1) * 1.15
            pc = lambda v: max(0, min(100, v / scale * 100))
            breach = c.get("breach")
            n_members = len(cluster_members.get(cname, []))
            body_rows = member_rows(cname)
            ghosts = sorted(cluster_ghosts.get(cname, []))
            ghost_html = (
                '<p class="note" style="margin-top:8px">No longer held / tracked only: '
                + "".join(f'<span class="tick gone" style="margin-right:4px">{esc(tk)}</span>' for tk in ghosts)
                + '</p>') if ghosts else ""
            body = ((f'<div class="scroll"><table><thead><tr><th>Name</th><th>Wt</th><th>Price</th>'
                    f'<th>Thesis</th><th>Signals</th><th></th></tr></thead>'
                    f'<tbody>{body_rows}</tbody></table></div>' if body_rows else
                    '<p class="note">No held ticker maps to this cluster.</p>') + ghost_html)
            rows.append(
                # the row's 5 cells are wrapped in a nested div.clus-summary-grid, NOT styled
                # directly on <summary> -- see the CSS fix note in the stylesheet above
                f'<details class="clus-row"{" open" if breach else ""}><summary><div class="clus-summary-grid">'
                f'<span class="name">{esc(cname)}<i>{n_members} held</i></span>'
                f'<span class="num">{actual:.2f}%</span>'
                f'<span class="num {"neg" if breach else "pos"}">{c.get("actual_pct_of_total_book",0):.2f}%</span>'
                f'<span class="num blank">[{lo:g},{hi:g}]</span>'
                f'<div class="band"><div class="ok" style="left:{pc(lo):.1f}%;width:{pc(hi)-pc(lo):.1f}%"></div>'
                f'<div class="tgt" style="left:{pc(tgt):.1f}%"></div>'
                f'<div class="mk{" bad" if breach else ""}" style="left:{pc(actual):.1f}%"></div></div>'
                f'</div></summary><div class="body">{body}</div></details>')
        out.append(
            '<section class="panel"><div class="phead"><h2>Clusters</h2>'
            '<span class="pill">ceiling on book &middot; floor on equity &middot; click a cluster to see its holdings</span></div>'
            f'<div class="pbody" style="gap:0"><div class="clus-hdr"><span></span>'
            '<span class="num">Equity</span><span class="num">Book</span>'
            '<span class="num">Band</span><span></span></div>'
            f'{"".join(rows)}</div></section>')

    return out


def _render_stop_loss_efficacy(stops_data):
    out = []
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

        out.append(
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

    return out


def _render_the_read_and_macro(narr, market_inputs, state, book_compute):
    out = []
    # -- the read + macro strip --
    session_text = narr.get("session_read")
    if session_text:
        short, rest = trim_lead(session_text, 400)
        more = (f'<details><summary>more</summary><div class="body">{esc(rest)}</div></details>'
                if len(rest) > 40 else "")
        gate = market_inputs.get("gate_classification")
        gate_pill = (f'<span class="pill {"b" if gate=="ESCALATING" else ("w" if gate=="AMBIGUOUS" else "g")}">'
                     f'Gate {esc(gate.title())}</span>') if gate else ""
        out.append(f'<section class="panel"><div class="phead"><h2>The read</h2>'
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
            out.append('<hr class="rule"><div class="macro">' + "".join(
                f'<div class="col"><span class="k">{esc(k)}</span><span class="v">{esc(v)}</span>'
                f'<span class="s">{esc(s)}</span></div>' for k, v, s in macro_cells) + '</div>')
        out.append('</div></section>')

    return out


def _render_sentiment_session_grid(state, market_inputs):
    out = []
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
        out.append(f'<div class="grid2">{left}{right}</div>')

    return out


def _render_week_ahead(state, ts):
    out = []
    # ================= the week ahead =================
    earnings_cal = dict(ticker_rows(state.get("data_cache", {}).get("earnings_calendar", {})))
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
    out.append('<section class="panel"><div class="phead"><h2>The week ahead</h2></div>'
             f'<div class="pbody"><div class="cal">{"".join(days)}</div></div></section>')

    return out


def _render_watchlist_setups(state):
    out = []
    # -- watchlist setups (added 2026-08-25, interactive dashboard). Previously fed only into
    # entry_setup triggers with no standalone rendering of its own -- these buttons let a
    # setup get suppressed or promoted directly, which entry_setup/bench_diversifier trigger
    # generation reads back via smith_risk.is_watchlist_suppressed.
    wl_setups = [w for w in (state.get("watchlist_setups") or [])
                if not smith_risk.is_watchlist_suppressed(state, w.get("ticker"))]
    if wl_setups:
        wrows = "".join(
            f'<div class="srow"><span class="slab">{esc(w.get("ticker",""))} '
            f'<i>{esc(w.get("type",""))}</i></span>'
            f'<span style="font-size:12.5px">{w.get("upside_pct","-")}% upside, '
            f'pos {w.get("pos","-")}{decision_buttons("watchlist", w.get("ticker",""))}</span></div>'
            for w in sorted(wl_setups, key=lambda w: -(w.get("upside_pct") or 0)))
        out.append('<section class="panel"><div class="phead"><h2>Watchlist setups'
                 '<span class="sub">not held -- entry candidates smith-watchlist scans for</span></h2></div>'
                 f'<div class="pbody"><div>{wrows}</div>'
                 f'<p class="note">As of {esc(state.get("watchlist_setups_as_of","-"))}. '
                 'Not a proposal to buy -- the raw material entry_setup triggers score against.</p>'
                 '</div></section>')

    return out


def _render_derisk_queue(derisk, state):
    out = []
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

        def _derisk_cell(r):
            # An override never removes the ticker from the queue -- see
            # smith_risk.derisk_override_for's own docstring: a real risk signal is only ever
            # annotated, not suppressed. Already-overridden tickers show the standing note
            # instead of the button (re-disagreeing with yourself isn't a new data point).
            ov = smith_risk.derisk_override_for(state, r["ticker"])
            if ov:
                return (f'<span class="rvf">&#9888;&#65039; user disagrees: '
                       f'{esc((ov.get("reason") or "")[:120] or "no reason given")} '
                       f'({esc(ov.get("date",""))})</span>')
            return decision_buttons("derisk", r["ticker"])

        def _thesis_cell(status):
            cls = {"strengthening": "g", "intact": "g", "watch": "w", "broken": "b"}.get(status, "")
            lbl = (status or "unknown").upper()
            return f'<span class="pill {cls}">{esc(lbl)}</span>'

        body = "".join(
            f'<tr><td class="num">{r["rank"]}</td><td><b>{esc(r["ticker"])}</b></td>'
            f'<td class="num"><b>{r["derisk_score"]:.0f}</b></td>'
            f'<td>{bar(r.get("fragility_score"), "f")}</td>'
            f'<td>{bar(r.get("stretch_score"), "s")}</td>'
            f'<td>{_thesis_cell(r.get("thesis_status"))}</td>'
            f'<td class="num">{(f"{r["abs_return_1m_pct"]:+.1f}%" if r.get("abs_return_1m_pct") is not None else "&mdash;")}</td>'
            f'<td class="num">{(f"{r["rel_strength_1m_pp"]:+.1f}" if r.get("rel_strength_1m_pp") is not None else "&mdash;")}</td>'
            f'<td class="num">{(f"{r["cap_multiple"]:.2f}x" if r.get("cap_multiple") else "&mdash;")}</td>'
            f'<td class="num">${r["market_value_usd"]:,.0f}</td>'
            f'<td class="sub">{_derisk_cell(r)}</td></tr>'
            for r in shown)

        out.append(
            '<section class="panel"><div class="phead"><h2>De-risk queue'
            '<span class="sub">ranked by damage-if-a-drawdown-comes, not by prediction</span></h2>'
            f'<span class="pill {st_cls}">{esc(st_lbl)}</span></div><div class="pbody">'
            f'<p class="note">{esc(derisk.get("headline",""))}</p>'
            '<div class="tw"><table class="tbl"><thead><tr><th>#</th><th>Name</th><th>Score</th>'
            '<th>Fragility</th><th>Stretch</th><th>Thesis</th><th>1m abs</th><th>vs SMH</th>'
            '<th>cap</th><th>Value</th><th></th></tr></thead>'
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
            '<b>Thesis</b> &mdash; the current per-name thesis status from smith-thesis. This is what '
            'turns a fragility/stretch reading into a decision: a fragile, stretched name on a '
            'STRENGTHENING or INTACT thesis is a candidate to trim into strength and stay long; the '
            'same fragility on a WATCH or BROKEN thesis is a candidate to cut, not just trim.<br>'
            'Sentiment (book-wide urgency dial, band &rarr; multiplier) still scales the whole '
            'queue behind the scenes but is no longer shown as its own column &mdash; it cannot '
            'manufacture stretch that does not exist per name, so it belongs in the score, not the '
            'table.<br><br>'
            '<b>This queue is shadow-scored and does not drive proposals.</b> Each deep run logs its '
            'top names to derisk_journal.json and scores them at 30/90d. It earns a vote in sizing '
            'decisions only once it has a real hit rate.'
            '</div></details></div></section>')

    return out


def _render_risk_cap_and_ltcg(risk, book_compute, base):
    out = []
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

    if riskcap_html:
        out.append(riskcap_html)

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
        out.append(f'<section class="panel"><div class="phead"><h2>LTCG watch'
                 f'<span class="sub">lots within 6mo of the {ltcg_months}-month boundary</span></h2>'
                 f'<span class="pill w">{len(ltcg_flags)} lots</span></div>'
                 f'<div class="pbody">{rows}</div></section>')
    elif os.path.exists(os.path.join(base, "lots.json")):
        out.append(f'<section class="panel"><div class="phead"><h2>LTCG watch'
                 f'<span class="sub">lots within 6mo of the {ltcg_months}-month boundary</span></h2>'
                 '<span class="pill g">clear</span></div>'
                 '<div class="pbody"><p class="note">No lot sits within 6 months of the '
                 f'{ltcg_months}-month LTCG boundary right now.</p></div></section>')

    return out


def _render_positions_table(state, risk_by_ticker, sector_map, risk, book_compute):
    out = []
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

        out.append(f'<section class="panel"><div class="phead"><h2>Positions<span class="sub">'
                 f'{len(holdings)}</span></h2></div><div class="pbody"><div class="scroll"><table>'
                 '<thead><tr><th>Name</th><th>Cluster</th><th>Qty</th><th>Price</th><th>Value</th><th>Wt</th>'
                 '<th>ATR20</th><th>&beta;</th><th>Stop</th><th>Stop px</th><th>Cap</th><th>Headroom</th></tr></thead>'
                 f'<tbody>{"".join(rows)}</tbody>{foot}</table></div></div></section>')

    return out


def _render_thesis_map(state, held_tickers, sector_map, thesis_status, thesis_text, thesis_evidence):
    out = []
    def _thesis_chips(items):
        """Render thesis chips with both evidence sides in the tooltip (G58, 2026-08-10).

        The chip's hover text used to be the bare one-liner -- which is exactly the artifact
        that lost 'despite Q4 EPS beat' on SNDK. Now the tooltip carries FOR / AGAINST
        explicitly, and an entry with a non-empty `evidence_against` gets a visible marker so
        a contested verdict is legible without hovering at all. Legacy string entries render
        as before, tagged unverified, so migration is visible rather than silent."""
        out = []
        for tk, body, raw in sorted(items, key=lambda i: i[0]):
            ef, ea, ver = thesis_evidence(raw)
            tip = [body[:200]] if body else []
            if ef:
                tip.append("FOR: " + " · ".join(str(e.get("claim", ""))[:90] for e in ef[:3]))
            if ea:
                tip.append("AGAINST: " + " · ".join(str(e.get("claim", ""))[:90] for e in ea[:3]))
            if isinstance(raw, dict):
                tip.append(f"verified: {ver or 'unverified'}"
                           + (f" ({raw.get('verified_against')})" if raw.get("verified_against") else ""))
            else:
                tip.append("pre-G58 entry -- single-sided, treated as unverified")
            # a dagger marks a contested verdict (both sides non-empty); a degree sign marks
            # an entry that has not been migrated to the evidence schema at all.
            mark = ""
            if isinstance(raw, dict):
                if ef and ea:
                    mark = '<sup title="contested -- evidence on both sides">&dagger;</sup>'
                elif ver in ("primary", "secondary"):
                    mark = '<sup title="source-verified">&check;</sup>'
            else:
                mark = '<sup title="pre-G58, single-sided">&deg;</sup>'
            # NOTE: .chip is `display:inline-flex; flex-direction:column`, so every DIRECT child
            # becomes its own row. The ticker and its marker must therefore be wrapped in a
            # single child element -- emitting a bare <sup> alongside the text would drop the
            # marker onto its own line between the ticker and the sector label. Same family of
            # trap as the 2026-08-08 <summary>-as-grid bug: valid markup, wrong layout, and
            # invisible to any tag-balance check.
            out.append(f'<span class="chip" title="{esc(" | ".join(tip))}">'
                       f'<span>{esc(tk)}{mark}</span>'
                       f'<i>{esc(sector_map.get(tk, "-"))}</i></span>')
        return "".join(out)

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
            # G58 (2026-08-10): entries are now either a legacy bare string or the evidence
            # object. Route both through the shared shims so this panel never re-derives a
            # second, divergent parse -- and so an unmigrated name still renders.
            st = thesis_status(txt)
            body = thesis_text(txt)   # handles both shapes -- smith_risk, consolidated 2026-08-16
            # status is usually a bare keyword but sometimes carries a bracketed note
            # (e.g. "strengthening [position closed ...]") -- thesis_status matches by prefix.
            # Membership-check the dict (not `groups.get(st) or other` -- an empty list is
            # falsy, so that pattern silently sent every ticker to `other` on every run).
            target = groups[st] if st in groups else other
            target.append((tk, body, txt))
        dotcls = {"strengthening": "dot-g", "watch": "dot-w", "broken": "dot-b"}
        blocks = []
        for st in ("strengthening", "watch", "broken"):
            items = groups[st]
            if not items:
                continue
            blocks.append(f'<div class="grp-h"><span class="{dotcls[st]}"></span>{st.title()}</div>'
                          f'<div class="chips" style="margin-bottom:12px">{_thesis_chips(items)}</div>')
        if other:
            blocks.append(f'<div class="grp-h">Other</div>'
                          f'<div class="chips" style="margin-bottom:12px">{_thesis_chips(other)}</div>')
        # G58: count how many held names still lack two-sided evidence, and say so plainly.
        # A dashboard that hides its own coverage gap invites more trust than the data earns --
        # same reasoning as the data-quality panel added 2026-08-06.
        n_two_sided = sum(1 for _tk, _b, raw in
                          [i for grp in list(groups.values()) + [other] for i in grp]
                          if isinstance(raw, dict)
                          and raw.get("evidence_for") is not None
                          and raw.get("evidence_against") is not None)
        cov = (f'<p class="note" style="margin-top:8px">Hover any ticker for its thesis, '
               f'evidence on both sides, and how it was verified. '
               f'<b>{n_two_sided} of {len(thesis)}</b> carry two-sided evidence (G58); the rest are '
               f'pre-migration entries still holding a single-sided one-liner and are treated as '
               f'<i>unverified</i> until smith-thesis next revisits them.</p>')
        # Confirm/Override rows, one per held name -- a separate compact list rather than
        # embedded in each chip (the chips are deliberately tiny; a button group doesn't fit).
        thesis_decide_rows = "".join(
            f'<div class="srow"><span class="slab">{esc(tk)} <i>{esc(thesis_status(txt) or "?")}</i></span>'
            f'<span>{decision_buttons("thesis", tk)}</span></div>'
            for tk, txt in sorted(thesis.items(), key=lambda kv: kv[0]))
        out.append(f'<details><summary>Thesis map<span class="c">{len(thesis)} of {len(held_tickers)} held</span></summary>'
                 f'<div class="body">{"".join(blocks)}{cov}'
                 f'<details style="margin-top:10px"><summary>Confirm or override a verdict</summary>'
                 f'<div class="body">{thesis_decide_rows}'
                 f'<p class="note" style="margin-top:6px">Override requires a reason -- your own '
                 f'read of the company is real signal and can move the status, but it is recorded '
                 f'as <code>user_stated</code>, never upgraded to a sourced verification.</p>'
                 f'</div></details></div></details>')

    return out


def _render_signal_history(state, held_tickers):
    out = []
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
        out.append(f'<details><summary>Signal history<span class="c">bullish / bearish</span></summary>'
                 f'<div class="body">{body}</div></details>')

    return out


def _render_open_gaps(state):
    out = []
    # -- open (non-closed) data gaps --
    gaps = [g for g in state.get("known_gaps", []) if g.get("status") not in ("closed", "wont_fix")]
    if gaps:
        rows = []
        for g in gaps:
            # A gap carrying a standing user_decision is never given a Mark Resolved button --
            # sync-decisions' server-side guard would skip the click anyway (see smith_math.py),
            # but not offering the button at all is the honest version of that same rule: it
            # tells the reader up front this one needs a chat conversation, not a tap.
            decide_s = "" if g.get("user_decision") else decision_buttons("gap", g.get("id", ""))
            rows.append(f'<div class="srow"><span class="slab"><b>{esc(g.get("id",""))}</b></span>'
                       f'<span style="font-size:12.5px;color:var(--ink-2)">{esc(g.get("description",""))[:280]}{decide_s}</span></div>')
        out.append(f'<details><summary>Open data gaps<span class="c">{len(gaps)} open</span></summary>'
                 f'<div class="body">{"".join(rows)}</div></details>')

    return out


def _render_retired_recent(props):
    out = []
    # -- auto-retired proposals, with a Revive button (added 2026-08-25, interactive dashboard).
    # Today's HIGH/MEDIUM/LOW tiers only ever show OPEN proposals -- once something auto-retires
    # there was previously no way to say "no, I disagree, keep this" short of a chat message
    # re-deriving why. Scoped to the most recent 15 so this doesn't become an ever-growing wall;
    # a revive is meant to catch something that JUST retired, not resurrect old history.
    retired_recent = sorted([p for p in props.get("proposals", []) if p.get("status") == "auto_retired"],
                            key=lambda p: p.get("retired_on") or "", reverse=True)[:15]
    if retired_recent:
        rows = []
        for p in retired_recent:
            decide_s = decision_buttons("auto_retired_proposal", p.get("id", ""))
            rows.append(f'<div class="srow"><span class="slab"><b>{esc(p.get("id",""))}</b> '
                       f'{esc(p.get("action",""))}</span>'
                       f'<span style="font-size:12.5px;color:var(--ink-2)">'
                       f'{esc((p.get("retired_reason") or "")[:200])}{decide_s}</span></div>')
        out.append(f'<details><summary>Recently auto-retired<span class="c">{len(retired_recent)} shown</span></summary>'
                 f'<div class="body">{"".join(rows)}</div></details>')

    return out


def _render_execution_log(trades_data):
    out = []
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
        out.append(f'<details><summary>Execution log<span class="c">{len(exec_trades)} trades, '
                 f'most recent 25 shown</span></summary><div class="body">{"".join(rows)}'
                 '<p class="note" style="margin-top:8px">Every entry carries the rationale '
                 'captured at the time -- hover the notes in trades.json for the full text.</p>'
                 '</div></details>')

    return out


def _render_data_quality(state, book_compute, risk, drift, derisk):
    out = []
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
        out.append(f'<details><summary>Data quality caveats<span class="c">{len(dq_all)} this run</span></summary>'
                 f'<div class="body">{rows}</div></details>')

    return out


def _render_self_learning(base):
    out = []
    # -- self-learning (added 2026-08-25, Phase 2). Nothing surfaced the engagement-rate
    # collapse before this -- it is the single most important number about this system right
    # now (61.5% of terminal proposals acted-on in July, 2.4% in August) and was sitting
    # unread in proposals.json the entire time the standing complaint escalated across three
    # reports. Rendered period-keyed, matching learn-revealed-preference's own hard rule:
    # never pool engagement rate across periods into one blended figure -- that is exactly the
    # mistake that produced the false $700-vs-$360 size effect this same audit found and
    # retracted (see the lessons list rendered below).
    try:
        rp = smith_learning.compute_revealed_preference(base)
    except Exception:
        rp = {}
    learning_store = load(os.path.join(base, "learning.json"), {})
    lessons = sorted(learning_store.get("lessons", []), key=lambda l: l.get("date") or "", reverse=True)[:5]
    trig_j = load(os.path.join(base, "trigger_journal.json"), {})
    derisk_j = load(os.path.join(base, "derisk_journal.json"), {})
    if rp or lessons or trig_j.get("hit_rate_by_key") or derisk_j.get("hit_rate_by_key"):
        rows = []
        if rp:
            rows.append('<div class="srow"><span class="slab">Engagement rate</span>'
                        '<span style="font-size:12.5px;color:var(--ink-2)">'
                        'share of terminal proposals (acted / acted+ignored+dismissed) '
                        'that were actually acted on -- period-keyed, never pooled</span></div>')
            for period, p in sorted(rp.items(), reverse=True):
                er = p.get("engagement_rate_pct")
                er_s = f'{er:.1f}%' if er is not None else '&mdash;'
                rows.append(f'<div class="srow"><span class="slab">{esc(period)}</span>'
                            f'<span style="font-size:12.5px">{er_s} '
                            f'(acted {p["acted"]["n"]} / ignored {p["ignored"]["n"]} / '
                            f'dismissed {p["dismissed"]["n"]}, n={p["terminal_n"]})</span></div>')
        for label, journal_data in (("Shadow trigger hit rates", trig_j),
                                    ("De-risk queue hit rates", derisk_j)):
            hrk = journal_data.get("hit_rate_by_key")
            if hrk:
                bits = " &middot; ".join(f'{esc(k)} {v["hit_rate_pct"]}% (n={v["n"]})'
                                         for k, v in hrk.items())
                rows.append(f'<div class="srow"><span class="slab">{esc(label)}</span>'
                            f'<span style="font-size:12.5px">{bits}</span></div>')
        try:
            stopcal = smith_learning.compute_stop_calibration(base)
        except Exception:
            stopcal = {}
        if stopcal.get("overall", {}).get("n"):
            ov = stopcal["overall"]
            coh_bits = " &middot; ".join(
                f'{esc(k)} {v.get("win_rate_pct")}% (n={v.get("n")})'
                for k, v in stopcal.get("by_cohort", {}).items() if v.get("n"))
            rows.append(f'<div class="srow"><span class="slab">Stop-distance calibration</span>'
                        f'<span style="font-size:12.5px">overall {ov["win_rate_pct"]}% '
                        f'(n={ov["n"]}) &mdash; {esc(ov["signal"])}. {coh_bits}. '
                        f'Escalation-only, policy.json untouched.</span></div>')
        if lessons:
            lbits = "".join(f'<div class="srow"><span class="slab">{esc(l.get("kind",""))}'
                            f' &middot; {esc(l.get("date",""))}</span>'
                            f'<span style="font-size:12px;color:var(--ink-2)">'
                            f'{esc((l.get("text") or "")[:220])}</span></div>' for l in lessons)
            rows.append(f'<details><summary>Recent lessons<span class="c">{len(lessons)} shown, '
                       f'{len(learning_store.get("lessons") or [])} total</span></summary>'
                       f'<div class="body">{lbits}</div></details>')
        # Escalated parameters (added 2026-08-25, interactive dashboard) -- this is the ONE
        # surface across all 9 where a click IS the intended learning mechanism, not a proxy
        # for one: `escalated` means a parameter has enough n to have a real opinion but wants
        # to move further than its bounded band allows, and promote() will never self-apply
        # that (see smith_learning.py's own comment on the point of the state). Approve is the
        # explicit human sign-off the state machine has been waiting for; Defer just leaves it
        # escalated, re-surfacing next run.
        escalated = {pid: p for pid, p in (learning_store.get("parameters") or {}).items()
                    if p.get("state") == "escalated"}
        if escalated:
            erows = "".join(
                f'<div class="srow"><span class="slab">{esc(pid)}</span>'
                f'<span style="font-size:12.5px">default {p.get("default")} &rarr; wants '
                f'{p.get("measured")} (n={p.get("n")}, band &plusmn;{p.get("band_pct")}%)'
                f'{decision_buttons("learning_param", pid)}</span></div>'
                for pid, p in escalated.items())
            rows.append(f'<details open><summary>Escalated parameters -- your call'
                       f'<span class="c">{len(escalated)} waiting</span></summary>'
                       f'<div class="body">{erows}</div></details>')
        out.append('<details><summary>Self-learning<span class="c">Phase 0-2</span></summary>'
                 f'<div class="body">{"".join(rows)}</div>'
                 '<p class="note" style="margin-top:8px">Observational only -- nothing here '
                 'auto-sizes a position yet. See learning.json / learn-status for the full '
                 'parameter state machine.</p></details>')

    return out


def _render_historical_charts(ch, policy):
    out = []
    # -- historical charts, separate collapsed panel --
    cap = policy.get("max_single_position_pct", 12)
    hist_charts = "".join([
        fig(ch.get("bookvalue"), "Book value & cash", "every ledger row"),
        fig(ch.get("drawdown"), "Drawdown vs trim ladder", "pre-committed rungs"),
        fig(ch.get("relative"), "Book vs SMH", "per period, clean data only"),
        fig(ch.get("weights"), "Position weights", f"against the {cap}% cap"),
    ])
    if hist_charts:
        out.append('<section class="panel"><div class="pbody" style="gap:0">'
                 '<details><summary>Historical charts<span class="c">ledger &middot; drawdown &middot; '
                 'benchmark &middot; weights</span></summary>'
                 f'<div class="body" style="display:flex;flex-direction:column;gap:26px">{hist_charts}</div>'
                 '</details></div></section>')

    return out


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
    triggers = run_file("compute_triggers.json")
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
    # moved up from the positions-table section (2026-08-08) so the cluster-expand feature below
    # can use it too -- single definition, both call sites read the same dict.
    risk_by_ticker = {r["ticker"]: r for r in risk.get("positions", [])}

    # These three were local reimplementations of a shape-parse that also existed three times
    # over in smith_math. Consolidated 2026-08-16 into smith_risk, which every consumer already
    # imports. This copy was the only CORRECT one (it whitelisted known statuses instead of
    # returning raw rpartition output) -- that behaviour is what the shared version adopted.
    thesis_status = smith_risk.thesis_status
    thesis_text = smith_risk.thesis_text

    thesis_evidence = smith_risk.thesis_evidence

    H = []
    H.append(f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
             f'<meta name="viewport" content="width=device-width,initial-scale=1">'
             f'<title>Agent Smith - US Book</title><style>{CSS}{chart_css(base)}</style>'
             f'</head><body><div class="wrap">'
             # Always emitted empty on a freshly-built page (added 2026-08-25) -- sync-decisions
             # has already drained whatever the live artifact was holding BEFORE this rebuild
             # ran (see SKILL.md's step 1.7), so a fresh build never has pending decisions to
             # carry forward. The client JS below appends to this array and republishes; it is
             # never populated server-side.
             '<script type="application/json" id="smith-decisions">[]</script>')

    # ---------------- masthead ----------------
    mode_label = "US Deep Review" if state.get("mode") == "deep" else "US"
    H.append(f'<header class="mast"><h1>Agent Smith <span>&middot; {esc(mode_label)}</span></h1>'
             f'<div class="stamp">{esc(ts[:16].replace("T"," "))}'
             f'<br>USD/INR {us.get("usdinr","-")} &middot; stops on ATR20 &middot; betas vs SMH</div></header>')

    # ---------------- status strip ----------------
    H.append(status_strip(us, dd, cash_pct, cash_band, cash_breach, risk, drift, book_compute))

    # ================= TIER: DECISIONS =================
    H.append('<div class="tier"><h2>Decisions</h2><div class="ln"></div></div>')

    H.extend(_render_accepted_awaiting_execution(props))

    H.extend(_render_ideas_and_housekeeping(props, policy, state, cash_breach, cash_pct, cash_band))

    H.extend(_render_factor_catalysts(state))

    H.extend(_render_trade_triggers(triggers))

    H.extend(_render_factor_themes(state))

    H.extend(_render_diversifier_bench(state))

    H.extend(_render_rotation_analysis(rotation))

    H.extend(_render_clusters(drift, state, held_tickers, risk_by_ticker, thesis_status, sector_map))

    H.extend(_render_stop_loss_efficacy(stops_data))

    H.extend(_render_the_read_and_macro(narr, market_inputs, state, book_compute))

    H.extend(_render_sentiment_session_grid(state, market_inputs))

    H.extend(_render_week_ahead(state, ts))

    H.extend(_render_watchlist_setups(state))

    # ================= TIER: BOOK COMPOSITION =================
    H.append('<div class="tier"><h2>Book composition</h2><div class="ln"></div></div>')

    # FIXED 2026-08-08: fig()'s `sub` param is passed through esc() internally (see its
    # definition above), so it needs the literal "·" character here, not the "&middot;" HTML
    # entity -- esc() would escape the "&" a second time into the literal text "&middot;".
    H.append(fig(ch.get("treemap"), "Allocation treemap",
                 "size = weight · color = cluster · red outline = over risk cap"))

    # -- de-risk queue (moved 2026-08-07: swapped position with clusters, per user request) --
    H.extend(_render_derisk_queue(derisk, state))

    H.extend(_render_risk_cap_and_ltcg(risk, book_compute, base))

    H.extend(_render_positions_table(state, risk_by_ticker, sector_map, risk, book_compute))

    # ================= TIER: DIAGNOSTICS =================
    H.append('<div class="tier"><h2>Diagnostics</h2><div class="ln"></div></div>')
    H.append('<div class="t3">')

    H.extend(_render_thesis_map(state, held_tickers, sector_map, thesis_status, thesis_text, thesis_evidence))

    H.extend(_render_signal_history(state, held_tickers))

    H.extend(_render_open_gaps(state))

    H.extend(_render_retired_recent(props))

    H.extend(_render_execution_log(trades_data))

    H.extend(_render_data_quality(state, book_compute, risk, drift, derisk))

    H.extend(_render_self_learning(base))

    H.append('</div>')  # /t3

    H.extend(_render_historical_charts(ch, policy))

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

    H.append(DASHBOARD_JS)
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

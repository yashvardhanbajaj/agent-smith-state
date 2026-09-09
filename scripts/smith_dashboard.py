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
import re
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
    # COMPACT (2026-09-06): the full sentence used to render inline every time -- now the badge
    # is a short chip, everything else lives in the hover tooltip.
    return (f'<span class="held-badge" title="You put this on hold {esc(str(when))}{times}{tail}; '
            f'it stays open until you accept or reject it.">HELD</span>')


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
    tip = (f'{lead} &mdash; ${st.get("combined_usd", 0):,.0f} combined{pct_s}{verb}')
    # COMPACT (2026-09-06): a full warning sentence used to render inline on every stacked row
    # (the layout bug this replaced: it was crammed into a 76px column and wrapped one word per
    # line). Now a short chip with the pct in it -- the number that actually matters at a
    # glance -- and the full member/severity detail in the tooltip.
    pct_disp = f'{pct:.0f}%' if isinstance(pct, (int, float)) else "STACK"
    return f'<span class="{cls}" title="{esc_attr(tip)}">&#9888; {pct_disp} stacked</span>'


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


def donut_fig(d):
    """Same chart dict shape as fig(), rendered WITHOUT the section/panel wrapper -- for
    embedding a donut directly inside an existing panel (Clusters, Positions) rather than as
    its own separate section (added 2026-09-07). Donut sits left, a vertical legend listing
    exact percentages sits right -- a donut is deliberately not where exact numbers are read
    from (dataviz: "part-to-whole at a glance only"), so the legend is not decorative here,
    it is the precise reading the wedges themselves can't give."""
    if not d or not d.get("svg"):
        return ""
    leg = ""
    if d.get("legend"):
        leg = ('<div class="donut-legend">' + "".join(
            f'<span><i style="background:{c}"></i>{esc(l)}</span>' for c, l in d["legend"])
            + "</div>")
    return (f'<div class="viz"><div class="donut-row">{d["svg"]}{leg}</div>'
            f'<p class="note" style="margin-top:10px">{esc(d.get("note",""))}</p></div>')


def _find_matching_close(html, open_tag_end, tag):
    """Given the index right after an opening `<{tag} ...>`, scan forward tracking nesting
    depth for that same tag name and return the index of the matching `</{tag}>`'s start.
    Returns -1 if no match (malformed input). Depth-aware, unlike a naive "first closing tag
    wins" regex -- needed because e.g. a panel's <div class="phead"> is not always flat (the
    read/macro panel nests a <div class="pills"> of its own inside the header)."""
    open_re = re.compile(rf'<{tag}\b[^>]*>')
    close_re = re.compile(rf'</{tag}>')
    pos, depth = open_tag_end, 1
    while depth > 0:
        nxt_open = open_re.search(html, pos)
        nxt_close = close_re.search(html, pos)
        if not nxt_close:
            return -1
        if nxt_open and nxt_open.start() < nxt_close.start():
            depth += 1
            pos = nxt_open.end()
        else:
            depth -= 1
            pos = nxt_close.end()
            if depth == 0:
                return nxt_close.start()
    return -1


def _collapsible(html, default_open=False):
    """Convert every top-level <section class="panel..."> block in `html` into a collapsible
    <details class="panel..." [open]>, with its <div class="phead"> becoming <summary
    class="phead">. Added 2026-09-07 for the redesign's information-hierarchy pass: the prior
    layout put all 26 sections at the same visual weight, always expanded, which is what made
    the page read as dense/undifferentiated. Rather than hand-editing 19 render_* functions this
    session hasn't touched (each with its own hard-won bug-fix history -- see the CSS block's
    own note on why those are left alone), this operates on their OUTPUT strings generically at
    the call site in build(), so every function keeps emitting exactly the markup it always has
    and build() alone decides what's open by default.

    Depth-tracked, not a naive "first closing tag wins" regex -- a panel can nest other <div>s
    (e.g. the read/macro panel's <div class="phead"> itself contains a <div class="pills">), and
    a first-</div>-wins version silently produced UNBALANCED output on exactly that panel: caught
    by an html.parser structural check before shipping, not by eyeballing the render.
    """
    open_attr = " open" if default_open else ""
    out, pos = [], 0
    sec_re = re.compile(r'<section class="panel([^"]*)">')
    while True:
        m = sec_re.search(html, pos)
        if not m:
            out.append(html[pos:])
            break
        out.append(html[pos:m.start()])
        sec_close = _find_matching_close(html, m.end(), "section")
        if sec_close == -1:  # malformed -- leave untouched rather than corrupt it further
            out.append(html[m.start():])
            break
        inner = html[m.end():sec_close]
        # swap this panel's own <div class="phead"> (there is exactly one, right at the top of
        # `inner`) for <summary class="phead">, matching ITS true close by the same depth-aware
        # scan -- not the first </div>, which may belong to something phead nests.
        phead_m = re.search(r'<div class="phead">', inner)
        if phead_m:
            phead_close = _find_matching_close(inner, phead_m.end(), "div")
            if phead_close != -1:
                inner = (inner[:phead_m.start()] + '<summary class="phead">'
                          + inner[phead_m.end():phead_close] + "</summary>"
                          + inner[phead_close + len("</div>"):])
        out.append(f'<details class="panel{m.group(1)}"{open_attr}>{inner}</details>')
        pos = sec_close + len("</section>")
    return "".join(out)


_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z(])')


def split_into_reads(text, n=5):
    """Split a narrative paragraph into its natural sentences for a scannable "top N reads"
    list, replacing the prior 400-char truncation + hidden "more" drawer (FIXED 2026-09-07,
    user: "the read part... is displaying just 1 sentence... the more tab... too much text...
    difficult to find important things"). Splits on sentence-ending punctuation followed by
    whitespace and a capital letter or opening paren -- deliberately simple, no NLP dependency.
    This works because narrative.json's session_read is itself written as short, complete
    declarative sentences with no internal abbreviations ("U.S.", "Inc.") that would mis-split.
    Never fabricates content: every returned item is a verbatim slice of the source text, so
    "top 5 reads" is a display reorganization, not new judgment the dashboard generator isn't
    allowed to originate (COMPUTE-FIRST / EVIDENCE PRINCIPLE, SKILL.md)."""
    text = (text or "").strip()
    if not text:
        return []
    return [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()][:n]


CSS = """
*{box-sizing:border-box}
.stack-badge{color:var(--ink-2)}
.stack-badge.hi{color:#c2688a;font-weight:600}
.held-badge{display:inline-block;margin-left:.5rem;padding:.08rem .4rem;border-radius:3px;
  font-size:.72rem;font-weight:600;letter-spacing:.02em;
  background:var(--surface-2);color:var(--ink-2);border:1px solid var(--line)}

/* ============ tokens -- redesigned 2026-09-07 =============================================
   Full visual redesign (user: "still don't like how it looks... too dense... feels dated...
   poor hierarchy... full redesign from scratch"). Every class name below stays IDENTICAL to
   the prior design -- the 26 render_* functions that emit markup by class name are untouched,
   deliberately: they carry ~20 documented, hard-won bug fixes (the .tw scroll-wrapper bug, the
   display:grid-on-<summary> bug, the h2 .sub spacing bug, the truncation-period bug, etc.) and
   rewriting that logic from scratch would risk reintroducing every one of them for a complaint
   that was never about correctness. What changed is the token system, the type, the panel
   chrome, and (in build(), below) the information hierarchy -- density and defaults, not data.

   COLOR: a cool graphite ground (not pure black -- a picked neutral, not an inherited one) with
   a desaturated slate-cyan accent for the Agent Smith "system" identity -- evokes precision
   instrumentation without the literal-Matrix-green cliche. The warm copper --action stays: it
   already reads correctly as "a human decision sits here" against a cool system palette, and a
   second redesign pass losing that contrast would be a regression, not an improvement.
   TYPE: Newsreader (a serif built for on-screen reading, variable optical size) carries section
   heads and the narrative "voice" prose -- the committed, wealth-manager-briefing gravitas this
   desk's own persona calls for, not a status-dump font. IBM Plex Sans carries body/UI/labels --
   the same family as the Agent Smith architecture diagram, so the product family reads as one
   thing. IBM Plex Mono carries every number, ticker and tabular figure, as before. */
:root{
  --ground:#f4f5f4; --surface:#ffffff; --surface-2:#eceeed;
  --ink:#14181a; --ink-2:#4c565b; --ink-3:#7c878c;
  --line:#dbe0df; --line-soft:#e9edec;
  --accent:#3d6b76; --accent-soft:#e2edee; --accent-line:#b3ccd0;
  --action:#935a26; --action-soft:#f7ece0; --action-line:#e0c19c;
  --good:#1f7a52; --good-soft:#e2f1e8;
  --warn:#96700f; --warn-soft:#f7efd8;
  --bad:#a13f37;  --bad-soft:#f7e5e2;
  --sans:"IBM Plex Sans",-apple-system,"Segoe UI",system-ui,sans-serif;
  --serif:"Newsreader",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --r:8px; --r-lg:12px;
  --shadow:0 1px 2px rgba(20,24,26,.04),0 2px 14px rgba(20,24,26,.04);
}
@media (prefers-color-scheme:dark){
  :root:where(:not([data-theme="light"])){
    --ground:#0a0c0e; --surface:#15181b; --surface-2:#1b1f22;
    --ink:#e7ebec; --ink-2:#a2acb1; --ink-3:#626c72;
    --line:#262b2e; --line-soft:#1c2124;
    --accent:#5fa0ae; --accent-soft:#15272b; --accent-line:#2b4a52;
    --action:#c9853f; --action-soft:#2a1d10; --action-line:#4d3419;
    --good:#4fa578; --good-soft:#10261a;
    --warn:#cca738; --warn-soft:#2a2210;
    --bad:#c46059;  --bad-soft:#2a1815;
    --shadow:0 1px 2px rgba(0,0,0,.35),0 2px 16px rgba(0,0,0,.25);
  }
}
:root[data-theme="dark"]{
  --ground:#0a0c0e; --surface:#15181b; --surface-2:#1b1f22;
  --ink:#e7ebec; --ink-2:#a2acb1; --ink-3:#626c72;
  --line:#262b2e; --line-soft:#1c2124;
  --accent:#5fa0ae; --accent-soft:#15272b; --accent-line:#2b4a52;
  --action:#c9853f; --action-soft:#2a1d10; --action-line:#4d3419;
  --good:#4fa578; --good-soft:#10261a;
  --warn:#cca738; --warn-soft:#2a2210;
  --bad:#c46059;  --bad-soft:#2a1815;
  --shadow:0 1px 2px rgba(0,0,0,.35),0 2px 16px rgba(0,0,0,.25);
}

body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  -webkit-font-smoothing:antialiased;line-height:1.55;font-size:14.5px}
.wrap{max-width:900px;margin:0 auto;padding:34px 22px 90px;display:flex;flex-direction:column;gap:34px}
h1,h2{margin:0;text-wrap:balance;font-weight:600;letter-spacing:-.01em;font-family:var(--serif)}
p{margin:0}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.voice{font-family:var(--serif);font-size:16.5px;line-height:1.65;color:var(--ink-2)}
.voice em{color:var(--ink);font-style:italic}
.pos{color:var(--good)} .neg{color:var(--bad)}
.col{display:flex;flex-direction:column}

/* ============ "the read" top-N list -- added 2026-09-07 (user: "remake the read section so
   it contains top 5 reads"). Each item is one whole sentence from the same session narrative,
   numbered because a ranked "top 5" is what was asked for -- not decoration on content that
   isn't actually a sequence (see artifact-design's own numbering caveat). Replaces a single
   dense paragraph + hidden "more" drawer with everything visible at once. ============ */
.read-list{display:flex;flex-direction:column;gap:2px}
.read-item{display:flex;gap:14px;align-items:baseline;padding:11px 0;border-top:1px solid var(--line-soft)}
.read-item:first-child{border-top:none;padding-top:0}
.read-num{font-family:var(--mono);font-size:11px;font-weight:600;color:var(--accent);
  flex-shrink:0;letter-spacing:.02em;min-width:1.4em}
.read-item .voice{font-size:15px;line-height:1.55}

/* ============ masthead -- editorial, not a form header ============ */
.mast{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;justify-content:space-between;
  padding-bottom:20px;border-bottom:1px solid var(--line)}
.mast h1{font-size:30px;font-weight:560;letter-spacing:-.015em}
.mast h1 span{color:var(--accent);font-weight:400;font-style:italic}
.stamp{font-family:var(--mono);font-size:11px;color:var(--ink-3);text-align:right;line-height:1.7;
  letter-spacing:.01em}

/* ============ hero -- REBUILT 2026-09-07, component-level pass. The prior "status strip" was
   5-8 equal-weight cells in a row -- a generic KPI-tile pattern, the same shape whether the
   number was Total Book or a footnote. A hero states what matters most FIRST and everything
   else is visibly secondary, which a grid of identical boxes cannot do no matter what colors or
   fonts sit inside it -- this is the actual fix for "still looks like the old dashboard": not a
   new coat of paint on the same tile grid, a different component. ============ */
.hero{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);
  box-shadow:var(--shadow);padding:26px 26px 22px;display:flex;flex-direction:column;gap:18px}
/* FIXED 2026-09-07 (user-reported alignment issue): label/value/delta used to share one
   baseline-aligned flex row with per-item align-self overrides (flex-start on the label,
   center on the delta) -- three different vertical anchors in one row is exactly the kind of
   mixed alignment that reads as "off" the moment the row wraps or the viewport narrows. Now a
   clean two-line stack: the label sits alone on its own line, the value and delta share a
   second row aligned on one baseline together -- no per-item override needed, nothing to
   misalign regardless of width. */
.hero-main{display:flex;flex-direction:column;gap:6px}
.hero-label{font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ink-3)}
.hero-value-row{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.hero-value{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:44px;
  font-weight:500;letter-spacing:-.03em;color:var(--ink);line-height:1}
.hero-delta{font-family:var(--mono);font-size:15px;font-weight:600;padding:3px 10px;
  border-radius:100px}
.hero-delta.pos{color:var(--good);background:var(--good-soft)}
.hero-delta.neg{color:var(--bad);background:var(--bad-soft)}
.hero-stats{display:flex;flex-wrap:wrap;gap:22px 30px;padding-top:16px;border-top:1px solid var(--line-soft)}
.hstat{display:flex;flex-direction:column;gap:3px}
.hstat .k{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3)}
.hstat .v{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:17px;font-weight:500;
  letter-spacing:-.01em;color:var(--ink)}
.hstat .v.flag{color:var(--bad)}
.hstat .s{font-family:var(--mono);font-size:10.5px;color:var(--ink-3)}
.macro{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:16px}
.macro .k{font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3)}
.macro .v{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:17px;font-weight:500;letter-spacing:-.02em}
.macro .s{font-family:var(--mono);font-size:11px;color:var(--ink-3)}

/* ============ panels ============ */
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);box-shadow:var(--shadow)}
.phead{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;
  padding:14px 18px;border-bottom:1px solid var(--line-soft)}
.phead h2{font-size:16px;font-weight:560}
/* collapsible panel -- a <summary class="phead"> reuses the ordinary panel header's flex layout
   exactly (class selectors apply regardless of tag), so a panel becomes collapsible by wrapping
   it in <details class="panel ..."><summary class="phead"> instead of
   <section class="panel"><div class="phead">. build()'s _collapsible() helper performs exactly
   this swap on a function's rendered output -- the redesign's information-hierarchy pass -- so
   the 26 render_* functions above never need to know or care whether their panel ends up always
   visible or tucked behind a click. */
details.panel>summary{cursor:pointer;list-style:none;padding:14px 18px;font-family:var(--serif);
  font-weight:560;font-size:16px;transition:background-color .12s}
details.panel>summary:hover{background:var(--surface-2)}
details.panel>summary::-webkit-details-marker{display:none}
details.panel>summary::before{content:"›  ";color:var(--accent);font-family:var(--sans);font-weight:600;
  display:inline-block;transition:transform .15s}
details.panel[open]>summary::before{transform:rotate(90deg) translateX(1px)}
/* .sub is used both on <span> (h2 subtitles) and <td> (muted table-cell text). */
.sub{color:var(--ink-3);font-family:var(--sans)}
h2 .sub{display:inline-block;margin-left:9px;font-family:var(--sans);font-weight:400;
  font-size:12px;letter-spacing:0;vertical-align:middle}
.pbody{padding:18px;display:flex;flex-direction:column;gap:14px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:22px;align-items:start}

.act{border-color:var(--action-line);background:var(--action-soft)}
.act .phead{border-bottom-color:var(--action-line)}
.act .phead h2{color:var(--action)}
details.panel.act>summary::before{color:var(--action)}

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

/* ============ donut embed (Clusters, Positions) -- added 2026-09-07 ============ */
.donut-row{display:flex;gap:22px;align-items:center;flex-wrap:wrap}
.donut-row svg{flex-shrink:0}
.donut-legend{display:flex;flex-direction:column;gap:6px;flex:1;min-width:160px}
.donut-legend span{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--ink-2);
  font-family:var(--mono);font-variant-numeric:tabular-nums}
.donut-legend i{width:10px;height:10px;border-radius:3px;flex-shrink:0}

/* ============ cluster bars -- REBUILT 2026-09-07, component pass. Was a 5-column grid (name |
   equity% | book% | band-text | a 26px-tall meter squeezed into the last 150px column) -- a
   spreadsheet row wearing new colours. This IS a magnitude-vs-target comparison (dataviz's own
   form heuristic: that job is a bar, full stop), so it gets a full-width bar each: the allowed
   band renders as a soft zone, the actual weight as a solid fill, the target as a sharp tick --
   one glance answers "where do I sit," which five packed columns made you calculate instead. */
details.clus-row{border-top:1px solid var(--line-soft);padding:12px 0}
details.clus-row:first-of-type{border-top:none;padding-top:0}
details.clus-row>summary{cursor:pointer;list-style:none;display:flex;flex-direction:column;gap:8px}
details.clus-row>summary::-webkit-details-marker{display:none}
details.clus-row>summary::marker{content:"";display:none}
.clus-top{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.clus-name{font-family:var(--serif);font-size:17px;font-weight:500;color:var(--ink);
  display:flex;align-items:baseline;gap:8px}
.clus-name::before{content:"›";color:var(--accent);font-weight:600;transition:transform .15s;display:inline-block}
details.clus-row[open] .clus-name::before{transform:rotate(90deg)}
.clus-name i{font-style:normal;font-family:var(--mono);font-size:11px;font-weight:400;color:var(--ink-3)}
.clus-pct{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:17px;font-weight:600;color:var(--ink)}
.clus-pct.neg{color:var(--bad)}
.clus-bar{position:relative;height:10px;background:var(--surface-2);border-radius:5px;overflow:visible}
.clus-band-zone{position:absolute;top:0;bottom:0;background:var(--accent-soft);border-radius:5px}
.clus-fill{position:absolute;top:0;bottom:0;left:0;background:var(--accent);border-radius:5px;opacity:.85}
.clus-fill.neg{background:var(--bad)}
.clus-target{position:absolute;top:-2px;bottom:-2px;width:2px;background:var(--ink)}
.clus-sub{font-family:var(--mono);font-size:11px;color:var(--ink-3)}
details.clus-row>.body{padding:12px 0 0}
.peer-tag{font-size:9.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  padding:2px 6px;border-radius:4px;white-space:nowrap}
.peer-tag.lead{background:var(--good-soft);color:var(--good)}
.peer-tag.lag{background:var(--bad-soft);color:var(--bad)}

/* ============ decision cards -- REBUILT 2026-09-07, a genuinely different component, not a
   reskin of the old row. The prior `.pr` was a flex-wrap ROW: a small colored badge, ticker,
   and amount all sitting on one text baseline, differentiated mainly by a 2px border-bottom --
   still recognizably a table row wearing new CSS variables. A card states the same information
   as a discrete object: a 4px colour STRIPE down the left edge carries the direction (so the
   eye reads BUY/SELL/TRIM as a shape and a colour before it reads the word), the ticker sits at
   real display size on its own line, the amount is peer-sized and pinned opposite it, and every
   secondary fact (cluster, conviction, trigger, stack/hold flags) collapses into one small meta
   line below -- closer to how a banking app states "here is one decision," further from "here
   is one row in a table of decisions." ============ */
.pr-card{display:flex;border-radius:10px;overflow:hidden;background:var(--surface);
  border:1px solid var(--line-soft);margin-bottom:8px}
.pr-card:last-child{margin-bottom:0}
.pr-card-stripe{width:4px;flex-shrink:0}
.pr-card-stripe.BUY{background:var(--good)}
.pr-card-stripe.SELL{background:var(--bad)}
.pr-card-stripe.TRIM{background:var(--warn)}
.pr-card-stripe.HOLD{background:var(--ink-3)}
.pr-card-body{flex:1;min-width:0;padding:12px 15px;display:flex;flex-direction:column;gap:6px}
.pr-card-top{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.pr-card-name{font-family:var(--serif);font-size:18px;font-weight:500;color:var(--ink);
  letter-spacing:-.005em;display:flex;align-items:baseline;gap:9px;min-width:0}
.pr-card-dir{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;flex-shrink:0}
.pr-card-dir.BUY{color:var(--good)} .pr-card-dir.SELL{color:var(--bad)}
.pr-card-dir.TRIM{color:var(--warn)} .pr-card-dir.HOLD{color:var(--ink-3)}
.pr-card-amt{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:18px;
  font-weight:600;white-space:nowrap;color:var(--action)}
.pr-card-amt.BUY{color:var(--good)} .pr-card-amt.SELL{color:var(--bad)} .pr-card-amt.TRIM{color:var(--warn)}
.pr-card-meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;font-size:11.5px;color:var(--ink-3)}
.pr-card-clus{font-family:var(--sans);font-weight:500}
.pr-card-extra{display:flex;flex-wrap:wrap;gap:6px 10px;padding-top:2px}
.pr-card .decide{margin:0}
/* priority groups -- collapsible */
details.pgrp{border-top:1px solid var(--line-soft);margin-top:8px;padding-top:8px}
details.pgrp:first-of-type{border-top:none;margin-top:0;padding-top:0}
details.pgrp>summary{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;padding:4px 0 8px}
details.pgrp.HIGH>summary{color:var(--bad)}
details.pgrp.MEDIUM>summary{color:var(--warn)}
details.pgrp.LOW>summary{color:var(--ink-3)}
details.pgrp>summary .n{background:var(--surface-2);color:var(--ink-2);border-radius:10px;padding:1px 8px;
  font-family:var(--mono);margin-left:8px;text-transform:none;letter-spacing:normal;font-weight:400}
details.pgrp>.body{padding:0}
/* live re-justification -- recomputed every run */
.lv{font-family:var(--mono);font-size:11px;color:var(--good)}
.lv::before{content:"live ";color:var(--ink-3);font-weight:700;letter-spacing:.06em}
.rvf{font-family:var(--mono);font-size:11px;color:var(--warn)}
/* compact inline drawer for a card's secondary detail */
.pr-more{margin-top:2px}
.pr-more>summary{font-family:var(--mono);font-size:10.5px;font-weight:600;letter-spacing:.04em;
  color:var(--accent);padding:0;text-transform:uppercase}
.pr-more>summary::before{content:"+ ";color:var(--accent)}
.pr-more[open]>summary::before{content:"\2212 "}
/* FIXED 2026-09-09 (user-reported: "when a stock inside of a cluster is expanded again the
   table is not comprehendable due to large text"): the base `td` rule sets white-space:nowrap,
   which is an inherited property -- a `.pr-more` dropped inside a table cell (the Clusters
   panel's per-row ladder rationale, added the same day) inherited that nowrap and rendered its
   whole paragraph as one unbroken line stretching the table far past the viewport instead of
   wrapping. `.pr-more` had never previously been used inside a table cell (only inside
   `.pr-card-body`, a flex div with no nowrap), so this never surfaced before. Reset wrapping
   and cap the width so an expanded remark reads as a short paragraph, not a horizontal scroll. */
.pr-more>.body{padding:8px 0 0;font-size:12px;white-space:normal;max-width:340px;line-height:1.5;color:var(--ink-2)}

/* ============ rotation ideas (paired trim+buy proposals) -- two cards joined by an arrow ==== */
.rotgrp{border-top:1px solid var(--line-soft);padding-top:8px;margin-bottom:2px}
.rotgrp:first-child{border-top:none;padding-top:0}
.rotgrp-h{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--accent);padding:0 0 8px}
.rotgrp-h .n{background:var(--accent-soft);color:var(--accent);border-radius:10px;padding:1px 8px;
  font-family:var(--mono);margin-left:8px;text-transform:none;letter-spacing:normal;font-weight:400}
.rotcard{display:grid;grid-template-columns:1fr 26px 1fr;gap:8px;align-items:center;
  padding:0;margin-bottom:8px}
.rotcard .pr-card{margin-bottom:0}
.rotarrow{text-align:center;font-size:16px;color:var(--accent);font-weight:700}
@media (max-width:560px){.rotcard{grid-template-columns:1fr}.rotarrow{transform:rotate(90deg);padding:2px 0}}

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

/* ============ factor catalysts -- REBUILT 2026-09-07, same card family as the decision cards
   above rather than the old badge-column grid (.ci: a fixed 78px column for the badge, text in
   the other). A card here carries the same stripe + body language: stripe colour = direction,
   the pill moves inside the card header, headline reads at real title size. ============ */
.cat-card{display:flex;border-radius:10px;overflow:hidden;background:var(--surface);
  border:1px solid var(--line-soft);margin-bottom:8px}
.cat-card:last-child{margin-bottom:0}
.cat-card-stripe{width:4px;flex-shrink:0}
.cat-card-stripe.THREAT{background:var(--bad)}
.cat-card-stripe.TAILWIND{background:var(--good)}
.cat-card-stripe.AMBIGUOUS{background:var(--warn)}
.cat-card-body{flex:1;min-width:0;padding:12px 15px;display:flex;flex-direction:column;gap:7px}
.cat-card-top{display:flex}
.cat-card-hh{font-family:var(--serif);font-size:16px;font-weight:500;line-height:1.4;color:var(--ink)}
.cb{font-size:9.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 8px;border-radius:100px}
.cb.TAILWIND{background:var(--good-soft);color:var(--good)}
.cb.THREAT{background:var(--bad-soft);color:var(--bad)}
.cb.AMBIGUOUS{background:var(--warn-soft);color:var(--warn)}

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
.day{background:var(--surface);padding:11px 12px;display:flex;flex-direction:column;gap:7px;min-height:64px}
.day.empty{min-height:0;padding:9px 12px;opacity:.55}
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

/* ============ tiers / details (t3) -- the primary wayfinding device on the page, restyled
   editorial (was a small uppercase label + rule; now a real section break the eye catches
   scrolling past, per the redesign's hierarchy pass) ============ */
.tier{margin-top:4px;display:flex;align-items:baseline;gap:16px}
.tier h2{font-family:var(--serif);font-size:20px;font-weight:500;font-style:italic;
  color:var(--ink-2);white-space:nowrap;letter-spacing:0}
.tier .ln{flex:1;height:1px;background:var(--line);transform:translateY(-4px)}
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
.mbar i.c{background:var(--accent)}
.pr .mbar{margin-right:6px}
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

# Donut hover-to-update-center (FIXED 2026-09-07, user-reported: the Clusters/Positions donut
# center label was hardcoded to the top segment and never changed on hover). Deliberately its
# own script, separate from DASHBOARD_JS's decisions IIFE above: this is pure display
# interactivity with no window.claude dependency, so it must run unconditionally, including in
# the read-only preview path where DASHBOARD_JS returns early before ever reaching its own
# listener setup.
DONUT_JS = r"""<script>
(function(){
  document.querySelectorAll('svg.donut-svg').forEach(function(svg){
    var pctEl = svg.querySelector('text[id$="-pct"]');
    var subEl = svg.querySelector('text[id$="-sub"]');
    if (!pctEl || !subEl) return;
    var defaultPct = pctEl.textContent, defaultSub = subEl.textContent;
    svg.querySelectorAll('path.mark').forEach(function(p){
      p.addEventListener('mouseenter', function(){
        pctEl.textContent = p.getAttribute('data-pct') + '%';
        subEl.textContent = p.getAttribute('data-label');
      });
      p.addEventListener('mouseleave', function(){
        pctEl.textContent = defaultPct;
        subEl.textContent = defaultSub;
      });
    });
  });
})();
</script>"""


def status_strip(us, dd, cash_pct, cash_band, cash_breach, risk, drift, book_compute):
    """REBUILT 2026-09-07, component-level pass (not a reskin): Total book is now the one hero
    number the eye lands on first, with today's move as a delta chip beside it -- everything
    that used to be N equal-weight tiles (Equity, P&L, Cash, Drawdown, Open risk, AI-capex) is
    now a secondary stat row, visually subordinate on purpose. Same data, same fields, nothing
    dropped -- see _render_data_quality's sibling comment on day_chg_pct_weighted being optional,
    unchanged here."""
    ai_capex_pct = drift.get("ai_capex_pct")
    prior_ai = drift.get("ai_capex_pct_prior")
    open_risk_pct = risk.get("aggregate_open_risk_pct")
    open_risk_cap = risk.get("aggregate_open_risk_cap_pct")
    open_risk_over = risk.get("aggregate_over_cap")
    total = (us.get("value_usd", 0) or 0) + (us.get("wallet_usd", 0) or 0)

    day_chg = book_compute.get("day_chg_pct_weighted")
    delta_html = ""
    if day_chg is not None:
        cls = "pos" if day_chg >= 0 else "neg"
        delta_html = f'<span class="hero-delta {cls}">{day_chg:+.2f}% today</span>'

    stats = []
    stats.append(("", "Equity", f'${us.get("value_usd",0) or 0:,.0f}', f'{us.get("count","-")} positions'))
    pnl_pct = book_compute.get("pnl_pct")
    if pnl_pct is not None:
        stats.append(("" if pnl_pct >= 0 else "flag", "P&amp;L", f'{pnl_pct:+.2f}%', "vs invested"))
    stats.append(("" if not cash_breach else "flag", "Cash",
                  f'{cash_pct:.1f}%', f'band [{cash_band[0]},{cash_band[1]}]'))
    stats.append(("flag" if abs(dd) >= 15 else "", "Drawdown", f'{dd:.2f}%',
                  f'{15-abs(dd):.2f}pt to warn' if abs(dd) < 15 else "past warn rung"))
    if open_risk_pct is not None:
        stats.append(("flag" if open_risk_over else "", "Open risk",
                      f'{open_risk_pct:.1f}%', f'cap {open_risk_cap:g}%' + (" · OVER" if open_risk_over else "")))
    if ai_capex_pct is not None:
        stats.append(("flag" if ai_capex_pct >= 90 else "", "AI-capex", f'{ai_capex_pct:.1f}%',
                      "of book" + (f', was {prior_ai:.1f}%' if prior_ai is not None else "")))

    stats_html = "".join(
        f'<div class="hstat"><span class="k">{k}</span><span class="v num {cls}">{esc(v)}</span>'
        f'<span class="s">{esc(s)}</span></div>' for cls, k, v, s in stats)

    return (f'<section class="hero"><div class="hero-main">'
            f'<span class="hero-label">Total book</span>'
            f'<div class="hero-value-row"><span class="hero-value num">${total:,.0f}</span>'
            f'{delta_html}</div></div>'
            f'<div class="hero-stats">{stats_html}</div></section>')


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
            pair_s = ' &middot; paired, self-funding' if pair else ''
            meta_s = f'{esc(pid)}{" &middot; accepted " + esc(when) if when else ""}{pair_s}'
            rows.append(
                f'<div class="pr-card"><div class="pr-card-stripe {b}"></div>'
                f'<div class="pr-card-body"><div class="pr-card-top">'
                f'<span class="pr-card-name"><span class="pr-card-dir {b}">{b}</span>'
                f'{esc(_clean_action(p, b))}</span>'
                f'<span class="pr-card-amt {b}">${p.get("size_usd", 0):,.0f}</span></div>'
                f'<div class="pr-card-meta">{meta_s}</div></div></div>')
        net_word = "raises cash by" if net >= 0 else "needs cash of"
        # COLLAPSIBLE (2026-09-06, user request) -- <details class="panel"> instead of
        # <section class="panel"><div class="phead">, see the CSS note above. Open by default:
        # this is a decisions-made-but-not-yet-filled queue, the kind of thing that should be
        # visible on load, not something the user has to remember to expand.
        out.append(
            '<details class="panel act" open><summary class="phead"><h2>Accepted &mdash; awaiting execution</h2>'
            f'<span class="pill a">{len(accepted)} decided, not yet filled</span></summary>'
            f'<div class="pbody"><div>{"".join(rows)}</div>'
            f'<p class="note"><b>${sells:,.0f}</b> of sells/trims against <b>${buys:,.0f}</b> of buys '
            f'&mdash; net {net_word} <b>${abs(net):,.0f}</b>. '
            'Accepting is a stated intention, not a trade: Agent Smith never places orders. '
            'A row leaves this panel only when the actual fill reaches the ledger.</p></div></details>')

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
            # REDESIGNED 2026-09-06 (user: "too much text... use data analytics tools... make
            # this sleek"). Two prior compaction passes still printed full sentences by default
            # (rationale, stacking warning) -- shrinking the TEXT wasn't the fix; the format was
            # still prose. This pass replaces sentences with the visual encodings the rest of
            # this dashboard already uses elsewhere (a conviction METER, not a "conviction 64
            # (medium)" sentence; a trigger TAG, not a paragraph explaining it; a stack ICON with
            # its number in it, tooltip for the rest) and moves every remaining sentence-shaped
            # field (rationale, live re-justification, retirement condition, tranche/stop/
            # shares/clamped sizing detail) into a compact label:value fact grid in the drawer --
            # not paragraph spans stacked on top of each other. No field was dropped; every one
            # still exists, most just changed from a sentence to a number+tooltip.
            bucket = p.get("direction_bucket", "HOLD")
            pid = p.get("id", "")
            action = esc(p.get("action", ""))
            clus_s = f'<span class="pr-card-clus">{esc(p["cluster"])}</span>' if p.get("cluster") else ""
            held_s = held_badge(p)
            stack_s = stacks_badge(p)

            # conviction METER (reuses the .mbar bar already used by the de-risk queue) instead
            # of a "conviction 64 (medium)" sentence -- the number IS the visual now.
            conv = p.get("conviction_score")
            conv_meter = ""
            if conv is not None:
                w = max(0.0, min(100.0, conv))
                conv_meter = (f'<span class="mbar" title="conviction {conv:.0f} '
                              f'({esc(p.get("conviction_tier",""))})">'
                              f'<i class="c" style="width:{w:.0f}%"></i></span>')

            # SHORT TAG for what triggered this, not the sentence explaining it -- the sentence
            # (trigger_type name + the human-readable trailing clause of the rationale, if any)
            # moves into the tag's own tooltip and into the drawer's fact grid.
            trigger = p.get("trigger_type", "")
            rationale = p.get("rationale", "") or ""
            tag_label = trigger.replace("_", " ") if trigger else (rationale[:24] + "…" if len(rationale) > 24 else rationale)
            tag_s = (f'<span class="rchip w" title="{esc_attr(rationale)}">{esc(tag_label)}</span>'
                     if tag_label else "")

            flags = p.get("review_flags") or []
            flag_s = "".join(f'<span class="rvf">&#9888;&#65039; {esc(x)}</span>' for x in flags)

            # -- everything else: a compact label:value fact grid, not stacked sentences --
            facts = []
            if rationale:
                facts.append(("Why", esc(rationale)))
            live = p.get("still_valid_because") or []
            if live:
                facts.append(("Still valid", "; ".join(esc(x) for x in live)))
            retires = p.get("retires_when")
            if retires:
                facts.append(("Retires when", esc(retires)))
            tranche = p.get("tranche_note")
            if tranche:
                facts.append(("Sizing", esc(tranche)))
            stop_px = p.get("stop_price_usd")
            price_px = p.get("price_usd")
            shares = int(p.get("size_usd", 0) / price_px) if price_px else None
            sizing_bits = []
            if stop_px:
                sizing_bits.append(f'stop ${stop_px:,.2f}')
            if shares:
                sizing_bits.append(f'~{shares} sh')
            clamped = p.get("clamped_by")
            if clamped:
                sizing_bits.append(f'wanted ${p.get("size_wanted_usd", 0):,.0f}, capped by {esc(clamped)}')
            if sizing_bits:
                facts.append(("Order", " &middot; ".join(sizing_bits)))
            rc = p.get("repeat_count", 1)
            if rc > 1:
                since = esc(str(p["history"][0].get("date", ""))[:10]) if p.get("history") else ""
                facts.append(("Repeated", f'{rc}&times;' + (f' since {since}' if since else "")))
            if pid:
                facts.append(("ID", esc(pid)))
            fact_grid = "".join(f'<div class="srow"><span class="slab">{esc(k)}</span>'
                                f'<span>{v}</span></div>' for k, v in facts)
            drawer = (f'<details class="pr-more"><summary>details</summary>'
                      f'<div class="body">{fact_grid}</div></details>') if facts else ""

            decide_s = decision_buttons("proposal", pid) if pid else ""
            # CARD, not a row (2026-09-07 component pass): stripe carries direction, name sits
            # at real display size on its own line with the amount peer-sized opposite it, and
            # every secondary fact -- cluster, conviction meter, trigger tag, held/stack flags,
            # the drawer, the decide buttons -- collapses into one small meta line beneath.
            meta_bits = "".join(x for x in (clus_s, conv_meter, tag_s, held_s) if x)
            extra_bits = "".join(x for x in (flag_s, stack_s) if x)
            extra_s = f'<div class="pr-card-extra">{extra_bits}</div>' if extra_bits else ""
            return (f'<div class="pr-card"><div class="pr-card-stripe {bucket}"></div>'
                    f'<div class="pr-card-body"><div class="pr-card-top">'
                    f'<span class="pr-card-name"><span class="pr-card-dir {bucket}">{bucket}</span>'
                    f'{action}</span>'
                    f'<span class="pr-card-amt {bucket}">${p.get("size_usd",0):,.0f}</span></div>'
                    f'<div class="pr-card-meta">{meta_bits}</div>{extra_s}{drawer}{decide_s}'
                    f'</div></div>')

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
            hrows.append(
                f'<div class="pr-card"><div class="pr-card-stripe TRIM"></div>'
                f'<div class="pr-card-body"><div class="pr-card-top">'
                f'<span class="pr-card-name"><span class="pr-card-dir TRIM">BREACH</span></span>'
                f'<span class="pr-card-amt">&mdash;</span></div>'
                f'<div class="pr-card-meta" title="{esc_attr(b)} -- bring it inside the band or '
                f'record why the breach is accepted.">{esc(b)}</div></div></div>')
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


def _catalyst_today(state):
    """The run date this dashboard is rendering, as a `date` -- the reference point for
    catalyst freshness. Falls back to the wall clock only if state carries no `ts`."""
    ts = str(state.get("ts") or "")[:10]
    try:
        return datetime.strptime(ts, "%Y-%m-%d").date()
    except ValueError:
        return datetime.now().date()


def _render_factor_catalysts(state):
    out = []
    # -- factor catalysts --
    # THE PANEL NO LONGER VANISHES (2026-09-08). It used to render only `if catalysts:`, so a
    # run where smith-catalyst returned [] produced no section at all -- and on 2026-09-08 that
    # is exactly what happened: a section diff showed 19 h2s before and after, with "Factor
    # catalysts" simply gone. That is the silent-failure shape SKILL.md's own regression guard
    # warns about: the reader cannot tell "nothing is moving the factor" from "this panel broke".
    # It now always prints, and says which of the two it means.
    today = _catalyst_today(state)
    catalysts = smith_risk.live_catalysts(state, today)
    fresh_n, carried_n = smith_risk.catalyst_carry_summary(state, today)
    scanned = state.get("factor_catalysts_as_of") or state.get("factor_themes_as_of")
    if fresh_n:
        sub = f'{fresh_n} new this run' + (f' &middot; {carried_n} carried forward' if carried_n else '')
    elif carried_n:
        sub = f'No NEW catalysts this run &middot; {carried_n} carried forward'
    else:
        sub = 'No live factor catalysts' + (f' &middot; last scanned {esc(str(scanned))}' if scanned else '')
    subpill = f'<span class="pill">{sub}</span>'
    if not catalysts:
        out.append('<section class="panel"><div class="phead"><h2>Factor catalysts</h2>'
                   f'{subpill}</div><div class="pbody"><div class="muted">'
                   'Nothing carried forward and nothing new &mdash; the last scan found no '
                   'catalyst clearing its sourcing bar, and every prior catalyst has aged out '
                   'past its own horizon. This is a finding, not a missing panel.'
                   '</div></div></section>')
    if catalysts:
        rows = []
        for i, c in enumerate(catalysts[:6]):
            dirn = {"threat": "THREAT", "tailwind": "TAILWIND"}.get(c.get("direction", ""), "AMBIGUOUS")
            exp = c.get("exposure_pct_equity")
            # "catalyst" has no natural stable id (headline+date is the real key) -- synthesize
            # one for the button's data-element-id and carry the real key along as extra data-*
            # attributes, which sync-decisions reads directly rather than looking anything up.
            extra = (f' data-headline="{esc_attr(c.get("headline",""))}" '
                    f'data-date="{esc_attr(c.get("date",""))}"')
            decide_s = decision_buttons("catalyst", f"c{i}", extra)
            # COMPACTED 2026-09-06 (user: report-like, too text-heavy) -- a long headline (these
            # run 150-250 chars) used to print in full; now truncated to one clause with the rest
            # plus the magnitude line behind a details toggle. affects/exposure stays visible --
            # that's the scannable "what does this touch" line, not prose.
            # REDESIGNED 2026-09-06 (same pass as Ideas/Housekeeping: sentence-shaped fields ->
            # visual chips + a label:value fact grid, not a shrunk paragraph). The full headline
            # is real signal and stays fully readable -- it just moved to the tooltip and the
            # drawer instead of printing 150-250 chars inline every time. affected tickers are
            # now individual chips (scannable at a glance) instead of a middot-joined string.
            headline = c.get("headline", "")
            head_tag = headline[:60] + "…" if len(headline) > 60 else headline
            mag = c.get("magnitude", "")
            affect_chips = "".join(f'<span class="tick {"g" if dirn=="TAILWIND" else ("b" if dirn=="THREAT" else "")}">{esc(x)}</span>'
                                   for x in c.get("affects", []))
            facts = [("Headline", esc(headline))]
            if mag:
                facts.append(("Magnitude", esc(mag)))
            if isinstance(exp, (int, float)):
                facts.append(("Exposure", f'{exp:.1f}% of equity'))
            facts.append(("Date", esc(c.get("date", "-"))))
            fact_grid = "".join(f'<div class="srow"><span class="slab">{esc(k)}</span><span>{v}</span></div>'
                                for k, v in facts)
            drawer = f'<details class="pr-more"><summary>details</summary><div class="body">{fact_grid}</div></details>'
            exp_chip = (f'<span class="tick">{exp:.1f}% equity</span>' if isinstance(exp, (int, float)) else "")
            if c.get("carried_forward"):
                lc = c.get("last_confirmed") or c.get("date") or ""
                exp_chip += (f'<span class="tick" title="Carried forward from an earlier scan; '
                             f'still inside its {smith_risk.catalyst_ttl_days(c)}d '
                             f'{esc_attr(c.get("horizon",""))} horizon">carried &middot; {esc(str(lc))}</span>')
            # CARD (2026-09-07 component pass): the badge moves from its own grid column into
            # the card header next to a real title-sized headline -- same visual family as the
            # decision cards above (a colour stripe on the left carrying the read), not the old
            # badge-column-plus-text-block layout.
            rows.append(
                f'<div class="cat-card"><div class="cat-card-stripe {dirn}"></div>'
                f'<div class="cat-card-body"><div class="cat-card-top">'
                f'<span class="cb {dirn}">{dirn}</span></div>'
                f'<div class="cat-card-hh" title="{esc_attr(headline)}">{esc(head_tag)}</div>'
                f'<div class="sch">{affect_chips}{exp_chip}</div>{drawer}{decide_s}</div></div>')
        out.append('<section class="panel"><div class="phead"><h2>Factor catalysts</h2>'
                 f'{subpill}</div>'
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

            # REDESIGNED 2026-09-06 (user-reported: Move/Size showing "--" for most rows read
            # as broken, and Why's mid-word ellipsis + trailing "+2⚠" read as garbled). Two
            # separate causes, two separate fixes:
            # (1) SHADOW blocks (laggard_rotation etc) NEVER carry a suggested_size by design --
            #     shadow triggers don't get sized until they earn a real hit rate (see this
            #     file's own standing rule, cited in the "how to read this" note below). A
            #     column that is empty for EVERY row in a block isn't missing data, it's a
            #     column that doesn't apply to this block -- so it's dropped entirely instead
            #     of printing a dash on every row, and the block header says why in one line.
            # (2) Move is genuinely absent for SOME rows (this run's data_quality: the ATR/RSI
            #     refresh was skipped for budget reasons, see smith-signals' own note) -- that
            #     column stays, "--" there is honest, not a bug.
            size_applies = key != "laggard_rotation" and any(
                (c.get("suggested_size_usd") or c.get("current_stop_usd")) for c in rows_t)
            move_applies = any(c.get("gain_pct") is not None or c.get("abs_return_1m_pct") is not None
                              for c in rows_t)

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
                # Why, as a proper chip: word-boundary-safe (never cuts mid-word), the reason
                # count and any blocker fold into ONE readable tooltip rather than a bare "+2"
                # and a floating warning glyph with no label.
                reasons = c.get("reasons") or []
                blockers = c.get("blockers") or []
                primary = reasons[0] if reasons else ""
                primary_short = primary if len(primary) <= 42 else primary[:42].rsplit(" ", 1)[0] + "…"
                tip_bits = []
                if len(reasons) > 1:
                    tip_bits.append(" · ".join(reasons))
                if blockers:
                    tip_bits.append("Blocked: " + " | ".join(blockers))
                tip = esc_attr(" — ".join(tip_bits)) if tip_bits else ""
                extra_n = f' <i>+{len(reasons)-1}</i>' if len(reasons) > 1 else ""
                blk_icon = ' &#9888;&#65039;' if blockers else ""
                why_cell = (f'<span class="rchip{" w" if blockers else ""}" title="{tip}">'
                           f'{esc(primary_short)}{extra_n}{blk_icon}</span>' if primary else "&mdash;")
                size_td = f'<td class="num">{amt}</td>' if size_applies else ""
                move_td = f'<td class="num">{secondary}</td>' if move_applies else ""
                trs.append(f'<tr><td><b>{esc(c["ticker"])}</b></td>'
                           f'<td class="sub">{esc(c.get("cluster") or "-")}</td>'
                           f'<td class="num">{(f"{rsi:.1f}" if rsi is not None else "&mdash;")}</td>'
                           f'{move_td}{size_td}'
                           f'<td class="sub">{why_cell}</td></tr>')
            size_th = "<th>Size</th>" if size_applies else ""
            move_th = "<th>Move</th>" if move_applies else ""
            not_sized_note = ('<span class="sub" style="margin-left:8px">shadow-scored, not '
                              'sized -- no vote until it earns a hit rate</span>') if not size_applies and vote == "SHADOW" else ""
            blocks.append(
                f'<div class="phead" style="border:0;padding:10px 0 4px"><h2 style="font-size:.82rem">'
                f'{label}<span class="sub">{how}</span></h2>'
                f'<span class="pill {vote_cls}">{esc(vote)}</span>{not_sized_note}</div>'
                f'<div class="tw"><table class="tbl"><thead><tr><th>Name</th><th>Cluster</th>'
                f'<th>RSI14</th>{move_th}{size_th}<th>Why</th></tr></thead>'
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
        # REDESIGNED 2026-09-06 (user: too much text, full freedom to redesign) -- same shape
        # as the pre-fix Factor catalysts: 3 lines of prose x 8 themes printed open by default.
        # This is a STANDING watch list (persistent structure), not this run's news -- it earns
        # a collapsed-by-default details wrapper, plus the same tag/chip/fact-grid treatment.
        rows = []
        for th in themes[:8]:
            name = th.get("name", "")
            watch = th.get("watch", "")
            live_keys = sorted([k for k in th if k.startswith("live_")], reverse=True)
            latest_live = th.get(live_keys[0]) if live_keys else None
            maps_chips = "".join(f'<span class="tick">{esc(x)}</span>' for x in th.get("maps_to", [])[:10])
            facts = [("Watching for", esc(watch))]
            if latest_live:
                facts.append((esc(live_keys[0].replace("live_", "").replace("_", " ").title() or "Latest"), esc(latest_live)))
            fact_grid = "".join(f'<div class="srow"><span class="slab">{k}</span><span>{v}</span></div>'
                                for k, v in facts)
            drawer = f'<details class="pr-more"><summary>details</summary><div class="body">{fact_grid}</div></details>'
            rows.append(f'<div class="ci"><span class="cb AMBIGUOUS">WATCH</span><div>'
                        f'<div class="hh">{esc(name)}</div>'
                        f'<div class="sch" style="margin:4px 0">{maps_chips}</div>{drawer}</div></div>')
        out.append(f'<details><summary>Factor themes<span class="c">the standing watch list, '
                 f'{len(themes)} tracked</span></summary><div class="body">{"".join(rows)}</div></details>')

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
                 '<b>Trim &mdash; risk cap</b> = over its ATR risk cap &mdash; UNLESS the name is strong '
                 '(strengthening thesis + net-bullish signal) and not yet overbought (RSI14 &le; 70); a '
                 'strong name over cap isn&rsquo;t rotated on cap mechanics alone, only once it&rsquo;s '
                 'also overbought. Everything else is unchipped (thesis and signal disagree, or both are flat). '
                 'MOMENTUM+VOLUME and TARGET GAP are excluded from the signal count &mdash; both fire on '
                 'moves in either direction by their own definition, so neither is unambiguously bullish '
                 'or bearish.</p>'
                 f'<div class="rgrid">{rgrid}</div></div></section>')

    return out


def _render_clusters(drift, state, held_tickers, risk_by_ticker, thesis_status, sector_map, ladder=None, ch=None):
    """Clusters panel -- allocation-vs-band PLUS the intra-cluster substitution ladder, ONE
    table per cluster (merged 2026-09-09, user: "why dont merge both the cluster and cluster
    ladder table. that will be more neater. add p/e ratios too"). These used to be two separate
    panels -- "Clusters" (weight vs. policy band, one member table per cluster) and "Cluster
    ladders" (smith-cluster's ranked substitution call, its own member table per cluster with a
    ladder) -- and a reader had to cross-reference GEV's row in one against GEV's row in the
    other to get the full picture. Now each cluster's `<details>` carries the band bar, the
    ranked member table (rank, weight, P/E, price, vs-cluster return, thesis, signals, the
    ladder's own rationale) and, when a ladder exists, its bench candidates and cluster-level
    thesis/margin-pool read in one place. A cluster with no ladder yet just shows the same
    table sorted by weight instead of rank, with a note saying so -- never a fabricated rank.
    """
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
        cluster_ladders_all = (state or {}).get("cluster_ladders") or {}
        pe_ratios = ((state or {}).get("data_cache") or {}).get("pe_ratios") or {}

        # rel_intra_pp per (cluster, ticker) -- each member against its OWN cluster's mean
        # return, not SMH -- computed by smith_math.py ladder, never re-derived here.
        intra = {}
        for cname_l, crow in ((ladder or {}).get("clusters") or {}).items():
            for m in crow.get("members") or []:
                intra[(cname_l, m.get("ticker"))] = m.get("rel_intra_pp")

        def pe_cell(tk):
            pe = pe_ratios.get(tk) or {}
            tpe, fpe = pe.get("trailing_pe"), pe.get("forward_pe")
            if tpe is None and fpe is None:
                return '<span style="color:var(--ink-3)">&mdash;</span>'
            t_s = f'{tpe:.1f}' if isinstance(tpe, (int, float)) else '&mdash;'
            f_s = f'{fpe:.1f}' if isinstance(fpe, (int, float)) else '&mdash;'
            return f'<span title="trailing / forward P/E, as of {esc(pe.get("as_of") or "?")}">{t_s}/{f_s}</span>'

        # SORT BY THE CLUSTER'S OWN LADDER RANK, WHEN ONE EXISTS (added on user request: "show
        # and sort according to the cluster specific ladder ranking, add a small remark/reason
        # along with the rankings"). The ladder (smith-cluster's ranked substitution call) is
        # the fleet's actual answer to "which of these names captures the shared tailwind" --
        # weight-order was never that, only a proxy. Held members with no ladder entry (a name
        # added after the ladder was last built) sort to the bottom of the ranked group, still
        # by weight, so a stale gap never masquerades as rank 1. Clusters with no ladder at all
        # fall back to the prior weight-only order.
        def _why_toggle(label, full_text):
            # Compact rationale: a small "+ AXIS" toggle inside the Name cell rather than a
            # dedicated table column full of prose (redesigned 2026-09-09, user: "the table is
            # not formatted well. too much text at the last column is making it bad"). Reuses
            # the existing `.pr-more` details/summary component (already styled for exactly
            # this -- collapsed by default, a few words as the closed label, the full reasoning
            # only on click) instead of inventing a new pattern or truncating into a tooltip
            # nobody notices is hoverable.
            if not full_text:
                return ""
            label = (label or "why").strip()
            if len(label) > 34:
                cut = label[:34].rsplit(" ", 1)[0] or label[:34]
                label = esc(cut) + "&hellip;"
            else:
                label = esc(label)
            return (f'<details class="pr-more"><summary>{label}</summary>'
                    f'<div class="body">{esc(full_text)}</div></details>')

        def member_rows(cluster_name):
            members = cluster_members.get(cluster_name, [])
            cladder = cluster_ladders_all.get(cluster_name) or {}
            rank_by_ticker, why_by_ticker, axis_by_ticker = {}, {}, {}
            for m in cladder.get("ranking") or []:
                t = m.get("ticker")
                if not t:
                    continue
                rank_by_ticker[t] = m.get("rank")
                reads = m.get("differentiator_reads") or []
                why_by_ticker[t] = (reads[0].get("read") or "") if reads else ""
                axis_by_ticker[t] = (reads[0].get("axis") or "") if reads else ""

            if rank_by_ticker:
                members = sorted(
                    members,
                    key=lambda tk: (rank_by_ticker.get(tk, 10 ** 6),
                                     -(holdings_by_ticker.get(tk, {}).get("weight_pct") or 0)))
            else:
                members = sorted(members, key=lambda tk: -(holdings_by_ticker.get(tk, {}).get("weight_pct") or 0))

            out_rows = []
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
                rank = rank_by_ticker.get(tk)
                rank_s = (f'<b>{rank}</b>' if rank else '<span style="color:var(--ink-3)">&mdash;</span>')
                pp = intra.get((cluster_name, tk))
                pp_html = ('<span class="mono%s">%+.1f pp</span>' % (" neg" if pp < 0 else "", pp)
                           if isinstance(pp, (int, float)) else '<span class="mono">&mdash;</span>')
                why_html = _why_toggle(axis_by_ticker.get(tk), why_by_ticker.get(tk))
                out_rows.append(
                    f'<tr><td class="mono">{rank_s}</td>'
                    f'<td class="name" style="text-align:left;padding-left:0">{esc(tk)}{why_html}</td>'
                    f'<td>{h.get("weight_pct",0):.2f}%</td>'
                    f'<td>{pe_cell(tk)}</td>'
                    f'<td>{f"${price:,.2f}" if price is not None else "&mdash;"}</td>'
                    f'<td>{pp_html}</td>'
                    f'<td class="txt">{st_s}</td>'
                    f'<td class="txt">{peer_s}{other_tags}</td>'
                    f'<td>{cap_s}</td></tr>')
            # bench candidates (non-held names smith-cluster ranks better than the laggard) --
            # part of the same substitution-ladder answer, so they belong in the same table,
            # not a separate one a reader has to go find. Priced and P/E'd the same as held
            # members (fetched 2026-09-09 -- previously these rows were all dashes) so a bench
            # name reads as a real comparable, not a placeholder.
            for b in (cladder.get("bench") or [])[:3]:
                bt = b.get("ticker") or ""
                bpx = b.get("price_usd")
                why_bt = (b.get("why_better_than") or "").strip()
                entry = (b.get("entry_condition") or "").strip()
                bench_why = " — ".join(t for t in (why_bt, entry) if t)  # literal em dash: esc() must still run on this text, and "&mdash;" would double-escape to "&amp;mdash;"
                why_html = _why_toggle("why better", bench_why)
                out_rows.append(
                    '<tr><td class="mono">&mdash;</td>'
                    f'<td class="name" style="text-align:left;padding-left:0"><b>{esc(bt)}</b> <i>bench</i>{why_html}</td>'
                    f'<td>&mdash;</td><td>{pe_cell(bt)}</td>'
                    f'<td>{f"${bpx:,.2f}" if isinstance(bpx, (int, float)) else "&mdash;"}</td>'
                    '<td class="mono">&mdash;</td><td>&mdash;</td><td>&mdash;</td><td></td></tr>')
            has_ladder = bool(rank_by_ticker)
            return "".join(out_rows), has_ladder, cladder

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
            body_rows, has_ladder, cladder = member_rows(cname)
            ghosts = sorted(cluster_ghosts.get(cname, []))
            ghost_html = (
                '<p class="note" style="margin-top:8px">No longer held / tracked only: '
                + "".join(f'<span class="tick gone" style="margin-right:4px">{esc(tk)}</span>' for tk in ghosts)
                + '</p>') if ghosts else ""
            no_ladder_note = ('<p class="note" style="margin-top:8px">No cluster ladder built yet for '
                               f'{esc(cname)} &mdash; sorted by weight.</p>') if body_rows and not has_ladder else ""

            # Cluster-level ladder context -- confidence, track record, cluster thesis, margin
            # pool, redundant pairs -- the part of the old separate "Cluster ladders" panel that
            # applies to the whole cluster rather than one row. Shown only when a ladder exists.
            ladder_sub = ""
            if has_ladder:
                conf = (cladder.get("confidence") or "").lower()
                conf_cls = {"high": "g", "medium": "w", "low": "b"}.get(conf, "")
                ct = cladder.get("cluster_thesis") or {}
                tr = [t for t in (cladder.get("track_record") or []) if t.get("scored")]
                hits = sum(1 for t in tr if t.get("correct"))
                # Only ever shown with its denominator -- a hit rate without a sample size is
                # the shape that makes 1-of-1 look like a track record.
                record = (" &middot; ladder calls %d/%d" % (hits, len(tr))) if tr else ""
                mp = cladder.get("margin_pool") or {}
                subs = []
                if ct.get("status") or ct.get("innings"):
                    subs.append("cluster thesis %s &middot; %s innings"
                                % (esc(ct.get("status") or "?"), esc(ct.get("innings") or "?")))
                if mp.get("moving_toward"):
                    subs.append("margin pool &rarr; %s" % esc(mp["moving_toward"]))
                for rp in (cladder.get("redundant_pairs") or [])[:2]:
                    if rp.get("verdict") == "redundant":
                        subs.append("%s are one bet &mdash; keep %s"
                                    % (esc(" + ".join(rp.get("pair") or [])), esc(rp.get("keep") or "?")))
                ladder_sub = (
                    '<p class="note" style="margin-top:8px">Ladder as of %s &middot; '
                    '<span class="pill %s">%s confidence%s</span>%s</p>' % (
                        esc(cladder.get("as_of") or "?"), conf_cls, esc(conf or "no"), record,
                        (" &middot; " + " &middot; ".join(subs)) if subs else ""))

            body = ((f'<div class="scroll"><table><thead><tr><th>#</th><th>Name</th><th>Wt</th>'
                    f'<th>P/E<span class="sub"> trail/fwd</span></th><th>Price</th>'
                    f'<th>vs cluster</th><th>Thesis</th><th>Signals</th>'
                    f'<th></th></tr></thead><tbody>{body_rows}</tbody></table></div>' if body_rows else
                    '<p class="note">No held ticker maps to this cluster.</p>')
                    + ladder_sub + no_ladder_note + ghost_html)
            # BAR, not a meter squeezed into a 150px grid column (2026-09-07 component pass):
            # one full-width track per cluster, the filled portion reads as a real magnitude at
            # a glance (dataviz's own form heuristic -- this IS a magnitude comparison, so it
            # should look like one), the target sits as a clear tick, and the allowed band is a
            # soft zone behind it rather than a sliver only visible on close inspection.
            book_pct = c.get("actual_pct_of_total_book", 0)
            rows.append(
                f'<details class="clus-row"{" open" if breach else ""}><summary>'
                f'<div class="clus-top">'
                f'<span class="clus-name">{esc(cname)}<i>{n_members} held</i></span>'
                f'<span class="clus-pct{" neg" if breach else ""}">{actual:.2f}%</span></div>'
                f'<div class="clus-bar"><div class="clus-band-zone" '
                f'style="left:{pc(lo):.1f}%;width:{max(pc(hi)-pc(lo),0):.1f}%"></div>'
                f'<div class="clus-fill{" neg" if breach else ""}" style="width:{pc(actual):.1f}%"></div>'
                f'<div class="clus-target" style="left:{pc(tgt):.1f}%"></div></div>'
                f'<div class="clus-sub">book {book_pct:.2f}% &middot; band [{lo:g},{hi:g}]% &middot; target {tgt:g}%</div>'
                f'</summary><div class="body">{body}</div></details>')
        donut_html = donut_fig((ch or {}).get("clusters_donut"))
        out.append(
            '<section class="panel"><div class="phead"><h2>Clusters</h2>'
            '<span class="pill">ceiling on book &middot; floor on equity &middot; ranked by cluster ladder where one exists</span></div>'
            f'<div class="pbody">{donut_html}'
            f'<div style="display:flex;flex-direction:column;gap:0">{"".join(rows)}</div></div></section>')

    return out


def _cluster_impact_bar_svg(cluster_rows):
    """Compact horizontal bar chart: net $ impact per cluster, pos/neg diverging from a zero
    line, sorted by |impact| descending -- added 2026-09-06 (user: 'use some data analytics and
    visualisation', the by-cluster table alone still read as a wall of numbers). Self-contained
    inline SVG rather than a smith_charts.py addition: this is a one-off per-cluster diverging
    bar, not a chart type reused elsewhere, and it needs no network/live data of its own."""
    if not cluster_rows:
        return ""
    rows = sorted(cluster_rows, key=lambda r: -abs(r[1]))[:10]
    maxabs = max(abs(v) for _, v in rows) or 1.0
    row_h, gap, label_w, bar_w = 22, 6, 190, 260
    w = label_w + bar_w + 70
    h = len(rows) * (row_h + gap)
    mid = label_w + bar_w / 2
    bars = []
    for i, (name, val) in enumerate(rows):
        y = i * (row_h + gap)
        frac = abs(val) / maxabs
        seg = (bar_w / 2) * frac
        color = "var(--bad)" if val < 0 else "var(--good)"
        x = mid - seg if val < 0 else mid
        label = name if len(name) <= 26 else name[:24] + "…"
        bars.append(
            f'<text x="{label_w-8}" y="{y+row_h*0.68}" text-anchor="end" class="lbl" '
            f'font-size="11" fill="var(--ink-2)">{esc(label)}</text>'
            f'<rect x="{x:.1f}" y="{y+3}" width="{seg:.1f}" height="{row_h-6}" rx="3" fill="{color}"/>'
            f'<text x="{(mid+seg+6) if val>=0 else (mid-seg-6)}" y="{y+row_h*0.68}" '
            f'text-anchor="{"start" if val>=0 else "end"}" font-size="11" fill="var(--ink-2)" '
            f'font-family="var(--mono)">${val:+,.0f}</text>')
    svg = (f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" '
           f'style="max-width:520px;display:block;margin:4px 0">'
           f'<line x1="{mid}" y1="0" x2="{mid}" y2="{h}" stroke="var(--line)" stroke-width="1"/>'
           + "".join(bars) + '</svg>')
    return svg


def _render_stop_loss_efficacy(stops_data, sector_map=None, cluster_order=None):
    out = []
    # -- stop-loss efficacy (added 2026-08-06, dashboard feature review; compacted 2026-09-06,
    # user request -- "simplify... make it compact and showing a few impact/analysis" -- after
    # the by-ticker roll-up alone still ran 57 rows). trades.json had 24 stop-loss fills with
    # exact prices and was referenced by this generator zero times before this panel existed;
    # the computation (smith_math.py cmd_stops, writes stops_analysis.json) now measures both
    # whether each stop helped vs holding through AND, per name, whether the re-entry after a
    # stop landed above or below the stop price. This function's job is to say what matters in
    # one glance -- everything underneath (57 names, every individual trade) is real and kept,
    # just moved behind one drill-down instead of printed in full by default.
    overall = stops_data.get("overall")
    if overall:
        reentry_summary = stops_data.get("reentry_summary") or {}
        by_cohort = stops_data.get("by_cohort") or {}
        by_ticker = stops_data.get("by_ticker") or []
        sector_map = sector_map or {}

        # cluster grouping computed up front so both the chart (visible) and the full
        # breakdown table (collapsed) share one stable ordering -- see the note further down.
        by_cluster = {}
        for r in by_ticker:
            by_cluster.setdefault(sector_map.get(r["ticker"], "Exited / not currently held"), []).append(r)
        order = cluster_order or []
        rank = {c: i for i, c in enumerate(order)}
        cluster_names = [c for c in by_cluster if c != "Exited / not currently held"]
        cluster_names.sort(key=lambda c: (rank.get(c, len(order)), c))
        if "Exited / not currently held" in by_cluster:
            cluster_names.append("Exited / not currently held")
        cluster_totals = [(cname, sum(r["combined_net_dollar_impact"] for r in by_cluster[cname]))
                           for cname in cluster_names]
        cluster_chart_svg = _cluster_impact_bar_svg(cluster_totals)

        net_cls = "pos" if overall["net_dollar_impact"] <= 0 else "neg"
        lower_pct = reentry_summary.get("reentered_lower_pct")
        lower_cls = "pos" if (lower_pct or 0) >= 50 else "neg"

        # ONE compact stat strip -- the whole "did stops help, did re-entries hold the edge"
        # story in six numbers, instead of two separate stat blocks before this change.
        cells = [
            ("Scored", str(overall["count"]), ""),
            ("Win rate", f'{overall["win_rate_pct"]:.0f}%' if overall.get("win_rate_pct") is not None else "&mdash;", ""),
            ("Net impact", f'${overall["net_dollar_impact"]:+,.0f}', net_cls),
        ]
        if reentry_summary:
            cells.append(("Re-entered", f'{reentry_summary["count"]} of '
                          f'{reentry_summary["count"]+reentry_summary["still_out_count"]}', ""))
            cells.append(("Bought back lower", f'{lower_pct:.0f}%' if lower_pct is not None else "&mdash;", lower_cls))
        summary_cells = '<div class="stops-sum">' + "".join(
            f'<div class="c"><span class="k">{esc(k)}</span><span class="v {cls}">{v}</span></div>'
            for k, v, cls in cells) + '</div>'

        # ONE compact cohort line instead of three multi-field rows.
        cohort_bits = []
        for key, label in (("cascade", "Cascade"), ("deliberate", "Deliberate"), ("unknown", "Untimed")):
            c = by_cohort.get(key)
            if c:
                cohort_bits.append(f'{label} <b>${c["net_dollar_impact"]:+,.0f}</b> ({c["count"]})')
        cohort_line = (f'<p class="note">{" &middot; ".join(cohort_bits)}</p>' if cohort_bits else "")

        # TOP MOVERS ONLY -- the actual "few impact/analysis" ask. Biggest net winners and
        # biggest net costs by ticker, 3 each, as compact chips rather than a 57-row table.
        winners = sorted([r for r in by_ticker if r["combined_net_dollar_impact"] > 0],
                          key=lambda r: -r["combined_net_dollar_impact"])[:3]
        losers = sorted([r for r in by_ticker if r["combined_net_dollar_impact"] < 0],
                         key=lambda r: r["combined_net_dollar_impact"])[:3]

        def chip(r, cls):
            reentry_note = (f' &middot; {r["reentry_count"]} reentry' if r["reentry_count"] else
                            (f' &middot; {r["still_out_count"]} still out' if r["still_out_count"] else ""))
            return (f'<span class="rchip {cls}" title="{r["stop_count"]} stop(s){reentry_note}">'
                    f'{esc(r["ticker"])} <i>${r["combined_net_dollar_impact"]:+,.0f}</i></span>')

        movers_html = ""
        if winners or losers:
            movers_html = '<div class="rgrid">'
            if winners:
                movers_html += ('<div class="rcol"><div class="grp-h"><span class="dot-g"></span>'
                                 'Biggest net winners</div><div class="chips">'
                                 + "".join(chip(r, "g") for r in winners) + '</div></div>')
            if losers:
                movers_html += ('<div class="rcol"><div class="grp-h"><span class="dot-b"></span>'
                                 'Biggest net costs</div><div class="chips">'
                                 + "".join(chip(r, "b") for r in losers) + '</div></div>')
            movers_html += '</div>'

        cluster_chart_block = (
            f'<hr class="rule"><h2 style="font-size:.82rem;margin-top:4px">Net impact by cluster'
            f'<span class="sub">stop $ + re-entry $, combined, per cluster</span></h2>'
            f'{cluster_chart_svg}' if cluster_chart_svg else "")

        dq_s = ("".join(f'<p class="note">{esc(x)}</p>' for x in (stops_data.get("data_quality") or [])))

        # -- FULL BREAKDOWN, collapsed by default (every one of the 57 names, every trade) --
        # Grouped by the book's existing cluster taxonomy (state.sector_map, added 2026-09-06,
        # user request) rather than a flat sort -- a name no longer held (DRAM, BX, META...)
        # has no current cluster, so it falls into its own "Exited / not currently held" group
        # rather than being silently mis-clustered.

        def _ticker_row(r):
            return (f'<tr><td class="name">{esc(r["ticker"])}</td><td class="num">{r["stop_count"]}</td>'
                    f'<td class="{"neg" if r["stop_dollar_impact"]<=0 else "pos"}">${r["stop_dollar_impact"]:+,.0f}</td>'
                    f'<td class="num">{r["reentry_count"]}</td>'
                    f'<td class="{"pos" if r["reentry_dollar_impact"]>=0 else "neg"}">${r["reentry_dollar_impact"]:+,.0f}</td>'
                    f'<td class="num">{r["still_out_count"]}</td>'
                    f'<td class="{"neg" if r["combined_net_dollar_impact"]<=0 else "pos"}">'
                    f'<b>${r["combined_net_dollar_impact"]:+,.0f}</b></td></tr>')

        # STABLE ordering by the book's own policy.json cluster_targets sequence (2026-09-06,
        # user request -- a magnitude sort reshuffled the whole table on every rebuild, which is
        # the opposite of what "sort by cluster" means: this is the same fixed cluster order
        # every other panel on this dashboard uses, so a name is always found in the same place
        # run over run). Any cluster not in that list falls back to alphabetical; "Exited / not
        # currently held" always sits last -- a different question from the live book's clusters.
        by_ticker_html = ""
        for cname, cluster_net in cluster_totals:
            rows_c = sorted(by_cluster[cname], key=lambda r: r["ticker"])
            net_cls = "neg" if cluster_net <= 0 else "pos"
            by_ticker_html += (
                f'<tr><td class="txt" colspan="6" style="font-weight:640;color:var(--ink-2);'
                f'padding-top:14px">{esc(cname)} <span class="sub">({len(rows_c)})</span></td>'
                f'<td class="{net_cls}"><b>${cluster_net:+,.0f}</b></td></tr>'
                + "".join(_ticker_row(r) for r in rows_c))
        rows_s = stops_data.get("stops") or []
        recent_rows = "".join(
            f'<tr><td class="name">{esc(r["ticker"])}</td><td class="blank">{esc(r["date"])}</td>'
            f'<td>${r["fill_price"]:,.2f}</td><td>${r["price_now"]:,.2f}</td>'
            f'<td class="{"pos" if r["move_pct"]>=0 else "neg"}">{r["move_pct"]:+.1f}%</td>'
            f'<td class="verd-{r["verdict"]}">{r["verdict"].upper()}</td>'
            f'<td><span class="cohort-tag {r["cohort"]}">{esc(r["cohort"])}</span></td></tr>'
            for r in rows_s[:30])

        full_breakdown = (
            '<details><summary>Full breakdown &mdash; all '
            f'{len(by_ticker)} names, every stop &amp; re-entry</summary><div class="body">'
            '<div class="scroll"><table><thead><tr><th>Name</th><th># stops</th>'
            '<th>Stop $ impact</th><th># re-entries</th><th>Re-entry $ impact</th>'
            '<th>Still out</th><th>Combined net</th></tr></thead>'
            f'<tbody>{by_ticker_html}</tbody></table></div>'
            '<p class="note" style="margin-top:8px">One row per name, every stop AND its matched '
            're-entry rolled into one figure. <b>Stop $ impact</b> (negative = the stop saved money) '
            'plus <b>Re-entry $ impact</b> (positive = bought back cheaper than sold) = '
            '<b>Combined net</b>.</p>'
            '<hr class="rule"><p class="note" style="margin-top:8px"><b>Individual trades</b> '
            '(most recent 30 of every scored stop) &mdash; Cascade = 3+ stops fired within a '
            '5-minute window; Deliberate = an isolated, mid-session stop; HURT means the price '
            'is now above the fill.</p>'
            '<div class="scroll"><table><thead><tr><th>Name</th><th>Date</th><th>Fill</th>'
            '<th>Now</th><th>Move</th><th>Verdict</th><th>Cohort</th></tr></thead>'
            f'<tbody>{recent_rows}</tbody></table></div>'
            '</div></details>')

        out.append(
            '<section class="panel"><div class="phead"><h2>Stop-loss efficacy'
            '<span class="sub">did the stop help, and did the re-entry hold the edge</span></h2>'
            f'<span class="pill">as of {esc(stops_data.get("as_of",""))}</span></div>'
            f'<div class="pbody">{summary_cells}{cohort_line}{movers_html}{cluster_chart_block}{dq_s}{full_breakdown}'
            '</div></section>')

    return out


def _render_the_read_and_macro(narr, market_inputs, state, book_compute):
    """REDESIGNED 2026-09-07 (user: "The read, i dont like it"), then further redesigned same
    day (user: "displaying just 1 sentence... the more tab... too much text... difficult to
    find important things... remake... top 5 reads"). Three changes now: the Gate pill sits as
    an eyebrow above the list instead of floating top-right; the single dense paragraph (400
    chars visible, the rest hidden behind a "more" drawer nobody wanted to open) is replaced by
    split_into_reads() breaking the same narrative text into up to 5 standalone sentence cards,
    all visible at once, numbered as a ranked list since "top 5" is literally what was asked
    for; and the macro numbers below reuse the hero card's `.hstat` component rather than a
    separate `.macro` grid, one stat-pair pattern for the whole page."""
    out = []
    session_text = narr.get("session_read")
    if session_text:
        reads = split_into_reads(session_text, 5)
        gate = market_inputs.get("gate_classification")
        gate_eyebrow = ""
        if gate:
            cls = "b" if gate == "ESCALATING" else ("w" if gate == "AMBIGUOUS" else "g")
            gate_eyebrow = f'<span class="pill {cls}" style="margin-bottom:10px">Gate: {esc(gate.title())}</span>'
        read_items = "".join(
            f'<div class="read-item"><span class="read-num">{i+1:02d}</span>'
            f'<p class="voice">{esc(r)}</p></div>' for i, r in enumerate(reads))
        out.append(f'<section class="panel"><div class="phead"><h2>The read</h2>'
                 f'<span class="pill">top {len(reads)}, this session</span></div>'
                 f'<div class="pbody">{gate_eyebrow}<div class="read-list">{read_items}</div>')

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
            out.append('<div class="hero-stats" style="padding-top:14px;border-top:1px solid var(--line-soft)">'
                       + "".join(
                f'<div class="hstat"><span class="k">{esc(k)}</span><span class="v num">{esc(v)}</span>'
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
        # FIXED 2026-09-06 (user-reported: an entirely empty white box on a weekend run, when
        # ES/NQ/Asia/SMH/gate are all None) -- this section rendered unconditionally on any
        # truthy market_inputs dict, never checking whether it actually had anything to show.
        if rows or sub:
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
    any_events = False
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
        any_events = any_events or hot
        label = "Today" if i == 0 else d.strftime("%a %-d")
        # COMPACT (2026-09-06, user-reported: 6 near-empty ~96px boxes for a quiet week wasted
        # a full screen of space). An event-free day now renders as a short single-line stub
        # (min-height dropped via the "empty" class) instead of the full-height cell -- a day
        # WITH events still gets the taller box, since that's where the content actually needs
        # the room.
        day_cls = " hot" if hot else (" empty" if not events else "")
        days.append(f'<div class="day{day_cls}"><span class="d">{esc(label)}</span>'
                    + "".join(events) + '</div>')
    if any_events:
        out.append('<section class="panel"><div class="phead"><h2>The week ahead</h2></div>'
                 f'<div class="pbody"><div class="cal">{"".join(days)}</div></div></section>')
    else:
        # Whole week is quiet -- one line beats six empty boxes.
        out.append('<section class="panel"><div class="phead"><h2>The week ahead</h2>'
                 '<span class="pill good">quiet</span></div>'
                 '<div class="pbody"><p class="note">No earnings prints or FOMC date in the '
                 'next 6 sessions.</p></div></section>')

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
            f'<td class="num">{(f"{r["cap_multiple"]:.2f}x" if r.get("cap_multiple") else "&mdash;")}'
            + (' <span class="tick g" title="strengthening + net-bullish + not yet overbought '
               '(RSI14 &le;70) -- cap multiplier not applied to fragility, exempted from Trim -- '
               'risk cap the same way, per rotation_bucket\'s rule">exempt</span>'
               if r.get("cap_exempt") else "") +
            f'</td>'
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


def _render_positions_table(state, risk_by_ticker, sector_map, risk, book_compute, cluster_order=None, ch=None):
    out = []
    holdings = state.get("holdings", [])
    if holdings:
        tot_value = sum((risk_by_ticker.get(h["ticker"], {}).get("market_value_usd") or 0) for h in holdings)
        tot_weight = sum(h.get("weight_pct", 0) for h in holdings)

        def _row(h):
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
            return (
                f'<tr><td class="name">{esc(tk)}</td>'
                f'<td>{qty:g}</td><td>{c_price}</td><td>{c_value}</td><td class="blank">{c_weight}</td>'
                f'<td class="blank">{c_atr}</td><td class="{beta_cls}">{c_beta}</td>'
                f'<td>{c_stop}</td><td>{c_stoppx}</td><td class="blank">{c_cap}</td>'
                f'<td class="{head_cls}" style="font-weight:640">{c_head}</td></tr>')

        # GROUPED BY CLUSTER (added 2026-09-06, user request), same stable policy.json
        # cluster_targets order used by the Stop-loss efficacy breakdown and every cluster-aware
        # panel on this dashboard -- a name is always found under the same cluster header in the
        # same position run over run. Within a cluster, holdings sort by weight descending (the
        # one place magnitude-sort is still right: within a cluster, biggest position first).
        by_cluster = {}
        for h in holdings:
            by_cluster.setdefault(sector_map.get(h["ticker"], "Unclassified"), []).append(h)
        order = cluster_order or []
        rank = {c: i for i, c in enumerate(order)}
        cluster_names = [c for c in by_cluster if c != "Unclassified"]
        cluster_names.sort(key=lambda c: (rank.get(c, len(order)), c))
        if "Unclassified" in by_cluster:
            cluster_names.append("Unclassified")

        body = ""
        for cname in cluster_names:
            hs = sorted(by_cluster[cname], key=lambda h: -(h.get("weight_pct") or 0))
            c_weight = sum(h.get("weight_pct") or 0 for h in hs)
            c_value = sum((risk_by_ticker.get(h["ticker"], {}).get("market_value_usd") or 0) for h in hs)
            body += (f'<tr><td class="txt" colspan="4" style="font-weight:640;color:var(--ink-2);'
                     f'padding-top:14px">{esc(cname)} <span class="sub">({len(hs)})</span></td>'
                     f'<td class="blank"><b>{c_weight:.1f}%</b></td>'
                     f'<td colspan="6" class="blank" style="text-align:left">${c_value:,.0f}</td></tr>'
                     + "".join(_row(h) for h in hs))

        agg_risk_pct = risk.get("aggregate_open_risk_pct")
        beta_book = book_compute.get("beta") or book_compute.get("primary_benchmark", {}).get("primary_beta")
        c_beta_book = f'<td class="pos">{beta_book:.3f}</td>' if beta_book is not None else '<td></td>'
        c_risk_foot = (f'<td colspan="3" class="blank" style="text-align:right">aggregate open risk</td>'
                      f'<td class="neg">{agg_risk_pct:.1f}%</td>' if agg_risk_pct is not None
                      else '<td colspan="4"></td>')
        foot = (f'<tfoot><tr><td class="name">Book</td><td></td><td></td>'
               f'<td>${tot_value:,.0f}</td><td class="blank">{tot_weight:.1f}%</td><td class="blank"></td>'
               f'{c_beta_book}{c_risk_foot}</tr></tfoot>')

        # DONUT (2026-09-07, user request) sits above the table as the quick "who's biggest"
        # view; the full table -- the one place exact per-position numbers live (ATR, beta,
        # stop, headroom, none of which a donut could ever show) -- moves behind its own
        # details toggle so the donut is what's seen first, not competed with immediately.
        donut_html = donut_fig((ch or {}).get("positions_donut"))
        table_html = ('<div class="scroll"><table>'
                 '<thead><tr><th>Name</th><th>Qty</th><th>Price</th><th>Value</th><th>Wt</th>'
                 '<th>ATR20</th><th>&beta;</th><th>Stop</th><th>Stop px</th><th>Cap</th><th>Headroom</th></tr></thead>'
                 f'<tbody>{body}</tbody>{foot}</table></div>')
        out.append(f'<section class="panel"><div class="phead"><h2>Positions<span class="sub">'
                 f'{len(holdings)}, grouped by cluster</span></h2></div><div class="pbody">{donut_html}'
                 f'<details class="pr-more" style="margin-top:4px"><summary>full table, every field</summary>'
                 f'<div class="body">{table_html}</div></details></div></section>')

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
            desc = g.get("description", "")
            desc_short = desc[:90] + "…" if len(desc) > 90 else desc
            rows.append(f'<div class="srow"><span class="slab"><b>{esc(g.get("id",""))}</b></span>'
                       f'<span style="font-size:12.5px;color:var(--ink-2)" title="{esc_attr(desc)}">'
                       f'{esc(desc_short)}{decide_s}</span></div>')
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
            reason = p.get("retired_reason") or ""
            reason_short = reason[:90] + "…" if len(reason) > 90 else reason
            rows.append(f'<div class="srow"><span class="slab"><b>{esc(p.get("id",""))}</b> '
                       f'{esc(p.get("action",""))}</span>'
                       f'<span style="font-size:12.5px;color:var(--ink-2)" title="{esc_attr(reason)}">'
                       f'{esc(reason_short)}{decide_s}</span></div>')
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
        fig(ch.get("relative"), "Beat or lag SMH, per period", "the gap each period, not a running total"),
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
    # ALWAYS recompute from cash_pct above, never trust drift.cash_breach directly (fixed
    # 2026-09-07, user-reported false breach). compute_drift.json can carry its OWN stale
    # cash_pct (found live: drift said cash_pct=0.0%/breach=True while the real, displayed
    # figure was 6.39% -- comfortably inside a [5,15]% band) if that stage ran against
    # different inputs than this build. A breach flag is only trustworthy when it agrees with
    # the number sitting right next to it on the page; recomputing here is cheap and the two
    # can never visibly contradict each other again.
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
             f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
             f'family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,560;'
             f'1,6..72,400;1,6..72,500&family=IBM+Plex+Sans:wght@400;500;600&'
             f'family=IBM+Plex+Mono:wght@400;500;600&display=swap">'
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

    # ================= TIER: DECISIONS (always visible -- redesign 2026-09-07) =================
    # Only the three genuinely actionable panels stay always-expanded. Everything that used to
    # sit in one flat, always-open list under this heading (11 sections) now sorts into
    # SIGNALS & CONTEXT or BOOK & RISK below, collapsed by default via _collapsible() -- the
    # direct fix for "too dense... poor hierarchy": the reader's eye used to have to do the
    # triage this heading now does for them.
    H.append('<div class="tier"><h2>Decisions</h2><div class="ln"></div></div>')

    H.extend(_render_accepted_awaiting_execution(props))

    H.extend(_render_ideas_and_housekeeping(props, policy, state, cash_breach, cash_pct, cash_band))

    # ================= TIER: SIGNALS & CONTEXT =================
    # CUT DOWN HARD (2026-09-07, user: "don't just use all the sections as is... keep high
    # priority things only"). This tier used to carry 9 sections; now 3. Cut: trade triggers
    # (meta-commentary on the proposal engine, not itself a decision input -- what got proposed
    # already shows in Ideas), factor themes (a slow-moving background watchlist), diversifier
    # bench (exploratory, nothing here is held), rotation analysis (the same rotation pairs
    # already render as cards inside Ideas), watchlist setups (exploratory, not held), sentiment
    # gauge + intraday/international session (context that doesn't change what to do today).
    # Kept: factor catalysts (real, dated, sourced news -- the one thing here that can actually
    # invalidate a thesis), the read + macro (short, three sentences), week ahead (event-risk
    # planning for a concentrated single-factor book). The render_* functions for everything cut
    # stay defined below, unused -- restoring one is a one-line change, not a rewrite, if any of
    # this turns out to be missed.
    H.append('<div class="tier"><h2>Signals &amp; context</h2><div class="ln"></div></div>')

    live_cats = smith_risk.live_catalysts(state, _catalyst_today(state))
    has_threat = any(c.get("direction") == "threat" for c in live_cats)
    H.extend(_collapsible(h, has_threat) for h in _render_factor_catalysts(state))

    H.extend(_collapsible(h, True) for h in _render_the_read_and_macro(narr, market_inputs, state, book_compute))

    H.extend(_collapsible(h) for h in _render_week_ahead(state, ts))

    # ================= TIER: BOOK & RISK =================
    # Allocation and exposure detail -- glance at the treemap, drill into the rest on demand.
    # Cut here (same pass): stop-loss efficacy (a backward-looking self-assessment of the stop
    # discipline, not something that changes today's decisions).
    H.append('<div class="tier"><h2>Book &amp; risk</h2><div class="ln"></div></div>')

    # FIXED 2026-08-08: fig()'s `sub` param is passed through esc() internally (see its
    # definition above), so it needs the literal "·" character here, not the "&middot;" HTML
    # entity -- esc() would escape the "&" a second time into the literal text "&middot;".
    H.append(_collapsible(fig(ch.get("treemap"), "Allocation treemap",
                 "size = weight · color = cluster · red outline = over risk cap"), True))

    H.extend(_collapsible(h) for h in
             _render_clusters(drift, state, held_tickers, risk_by_ticker, thesis_status, sector_map,
                               run_file("compute_ladder.json"), ch))

    # -- de-risk queue (moved 2026-08-07: swapped position with clusters, per user request) --
    H.extend(_collapsible(h) for h in _render_derisk_queue(derisk, state))

    H.extend(_collapsible(h) for h in _render_risk_cap_and_ltcg(risk, book_compute, base))

    H.extend(_collapsible(h) for h in _render_positions_table(state, risk_by_ticker, sector_map, risk, book_compute,
                                       list(policy.get("cluster_targets", {}).keys()), ch))

    # ================= DIAGNOSTICS -- REMOVED (2026-09-07, user request) =====================
    # Cut entirely, not collapsed: thesis map, signal history, open data gaps, recently
    # auto-retired, execution log, data quality caveats, self-learning. All were audit-trail /
    # debug-style detail -- useful for investigating something specific, never for deciding what
    # to do today, and their prose was a large share of the page's total text. Historical charts
    # (equity curve, drawdown, benchmark, weights) survive, folded into Book & risk below --
    # visual and glanceable, not diagnostic prose, so they earn their place on a trimmed page.
    # The render_* functions for every cut section stay defined below, unused; the trades.json /
    # base-dir loads that fed only cut sections are left in place too rather than half-threading
    # their removal through this function's top -- both are cheap, inert, and easy to wire back.
    H.extend(_collapsible(h, True) for h in _render_historical_charts(ch, policy))

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
        # COMPACT (2026-09-06) -- up to 3 flags at 200 chars each could run 600+ chars in one
        # unbroken footer paragraph. Each flag now truncates to one clause, full text on hover.
        def _flag_chip(f):
            txt = f.get("flag", "")
            short = txt[:70] + "…" if len(txt) > 70 else txt
            return f'<b>{esc(f.get("ticker",""))}</b> <span title="{esc_attr(txt)}">{esc(short)}</span>'
        bits = "; ".join(_flag_chip(f) for f in confirm_flags[:3])
        H.append(f'<p class="note">Needs confirmation: {bits}</p>')
    H.append(f'<p class="note">Mandate: {esc(str(mandate.get("objective","-")).replace("_"," "))} &middot; '
             f'horizon {esc(hz)}y &middot; benchmark {esc(mandate.get("benchmark","-"))} &middot; '
             f'risk budget {esc(str(mandate.get("risk_budget_pct","-")))}%.</p>')
    H.append('</footer>')

    H.append(DASHBOARD_JS)
    H.append(DONUT_JS)
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

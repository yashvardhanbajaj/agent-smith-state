# Agent Smith — dashboard reference

**v2 as of 2026-09-09.** The builder is `scripts/smith_dashboard.py`. The previous generation
is archived at `archive/smith_dashboard_v1.py` and is not run — its per-panel HTML is kept only
as a reference for what a panel used to look like when porting or checking one.

Read this before editing the builder, or when a rendered panel looks wrong. SKILL.md §6 keeps
the operative rules (generate don't author; read the printed panel counts; reuse `artifact_url`;
declare `capabilities: {"self": {}}`).

---

## Why v2 exists

v1 was 193KB of Python emitting 193KB of pre-baked HTML from ~35 `_render_*` string builders
wired together by hand in `build()`. Two problems, one fatal:

**It had silently regressed.** `build()` called only 12 of those ~35 functions. Thirteen panels
were defined and never invoked — thesis map, signal history, execution log, data-quality
caveats, self-learning, stop-loss efficacy, watchlist setups, factor themes, trade triggers,
diversifier bench, rotation analysis, retired proposals, open gaps. The entire Diagnostics tier
was absent from the published page for weeks. Every one of those builders had passing unit
tests; nothing tested that any of them was *reached*. This is the exact failure the 2026-07-28
REGRESSION GUARD was written to prevent, and a written instruction did not prevent it.

**It was a document, not an instrument.** 20 stacked sections, no filtering, no cross-linking.
254 proposals existed and the page showed 12.

## The structural answer

v2 builds ONE payload dict, embeds it as JSON, and ships a client-side app that renders from it.
A panel can no longer vanish through a missing call:

- `REQUIRED_KEYS` lists every key the client renders. `assert_payload_complete()` raises
  `SystemExit` naming the missing key. **Do not trim this list to make a build pass** — that is
  the regression repeating itself with extra steps.
- `tests/unit/test_smith_dashboard_payload.py` pins the floor (≥30 keys, and the specific keys
  for the thirteen panels v1 dropped).
- `tests/verify_dashboard.sh` diffs the full output against `tests/golden/dashboard_case1.html`.
- `main()` prints panel counts on every build. Read them.

Adding analysis = adding a payload key + a renderer, both in one place.

## Tabs

The manifest is the `TABS` array at the bottom of the client JS. One list, five entries.

| Tab | Carries |
|---|---|
| **Command** | the read, macro strip, sentiment gauge, open proposals (priority tiers + rotation pairs), accepted-awaiting-execution, all 13 trigger families, factor catalysts, week ahead |
| **Book & risk** | allocation treemap, expandable clusters w/ substitution ladders, sortable/filterable positions table, risk-cap breaches, LTCG watch, de-risk queue, 4 charts |
| **Conviction** | cycle position + falsifier, thesis map w/ evidence for and against, full cluster ladders + bench, signal history, quality audit, watchlist, diversifier bench, stress table |
| **Track record** | proposal accuracy by direction, bucket hit rates, stop-loss efficacy (cascade vs deliberate), every proposal ever made (searchable), execution log, self-learning readiness |
| **Diagnostics** | freshness contract, data-quality caveats, open gaps, run outages, attribution, run ledger |

**Ticker sheet.** Every ticker anywhere on the page is a `<button class="tk" data-tk="X">`.
Clicking opens a right-side sheet (not a modal — list context stays visible) with that name's
position, thesis + evidence, cluster rank, triggers firing now, proposal history, fills,
stop-loss record, hit-rate grades and tax lots.

## The decisions round trip

Unchanged in format, so `smith_math.py sync-decisions` parses v1 and v2 pages identically:
decisions accumulate in `<script type="application/json" id="smith-decisions">`, and a click
republishes the page via `window.claude.self.publish` with the blob swapped.

**v1's landmine is gone — do not reintroduce it.** v1 located the clicked row by string-matching
the literal substring `data-surface="X" data-element-id="Y"` inside the pristine HTML, so
reordering two attributes silently broke the "recorded" confirmation (the decision still
persisted, so it failed quietly rather than loudly). v2 renders rows *from* the decisions array,
so a recorded decision simply re-renders as recorded. Only the blob is swapped in the pristine
source; no string surgery touches markup.

Still true, and load-bearing: `PRISTINE` is captured **once, at load**, before any click, per
`window.claude.self`'s own contract. Never serialize the live DOM after a mutation.

## CSS landmines that survived the rewrite

These are properties of HTML and the browsers, not of v1, so they still apply:

- **Never join a list with an HTML entity and pass the joined string through `esc()`.**
  `esc()` escapes every `&`, so `&middot;` renders as the visible text "&middot;". Escape each
  item individually, or use the literal `·` character.
- **Every CSS class used must have a rule in the stylesheet.** An undefined class fails silently
  — no browser warning. Grep the CSS block before adding a new one.
- **Never set `display:grid` or `display:flex` on a `<summary>`.** Several engines fall back
  toward block flow and the children overlap. Wrap the row's content in a plain child `<div>`
  and grid THAT — `.srow` is the working example. Keep `summary::marker{display:none}` alongside
  the `-webkit-details-marker` rule; the webkit-only rule leaves a stray triangle elsewhere.

## Honesty constraints — do not "fix" these to make numbers look cleaner

- Ledger rows whose `value_trust` is not `ok` are **excluded from chart scales** and the chart
  states how many it excluded. Marked, never dropped: a corrupt price-feed reading must not set
  an axis, and must not disappear either.
- Cumulative book-vs-benchmark is **not plotted** while `external_flow_usd` is unpopulated,
  because a cumulative line would mix deposits with returns. Only per-period relative
  performance is shown, and an all-null rolling window renders its own note rather than an
  empty panel.
- Bucket hit rates below n=5 are labelled "too few to judge"; below 40% at n≥5 they are labelled
  de-emphasised. A rate without its n is not a rate.

## Verifying layout changes

A tag-balance check on the HTML string catches missing tags but **cannot** catch a CSS layout
bug — the `<summary>` markup above was perfectly valid, `display:grid` just did not apply. For
any layout-affecting change, load the real file through a browser context:
`python3 -m http.server <port> --directory /Users/yb/Claude/AgentSmith`, then navigate to
`http://localhost:<port>/dashboard.html`. `file://` URLs render as inert snapshots with no JS
context and will not catch this class of bug; neither will `curl` or a text diff.

Because v2 renders client-side, the useful check is now a JS one — query the live DOM for panel
headings, row counts and out-of-bounds SVG labels rather than screenshotting each section.

Note: served locally without a charset header the page shows mojibake for em dashes. That is the
local server, not the file — the Artifact wrapper supplies `<meta charset>`.

## Publish

Via the Artifact tool. **URL persistence:** pass `state.json`'s `artifact_url` as the `url`
parameter or a new session mints a new URL; write the returned URL back. Every publish declares
`capabilities: {"self": {}}` — that is what makes the decision buttons work.

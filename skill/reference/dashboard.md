# Agent Smith — dashboard reference

**v2 as of 2026-09-09.** The builder is `scripts/smith_dashboard.py`. The previous generation
is archived at `archive/smith_dashboard_v1.py` and is not run — its per-panel HTML is kept only
as a reference for what a panel used to look like when porting or checking one.

Read this before editing the builder, or when a rendered panel looks wrong. SKILL.md §6 keeps
the operative rules (generate don't author; read the printed panel counts; reuse `artifact_url`;
declare `capabilities: {"db": {}}`).

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

**Rewritten 2026-09-16 onto the `db` runtime capability** (see DB MIGRATION below). Rows still
render client-side *from* the `DEC` array (`decideBox`, unchanged since v2) — that design
survived the migration untouched. What changed is where `DEC` comes from and how a click lands.

**v1's landmine is still gone, for the same reason as before.** v1 located the clicked row by
string-matching the literal substring `data-surface="X" data-element-id="Y"` inside the pristine
HTML, so reordering two attributes silently broke the "recorded" confirmation. Rows are rendered
*from* the decisions array, never string-matched against markup — true under both the v2 publish
design and the current db design.

## DB MIGRATION (2026-09-16)

**Why.** The v2 design stored decisions inside the published page itself: a click read the
pristine HTML's `<script id="smith-decisions">` blob, appended the new decision, and
republished the WHOLE document via `window.claude.self.publish`. Reading them back cost the
same amount in the other direction — §1.7's sync had to `WebFetch` the entire ~600KB page just
to pull that one blob back out (120K+ tokens per sync, twice in one FOMC-day run — see the
2026-09-15 efficiency review). The page's *content* was never the expensive part; the
decisions were riding inside it for no reason connected to what they are.

**What changed.** Decisions now live in the artifact's `db` capability, in a `decisions`
collection — one document per click, written directly (`db.collection("decisions").add(payload)`),
read directly (`db.collection("decisions").get()`). No page republish happens on a click at all
any more; `window.claude.self`/`artifact` is not used anywhere in this file's client JS. The
publish declaration moved from `capabilities: {"self": {}}` to `capabilities: {"db": {}}`.

- **Client (`DECISIONS_JS`).** On load, `claude.use("db")` resolves the namespace (or `null` —
  `readOnly()`, same banner as before). A successful resolve does one `collection("decisions").get()`,
  populates `DEC`, and calls the existing global `render(currentTab())` to re-paint with real
  decisions — the very first paint still happens with `DEC = []` (APP_JS's own
  `DOMContentLoaded` handler), so a viewer sees the page immediately and decisions fill in a
  beat later, same UX as v2's synchronous blob just spread across two paints instead of one.
  A click builds the same `payload` shape as before (`surface`, `element_id`, `decision`,
  `reason`, `decided_on`, plus `new_status`/`headline`/`date` where the surface needs them),
  writes it with `.add()`, and pushes it onto the local `DEC` array — no re-render needed since
  `decideBox` already showed the optimistic "Recorded" span synchronously before the write even
  lands. `db`'s own error codes (`not_granted`, `capability_disabled`, `capability_removed`,
  `revoked`) drop to `readOnly()`; anything else is a plain alert.
- **Server (`sync-decisions`).** `smith_math.py sync-decisions` now takes `--records-file`
  (a JSON array the orchestrator wrote from an `Artifact action:"read_db"` call against the
  `decisions` collection) instead of `--html-file`. The per-decision reconciliation loop
  (`cmd_sync_decisions`'s body) is unchanged — it never cared how the array reached it. The old
  `--html-file` path (`_extract_decisions`, regex over a `<script>` tag) is kept as a documented
  LEGACY fallback, not removed, in case a page published before this migration is still live
  somewhere and needs one last sync.
- **The decisions collection never gets pruned.** Every sync reads the WHOLE collection (it's
  naturally small — dozens of clicks over months, nowhere near the 5,000-document-per-artifact
  cap) and relies on the SAME idempotent "already {status}" skip logic `cmd_sync_decisions`
  always had to make re-syncing safe — a decision already applied just gets skipped again,
  cheaply. This mirrors v2's own design (which also never trimmed the accumulating blob) rather
  than introducing a new deletion path with its own failure modes.
- **A real side effect, not just an implementation swap: republishing the dashboard is no
  longer destructive.** Because decisions never lived in the published HTML to begin with under
  this design, a fresh `smith_dashboard.py` build can be republished at any time without risking
  an unsynced click — the "must not republish if sync was skipped" rule (§1.7's step 0, §6's
  PUBLISH paragraph) existed ONLY because v2's design put decisions inside the very content
  being overwritten. Sync-before-build is still worth doing so the freshly built page reflects
  reconciled proposal/state changes, but it is no longer a data-loss guard.

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
`capabilities: {"db": {}}` — that is what makes the decision buttons work (rewritten 2026-09-16,
see the DB MIGRATION section below; replaced `{"self": {}}`, which the page no longer needs at
all — nothing client-side calls `window.claude.self`/`artifact` any more).


## Moved from SKILL.md on 2026-09-14

> Moved verbatim out of SKILL.md on 2026-09-14 (core cut to <=60KB). Load this file only when the core step that cites it runs. Where this text and the core disagree, the core wins — it reflects the scripted flow (`preflight`, `smith_fetch.py`, `dispatch-plan`, `postflight`).

### 1.7. DASHBOARD DECISION SYNC (added 2026-08-25; moved onto the `db` capability 2026-09-16 — see DB MIGRATION above; still gated by frequency since 2026-09-14 — see step 0 below)
The interactive dashboard (§6) lets the user click Accept/Reject/Hold on proposals and equivalent decisions on 8 other surfaces (auto-retired proposals, watchlist setups, the diversifier bench, the de-risk queue, known gaps, learning-parameter escalations, thesis verdicts, factor catalysts). A click writes one document directly to the artifact's `db` capability (`decisions` collection) — this step is where that accumulated data actually gets read and applied.

**0. FREQUENCY GATE (added 2026-09-14, closes a real token-waste finding).** Even though a `db` read is cheap on its own (a handful of small documents, not the whole page), a sync still costs an `Artifact action:"read_db"` call and a script call, and engagement has run roughly 1 sync-worthy click per ~25 runs historically — so the gate stays. **Always run the full sync on a DEEP run.** **On a QUICK or PRICED REFRESH run, skip steps 1-4 entirely unless `state.json.dashboard_last_synced_ts` is missing or more than 24 hours old, or the user explicitly asks to sync/check the dashboard.** State which happened in one line either way — "Dashboard sync: skipped (synced 3h ago)" is a normal, expected line, not a silently-dropped step. **Unlike before 2026-09-16, a skipped sync no longer blocks §6 from republishing** — decisions live in the db, not in the page, so a fresh build can't clobber them; sync before publish is still worth doing so the page reflects reconciled state, not to prevent data loss.

1. Read `state.json.artifact_url`. If absent (first run, dashboard never published), skip this step entirely and say so in one line — nothing to sync yet.
2. `Artifact action:"read_db"`, `url` = `state.json.artifact_url`, `db_op:"list"`, `collection:"decisions"` (a generous `query.limit`, e.g. 500 — the collection is naturally small). Write the returned documents to a flat JSON array file, `runs/<ts>/dashboard_decisions.json` — each entry carrying its document id as `id` plus the decision fields (`surface`, `element_id`, `decision`, `reason`, `decided_on`, and `new_status`/`headline`/`date` where the surface wrote them). This result is small (a handful of documents at most); it does not carry the 120K-token cost the old WebFetch-the-whole-page path did.
3. Run `python3 scripts/smith_math.py sync-decisions --base-dir . --records-file runs/<ts>/dashboard_decisions.json --today <date>`. This is fully deterministic — it parses the array and dispatches per-surface, it is never eyeballed or hand-applied. It also stamps `state.json.dashboard_last_synced_ts`, which is what step 0's gate reads next time. (LEGACY: `--html-file` still works against a page published before this migration — see DB MIGRATION above.)
4. **State the result in one line at the top of the briefing** — "Dashboard sync: 2 accepted, 1 rejected, 1 held since last run" or "Dashboard sync: nothing pending." Silent reconciliation is exactly the kind of thing this codebase's own standing discipline says never to do (see G50, the factor-catalysts persist gap that went undetected for a week because nothing announced it).

**What each surface does, briefly (full design: `sync-decisions`'s own docstring in smith_math.py)** — Accept: `status: "accepted_by_user"`, distinct from a ledger-confirmed `executed`/`fulfilled`/`filled`, since a click is a stated intent, never proof of a trade. Reject: identical code path to a chat `dismiss P-014`. Hold: proposal stays open, gains `held_on`/`held_reason`. Revive: reopens an auto-retired proposal. Watchlist/diversifier "not interested": writes `state.watchlist_suppressed`, read by `entry_setup`/`bench_diversifier` trigger generation in `cmd_triggers` so a suppressed ticker stops being re-proposed. De-risk "disagree": writes `state.derisk_overrides`, which `cmd_derisk`'s dashboard rendering shows ALONGSIDE the computed score, never instead of it — a real risk signal is annotated, never suppressed. Gap "resolve": standard gap-closing shape, EXCEPT a gap carrying a `user_decision` field (a standing directive from a prior real conversation, e.g. G18's "confirmed LEAVE AS wont_fix, do not re-open") is never offered the button at all — that one needs a chat conversation, not a tap, and the dashboard doesn't pretend otherwise. Learning-parameter "approve": the one surface where a click IS the intended mechanism — moves an `escalated` parameter to `active` at its measured value via `smith_learning.user_force_approve`, which no-ops safely if the parameter has since moved out of `escalated` (a stale click never forces a value the user wasn't actually looking at). Thesis "confirm": logged as an observation only, never bumps `verified`. Thesis "override": requires a reason, writes `verified: "user_stated"` — a real, distinct evidence tier that can move a status but never masquerades as a sourced primary/secondary check. Catalyst "priced in": adds to `state.catalyst_suppressed`; smith-catalyst's dispatch prompt is told not to re-surface a suppressed (headline, date) pair.

**Single-user assumption, stated so it's never rediscovered as a surprise**: a `db` write lands under the clicking viewer's own authority, and the default access rules give every signed-in viewer of a `db` artifact both read and write on the shared `decisions` collection. If this dashboard is ever shared, anyone with access could inject a fake decision on any of the 9 surfaces — including a Thesis Override or a Learning-parameter Approve, both of which change what the system believes, not just what it measures. No access-rule restriction is declared; keep the artifact unshared.

### 6. DASHBOARD ARTIFACT

**GENERATED, NOT HAND-WRITTEN.** The same compute-first rule that governs arithmetic governs the
dashboard — do NOT author dashboard HTML yourself. Run the compute pipeline (`smith_math.py
pipeline`), then `score` → `proposals` → `stops` → `validate` individually, then:

- `python3 scripts/smith_math.py stops --base-dir . --prices-json <tickers.json> --today <date>` — writes the standing `stops_analysis.json`. `--prices-json` is a flat `{"TICKER": price_usd}` map YOU fetch (the script has no network). Probe with a file containing `{}` (an empty JSON **object** — `/dev/null` is not valid JSON) and it names the tickers it needs; `cmd_stops` refuses to overwrite the file with fewer stops than it already holds. Skippable when `trades.json` has no new unscored stop-loss fills. **Merge multiple fetch rounds via `smith_math.py merge-prices --inputs a.json b.json ... --out prices.json`, never by hand** (added 2026-09-10) — it accepts either a flat map or raw yfinance `get_stock_price(format=json)` output per file (extracting `.price` from the nested shape automatically), last file wins on a collision, and a non-numeric value is named in `skipped` rather than silently dropped or coerced. This replaced three separate hand-written `python3 << EOF ... json.dump(...)` merge blocks in a single 2026-09-10 sweep — each one a fresh chance to fat-finger a key or lose a ticker.
- Write `narrative.json` — `{"as_of": "<today's date>", "session_read": "..."}` — with this run's judgment prose (optional). **`as_of` is not optional once you write the file** (added 2026-09-15, closes G96): narrative.json carries no FRESHNESS-table TTL, so a 2026-09-09 read sat under a 2026-09-14 dashboard header looking current for 5 days until the user caught it by inspection — the panel now renders `as_of` as its own subtitle instead of the run's build timestamp, and a missing key renders as "date unknown" rather than silently borrowing today's date. The macro strip beside it is NOT narrative; it comes from `market_inputs.json` / `state.fomc_cache` / `compute_book.json`. Same rule applies to `state.macro_read.as_of`, already required upstream — the dashboard panel now shows it next to the regime note for the identical reason.
  **`session_read` is PORTFOLIO ANALYSIS ONLY, never a changelog of what the desk did to its own machinery** (user correction, 2026-09-15). Written the same day as the G96 fix above, the very first corrected `session_read` itself violated this: it narrated that two proposals "were briefly auto-retired purely for being restated 3-4 times, then revived" and explained the rule change behind it — meta-commentary about the proposals engine's own internal history, not a read on the market or the book. The user's own words: *"why the dashboard is showing such history of execution. i think i should give cleaner and the actual output not what have happened to it."* A proposal's current status (open/retired/priority) is already visible in its own panel with its own `retired_reason` — the narrative does not need to re-explain how it got there, and never should. If a proposal's situation changed in a way worth narrating, describe the PORTFOLIO fact (e.g. "KLAC and CIEN are executable now alongside APH") not the SYSTEM fact (e.g. "were auto-retired then revived because a rule changed"). Save process history for `known_gaps`/commit messages/DECISIONS.md, which exist for exactly that and are not user-facing.
- `python3 scripts/smith_dashboard.py --base-dir .` → rewrites `dashboard.html` from state/policy/ledger/proposals/trades/stops plus `narrative.json`. It prints a panel-count summary (positions, clusters, proposals, trigger families, stops, dq, gaps) — **read those counts, they are the regression check.**

**DASHBOARD v2 (2026-09-09).** The builder was rewritten. It no longer assembles the page from ~35 hand-wired HTML string builders; it builds ONE payload dict, embeds it as JSON, and ships a client-side app that renders five tabs (Command · Book & risk · Conviction · Track record · Diagnostics) with sortable/filterable tables, a full 254-row proposal-history browser, and a ticker sheet that pulls one name's thesis, evidence, cluster rank, live triggers, fills, stops and hit-rate grades into one place. v1 is kept at `archive/smith_dashboard_v1.py` as the reference for what a panel used to look like — it is not run.

**REGRESSION GUARD (2026-07-28, restated and now enforced in code).** v1's guard was a written instruction to diff before publishing, and it failed: `build()` ended up calling only 12 of its ~35 `_render_*` functions, so thirteen panels — thesis map, signal history, execution log, data-quality caveats, self-learning, stop-loss efficacy, watchlist setups, factor themes, trade triggers, diversifier bench, rotation analysis, retired proposals, open gaps — were defined, never called, and silently absent from the published page for weeks. Their unit tests all still passed, because each builder worked fine in isolation; nothing tested that it was *reached*. v2 replaces the instruction with a mechanism: `REQUIRED_KEYS` + `assert_payload_complete()` fail the build if a payload key goes missing, `tests/unit/test_smith_dashboard_payload.py` pins the floor, and `tests/verify_dashboard.sh` diffs the whole output against a golden master. **Still diff byte size before publishing** — but the guard no longer depends on someone remembering to.

**PUBLISH — republishing is safe any run, since 2026-09-16** (see DB MIGRATION above; supersedes the 2026-09-14 hotfix that made publish conditional on §1.7's sync — decisions live in the `db` capability now, not inside the page, so a fresh build can never clobber an unsynced click). Syncing first is still good practice (the freshly built page then reflects reconciled proposal/state changes), but is no longer required before publishing. Publish via the Artifact tool. **URL PERSISTENCE — critical**: if state.json has `artifact_url`, pass it as the tool's `url` parameter or a new session mints a NEW url; save the returned URL back to `artifact_url` after. Every publish must declare `capabilities: {"db": {}}` — that is what lets the Accept/Reject/Hold buttons write decisions (§1.7 drains them next run). Both modes run the same builder; it is cheap and always reflects current state.

**HONESTY CONSTRAINTS baked into the charts — do not "fix" them to make numbers look cleaner:** (a) ledger rows whose `value_trust` is not `ok` are drawn ringed/hatched and EXCLUDED from scales and win/loss counts; (b) cumulative book-vs-SMH is deliberately NOT plotted while `external_flow_usd` is unpopulated, because a cumulative line would mix deposits with returns.

**FULL SPECIFICATION → `reference/dashboard.md`.** The payload contract, the tab manifest, the CSS landmines that survived the rewrite (`&middot;` through `esc()`, undefined CSS classes, `display:grid` on `<summary>`) and the browser-verification procedure live there. **Read it before editing `scripts/smith_dashboard.py`, or when a panel renders wrong** — it is engineering detail for changing the builder, not a step this run executes. One v1 landmine is now GONE and should not be reintroduced: v1 located a clicked row by string-matching `data-surface="X" data-element-id="Y"` in the pristine HTML, so reordering two attributes silently broke the "recorded" confirmation. v2 renders rows *from* the decisions array, so no string surgery on markup happens at all — only the blob itself is swapped.


# Agent Smith — dashboard reference

Split out of `SKILL.md` §6 on 2026-08-30. It was 18.4KB of a 143KB file read **in full on every
run**, including quick runs that never touch most of it — while `scripts/smith_dashboard.py` is
the actual authority for everything in here. The required-section list, the three 2026-08-08
rendering bugs, the CSS landmines and the interactive layer's attribute-order trap are all
engineering notes for someone editing that script, not instructions the orchestrator executes.

SKILL.md keeps the operative rules (generate, don't author; regression-guard the diff; reuse
`artifact_url`; declare `capabilities: {"self": {}}`). Read this file before editing
`smith_dashboard.py` or `smith_charts.py`, or when a rendered panel looks wrong.

---

## The full specification, as it stood at the split
**REGRESSION GUARD (added 2026-07-28).** On 2026-07-28 two consecutive rebuilds shipped a ~30KB dashboard that silently
dropped four SVG charts and the entire Diagnostics tier, regressing work done in an earlier session (commit 7cb26ea,
"generate it from state + charts instead of hand-writing prose"). The user caught it, not the desk. **Before publishing,
diff the new file against the last published version: if section count or byte size falls materially, you are deleting
someone's work — stop and merge instead of overwriting.** The dashboard is cumulative; sections are added, not replaced.

REQUIRED SECTIONS (a rebuild missing any of these is incomplete — revised 2026-08-06, dashboard feature review: added
stop-loss efficacy, P&L/day-change, factor themes, diversifier bench, LTCG watch, execution log, data-quality caveats,
and forward-looking proposal retirement text; the 2026-07-29/G34 list below this line predates those):
- Masthead · Status strip, **8 cells when the run supplies the data, 6 minimum**: total book, equity, **P&L%** (from
  `compute_book.json`'s `pnl_pct`, INDmoney's own invested-vs-current — renders only when non-null), **Today**
  (`day_chg_pct_weighted`, a book-weighted day-change — renders only when the run's `holdings.json` rows carried a
  `day_chg_pct` overlay; see §2's holdings.json schema note), cash%+band, drawdown, open risk%+cap,
  AI-capex%
- Decisions tier: open proposals, **grouped into collapsible HIGH/MEDIUM/LOW priority `<details>` sections**
  (added 2026-08-03, G47 — see §7's proposals.json entry for the deterministic scoring rule; HIGH starts expanded,
  MEDIUM/LOW start collapsed), each row carrying a BUY/TRIM/SELL/HOLD color badge on BOTH the action label and the
  dollar amount (same visual language as the factor-catalyst TAILWIND/THREAT/AMBIGUOUS badges) plus its cluster tag
  in the left label column, while its stable `id` and (when repeated) "recommended N&times; since DATE" sit as a
  small meta line under the rationale in the middle column, not stacked in the left column — keeping that column
  a fixed narrow width regardless of how much repeat/id metadata a proposal carries. Since 2026-08-06 each surviving
  row also carries `still_valid_because` (live, recomputed reasons), `review_flags` (price drifted ≥10% since
  proposed — re-size before acting), a `tranche_note` when a trim cures under 90% of its trigger's dollar excess
  (honest sizing, added 2026-08-06 — see §6's honest-sizing note), and a forward-looking `retires_when` line
  ("MRVL drops under its ATR risk cap") so the auto-retirement logic in §7's proposals.json entry reads as legible,
  not mysterious. **Rotation ideas** (added 2026-08-06, same change): proposals sharing a `pair_id` render together,
  above the priority tiers, as a linked sell-leg → buy-leg card rather than split across HIGH/MEDIUM/LOW
  · factor catalysts · **factor themes** (added 2026-08-06 — the standing structural watch list each catalyst gets
  checked against; companion to catalysts above, which are event-driven) · **diversifier bench** (added 2026-08-06 —
  smith-scout's priced non-AI-capex candidates from `state.diversifier_candidates`, green chip = clean diversifier,
  amber = has AI-adjacent overlap; not a proposal to buy, a bench of what a real hedge would look like) ·
  **rotation analysis** (accumulate / rotate out / trim — risk cap, rule-based per `scripts/smith_risk.py`'s
  `SIGNAL_POLARITY` table) · **clusters** (moved here 2026-08-07, swapped with de-risk queue, per user request —
  a decision-relevant section belongs in Decisions, not buried after the composition treemap; equity% and book%
  side by side, target-band meter; **expandable** since 2026-08-08 — each cluster is a `<details>` row, click to
  see its member holdings: ticker, weight%, price, thesis status dot, and signal tags including a distinct badge
  for PEER LEADER/PEER LAGGARD from `state.signal_history`, plus a warning icon if the name is over its own risk
  cap — a plain `<table>` couldn't do this without JS, which this dashboard deliberately has none of, so it's
  built from the same `<details>/<summary>` idiom the priority tiers and Diagnostics already use; own full-width
  panel, pulled out of the risk-cap-breaches grid2 pairing since the expanded member table needs the width.
  **Struck-through "no longer held" tickers** (added 2026-08-07, same user request) — each cluster's expanded
  body also lists any ticker `sector_map` still maps to that cluster but that isn't in `held_tickers` (exited
  positions, or names only ever tracked), rendered as `<span class="tick gone">` chips under a "No longer held /
  tracked only:" line — the same `.tick.gone{opacity:.42;text-decoration:line-through}` convention the Signal
  History panel already used, not a new visual language) · **stop-loss efficacy** (added 2026-08-06 — see the
  `stops` subcommand note in §6; cascade-vs-deliberate cohort comparison of every stop-loss fill against its
  current price) · the read · macro strip (10-yr, VIX, SMH, worst Asia index, Fed, beta vs SMH)
- Sentiment gauge + intraday & international session (side by side)
- The week ahead (earnings/FOMC calendar, 6 days forward)
- Book composition tier: **allocation treemap** (squarified, color by cluster, red outline = over risk cap) ·
  **de-risk queue** (moved here 2026-08-07, swapped with clusters, per user request — ranked fragility × stretch
  × friction, shadow-scored, see 2.9c) · risk-cap breaches (from `compute_risk.json`'s
  real ATR-based caps, not a qualitative flag match) · **LTCG watch** (added 2026-08-06 — lots within 6 months of
  the policy's LTCG boundary from `compute_book.json`'s `ltcg_flags`; an empty result renders an explicit "clear"
  pill, not a vanished section, since the empty state is itself a real, positive statement) · full positions table
  (ticker, cluster, qty, price, value, weight, ATR20, beta, stop, stop price, cap, headroom)
- Diagnostics tier, collapsed: thesis map (grouped by status, **filtered to currently-held tickers only** — fixed
  2026-08-06 after the panel claimed "36 held" while the book held 28; stale theses for exited names stay in
  `state.thesis` for history but no longer render as if current) · signal history (grouped bullish/bearish,
  struck-through for no-longer-held tickers) · open (non-closed) data gaps · **execution log** (added 2026-08-06 —
  `trades.json`'s full captured-rationale history, most recent 25 shown, "why" not just "what") ·
  **data quality caveats** (added 2026-08-06 — every compute step's self-reported `data_quality` array plus
  `state.data_quality`, unioned; a dashboard hiding its own uncertainty invites more trust than the numbers earn) ·
  **Historical charts** (the 4 original SVG charts — book value & cash, drawdown ladder, book vs SMH, weights vs cap
  — as their own collapsed panel; the book-value chart now marks every date with scored stop-loss fills, see the
  `stops` subcommand note in §6 — as their own collapsed panel, not the always-open KPI tier those used to live in)

GENERATED, NOT HAND-WRITTEN (changed 2026-07-26; extended 2026-07-29 per G34, and 2026-08-06 with the `stops` step). Do NOT author dashboard HTML yourself — the same compute-first rule that governs arithmetic governs the dashboard. Compute pipeline order matters: `book → risk → drift → journal → attribution → rotation → sentiment → derisk → triggers` (all nine via `smith_math.py pipeline`), then `score` → `proposals` → `stops` → `validate` individually. Corrected 2026-08-15: the old list omitted journal, attribution and triggers entirely, which is exactly why `triggers` went unrun on the 08-15 deep review until the strategist flagged its absence — every proposal that run therefore carried `trigger_type: null`. (`risk`, `rotation` and `derisk` are `smith_math.py` subcommands — `risk` needs `compute_book.json` in the run-dir first, `rotation` needs `compute_risk.json`, and `derisk` needs both `compute_risk.json` and `compute_sentiment.json`, so it runs after sentiment). Then run:
- `python3 scripts/smith_math.py stops --base-dir . --prices-json <tickers.json> --today <date>` — writes the standing `stops_analysis.json` (NOT run-dir scoped, unlike the others, so run-pruning to the last 10 never loses it). `--prices-json` is a flat `{"TICKER": price_usd}` map YOU must fetch (this script has no network access by design) for every ticker with a stop-loss fill in `trades.json` that isn't already scored — run it first with a file containing just `{}` (an EMPTY JSON OBJECT, **not** `/dev/null` -- an empty file is not valid JSON and the command errors out) if unsure which tickers need prices; as of 2026-08-16 that probe is safe, because `cmd_stops` REFUSES to overwrite `stops_analysis.json` with fewer stops than it already holds and instead prints the tickers it needs (before that guard, this exact probe silently destroyed the 94-row efficacy record twice); unscored tickers are listed in the output's `data_quality`, not silently dropped. Skippable if `trades.json` has no new unscored stop-loss fills since the last run (the file is idempotent to re-run with the same prices).
- `python3 scripts/smith_dashboard.py --base-dir .` → rewrites `dashboard.html` from state.json/policy.json/ledger.csv/proposals.json/trades.json/stops_analysis.json plus `narrative.json`, embedding five inline-SVG charts produced by `scripts/smith_charts.py` (book value + cash stacked area — now with a small red triangle on any date that had a scored stop-loss fill, hover for tickers — drawdown-vs-trim-ladder meter, per-period book-vs-SMH diverging bars, position weights vs cap, and the allocation treemap).

Before running it, write `narrative.json` — `{"session_read": "..."}` — with this run's judgment prose (optional; omit the key and the "the read" panel is skipped). The macro strip next to it is NOT narrative — it's pulled straight from `market_inputs.json`/`state.fomc_cache`/`compute_book.json`, never hand-typed.

STRUCTURE the builder enforces, and the reason for it: the old 16-flat-section layout (3,164 words, proposals buried at section 11, zero charts) was replaced 2026-07-26 with a leaner 3-tier design, which was itself found 2026-07-29 (G34) to have fallen behind a richer version that got hand-authored once and never ported into the generator. The current structure is the richer one, generated properly this time: **DECISIONS** (proposals, catalysts, rotation, the read — always open, first), a sentiment/session pair, a week-ahead calendar, **BOOK COMPOSITION** (treemap, clusters, risk caps, positions — always open), **DIAGNOSTICS** (thesis, signals, gaps, plus historical charts — collapsed). Prose rule: one sentence inline, anything longer inside `<details>`. The chat briefing still carries the narrative — the dashboard's own prose stays to "the read" and macro numbers, not a second copy of the full briefing.

Charts follow the `dataviz` skill: validated palette (blue/yellow/red passed the six checks in both modes), one axis per chart and never a dual axis, direct labels on the light-mode yellow (sub-3:1, relief rule), `<title>` hover on every mark. If you change chart code, re-run `scripts/validate_palette.js` and re-render to look at it before shipping.

THREE RENDERING BUGS FOUND 2026-08-08 (user-reported: literal "&middot" text visible on the page, heading subtitles running into the heading with no space, and — the very next round, after shipping the expandable-cluster feature — the cluster rows rendering as unstyled overlapping text with the band meter dropping to its own line below) — all three are landmines worth naming explicitly since they're easy to reintroduce:
- **Never join a list with an HTML entity separator (`" &middot; ".join(items)`) and then pass the WHOLE joined string through `esc()`.** `esc()` escapes every `&` it sees, so `&middot;` becomes the literal text `&amp;middot;`, which renders on the page as the visible string "&middot;" instead of a dot. Escape each item individually first (`" &middot; ".join(esc(x) for x in items)`), or use the literal `·` Unicode character instead of the entity wherever the string is headed through `esc()` — that's what `fig()`'s `sub` parameter needed, since `esc()` doesn't need to touch a plain Unicode character. Found in three places: the Factor catalysts `affects` field, Factor themes `maps_to` field, and the treemap's `fig()` sub-text.
- **Every CSS class used in the generator's HTML must have a matching rule in `CSS`** — `<span class="sub">` had been used as a heading-subtitle class throughout the file (Factor themes, Diversifier bench, Stop-loss efficacy, LTCG watch, Positions, De-risk queue) with **zero CSS definition anywhere**, so it inherited no spacing and ran directly into the heading text. Fixed with a base `.sub{color:var(--ink-3)}` (covers `td.sub` too) plus a `h2 .sub{margin-left:8px;...}` override scoped to the heading context only. When adding a new `<span class="...">` or `<td class="...">`, grep the CSS block first to confirm the class actually exists — an undefined class fails silently, there's no browser warning.
- **Never set `display: grid` or `display: flex` directly on a `<summary>` element.** `<summary>` has special UA-stylesheet and marker-box handling per the HTML rendering rules, and several browser engines silently ignore or only partially apply an author `display: grid`/`flex` on it, falling back toward block flow — child `<span>`s collapse to inline-in-block and wrap/overlap each other, while any sibling `<div>` forces its own line (divs are block-level by default), producing exactly the "overlapping text, meter dropped to its own row" symptom this shipped with initially. Confirmed by loading the real dashboard through a local `python3 -m http.server` (see below) and reading `getComputedStyle` in the browser console — `display` computed to `list-item`, not `grid`, despite the CSS saying otherwise. **The fix used throughout this codebase now**: never style `<summary>` itself as grid/flex — wrap the row's content in a plain child `<div>` (`.clus-summary-grid` is the working example) and apply the grid/flex to THAT div instead, leaving `<summary>` with only simple properties (`cursor`, `padding`, `list-style:none`). Every engine handles that correctly. Also needed `summary::marker{display:none}` alongside the existing `summary::-webkit-details-marker{display:none}` to fully suppress the native disclosure triangle across engines — the webkit-only rule alone left a stray marker visible.

**Verifying dashboard layout changes going forward**: a static `esc()`/tag-balance check on the HTML string (counting `<div`/`</div>`, `<details`/`</details>` etc.) catches missing/extra tags but CANNOT catch a CSS layout bug like the `<summary>` one above — the markup was perfectly valid, `display:grid` just didn't apply. For any layout-affecting CSS change (not just a new panel's content), load the actual file through a real browser context and inspect it: `python3 -m http.server <port> --directory /Users/yb/Claude/AgentSmith`, register that as a `.claude/launch.json` entry (the Browser tool's `preview_start` needs the config in the SESSION's primary working directory, not this one), navigate to `http://localhost:<port>/dashboard.html`, and either screenshot the section or run `getComputedStyle(el).display` etc. via the JS tool — `file://` URLs render as inert static snapshots with no JS context, they will not catch this class of bug. A raw `curl`/text diff won't either; layout bugs are invisible to both.

HONESTY CONSTRAINTS baked into the charts, do not "fix" them by making the numbers look cleaner: (a) ledger rows whose `value_trust` is not `ok` are drawn ringed/hatched and EXCLUDED from scales and win/loss counts — a corrupt price-feed reading is never allowed to set an axis or count as performance; (b) cumulative book-vs-SMH is deliberately NOT plotted while `external_flow_usd` is unpopulated, because a cumulative line would mix deposits with returns — only per-period relative performance is shown.

Then publish via the Artifact tool. URL PERSISTENCE — critical: if state.json has "artifact_url", pass it as the Artifact tool's `url` parameter so the same page updates (new sessions mint a NEW url otherwise); after publishing, save the returned URL into state.json as "artifact_url". Both modes run the same builder — it is cheap and always reflects current state.

**CAPABILITIES (added 2026-08-25, interactive dashboard).** Every publish must declare `capabilities: {"self": {}}` — this is what lets the page's Accept/Reject/Hold and equivalent buttons on the other 8 surfaces republish themselves with an embedded decision (see §1.7 for the full round trip and why no other capability could do this). Passing `capabilities` explicitly is required on every publish call for this artifact — omitting it carries the prior declaration forward per the tool's own contract, but state the intent explicitly here rather than relying on that silently.

**THE INTERACTIVE LAYER'S OWN LANDMINE**, same spirit as the three 2026-08-08 rendering bugs above — worth naming so a future edit doesn't reintroduce it silently: `scripts/smith_dashboard.py`'s `decision_buttons()` emits each row's opening tag as `<div class="decide" data-surface="X" data-element-id="Y"...>`, and the client JS locates that exact row for its "recorded" swap by searching for the literal contiguous substring `data-surface="X" data-element-id="Y"`. **If a future edit reorders those two attributes, or inserts something between them, the visual "recorded" swap silently stops working** — the decision itself still PERSISTS correctly (the decisions-blob swap is a separate, independent regex match against the whole page), so this fails quietly rather than loudly: the click still works, but the button just doesn't visually confirm it did. Keep `data-surface` immediately followed by `data-element-id` in `decision_buttons()` if it's ever touched. The JS itself captures `document.documentElement.outerHTML` once, at load, before any click — never the live DOM after a mutation — per `window.claude.self`'s own documented contract; do not "simplify" this to `document.documentElement.outerHTML` read at publish time instead of load time, since a second click before the first one's reload lands would then be serializing an already-disabled, already-mutated DOM.


# Changelog

Dated record of fixes and decisions. See [ARCHITECTURE.md](ARCHITECTURE.md) for what
currently exists, [POLICY-DECISIONS.md](POLICY-DECISIONS.md) for policy-specific
rationale.

## 2026-09-08 (factor-catalyst carry-forward: an empty scan is not a retirement)

**Observed live on the 2026-09-08 deep run.** First session after a Labor Day long weekend,
news genuinely thin. `smith-catalyst` ran five searches and correctly returned
`"catalysts": []` — nothing cleared its sourcing bar. `_merge_catalyst`'s wholesale REPLACE
then wiped `state.factor_catalysts`, and in one run:

- live `catalyst_threat` triggers went **6 → 0**;
- the **"Factor catalysts" panel disappeared** from the dashboard (a section diff showed 19
  `h2`s before and after, with that one dropped and "Cluster ladders" added);
- the two CXMT HBM3E items dated 2026-09-01 and 2026-09-03 — structural, days old, still live
  — were deleted because they were not *re-reported* in a window that started after them.

**The bug is a conflation.** "No NEW catalyst found in this window" was being stored as "no
catalyst exists". The first is a claim about the scan; the second is a claim about the world,
and only the second justifies deleting evidence the desk already has. Storing a scan's silence
as a fact about the world silently removes risk signals that were properly sourced when found.

- **`_merge_catalyst` is now a carry-forward merge** (`scripts/smith_memory.py`). Three
  distinct states, only one of which deletes anything: **no `catalysts` key** → the agent did
  not run, array untouched (unchanged behaviour); **a `catalysts` list, empty or not** → merged
  by `(headline, date)`, returned items stamped `last_confirmed: today`, everything else
  carried forward with `carried_forward: true` and its original `first_seen`; **`retired_catalysts`**
  naming specific `(headline, date)` pairs → those, and only those, deleted, with the agent's
  reason recorded in the merge result.
- **Each catalyst now expires on its OWN horizon**, not on the next scan's mood —
  `smith_risk.CATALYST_TTL_DAYS`: structural 45d, immediate 10d, mechanical 7d, noise 3d,
  default 14d, measured from the later of `date` and `last_confirmed`. A structural threat
  outlives a noise one by design; carrying forward stays bounded, so the array cannot become
  the accumulating log the REPLACE rule was guarding against. An unparseable date never expires
  anything — that is a data-quality problem, not a licence to delete a threat.
- **One reader for the freshness rule**: `smith_risk.live_catalysts(state, today)`, used by both
  `cmd_triggers`' `catalyst_threat` precompute and the dashboard, so the two cannot drift. A
  carried-forward catalyst fires at **full size** — it is not downweighted — with its
  `last_confirmed` date disclosed in the reason line so the strategist can see the evidence's age.
- **The dashboard panel no longer vanishes.** It always renders, and says which case it means:
  "N new this run · M carried forward", "No NEW catalysts this run · N carried forward", or
  "No live factor catalysts · last scanned <date>". A disappearing panel is exactly the
  silent-failure shape SKILL.md's own regression guard warns about. Carried entries wear a
  `carried · <date>` chip. `factor_catalysts_as_of` is now stamped by `merge-tails`, so "last
  scanned" is a real fact rather than an inference from the newest catalyst.
- **`smith-catalyst` must now confirm or retire what it can already see.** Its slice has always
  embedded `state.factor_catalysts`; the agent file now spells out the three options (re-list =
  confirm, `retired_catalysts` = delete with a sourced reason, silence = carry forward) and
  states the rule directly: **silence is not retirement**.
- **Data repair**: the two CXMT catalysts wiped on 2026-09-08 were restored to `state.json`
  from `runs/2026-09-07-0741/out_catalyst.json`, marked carried forward with
  `last_confirmed: 2026-09-07`.
- **Tests**: `tests/unit/test_smith_catalyst_freshness.py` (12 cases — empty return carries
  forward and does not forge a confirmation; absent key changes nothing; explicit retirement
  deletes and must match the date, not just the headline; noise ages out while structural
  survives the same gap; structural eventually ages out too; an unparseable date never expires;
  `live_catalysts`/`catalyst_carry_summary` readers), plus dashboard cases for the
  carried-forward count and the stale-entry drop, and a trigger case proving a carried-forward
  catalyst still fires at full size. Golden dashboard master updated for the new subtitle pill
  (the only rendered diff).

## 2026-09-08 (benchmark plausibility gate)

**User-reported**: the dashboard's "Beat or lag SMH, per period" chart showed impossible
periods — `SMH +754.66%`, `-123.90%`, `+579.06%` in a single session — and its footer
("17 of 29 periods beat SMH") was COUNTING them, so every relative-performance statement
the desk made was suspect.

- **Root cause is a WRITE, not the chart.** `ledger.csv`'s `smh` column holds a mix of real
  SMH levels (~$545–590) and a completely different quantity. On 2026-08-12 and 2026-08-13
  the real close (586.22, 584.83) sits one column to the RIGHT, in `est_net_flows_usd`, and
  the net flow (4896.61, −1170.30) is in `smh` — an argument-order slip. On 2026-08-25 and
  2026-08-26 a flow figure was passed as `--smh` outright. A period-over-period percentage
  taken across two different units isn't a small error, it's a category error. Same
  measurement-basis-mismatch class the weekly report already guards against.
- **`append-ledger` now refuses an implausible `--smh`** (smith_memory.py): the value is
  checked against the MEDIAN of the last 10 recorded levels — not the last one, which is
  exactly what a corrupt cell overwrites — and rejected if it implies a move beyond
  `BENCHMARK_WEEKLY_PLAUSIBLE_PCT` (±25%). When `--est-net-flows-usd` IS a plausible level,
  the error names the swap explicitly. An empty benchmark cell is honest; a wrong one is not,
  so the write is refused rather than repaired downstream. ledger.csv itself is NOT
  hand-edited — the historical rows stay as written and are excluded at read time.
- **`chart_relative` excludes out-of-band periods** (smith_charts.py) through the same
  `#hatch` mechanism the corrupt-price-feed exclusions already used, with the reason named in
  the tooltip. The footer now reads "N of M **scored** periods" and states how many were
  hatched and why. Side effect worth noting: with the corrupt bars no longer setting the
  axis, the scale went from ±1000% to ±8% and every real bar is legible for the first time.
- **Pinned** by `tests/unit/test_smith_benchmark_plausibility.py` (7 tests): an out-of-band
  period is hatched not plotted, the beat/lag tally ignores it, an in-band period still
  counts, and the four `append-ledger` paths (refuse / name the swap / accept a real level /
  allow an empty cell). `tests/golden/dashboard_case1.html` regenerated deliberately.

## 2026-07-26 (review/cleanup pass)

**Fixed two live defects before they could fire on a scheduled run:**
- **Drawdown denominator bug**: `drawdown_pct` was equity vs equity-only peak. A cash
  conversion (07-24: $18k moved equity→wallet) would read as a ~49% equity
  "drawdown" on the next run and fire the new drawdown-ladder's -25% RISK_OFF rung
  on a book actually down ~12% on a total-book basis. Fixed in both `cmd_book` and
  `cmd_drift` (smith_math.py) to track `peak_total_book_usd` and measure drawdown on
  total book (equity+wallet). Seeded the real historical peak ($44,873.02, from
  ledger.csv's 07-18 row) into state.json so the next run computes correctly
  (-11.77%, normal) instead of bootstrapping off today's total as a false peak.
- **Guessed betas reverted**: SNDK/DRAM/IREN/ARM had estimated beta values inserted
  directly into `data_cache.betas` with no distinguishing flag — violates the
  orchestrator's own guardrail ("never estimate a number the script wasn't handed
  directly; emit null + flag instead"). Reverted; the script's existing
  `beta_missing` fallback now correctly flags these 4 names (25.7% of book) in
  data_quality instead of the guess being silently trusted.
- Removed 3 static prose fields (`benchmark_note`, `sizing_context`,
  `factor_attribution_note`) that were unimplemented-feature TODOs emitted as if
  computed data on every run.
- Deleted a stale `.running` lockfile (11h old, orphaned from an interrupted run).

**Token-efficiency pass** (~55% cut to fixed per-run memory-load cost, nothing
deleted — moved to archives):
- `proposals.json`: 64→11 live entries (10.5k→1.9k tok). Archived 53 entries with a
  terminal, non-scoreable status to `proposals-archive.json`.
- `state.json` `known_gaps`: 19→10 entries. Archived 9 resolved gaps to
  `known-gaps-archive.json`; trimmed 6 open entries from long narratives to compact
  status lines. Corrected two stale statuses in passing: G25 (qty_changes fix) was
  live-fixed 2026-07-26 but never marked resolved in the registry; G28's two open
  user-decisions were both closed 2026-07-25 but the gap stayed open.
- `state.json` `thesis`/`sector_map`: 36→24 entries each. Retired 12 exited-position
  entries to `exited-holdings-archive.json`.
- `policy.json` `notes`: 11 essays (4.5k chars) → 4 short pointers. Full rationale
  moved to `POLICY-DECISIONS.md`.
- Collapsed 8 overlapping root status docs (AGENT-AUDIT, ARCHITECTURE-AUDIT-
  COMPLETION, TIER1-FIXES, TIER2-TIER3-ENHANCEMENTS, SELL-DISCIPLINE-FRAMEWORK,
  TIER21-HBMTRACKER-INTEGRATION, SESSION-SUMMARY — same content restated 3-4x) into
  this changelog + ARCHITECTURE.md.

## 2026-07-26 (Tier 2/3 feature work)

- **Sell-discipline framework** (Tier 2.3): added `drawdown_trim_ladder` to
  policy.json — 4 rungs from -15% (warn) to -25% (risk-off/move-to-cash). Wired into
  `cmd_drift` to emit a `drawdown_action` recommendation. See POLICY-DECISIONS.md.
- **SOX/SMH benchmarking** (Tier 2.5): added `benchmark_betas` to state.json (SOX
  1.19 primary, SMH 1.19 peer, SPX 1.491 flagged misleading). `cmd_book` now emits
  `primary_benchmark`. Removes the false Friday anomaly (SPX predicted +0.075%,
  actual was -5.06%; SOX beta ~1.19 matches the actual move).
- **HBMTracker integration** (Tier 2.1): `smith-thesis.md` gained a task to WebFetch
  HBMTracker/history.json + forecast.json when Memory-cluster names (MU/SNDK/DRAM/
  EWY) are held, extract latest HBM3E ASP, and reconcile against thesis verdicts
  (e.g. "strengthening" vs a -51% ASP decline from H1-2025 peak). Outputs
  `thesis_tensions` in the JSON tail. Not yet deep-run tested live.
- **Agent skeletons created** (Tier 3.1-3.3): `smith-cycle` (AI capex cycle
  position), `smith-earnings` (earnings calendar + option-implied move),
  `smith-tax` (LTCG lot sequencing). None wired to live data sources yet;
  `smith-tax` additionally blocked on `lots.json` being empty.
- **Designed, not built** (Tier 2.2/2.4/2.6/2.7, Tier 3.4/3.5): AI-capex cycle data
  sourcing, volatility-aware proposal sizing, market/sector/idio attribution
  decomposition, lots.json seeding guide, regime-conditional diversifier screening,
  dashboard book-value sparklines.

## 2026-07-25

- **G28 resolved**: policy.json cluster targets had summed to 105% (Diversified 5%
  bolted onto an already-100%-summing AI-cluster set) alongside a mixed-denominator
  drift table (clusters equity-based, cash total-book-based — never comparable).
  Fixed: Diversified/Regional ETF target set to 0; denominators declared explicitly
  (`cluster_target_denominator: invested_equity`, `cash_pct_denominator: total_book`,
  `ai_capex_denominator: invested_equity`); `validate_policy()` added to
  smith_math.py to catch this defect class going forward.
- **User decision**: AI-capex concentration affirmed intentional ("high conviction
  on AI Infra and capex"). `max_ai_capex_factor_pct` raised 90→100;
  `ai_capex_factor_flag_threshold_pct` set to null; `concentration_is_intentional:
  true` added.
- **Cash correction**: user flagged the persisted cash figure ($5,656.86) as stale
  vs actual (>$10k). Root cause: the 07-24 18:29 IST run was captured pre-market (31
  min before the 09:30 ET open), missing the entire US session. That session saw a
  severe broad AI-capex selloff (weighted avg -5.06%, worst SNDK -10.79%) coinciding
  with 5 full exits (GLW/NBIS/IREN/+2) and 8 position halvings, raising wallet cash
  from $5,656.86 to $18,131.51 (45.8% of book). Trade rationale was never captured
  (G26) — read as one de-risking event, not two unrelated ones.

## 2026-07-24

- Daily scheduled run rescheduled 14:30→07:30 IST weekdays (was pre-market/05:00 ET,
  missing the full prior US session; now post-close/22:00 ET previous day).
- `qty_changes` fixed to catch full exits and new entries (previously only diffed
  tickers present in both prior and current snapshots — G25).
- `trades.json` created for trade-rationale capture; `cmd_book` attaches
  `trade_reason` to every qty_change going forward.
- Proposal lifecycle rules added (`cmd_proposals`): auto-supersede duplicates,
  auto-expire >7 days old, auto-void on cleared breach or exited position.
- Cache-staleness validation added (`validate_cache_events`): flags a `fomc_cache`
  whose `next_check_date` has already passed.
- Journal scoring 14-30d window alert added so upcoming hit-rate activation is
  visible before it fires.

## 2026-07-23

- G21: smith-rebound successfully triaged a hot pre-market session (resolved).
- G22: INDmoney price feed produced internally-consistent but fabricated intraday
  gains (+10-20% on ~10 names while SPX/NDX were flat) — cross-checked against
  yfinance, discarded wholesale for the run. More severe than prior staleness
  issues (G3) since this was actively wrong, not merely lagging.

## 2026-07-20

- Beta cache partially populated (25/29 names) via smith-book refresh; SNDK/DRAM
  unavailable from any source, ARM/IREN computed values exceeded the 0-3.5
  plausibility band and were discarded (G15 opened).
- Pre-market price overlay implemented: `get_us_stocks_details.ext_hr_live_price`
  used in place of stale snapshot prices whenever `market_session` is pre-open and
  current time is at/after 1:30pm IST (US pre-market open). Cross-validated against
  FMP's aftermarket quotes, agreement within cents (G3 per-name fix).

## 2026-07-18

- "Compute/Hyperscaler" cluster line added to policy.json (target 10%, band
  [5,15]) — cluster existed in `ai_capex_clusters` but had no target/band, leaving
  7.9%+ of the book untracked by drift analysis.
- A reported SNDK single-position breach (12.352%) was traced to a stale INDmoney
  per-position price; true weight was 10.482%, no breach (G14, folded into G3).
- Ticker-mislabeling incident: an inferred ticker pointed at the wrong instrument
  (MEM/DRAM confusion). Fixed by never inferring a ticker from a display name —
  resolve once, cache in `data_cache.ticker_map`, flag new resolutions for user
  verification.

## 2026-07-12/13 (bootstrap)

- First Agent Smith runs. `state.json`/`policy.json`/`ledger.csv`/`journal.json`
  schema established. Policy drafted from the initial book (`"confirmed": false`).

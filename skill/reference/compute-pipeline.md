# Compute pipeline, price sources and cache TTLs

> Moved verbatim out of SKILL.md on 2026-09-14 (core cut to <=60KB). Load this file only when the core step that cites it runs. Where this text and the core disagree, the core wins — it reflects the scripted flow (`preflight`, `smith_fetch.py`, `dispatch-plan`, `postflight`).

### 2. PREFETCH, TICKER RESOLUTION & COMPUTE — one pass for everyone (full sweeps only)
1. Make ONE networth_holdings(US_STOCK) call (INDmoney tool names vary — discover via ToolSearch). If it fails, report the failure plainly and stop — no elaborate fallback protocol. GUARD: an empty holdings list on a book that had holdings last run is a red flag, not a sell-out — surface it and stop rather than persisting a zeroed state.
1.5. SANITY GATE — **script-owned** (moved into `cmd_book` 2026-09-14). `compute_book.json`'s `persist_safe` is false, with each reason in `reconciliation.breaches`, when row weights don't sum to 100 ± 0.5, USD/INR is outside 70–120, the total book (equity + wallet) moved >15% since the last ledger row with no qty change to explain it, or rows and aggregate diverge >3% (G3). Read it; never recompute it. When false: say so, mark data_quality, analysis may proceed clearly labelled, and `commit-state` withholds the price keys by itself.
2. TICKER RESOLUTION (never infer a ticker from a holding's name): look up each holding's name in `state.json.data_cache.ticker_map` (name → ticker, long TTL). For any name not in the cache, resolve it properly — a real ticker-lookup tool or a yfinance symbol search, never a guessed abbreviation — cache the result, and add a one-line "new ticker auto-resolved: NAME → TICKER, verify" flag to this run's briefing. This is the control that prevents a repeat of the 2026-07-13 MEM/DRAM mislabeling incident (an inferred ticker silently pointed at the wrong instrument for a run).
2.5. PRE-MARKET PRICE OVERLAY — **script-owned (2026-09-14):** `smith_fetch.py`'s `live_quotes.json` already carries the newest pre/post-market price per ticker against the prior regular close. Pass it to `build-holdings`. Only for tickers in `no_live_quote`, or when `quotes` is in `fallback_needed`, use INDmoney `get_us_stocks_details` (`ext_hr_live_price`, batches of ≤10) or yfinance MCP `get_stock_price` — save the raw output and fold it in with `merge-prices`, never by hand.
3. Create the run directory `runs/<YYYY-MM-DD-HHMM>/`. **Write `holdings.json` via `smith_math.py build-holdings` — never by hand.** Added 2026-09-10 after a run where hand-writing this file in an inline Python snippet cost most of a sweep's wall-clock and produced two real defects the same day: `day_chg_pct` was left null on every row (the inline script never wired the field through), silently starving `compute_buckets.json`'s STRONG DOWNTREND/UPTREND classification until a user caught an unflagged -9.6% move; and two tickers absent from the live pull (real stop-outs) were guessed to be a snapshot glitch and silently carried forward at last-known qty — the IDENTICAL wrong guess an earlier run had already made for the identical tickers, because nothing forced a check. Call:

   `python3 scripts/smith_math.py build-holdings --base-dir . --run-dir runs/<ts> --snapshot-json <raw networth_holdings(US_STOCK) result, saved to a file> --live-quotes-json <flat {TICKER:price} or {TICKER:{price,changePct}} map, from step 2.5/2.5b's live fetch> --usdinr <> --wallet-usd <US_STOCK_WALLET current_value_usd> --macro-json runs/<ts>/market_inputs.json`, then `python3 scripts/smith_math.py session-gate --base-dir . --run-dir runs/<ts> --write-holdings` (computes `market_session` and GATE v2 and writes both into holdings.json)

   This mechanically builds every row (ticker/name/qty/price/weight_pct/pnl_pct), computes `day_chg_pct` from the live quote's `changePct` when one was fetched (never from INDmoney's own `one_day_change_percentage`, measured unreliable — see DECISIONS.md#G94), and writes `totals`/`live_quotes` in the exact shape `cmd_book` expects. **It never carries a ticker forward and never silently drops one**: any ticker present in state.json's prior holdings but absent from this snapshot is named in the output's `dropped_since_last_run` — resolve it via the LEDGER trigger (search confirmation emails) before treating it as anything, rather than guessing. Read the command's own docstring (`smith_math.py build-holdings --help` or the source) before extending it — the whole point is that this transformation happens in ONE place now, not once per run in the orchestrator's head.

   **3.5 LEDGER BEFORE COMPUTE (2026-09-14).** `build-holdings` emits `qty_changes` (and a `next_step` when it is non-empty). If it is non-empty, run the LEDGER pipeline (§3b) NOW — `ledger-parse` → `ledger-apply --write` — so `pipeline`'s `lots` and `book` stages see this run's fills instead of sizing against the previous trade record. Check `aggregate_source`: `rows (no independent aggregate)` means the G3 divergence check has nothing independent to compare against — pass `--aggregate-usd` if the snapshot lacked `asset_summary.total_value_usd`.
   **Also write a top-level `live_quotes` map — `{"TICKER": price_usd, ...}` — whenever this run fetched live per-name quotes at all** (added 2026-08-07, closes G32). Cost nothing extra: these are the prices you already pulled in step 2.5/2.5b. `smith_math.py book` uses them to arbitrate WHICH feed is stale when rows and aggregate disagree, emitting `reconciliation.live_arbitration` with a `verdict` (`rows_stale` / `aggregate_stale` / `both_agree_with_live` / `inconclusive` / `insufficient_coverage`) and a `trust` field naming the source to rebuild from. This replaces a judgement call that has direction risk in both directions — G3 was aggregate-lags-rows, the three 07-29/30 recurrences were rows-lag-aggregate, and defaulting to either is wrong half the time. Arbitration needs ≥90% row coverage or it declines to infer a direction, and a confident verdict still does NOT re-enable the persist: it tells you what to rebuild from, then you re-run.
4. Run the compute script for every subcommand and save each result into the run directory:
   - **PREFERRED — one call runs them all in dependency order:**
     `python3 scripts/smith_math.py pipeline --base-dir . --run-dir runs/<ts> --today <date> --lots lots.json`
     Added 2026-08-15. It runs indicators → freshness → lots → book → universe → risk → drift → journal → attribution → rotation → buckets → sentiment → derisk → triggers → ladder,
     asserts each stage's inputs exist BEFORE running it, checks each output is non-empty AFTER, and aborts naming the
     first broken stage. **Exit 0 is not treated as success if the payload is hollow** — that check exists because on
     2026-08-15 `rotation` ran before `risk` had succeeded, exited 0, wrote a file with ZERO tickers, and the only thing
     that noticed was a missing section in the published dashboard. A stage that ran but produced nothing is a failure
     wearing a green light. Exit code is 1 on any failure, so it is safe to gate on. **Degraded, not failed (2026-09-14):** `sentiment` (missing or partial `market_inputs.json`) and `lots` (rebuild did not reconcile) continue as `DEGRADED` and are listed in `degraded` — say so in data_quality. A failed stage's `error` carries the real reason; resume with `--from <stage>`.
     It deliberately does NOT run `score`/`stops` (they need prices you must fetch first), `proposals` (runs after the
     strategist appends), or `validate` (a policy check, not a per-run compute). Run those explicitly, below.
   - Individual stages, for debugging one in isolation:
   - `python3 scripts/smith_math.py book --run-dir runs/<ts> --lots lots.json` → `compute_book.json`
   - `python3 scripts/smith_math.py journal --run-dir runs/<ts>` → `compute_journal.json` (scores/locks every entry; publishes `bucket_hit_rates`, `bucket_hit_rates_7d`, `name_bucket_grades` from signals fired on/after `ENGINE_EPOCH` only, stamped `bucket_rates_epoch`; `legacy_entries_excluded` counts the rest)
   - `python3 scripts/smith_math.py attribution --run-dir runs/<ts>` → `compute_attribution.json`
   - `python3 scripts/smith_math.py drift --run-dir runs/<ts>` → `compute_drift.json`
   - `python3 scripts/smith_math.py sentiment --base-dir . --market-inputs runs/<ts>/market_inputs.json` → `compute_sentiment.json`
   - `python3 scripts/smith_math.py buckets --base-dir . --run-dir runs/<ts> --today <date>` → `compute_buckets.json` (runs inside `pipeline`). **Added 2026-09-06; it SUPERSEDES the `relative_strength_1m` carve-out in COMPUTE-FIRST above.** smith-signals was the fleet's largest agent — 144,878 tokens / 22 tool calls on the 2026-09-06 deep run, and it dispatches on EVERY sweep including quick — while most of what it returned was arithmetic over caches the script already owned: STRONG UPTREND is a day-move over ATR20, PEER LEADER is cached relative strength over cached dispersion, TARGET GAP is price against a cached analyst target. Measured cost is nearly FLAT across all twelve agents (75K–145K regardless of what any of them does), so arithmetic left inside an agent is arithmetic bought at LLM prices every run, forever. The carve-out predated that measurement. Buckets needing a 52-week range are reported as `deferred_pos_buckets` until `data_cache.wk52` exists — never guessed. Judgment legs carry a `?` suffix and remain the agent's to promote or drop.
   - `python3 scripts/smith_math.py triggers --base-dir . --run-dir runs/<ts> --today <date>` → `compute_triggers.json` (needs `compute_risk.json`, `compute_rotation.json`, `compute_drift.json` and `compute_book.json` in the run dir first — see §2.9d)
   - Any subcommand exiting non-zero: `pipeline` names the stage and its real `error`; note it in data_quality and leave that section `null`. Never have an agent compute it inline instead (COMPUTE-FIRST).

5. **RENDER THE AGENT EMBEDS — do not hand-assemble them** (added 2026-08-16, rebuilt the same day after measuring it):

   `python3 scripts/smith_math.py slices --base-dir . --run-dir runs/<ts> --mode <mode> --today <date> [--agents a,b,c]`

   **THE DATA FLOW, in order — this ordering is the efficiency, not an accident:**
   `market inputs + holdings` → `pipeline` (9 computes, writes compute_*.json) → **`slices`** → dispatch agents → merge tails → PERSIST → `compact`.
   Slices MUST run after the pipeline, because it hands agents *paths* to compute files and reports any that are missing in `problems`. Read that array before dispatching.

   **What it does and why.** v1 inlined everything and was measured: 11 slices, 469KB, **56.3% duplicated payload** — `thesis` copied into 4 agents at 27KB each, `open_flags` broadcast to all 10, and `compute_*.json` inlined into 5 agents *despite those files already sitting in the same directory*. v2 fixes three things:
   - **Refs, not copies.** Anything already on disk is handed over as a path in `read_these_files`. Agents read what they need, when they need it, and can read selectively instead of carrying 27KB to use one field of.
   - **Content-addressed shared payloads.** Any payload ≥2KB is materialised **once** into `runs/<ts>/shared/<name>.<hash>.json` and referenced. Dedup is by **content**, so two agents asking for the same data under different keys still get one file. A size rule rather than a hand-maintained list of "big keys", because such a list is one more thing that goes stale.
   - **Shared external snapshots.** Resources more than one agent reads — the HBM tracker is read by `thesis`, `catalyst` **and** `cycle` — are snapshotted once into `shared/`. This cuts three live reads to one **and removes a real correctness hazard: agents reading the same moving file at different moments can legitimately disagree, and then the desk holds two "facts".** The snapshot makes each run internally consistent by construction.

   **Result: 469KB → 134KB total (71% less), and the slices themselves are 92% smaller — while covering 14 agents instead of 11.**

   **SKIP WHAT CANNOT HAVE CHANGED (added 2026-08-16).** Each slice carries an `inputs_digest` fingerprinting its inline values *and the content of every referenced file*. `slices` compares against the previous run and returns `skip_candidates`: agents whose inputs are **byte-identical** and which reason only over files, so they cannot produce a new finding — reuse their prior output instead of dispatching. On the 2026-08-16 run, `book`, `scout` and `macro` were dispatched against data identical to the previous deep review at roughly 90K subagent tokens each; that is ~270K tokens for three restatements.

   Two categories are **never** listed as skippable, and the distinction is the whole safety of the mechanism:
   - **External readers** (`signals`, `thesis`, `watchlist`, `catalyst`, `scout`, `macro`, `earnings`, `cycle`, `quality`) — their real input is news and prices, which move even when state does not. An unchanged slice says nothing about the world.
   - **`strategist`** — its true inputs are the Stage-1 JSON tails, which arrive inline in its prompt and never touch its slice. Its digest can be identical while every analyst finding beneath it changed. **A digest that cannot see an input must never vote on skipping it.**

   So the saving is real but bounded: it applies to `book`, `ledger`, `tax` and `rebound`. Treat `skip_candidates` as a recommendation to verify, not an instruction — and if you skip an agent, say so in the briefing rather than letting its section silently vanish.

   You still choose WHICH agents to dispatch and write the prose framing; this guarantees the data half is complete, deduplicated and identical every run. Hand-assembly is what dropped `status:"active"` and `peak_total_book_usd` on 2026-08-16, each silently emptying a dashboard panel.


Every sub-agent receives the resolved holdings.json AND the relevant compute_*.json inline — none of them re-fetches the holdings list or redoes arithmetic the script already did.

### 2.5b. PRICE SOURCE — pick the cheap pipe (added 2026-07-28)
`get_us_stocks_details` costs **726 chars/symbol**; yfinance `get_stock_price` costs **232** for the same decision-relevant fields (price, prev_close, day high/low). That is a 3.1x tax, and on a 20-name book it is 14.2K vs 4.5K per pull.
- **market_session == pre-open** → `get_us_stocks_details`, batched ≤10, because only it carries `ext_hr_live_price`. This is the one case where the heavy call earns its cost.
- **intraday / post-close** → `get_stock_price`, all names in one call. Do NOT use the INDmoney per-name endpoint here; the extended-hours field is meaningless while the cash session is printing.
- **Never re-pull the same symbol within 20 minutes** unless the user asks for a fresh check or you are about to hand over an actionable stop level.

### 2.5c. PULL-ONCE PRINCIPLE — every shareable data class, not just prices (added 2026-09-01, closes a token-waste finding)
**The general rule, stated once so it doesn't have to be re-derived per data type: if two things dispatched in the same run could plausibly want the same external fact, fetch it once (upfront if the need is knowable before dispatch, or via a shared cache if not) and hand it to both — never let each discover its own need independently.** Four concrete applications exist today; add a fifth here rather than leaving a new instance of the same failure to be found the hard way again:

- **Prices — ticker union, fetch once.** Measured 2026-09-01: a single run made 4 separate batched price-fetch calls — market inputs (9 tickers), holdings (30), `score`'s probe-then-fetch (18, ~12 overlapping with holdings), `stops`' probe-then-fetch (57, ~25 overlapping with holdings) — with ~37 tickers re-fetched across calls a single upfront batch would have already covered. **Before making the first price-fetch call each run, build the full known ticker union**: the CORE 9 macro proxies (§1.5) + every current holding (from the fresh `networth_holdings` pull, before step 2's ticker resolution even finishes — you already have the display names) + `score`'s and `stops`' `needs_prices` lists, gettable cheaply by probing both with an empty `{}` file before fetching anything (the probe costs no price-fetch calls, only a script invocation). Fetch the union in as few batched `get_stock_price` calls as the tool allows, write it to `holdings.json`'s `live_quotes` map (§2.6's standing convention), and have `book`/`score`/`stops` read from that map first, falling back to a second targeted fetch only for a ticker genuinely absent from it.
- **Analyst targets — cache-check before fetch, cross-agent.** smith-signals fetches analyst targets for every holding as a free byproduct of a news call it makes anyway (efficient, keep as-is) and writes `data_cache.analyst_targets` (7-day TTL). smith-watchlist independently fetched its OWN target prices with no cache awareness — found 2026-09-01: a third or more of any watchlist slice is names that are ALSO current holdings (AVGO/NVDA/MU/ASML/TER/TSM/GEV/INTC/GOOG recur constantly), so smith-watchlist was re-fetching a target price smith-signals had already priced. Fixed: smith-watchlist.md now checks the embedded `data_cache.analyst_targets` cache first (same pattern as its existing `earnings_calendar` check) and only fetches for tickers missing or stale. This is a cross-RUN win, not same-run — Stage 1 dispatches in parallel, so watchlist sees the cache as it stood going INTO this run, not signals' fresh writes mid-run — but since signals refreshes analyst_targets every run, the cache is rarely more than a day stale for held names, so the saving is real on most runs.
- **Email/Gmail — one reconciliation pass.** Only the LEDGER pipeline (§3b) searches INDmoney confirmation emails; nothing else in the run does.
- **External snapshots (HBM tracker, etc.) — already solved, the working precedent.** `slices` (§2, step 5) snapshots any resource more than one agent reads (e.g. `/Users/yb/Claude/HBMTracker/consumer_view.json`, read by `thesis`, `catalyst` and `cycle`) once into `runs/<ts>/shared/`, so three agents reading the same moving file at different moments can't legitimately disagree — this cut three live reads to one AND removed a correctness hazard, not just a cost. Use this exact mechanism (`shared/<name>.<hash>.json`, content-addressed) for any future resource more than one Stage-1 agent needs.

None of these four change WHAT gets fetched, only how many times the same fact gets asked for. Before adding a new cross-agent data need anywhere in this pipeline, check whether it fits one of the four patterns above rather than inventing a fifth ad hoc approach.

### 2.6. PERSIST GATE (added 2026-07-28, closes G3)
`compute_book.json` now emits `reconciliation` and `persist_safe`. The script compares the row-level sum of holdings against the snapshot total and any `aggregate_value_inr` supplied, and sets `persist_safe: false` when either diverges >3%. **When `persist_safe` is false: do NOT write state.json and do NOT append a ledger row.** Report the divergence, run the analysis clearly labelled provisional, and stop. This replaces the manual STALENESS-GATE judgement call for the aggregate-vs-rows case; the live-quote crosscheck in HARD RULES still applies to per-name prices.

### 2.7. DATA-FETCH METHODS THAT WORK (added 2026-07-28)
- **Daily bars**: yfinance auto-aggregates to weekly for `period >= 3mo`, and enforces a **global row budget of ~69 rows shared across every symbol in the call** — it does NOT switch to weekly on symbol count, and it reports the shortfall explicitly per symbol in `_truncated: {total, returned}`. Measured 2026-09-06 at `period='1mo'` (23 trading days): 3 symbols → 23 rows each (69, complete) · 4 symbols → 17 each (68) · 10 symbols → 6 each (60). `max_rows` does not raise the budget (verified: max_rows=25 with 10 symbols still returned 6) — it is a per-symbol ceiling. So the safe batch is `floor(69 / rows_needed)`, which is **3 for a 1-month daily pull**, and ATR20 needs 21 bars so 3 is a real limit rather than folklore. **Assert on `_truncated` rather than trusting the symbol count**, so a changed period or row requirement fails loudly instead of silently returning short series.
- **Earnings dates**: use `get_earnings` and take the latest quarterly `reportedDate` + ~91 days; cross-check near-dated names against FMP's earnings-calendar range endpoint. yfinance's own earnings-calendar endpoint is unreliable (was G20). FMP's per-symbol `earnings-company` endpoint is plan-blocked.
- **Betas**: compute vs **SMH**, not SPX. The SPX beta was shown to be actively misleading (predicted +0.075% for a session that delivered -5.06%).

### 2.8. CACHE TTLs — do not refresh what has not moved (added 2026-07-28)
Measured 2026-07-28: a quick run was costing ~119KB of raw payload (~33k tokens), and **18 of 27 calls were avoidable**. The dominant waste was re-deriving slow-moving quantities.

**This table is the canonical TTL reference — every `data_cache.*` key with a global TTL lives here, cross-checked against `smith_core.FRESHNESS` (2026-09-01: brought back in sync after drifting; `analyst_targets`'s "refresh on" was wrong for weeks, see below).**

| cache | TTL | refresh on | owner |
|---|---|---|---|
| `atr20` | 7 days | every run, `indicators` stage from smith_fetch bars | script |
| `rsi14` | 7 days | every run, `indicators` stage from smith_fetch bars | script |
| `rel_strength_1m` | 7 days | every run, `indicators` stage from smith_fetch bars | script |
| `rel_strength_1m_peer` | 7 days | every run, `indicators` stage from smith_fetch bars | script |
| `ret_5d` | 3 days | every run, `indicators` stage from smith_fetch bars | script |
| `betas` | 30 days | every run, `indicators` stage (vs SMH, ≥60 daily returns) | script |
| `earnings_calendar` | 30 days | deep runs via smith_fetch; smith-earnings confirms | script + smith-earnings |
| `earnings_facts` | until the next reported quarter supersedes it | on print, any mode (EARNINGS/EARNINGS VERIFY triggers, §3) | smith-earnings |
| `ticker_map` | 365 days | new holding only | orchestrator |
| `wk52` | 7 days | every run, `indicators` stage from smith_fetch bars | script |
| `analyst_targets` | 7 days | **every run smith-signals dispatches, quick or deep** — free byproduct of a news call it makes anyway, corrected 2026-09-01 (this row previously said "deep run only", which was never true of the agent's actual behavior) | smith-signals |
| `etf_constituents` | 30 days | deep run only | smith-thesis |
| `sector_map` | 30 days | deep run only | smith-thesis |
| `quality_financials` (per ticker, no global TTL — see smith-quality.md task 0) | ~75 days, or sooner if `earnings_facts[ticker].reported_date` is fresher | smith-quality dispatch (monthly/on-demand) | smith-quality |
| `edgar_cache.json` — `ticker_cik` | 180 days | on `smith_edgar.py` invocation with `--base-dir` | (standalone file, not in state.json) |
| `edgar_cache.json` — `concepts` (per cik:tag) | 3 days | on `smith_edgar.py` invocation with `--base-dir` | (standalone file, not in state.json) |

**INDICATOR CACHES REFRESH EVERY RUN (2026-09-14).** `smith_fetch.py` pulls daily bars and the `indicators` pipeline stage recomputes ATR20/RSI14/relative strength/ret_5d/52w/betas on every sweep, quick included, so the old deep-only MANDATORY REFRESH is gone. If `bars` degraded and the fallback also failed, the caches stay as they were and `freshness` reports their age — never estimate them.

**COVERAGE COUNTS TOO, NOT JUST AGE.** `compute_triggers.json` now reports `rsi_coverage_pct` / `rel_coverage_pct` / `*_missing` against held names, and flags below `TRIGGER_CACHE_MIN_COVERAGE_PCT` (85%). A perfectly fresh cache that covers 77% of the book — the measured figure on 2026-08-30 — leaves eight held names structurally unable to trigger. Refresh the named missing tickers; a trigger cannot fire on a name its cache cannot see.

**On a QUICK run past the 10-day suppression floor, say so in the briefing header as a headline** — `Trigger layer: DARK (rsi14 18d old)` — never as a `data_quality` bullet at the end.

**Other caches** (analyst targets, quality financials, thesis, catalysts) keep their own TTLs above; quick runs read them as-is unless a trigger in §3b dispatches their owner.

**Budget:** lean quick run ≈ 4 calls / 26KB. Lean deep run ≈ 12 calls / 87KB. If a quick run exceeds ~8 calls, something is being re-derived that should have been cached.


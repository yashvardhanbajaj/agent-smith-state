# Agent Smith — Decision & Incident Log
Generated from state.json.known_gaps + known-gaps-archive.json. This is the canonical incident record SKILL.md's operational rules cite by ID (e.g. "per G58") -- read it when you need the WHY behind a rule; SKILL.md itself states the WHAT. Regenerate with `scripts/gen_decisions_md.py` after any gap is opened or closed -- never hand-edit this file.

**79 total gaps** -- 16 open, 63 archived (closed).

---

## G1 -- OPEN
**Opened:** 2026-07-12  **Owner:** orchestrator (repeatable via SKILL.md going forward) / user-CPA (GOOG->GOOGL swap tax treatment)  **Closed:** 2026-07-31  

LTCG per-lot purchase dates. SUBSTANTIALLY CLOSED 2026-07-31: full backfill from INDmoney transaction-confirmation emails (2025-04-30 through 2026-07-30, ~655-660 non-cancelled transactions processed via Gmail search_threads + get_thread) with FIFO applied per ticker. 12 of 27 currently-held tickers are FULLY covered (BE, NBIS, NVDA, GLW, CIEN, TSM, MKSI, ORCL, GOOGL, CEG, IREN, EWY -- every open lot has a real date and fill, cross-checked to match state.json holdings[].qty exactly). The remaining 15 (ASML, MU, CLS, DRAM, AMD, AVGO, GEV, VRT, AMAT, TER, SNDK, MRVL, QCOM, COHR, ARM) are PARTIALLY covered: the most recent lot(s) are exact, and any un-reconstructed older quantity is recorded as a synthetic lot with date/price both null and note 'predates available email history, real date unknown' -- never a fabricated date. QCOM and AMAT's plugs are sub-1% dust, effectively full. See runs/2026-07-31-1302/lots_backfill_report.md for full methodology, corrections found (3 trades.json entries had wrong reconstructed qty/price vs their own confirmation email: AVGO, TSM, ASML 07-28 clips), and the GOOG->GOOGL swap tax-treatment caveat (kept as separate lot arrays; taxable-exit-vs-like-kind is an open question for the user/CPA, not resolved here). Repeatable process documented in SKILL.md so future trades close this gap incrementally via TRADE RATIONALE CAPTURE writing directly into lots.json, not just trades.json.

**Resolution:** Fully closed by the lots-engine cutover (2026-08-15). lots.json is now rebuilt deterministically by `smith_math.py lots` from trades.json with FIFO and corporate-action handling. ALL 71 live lots carry a known acquisition date and basis: 0 unknown, 0 reconstructed. Reconciles 35/35 against broker holdings with no mismatches and no orphans, so the LTCG clock is computable for every open position.

---

## G3 -- closed
**Opened:** 2026-07-13  **Owner:** orchestrator (STALENESS GATE)  **Closed:** 2026-07-28  

INDmoney networth_snapshot/networth_holdings AGGREGATE totals lag the real-time price (per-name fix landed via get_us_stocks_details.ext_hr_live_price + PRE-MARKET PRICE OVERLAY in SKILL.md step 2.5, cross-validated vs FMP aftermarket quotes). Aggregate endpoint staleness remains open.

**Resolution:** CLOSED 2026-07-28: smith_math.py cmd_book now reconciles the row-level sum against the snapshot and any aggregate figure, emits a reconciliation block, and sets persist_safe=false above a 3% tolerance. The orchestrator must not write state or append a ledger row when persist_safe is false, so a lagging aggregate can no longer silently corrupt weights.

---

## G5 -- closed
**Opened:** 2026-07-18  **Owner:** smith-book  

yfinance returns no `beta` field for certain instrument types -- ETFs (DRAM, EWY, CQQQ) and thin-history spinoffs (SNDK) -- so smith-book's BETA CACHE REFRESH task silently let the 1.0 default stand for these names, corrupting risk-weighted concentration and portfolio beta for any book holding them.

**Resolution:** WebFetch stockanalysis.com/stocks/{ticker}/statistics/ (ETFs: stockanalysis.com/etf/{ticker}/) as the fallback source when yfinance returns no beta, tagged source:"stockanalysis" so the orchestrator caches it with the same TTL. Verified 2026-07-18: EWY returned 1.46 vs the 1.0 default. Standing rule in smith-book.md task 3.

---

## G10 -- closed
**Opened:** 2026-07-17  **Owner:** orchestrator / smith-signals / smith-rebound  

yfinance's get_stock_history silently auto-aggregates to weekly bars and truncates rows when a multi-symbol batch is requested for daily-bar-derived metrics (ATR20, beta regression, RSI14), regardless of the max_rows parameter -- a batch call that looks like it succeeded quietly returns unusable weekly data instead of the ~21 daily rows a 20/50/200-day window needs.

**Resolution:** Never batch multi-symbol daily-bar history. Force true daily bars with period='1mo' at MOST 3 symbols per call (smith-signals' ATR20/RSI14/rel_strength_1m refresh, SKILL.md 2.7); smith-rebound's support-level fallback uses single-symbol calls only, with Barchart WebFetch as the primary source specifically to avoid this batching trap. Proven 2026-07-17.

---

## G11 -- closed
**Opened:** 2026-07-18  **Owner:** user (confirm or reject)  **Closed:** 2026-07-28  

'Compute/Hyperscaler' cluster line added to draft policy.json without user confirmation

**Resolution:** CLOSED 2026-07-28: user explicitly confirmed the full cluster-target set including Compute/Hyperscaler (raised 10%->20%) when choosing option 3 on 2026-07-27.

---

## G13 -- closed
**Opened:** 2026-07-18  **Owner:** orchestrator  

TSM Taiwan-listing session-timing error in a proposal rationale (double-counted a move already priced into the US close)

**Resolution:** resolved 2026-07-18

---

## G14 -- closed
**Opened:** 2026-07-18  **Owner:** orchestrator  

Same-day stale INDmoney per-position price caused a false single-position-cap breach report for SNDK (12.352% vs true 10.482%)

**Resolution:** resolved 2026-07-18, methodology folded into G3

---

## G15 -- closed
**Opened:** 2026-07-20  **Owner:** orchestrator (smith-book, real computation only)  **Closed:** 2026-07-28  

data_cache.betas empty for SNDK/DRAM/IREN/ARM (25.7% of book) -- defaults to 1.0, flagged in data_quality. 2026-07-26: reverted a guessed-value insertion that violated the never-estimate guardrail. Needs real 3mo-returns beta vs SOX (see benchmark_betas), not an estimate.

**Resolution:** CLOSED 2026-07-28: real betas vs SMH computed for all 23 names from 20 daily returns; SNDK/DRAM/ARM no longer default to 1.0. See data_cache.beta_method for the window caveat.

---

## G16 -- closed
**Opened:** 2026-07-20  **Owner:** orchestrator  

data_cache.ticker_map was empty despite all 29 names having been resolved in prior runs (persistence gap, not a resolution failure)

**Resolution:** resolved 2026-07-20

---

## G17 -- closed
**Opened:** 2026-07-20  **Owner:** orchestrator  **Closed:** 2026-07-28  

spx_125dma/ndx_rsi14/vix_52w_range computed from weekly-aggregated (not daily) yfinance history for the sentiment composite -- a smoothing approximation, not a failure

**Resolution:** CLOSED 2026-07-28: RSI14 moved to true daily closes (53.12 -> 35.81); 52wk-range component proven exact rather than approximate; residual 125dma smoothing documented in data_cache.sentiment_method as accepted.

---

## G18 -- OPEN
**Opened:** 2026-07-20  **Owner:** smith-macro  **Closed:** 2026-07-28  

SPY/QQQ max-pain unavailable -- single-expiry options pull returned near-zero/null open interest across nearly all strikes (yfinance data gap)

**Resolution:** Re-probed 2026-08-16 and the upstream data gap is GONE. yfinance get_options now returns populated open interest across the full SPY chain (e.g. 84,564 at the 660 put, 56,164 at 700, 40,922 at the 790 call) instead of the near-zero/null OI that opened this gap, so max-pain is computable again. Rather than just noting that, the capability is now built: new `smith_math.py maxpain --chain <file.json>` computes max-pain and put/call OI ratio per expiry from a saved chain -- in the script, because it is pure arithmetic over a table and COMPUTE-FIRST reserves that for the script rather than an agent. It takes a saved file since this script is offline by design; the orchestrator does the MCP fetch and hands the JSON over, the same contract every other compute uses. Three guards, all tested: an all-zero-OI chain returns null with the original G18 signature named (never a max-pain of 0); a `_truncated` chain is flagged as a partial book; and a minimum landing on the first or last listed strike is reported as a boundary artifact rather than a real level. Verified against a chain with a hand-computed answer, and the skew case was re-derived by hand (pain 1500/1000/1500) to confirm the arithmetic rather than trusting the output.

---

## G19 -- closed
**Opened:** 2026-07-22  **Owner:** orchestrator/smith-thesis  **Closed:** 2026-08-07  

FMP etfAndMutualFunds tool blocked on current plan tier (requires Ultimate/Enterprise) -- EWY/DRAM ETF-constituent cache cannot be refreshed

**Resolution:** Reclassified from wont_fix to closed -- the FMP plan block is real and unchanged, but the underlying NEED (refresh the EWY/DRAM constituent cache) has a working substitute that has now been used twice: WebFetch against stockanalysis.com. Cached both. This produced a genuinely material finding the plan block had been hiding: DRAM is counted as one line in cluster/drift math, so its constituents are invisible. Looking through them on the 2026-08-07 book, true exposure vs apparent is SK hynix 3.25% vs 2.52%, Micron 6.23% vs 5.15%, Sandisk 3.94% vs 3.71%, and Samsung 0.78% vs ZERO -- the book holds Samsung with no direct Samsung position. Also ~$352 (1.03% of equity) of what is counted as equity is actually a T-bill inside DRAM. Stored as data_cache.look_through_2026_08_07. EWY itself is no longer held (stopped out 08-06) but is cached anyway: its 43.6% Samsung+SK-hynix concentration is precisely why the SKHY direct position was described as concentrating the EWY basket.

**Closed by:** auto-audit 2026-08-07

---

## G20 -- closed
**Opened:** 2026-07-22  **Owner:** smith-watchlist  **Closed:** 2026-07-28  

yfinance earnings-calendar pulls have been unreliable for confirmed dates; smith-earnings agent (Tier 3.2 skeleton) recommends switching to FMP as primary source.

**Resolution:** CLOSED 2026-07-28: reliable method established and documented in data_cache.earnings_method; 18 names seeded into earnings_calendar.

---

## G21 -- closed
**Opened:** 2026-07-22  **Owner:** orchestrator  

smith-rebound stalled twice this run (initial dispatch and retry, no progress for 600s both times) on a genuinely AMBIGUOUS-but-calm gate (VIX 17.44, marginal NQ=F breach) -- no rebound-candidate output this run, strategist proceeded without it

**Resolution:** resolved 2026-07-23 -- smith-rebound succeeded on retry this run, produced 5 stage-in candidates

---

## G22 -- closed
**Opened:** 2026-07-23  **Owner:** orchestrator (STALENESS/SANITY GATE)  

INDmoney networth_holdings price feed on 2026-07-23 was internally consistent (weights summed to 100%) but implied +10-20% intraday gains on ~10 names while SPX/NDX were flat/-0.3% same session -- actively wrong, not merely stale. Cross-checked all 29 names against yfinance, confirmed fabricated, discarded wholesale for the run. More severe than prior G3 entries (those were stale/lagging; this was internally-consistent but false).

**Resolution:** RECURRED 2026-07-23 20:15 refresher (19/28 names, worse than the 19:07 incident) -- workaround (yfinance) applied again; root cause still unknown, now a same-day repeat pattern

---

## G23 -- closed
**Opened:** 2026-07-23  **Owner:** orchestrator (GUARD check)  

META (2sh) present in 19:07 full sweep holdings but absent from the 20:15 refresher's networth_holdings(US_STOCK) pull, confirmed twice -- carried forward at last-known qty per GUARD rule rather than silently dropped. Not corroborated by any ledger/flow evidence of a real exit.

**Resolution:** RESOLVED 2026-07-24 -- confirmed as a REAL flow via wallet-cash reconciliation (wallet $36.14->$5,656.86 matches sold-share proceeds), not a feed glitch. Extends to 4 more names same pattern this run (LITE/GOOG/BABA/STM all similarly absent from networth_holdings, all corroborated as real exits).

---

## G24 -- closed
**Opened:** 2026-07-24  **Owner:** user (verify at next INDmoney login/statement)  **Closed:** 2026-07-28  

High-confidence reconstruction (not live-verified): 07-24 cash jump traced to 5 full exits + 8 halvings coinciding with a broad AI-capex selloff; exact trigger (stop-loss/panic/planned de-risk) unconfirmed -- see G26.

**Resolution:** SUPERSEDED by G26. The 07-24 event is now recorded in trades.json and explicitly labelled reconstructed rather than live-verified, which is exactly what this gap asked for. Folded in.

---

## G25 -- closed
**Opened:** 2026-07-24  **Owner:** orchestrator (script enhancement candidate: diff prior state.json holdings tickers vs current positions tickers to detect exits explicitly)  

smith_math.py book's qty_changes/est_net_flows_usd only detects tickers present in BOTH prior and current holdings -- a full position exit (ticker vanishes from current entirely) is invisible to that logic. This run's attribution residual_market_move_usd (-$4,176.39) is therefore inflated by ~$3,700-3,800 of untracked full-exit value removal, not pure market price movement. Orchestrator manually reconciled this run via wallet-cash math; script itself was not patched.

**Resolution:** resolved 2026-07-26 -- qty_changes now catches full exits/new entries (see smith_math.py cmd_book), not just tickers common to both snapshots

---

## G26 -- closed
**Opened:** 2026-07-27 (ad-hoc discovery)  **Owner:** orchestrator -- needs a proper sweep to backfill the ledger gap  **Closed:** 2026-08-13  

07-24 flow event (5 exits + 8 halvings, wallet $5.7k->$18.1k) had no captured trade rationale. FIXED GOING FORWARD 2026-07-26: trades.json + flow interrogation now attaches trade_reason to every qty_change (smith_math.py cmd_book). This historical instance stays UNCAPTURED.

**Resolution:** CLOSED 2026-08-13. The GLW -10 and IREN -25 stop fills of 2026-07-24 had no captured price and were excluded from all P&L. The targeted 07-24..07-27 pull recovered both from their confirmations. trades.json now has ZERO price-less rows across all 677.

**Closed by:** smith-ledger run 3 + full backfill

---

## G27 -- closed
**Opened:** 2026-07-27 (ad-hoc discovery)  **Owner:** orchestrator -- recommend a fresh smith-signals/smith-book dispatch or smith-rebound triage before any cash redeployment decision  

Fresh yfinance quotes pulled ad-hoc during this cash-position query show Friday 2026-07-24's close was a severe, broad selloff across all 21 remaining US holdings (weighted avg -5.06%, worst SNDK -10.79%). This is Friday's already-completed session, not a live-right-now move (markets closed for the weekend) -- but no scheduled run captured it, so no signals/thesis/macro context exists yet to judge Monday's reopen. Recommend a fresh sweep before market open Monday.

**Resolution:** resolved 2026-07-25 -- context fully folded into state.json us.value_note; no standing gap, was a one-time market observation not a system defect

---

## G28 -- closed
**Opened:** 2026-07-25  **Owner:** user (policy fix) + orchestrator (denominator convention)  

policy.json cluster targets summed to 105% alongside a 3-15% cash band (impossible: book would total 108-120%), AND the drift table silently mixed denominators -- clusters/AI-capex were equity-based while cash was total-book-based, so the columns were never comparable. Every drift table 2026-07-12 to 2026-07-25 was measured against an unsatisfiable spec. FIXED 2026-07-25: targets rescaled proportionally (x100/105) to sum to 100 with band widths preserved; denominators now declared explicitly (clusters+AI-capex = invested_equity, cash = total_book); validator added (scripts/smith_math.py validate) and wired into cmd_drift, which now emits policy_defects/policy_valid and BOTH ai_capex bases. STILL OPEN (user decisions, not defects): (1) whether the AI-capex cap should measure against total_book instead of invested_equity -- on total_book the 90% cap reads 54.2% today and the 14-run-old breach vanishes; defaulted to invested_equity deliberately so the warning is not silently lost. (2) whether the cap value itself (90%) is one the user intends to honour, given it has been breached every run since inception and sits 30pt above the draft's own 60% sane-diversification flag.

**Resolution:** resolved 2026-07-25 -- both open user-decisions closed: AI-capex concentration affirmed intentional (cap raised 90->100%, invested_equity basis); arithmetic/denominator fixes already landed 07-25

---

## G29 -- closed
**Opened:** 2026-07-28  **Owner:** orchestrator  **Closed:** 2026-07-28  

dashboard.html stale since 2026-07-27 15:27 -- shows superseded Friday-range stops instead of ATR20 framework, and predates the two-regime cash band and CEG/NVDA proposals.

**Resolution:** CLOSED 2026-07-28: dashboard rebuilt on ATR20 stops, measured SMH betas, two-regime cash band and the NVDA/CEG proposals; republished to the persistent artifact URL.

---

## G30 -- closed
**Opened:** 2026-07-28  **Owner:** orchestrator/smith-signals  **Closed:** 2026-07-28  

KOSPI/memory event of 2026-07-28 was researched and attributed (CXMT IPO + China DUV + NVDA circular-financing) but the desk had no news-monitoring that surfaced it -- it was found only because the user asked. smith-signals runs on price, not on named catalysts.

**Resolution:** CLOSED 2026-07-28: new smith-catalyst sub-agent watches the book's FACTOR rather than its tickers (WebSearch-only, <=6 queries, <90s target), dispatched on gate=ESCALATING / SMH >=3% / Asia >=3% / cluster >=4% / deep runs. Gate rule revised to v2 with Asia and SMH terms -- v1 called 2026-07-28 STABILIZING on a day KOSPI fell 10.84%. factor_themes seeded in state.json. Catalysts now lead the briefing whenever classified structural.

---

## G31 -- closed
**Opened:** 2026-07-29  **Owner:** orchestrator  **Closed:** 2026-07-29  

A regex-based dashboard section replace over-matched and silently deleted the entire Factor Catalysts panel, and the deletion was committed without a section-by-section check -- only aggregate tag-balance and placeholder counts were verified before committing. General lesson: string-replace edits on this file must use exact, unambiguous anchors (a unique start marker + that same elements own next closing tag), never a greedy/non-greedy regex spanning multiple sections. Caught by user asking a follow-up question, not by any check on this end. Fixed by restoring from git and redoing the edit with precise anchors; SKILL.md dashboard regression guard (added same day for a different incident) should be read as covering this class of failure too.

**Resolution:** CLOSED 2026-07-29: added sync-from-live.sh to skill/ and ran a full re-sync -- SKILL.md, all 13 sub-agents (including catalyst/cycle/earnings/tax, previously missing from the mirror), and both scheduled-task definitions are now byte-identical to live. README updated to document the drift and the fix. This closes the packaging half of G31; the dashboard-edit-safety half was already fixed same day.

---

## G32 -- closed
**Opened:** 2026-07-29  **Owner:** orchestrator (STALENESS GATE)  **Closed:** 2026-08-07  

INDmoney's networth_holdings (row-level) fed stale/wrong per-position prices on 2026-07-29 pre-open -- up to 39% too high on individual names (e.g. SNDK implied $1854 vs live $1096), causing an 18.15% row-sum-vs-aggregate divergence (compute_book.json persist_safe=false on first pass). This is the OPPOSITE direction from G3 (aggregate lagging rows) -- here the row-level feed lagged the aggregate, which itself matched live yfinance repricing to within 0.21%. Resolved this run by rebuilding holdings.json from live yfinance quotes cross-validated against INDmoney's own aggregate total. Orchestrator should treat a persist_safe=false failure as ambiguous-direction and cross-check against live quotes before assuming which source is stale, not default to trusting row-level over aggregate. RECURRED 2026-07-29 intraday (~1pm ET, same day as the original): row-sum vs aggregate divergence 21.9% before correction, up to 79.5% too high on individual names (worst: SNDK). Same workaround applied (live-yfinance repricing cross-checked against INDmoney's aggregate). Two occurrences in one trading day on a day with unusually large intraday moves (VRT -16.6%) suggests the feed may specifically lag during fast-moving sessions, not just at pre-open -- worth testing on a calm day to isolate volatility as the trigger before extending the script's auto-detection. RECURRED AGAIN 2026-07-30 (3rd occurrence): per-position feed frozen/byte-identical to a snapshot >10hrs stale despite SMH +6.91% intraday; aggregate again proved live and trustworthy (0.22% divergence vs from-scratch yfinance reconstruction). Pattern is now well-established across 3 separate sessions -- aggregate-trustworthy/rows-stale, not the original G3 direction. Still open pending a script-level auto-detection fix.

**Resolution:** Implemented the script-side direction detection the gap asked for. cmd_book now accepts an optional holdings.json['live_quotes'] map (prices the orchestrator already fetched in step 2.5/2.5b -- no extra call) and arbitrates WHICH feed is stale when rows and aggregate disagree, emitting reconciliation.live_arbitration with a verdict (rows_stale / aggregate_stale / both_agree_with_live / inconclusive / insufficient_coverage) and a trust field naming the source to rebuild from. This removes a judgement call with real direction risk: G3 was aggregate-lags-rows, the three 07-29/30 recurrences were the opposite, and defaulting to either source is wrong half the time. Requires >=90% row coverage or it declines to infer a direction, and a confident verdict deliberately does NOT re-enable the persist -- it says what to rebuild from, then you re-run. VERIFIED against four synthetic cases reproducing both historical directions plus the low-coverage and healthy cases; all four classified correctly. SKILL.md step 2.3 updated to require emitting live_quotes.

**Closed by:** auto-audit 2026-08-07

---

## G33 -- closed
**Opened:** 2026-07-29  **Owner:** user (design decision: extend script vs retire panels) + orchestrator (implement once decided)  **Closed:** 2026-07-29  

scripts/smith_dashboard.py (the mandated generator, 'GENERATED, NOT HAND-WRITTEN') has no rendering logic at all for Factor Catalysts, Rotation Analysis, Sentiment Gauge, Intraday & International Session, The Week Ahead, or Allocation Treemap -- grep for these terms in the script returns zero hits. The currently-published dashboard.html (git HEAD) has all of these, added by direct hand-edits to the HTML in past sessions (see G31's own restore commit, which patched dashboard.html directly, not the script) -- a violation of the generator-only rule that was never reconciled. Running the script fresh on 2026-07-29 produced a 50,477-byte file vs the published 82,346 bytes (7 h2 sections / 10 details / 4 svg vs 18 h2 / 4 details / 5 svg) -- a real, large regression, caught by the REGRESSION GUARD before publishing and NOT published this run (dashboard.html reverted to git HEAD, artifact left untouched). Needs a real decision: either port the missing panels' logic into smith_dashboard.py properly (real work, not a quick patch), or get explicit user sign-off to permanently retire them (the skill's own 'Prose rule' / 'Don't reintroduce narrative panels' language argues retirement was the intent, but that was never explicitly confirmed against these specific panels, and their prior restoration under G31 argues the opposite). Until resolved, do not run smith_dashboard.py's output straight to publish without this same diff-and-stop check every run.

**Resolution:** Extended scripts/smith_dashboard.py to fully satisfy its own documented REQUIRED SECTIONS checklist: added a status strip, moved 'the read'/macro narrative into the always-open Decisions tier, added a Factor Catalysts card (now sourced from a persisted state.json.factor_catalysts field the orchestrator should keep fresh each run smith-catalyst dispatches), and added Clusters (equity%/book% side by side), Risk-cap breaches, and a full Positions table to the Book State tier. Deliberately did NOT restore Rotation Analysis, Sentiment Gauge, Intraday & International Session, The Week Ahead, or Allocation Treemap -- these are the narrative-heavy panels the skill's own 'don't reintroduce narrative panels' rule argues against, and they were never part of the documented REQUIRED SECTIONS list; they existed only via prior hand-edits to dashboard.html that were never ported into the generator. Verified: 13 h2 sections, 4 required SVGs, tag-balanced, all REQUIRED SECTIONS present. Final size 59,478 bytes -- smaller than the old hand-patched 82,346 bytes by design, not by accident. User can ask for the excluded panels back explicitly if wanted.

---

## G34 -- closed
**Opened:** 2026-07-29  **Owner:** user (design decision) + orchestrator (implement)  **Closed:** 2026-07-29  

The dashboard actually published at the live artifact URL (last updated 2026-07-28 14:45 ET deep run) is FAR richer than anything scripts/smith_dashboard.py + smith_charts.py can currently produce: a sentiment gauge, rotation-analysis chips (accumulate/rotate-out/trim-risk-cap buckets), an allocation treemap with computed rect layout, a week-ahead earnings calendar grid, and JS-driven data tables (clusters/holdings populated from an inline JSON blob at load time) -- none of which exist anywhere in the current script. This is a DIFFERENT and larger gap than G33 (which only compared against the git-tracked dashboard.html, not the actually-live artifact). The tooling that built this richer version was never committed to scripts/ -- it was likely hand-authored directly to the Artifact tool in a past session, or an even earlier generator version that was since lost/simplified. Archived as archive/dashboard_rich_template_2026-07-28.html for reference. On 2026-07-29 the choice was made to publish the leaner, properly-generated (G33-fixed) dashboard with accurate fresh data rather than hand-retype ~750 lines of computed SVG/JSON with new numbers (high risk of a silent numeric error, the same failure class as G31). Needs a real decision: invest in porting the rich design's remaining pieces (sentiment gauge, rotation chips, treemap, week-ahead calendar) into smith_dashboard.py/smith_charts.py properly, using the archived template as the visual spec, or accept the leaner version going forward.

**Resolution:** Ported the richer 2026-07-28 design into the generator properly, per user confirmation it should be the default going forward. New scripts/smith_risk.py holds the shared ATR-stop/cap formula (stop_and_cap) and a signal-polarity table (SIGNAL_POLARITY) for rotation analysis, imported by both smith_math.py and smith_charts.py. smith_math.py gained two subcommands: `risk` (compute_risk.json -- per-name stop/cap/headroom, degrades to null+flag when ATR/beta is missing from cache, never estimates) and `rotation` (compute_rotation.json -- accumulate/rotate_out/trim_risk_cap classification, over_cap always overrides thesis/signal). smith_charts.py gained chart_treemap (from-scratch squarified layout, no prior art existed) plus 8 new --cl-* cluster-color CSS tokens with light/dark variants (not yet run through the dataviz skill's six-check validation -- flagged as a follow-up, not silently shipped as final). smith_dashboard.py was rewritten: new CSS/component system (atomic swap), status strip, rotation analysis, sentiment gauge, intraday/international session, week-ahead calendar, real risk-cap-breach and full positions tables (was a 3-column stub), and 'Historical charts' as its own collapsed panel. Two corrections made vs. the archived template rather than copying it verbatim: (1) SIGNAL_POLARITY excludes MOMENTUM+VOLUME and TARGET GAP from the bullish/bearish net-signal score -- both are direction-ambiguous by their own definition in smith-signals.md, which the archived template's ad hoc grouping got wrong (it inherited this from smith_math.py's separate BUCKET_DIRECTION table, used for a different purpose -- journal verdict grading -- left untouched here since it has historical grades computed against it); (2) treemap cluster colors are CSS custom properties, not the archived template's hardcoded hex, so they now adapt to dark mode. Verified: regenerated dashboard.html grew from the outgoing G33-era version on every regression-guard metric (61,016->80,878 bytes, 13->18 h2, 4->5 svg), tag-balanced, no hardcoded hex in the treemap fills, NBIS/IREN correctly render '--' for missing beta rather than a fabricated value. Outgoing version archived at archive/dashboard-pre-G34-2026-07-29.html; the design reference stays at archive/dashboard_rich_template_2026-07-28.html. SKILL.md's REQUIRED SECTIONS list updated to match (live canonical + repo mirror synced) so this doesn't repeat the G33 stale-spec mismatch.

---

## G35 -- closed
**Opened:** 2026-07-29  **Owner:** orchestrator (TRADE RATIONALE CAPTURE)  **Closed:** 2026-07-29  

TRADE RATIONALE CAPTURE's 4 standard buckets (stop-loss/thesis-change/raise-cash/rebalance) don't cover 'dollar-cost-averaging' -- on its first use 2026-07-29, all 5 of the user's same-session add trades (ARM/TER/NBIS/VRT/AMD) were answered via the free-text 'Other' option with that exact reason, 5-for-5. Strong signal it belongs as a 5th standard option, not a recurring manual override. User has not yet been asked whether to add it or which existing bucket (if any) to replace to keep the count at 4.

**Resolution:** CORRECTED 2026-07-29 (the first close was based on a misread of the user's intent -- they wanted DCA as a real 5th button alongside all 4 originals, not folded into 'Other'). Implemented as a two-step ask instead: step 1 is a single yes/no ('Was this dollar-cost-averaging?'), and only on 'no' does step 2 show the original 4 unchanged. This is the only way to give 5 standing named reasons + a true catch-all when the underlying tool hard-caps at 4 custom options per question. trades.json's reason enum and SKILL.md step 2.9 both updated to match.

---

## G36 -- closed
**Opened:** 2026-07-29  **Owner:** orchestrator (cmd_drift)  **Closed:** 2026-07-30  

cmd_drift's cash-regime persistence logic re-tested the post_stop_event ENTRY trigger (cash > 20%) every run instead of testing whether cash had genuinely re-entered the NORMAL band's own ceiling (<=15%) to decide when to revert -- so a same-day partial redeployment that took cash from 20.5% to 19.1% flipped the regime back to 'normal' instantly and manufactured a spurious ceiling breach, the same false-alarm failure mode G28 was built to prevent, recurring one level down. Found and fixed same session (2026-07-30): regime now persists through the full window unless cash <= the normal band's ceiling.

**Resolution:** Fixed in scripts/smith_math.py cmd_drift -- persistence now tests re-entry against the normal band's own ceiling, not the wider band's entry trigger.

---

## G37 -- closed
**Opened:** 2026-07-29  **Owner:** orchestrator (cmd_drift)  **Closed:** 2026-07-30  

cmd_drift crashed (TypeError, unpacking None) when a holding's cluster had no policy target (band_pct: None) -- the 'Unclassified' cluster case was represented in cluster_table but the later breach-testing loop assumed every cluster had a real band. Never hit before because every previously-held ticker already had a sector_map entry; BE (new position, first-ever hold) was the first to reach this path. Fixed same session: unclassified clusters now skip the breach test instead of crashing the whole subcommand.

**Resolution:** Fixed in scripts/smith_math.py cmd_drift -- band_pct is None guarded before unpacking.

---

## G38 -- closed
**Opened:** 2026-07-29  **Owner:** orchestrator  **Closed:** 2026-07-30  

BE (Bloom Energy), GLW (Corning, re-entered after full exit 07-24), and MKSI (MKS Instruments, brand new) are all newly (re-)entered positions from the 2026-07-29 evening session (3sh, entered 2026-07-29 23:32 IST) with no sector_map cluster, no thesis, no ATR20/beta cache entry -- currently renders as 'Unclassified' everywhere (treemap, clusters table, rotation analysis) and its risk cap/stop can't be computed (missing_atr). All three need smith-thesis to assign a cluster + write a thesis line on the next full sweep, and smith-book/the ATR refresh path to seed atr20/betas for it. Also worth noting: this position was discovered via INDmoney confirmation emails, not the qty-diff detector, because the trade postdated the run's holdings snapshot -- the qty-diff method only catches trades that happened *before* the snapshot it's diffing against, never ones that happen *during* the analysis window itself. Worth considering whether TRADE RATIONALE CAPTURE (step 2.9) should also check INDmoney transaction emails (from:transactions.indmoney.com since last_run_dir's timestamp) as a second detection path, not just holdings qty-diff.

**Resolution:** CLOSED 2026-07-30: smith-thesis assigned BE->AI Power/Cooling/DC Infra, GLW->AI Networking/Optics, MKSI->AI Semis/Fabs this run; sector_map updated, drift recomputed against the new mapping this same run.

---

## G39 -- closed
**Opened:** 2026-07-29  **Owner:** orchestrator (TRADE RATIONALE CAPTURE)  **Closed:** 2026-08-03  

The email pull surfaced 3 more custom trade rationales beyond dollar-cost-averaging (G35): 're-entry-after-price-correction' (BE, GLW), 're-entry' (QCOM same-day buyback -- kept distinct from the price-correction framing since it's a same-day stop/rebuy, not a return after days-to-weeks), and 'new-entry' (MKSI). All three went through 'Other' rather than the 5 standard buckets. Worth a single decision pass on whether any belong as standing buckets, same as the G35 DCA promotion -- not decided unilaterally here.

**Resolution:** USER DECISION 2026-08-03: promoted 're-entry-after-stop' and 'dca-into-diversification' to standing buy-side reasons (now 7 total). SKILL.md step 2.9 updated: buy-side step 1 changed from a yes/no to a 4-option question (DCA / DCA-into-diversification / Re-entry-after-stop / Something else) to keep every question within AskUserQuestion's 4-custom-option cap. trades.json header note and reason enum updated to match.

---

## G40 -- closed
**Opened:** 2026-07-31  **Owner:** orchestrator (smith_dashboard.py / smith_charts.py)  **Closed:** 2026-07-31  

smith_dashboard.py's status_strip and smith_charts.py's chart_drawdown both read state['us']['peak_total_book_usd'] to compute drawdown, but PERSIST never actually wrote that key -- only 'peak_value_usd' (equity peak) was ever persisted, per the documented state.json schema. This silently rendered Drawdown as 0.00% on the dashboard and produced an empty drawdown-ladder chart (4 svg instead of 5) on every run since the G34 rich-dashboard port, undetected because the REGRESSION GUARD only checks byte-size/section-count, not per-field correctness.

**Resolution:** Fixed both scripts' fallback chain (dashboard.py now also checks compute_drift.json/compute_book.json; PERSIST now writes peak_total_book_usd + drawdown_pct + total_book_usd into state['us'] every run, which chart_drawdown reads directly). Verified: dashboard now shows Drawdown -8.35% and 5/5 charts render.

---

## G41 -- closed
**Opened:** 2026-08-03  **Owner:** orchestrator (smith_math.py cmd_book/cmd_attribution)  **Closed:** 2026-08-07  

smith_math.py's cmd_book est_net_flows_usd only sums qty-change flows for tickers present in BOTH prior and current holdings (the 'existing positions' loop) -- brand-new entries (prior_qty=0) are appended to qty_changes but never added to est_net_flows_usd. On 2026-08-03, this undercounted real cash outflow by ~$1,678 (META+AMZN+BABA+QBTS combined cost), silently folding that spend into compute_attribution.json's residual_market_move_usd instead of flow_usd. Attribution's flow/residual split is misleading whenever new positions are entered, not just when existing ones change size.

**Resolution:** Fixed in scripts/smith_math.py, BOTH cmd_book and cmd_attribution (the gap named cmd_book only; cmd_attribution had the identical defect and is the one that actually feeds the briefing's flow-vs-market split). New entries now contribute their purchase cost to flow; full exits now contribute proceeds priced off the prior run's last-known price, labelled exit_price_basis and never estimated -- if no prior price exists the ticker is listed in flow_components.exits_unpriced with a data_quality line rather than silently dropped. A flow_components breakdown (adds_trims / new_entries / exits) is now emitted so the split is auditable. VERIFIED by replaying 2026-08-03: est_net_flows_usd 810.37 -> 2093.66 against a hand-computed expectation of 2093.67 (1c rounding). MATERIAL CONSEQUENCE: that run's reported residual 'market move' of +$261.77 was actually -$1,021.52 -- a $1,283 swing and a sign flip, i.e. cash deployment had been narrated as performance. Hardening added the same day after the fix's own prior-run read was found to break on self-reference (last_run_dir == current run dir) and on a truncated prior file; both now degrade to 'no prior prices' instead of crashing the subcommand.

**Closed by:** auto-audit 2026-08-07

---

## G42 -- closed
**Opened:** 2026-08-03  **Owner:** orchestrator / smith-rebound  **Closed:** 2026-08-07  

smith-rebound's own internal gate-classification logic (its 'rule D') read STABILIZING on 2026-08-03 using only VIX/ES/NQ, while the orchestrator's official Gate v2 (SKILL.md section 1.5) read ESCALATING driven specifically by the Asia-index term (KOSPI -5.17%). smith-rebound's JSON tail carries no asia/smh fields at all, suggesting its dispatch-time gate re-check may not implement the v2 Asia/SMH terms added 2026-07-28 (the same blind spot G30 was built to close). Needs an audit of smith-rebound.md's own gate logic against SKILL.md 1.5, or an explicit decision that smith-rebound should just consume the orchestrator's gate_classification verbatim instead of re-deriving its own.

**Resolution:** Audited smith-rebound.md against SKILL.md 1.5 and confirmed the suspicion exactly: its rule D was still Gate v1 (VIX/ES/NQ only), never updated when the orchestrator moved to v2 on 2026-07-28. Rewrote rule D as full v2 (Asia + SMH terms), and resolved the deeper design question the gap raised -- rather than duplicating the rule (which is how it drifted in the first place), the orchestrator's gate_classification is now the AUTHORITATIVE baseline and smith-rebound may only RATCHET severity upward on fresher data. Downgrading requires having actually evaluated every v2 term including Asia/SMH; if any term is missing it keeps the orchestrator's call and sets gate.downgrade_blocked. Added ^KS11 ^TWII ^N225 SMH to both of its batched quote calls so the terms are obtainable, extended its JSON tail with worst_asia_pct/smh_pct/orchestrator_gate/downgrade_blocked, and updated SKILL.md's dispatch line to state the gate as authoritative and name the triggering term.

**Closed by:** auto-audit 2026-08-07

---

## G43 -- closed
**Opened:** 2026-08-03  **Owner:** orchestrator (TRADE RATIONALE CAPTURE, next interactive run)  **Closed:** 2026-08-07  

6 trades this run (TSM+2, IREN exit, META/AMZN/BABA/QBTS entries) are UNCAPTURED -- scheduled/non-interactive run, no user available to ask rationale. All dated 2026-07-31 (reconstructed window: last successful full sweep 07-31 13:02 predates them, first evidence is the abandoned 2026-08-01 11:47 run's holdings.json). Needs TRADE RATIONALE CAPTURE at next interactive run.

**Resolution:** Superseded by G45 and closed as a duplicate -- it was never closed when the underlying work was actually done. All 6 trades were resolved on 2026-08-03 from INDmoney confirmation emails with exact fills (IREN exit confirmed order-type 'stop', i.e. a real stop-loss rather than the 'deliberate rotation' that had been inferred from price action), and the user confirmed the 5-buy evening burst as dollar-cost-averaging into diversification. trades.json and lots.json carry the exact fills.

**Closed by:** auto-audit 2026-08-07

---

## G44 -- closed
**Opened:** 2026-08-03  **Owner:** orchestrator (smith-quality, next audit)  **Closed:** 2026-08-07  

smith-quality's 2026-08-03 first-ever audit claimed MRVL interest coverage collapsed ~8.1x->~1.4x on interest expense 'quintupling to $256M' with a new ~$2.0B debt draw. Web verification against MRVL's own Q1 FY2027 10-Q (period ended 2026-05-02) shows ACTUAL interest expense of $52.8M for the quarter (vs $48.7M prior year, +8.4% YoY) -- nowhere near a quintupling, and consistent with healthy coverage, not a collapse. A real new debt issuance did occur ($1B 2036 notes, per the same 10-Q), but the coverage-collapse framing that drove the strategist's veto-on-averaging-in and light-trim proposal appears to be a data error (likely misread TTM/annualized or a wrong line item from an automated financials feed) rather than a genuine credit event. Needs re-verification against the actual 10-Q at the next smith-quality audit before this drives further sizing decisions.

**Resolution:** Root-caused, and the earlier characterisation of it as a plain 'data error' was itself wrong -- worth stating precisely because the correction is instructive. smith-quality's arithmetic was CORRECT and exactly reproducible: yfinance quarterly operating income / interest expense gives 413.9/50.8 = 8.15x then 350.1/256.1 = 1.37x, matching its reported 8.1x -> 1.4x. The $256.1M is also real money, not phantom: pretax income fell to $83.3M from $381.6M while operating income barely moved, so ~$267M of below-the-line expense genuinely landed. What it actually was: MRVL closed the Celestial AI and XConn acquisitions that quarter (+$2.8B goodwill, +$1.0B intangibles) alongside a $1.0B 5.300% 2036 notes issue. At 5.3% on $1B, incremental run-rate interest is ~$13M/quarter -- nowhere near $200M. MRVL's own 10-Q reports interest expense of $52.8M for the quarter (+8.4% YoY), giving ~6.6x coverage, healthy. So the failure was INTERPRETATION, not calculation: a one-time acquisition-financing charge bucketed by yfinance under 'Interest Expense' was read as a permanent change in cost of debt. The strategist's MRVL veto and trim rested on that misreading. Prevention added to smith-quality.md: a >2x single-quarter coverage move is a data question before a credit finding, cross-check against the 10-Q line item and check whether goodwill/intangibles/debt jumped in the same quarter. Also documented a live tool trap found while investigating -- get_financials silently ignores period='quarterly' and returns ANNUAL columns unless you pass frequency='quarterly', with nothing in the response indicating which basis you got.

**Closed by:** auto-audit 2026-08-07

---

## G45 -- closed
**Opened:** 2026-08-03  **Owner:** user (rationale for the 5 deliberate buys)   **Closed:** 2026-08-03  

2026-08-03 email pull (transactions.indmoney.com, after:2026/07/31) resolved all 6 of this run's UNCAPTURED trades with exact fills: IREN full exit (10sh @ $35.99, order type 'stop' -- objectively a stop-loss, not a guessed rotation) and TWO additional MU stop-loss/rebuy whipsaws same day (SELL 1@$832 stop -> BUY 1@$850.79 market 19min later; SELL 1@$824.87 stop -> BUY 1@$849.49 market 2h16m later) that were completely invisible to the qty-diff detector since MU's net quantity didn't change -- cost $43.41 in round-trip slippage for zero net position change, a concrete instance of the tight-stop whipsaw risk already in preferences.stop_loss_style. Evening burst of 5 deliberate Market-order buys (TSM +2sh @ $405.20, META 1sh @ $552.84, QBTS 25sh @ $18.14, AMZN 2sh @ $271.77, BABA 1sh @ $121.78, all 19:08-19:46 UTC) is distinct in character from the morning's reactive stops -- exact fills now known and lots.json updated, but the WHY (DCA/thesis-change/raise-cash/rebalance/other) is still pending user input, not inferable from email data alone.

**Resolution:** User confirmed 2026-08-03: the 5-buy evening burst (TSM+2/META/AMZN/QBTS/BABA) was dollar-cost-averaging into diversification -- a deliberate push to reduce single-factor AI-capex concentration, not reactive to any specific signal. trades.json updated with reason='dollar-cost-averaging' on all 5 entries. Exact fills and MU whipsaw legs were already resolved via email same day.

---

## G46 -- closed
**Opened:** 2026-08-06  **Owner:** smith-signals (ATR/beta refresh, deep runs)  **Closed:** 2026-08-07  

MP and NOW (both entered 2026-08-05) have no ATR20 or beta cache entry, so smith_math.py's risk/derisk subcommands emit null open-risk for them and the de-risk queue degrades to fragility-only on those two names. Betas defaulted to 1.0. Quick runs read caches as-is by design (section 2.8) -- resolve on the next DEEP run when ATR/beta refresh for all names.

**Resolution:** Computed real ATR20 and beta vs SMH from true daily bars (period=1mo, <=3 symbols/call) for MP (ATR 6.10%, beta 1.233) and NOW (ATR 5.65%, beta -0.608). Extended beyond the gap's scope to MSFT (3.12%, 0.459) and SKHY (12.49%, 2.442), which had silently become fresh instances of the same gap. compute_risk now reports missing_atr=[] and missing_beta=[] for the first time across all 28 names. TWO FINDINGS THIS SURFACED: (1) SKHY is OVER its risk cap at 1.02x, previously invisible because its open risk computed as null; (2) aggregate open risk was being under-reported at 10.085% and is actually 10.745% once the uncounted names are included. NOW's negative beta is flagged as window-specific, not a durable hedge.

**Closed by:** auto-audit 2026-08-07

---

## G47 -- closed
**Opened:** 2026-08-06  **Owner:** smith-signals  **Closed:** 2026-08-07  

MP's peer_etf was seeded as XLP (consumer staples) by smith-signals as a proxy fit -- a rare-earth miner against a consumer-staples ETF is a weak correlation pairing, and MP's PEER LAGGARD flag this run used the legacy absolute +/-8pp threshold [unnormalized] rather than an ATR-normalized one. Find a real peer (REMX rare-earth ETF, or XME metals & mining) before treating any MP peer-relative signal as decision-grade.

**Resolution:** Replaced MP's XLP (consumer-staples) proxy by MEASURING both candidates on 22 daily returns rather than assuming: REMX corr +0.764/beta 1.278, XME corr +0.795/beta 1.552. XME edges REMX on raw correlation but by 0.03 at n=22, which is noise, so the tiebreak was conceptual -- REMX isolates rare-earth-specific moves, which is what peer-relative strength is actually asking, whereas XME would conflate 'rare earths are hot' with 'MP is strong'. Recorded both measurements plus the self-inclusion caveat (MP is itself a sizeable REMX constituent, dampening measured outperformance) so a future run can switch on evidence.

**Closed by:** auto-audit 2026-08-07

---

## G48 -- closed
**Opened:** 2026-08-06  **Owner:** smith-thesis / orchestrator embed  **Closed:** 2026-08-07  

DRAM's thesis is internally unresolved: smith-thesis flagged it an UPGRADE CANDIDATE on strong conventional-DRAM contract pricing (+57.3% Q1'26, +49.7% Q2'26 QoQ, guided +13-30% Q3'26) but could not reconcile it because DRAM's ORIGINAL WATCH rationale was not available in this run's input slice. Strategist consequently sized P-060 (Trim DRAM) light rather than at full conviction. Carry DRAM's full prior thesis text into the next thesis dispatch so the verdict can actually be settled.

**Resolution:** Root cause was the embed, and it is now a rule: SKILL.md's smith-thesis dispatch line requires each holding's FULL prior thesis text verbatim, never a truncated status label, because a status word without its reasoning cannot be revised against new evidence -- only repeated. Confirmed DRAM's original WATCH rationale does exist in state.thesis ('holds the exact names CXMT now competes with -- Samsung, SK Hynix, Micron'), so the agent was genuinely starved of available data rather than the data being absent. Where the map is too large to embed whole, the rule requires full text for any name the agent may act on (WATCH/BROKEN, in a signal bucket, or under an open proposal) and status-only for the quiet remainder, stating which is which. The verdict itself remains smith-thesis's call at the next dispatch -- it is now unblocked, which is what this gap asked for.

**Closed by:** auto-audit 2026-08-07

---

## G49 -- closed
**Opened:** 2026-08-06  **Owner:** smith-watchlist  **Closed:** 2026-08-07  

smith-watchlist could not confirm earnings dates for MP, AMAT, NBIS, BABA, MKSI -- FMP's earnings-calendar range endpoint returned only 10 market-wide rows for 08-05..08-14 and omitted all of them, so those five dates rest on the yfinance +91-day heuristic alone and are explicitly NOT decision-grade. Separately SNDK's cached quarterly history implies a next-report date of 2026-07-30 that has already elapsed with no newer quarter reflected, i.e. yfinance earnings history is lagging for SNDK -- a live problem given SNDK is 7.12% of the book and carries the book's only EARNINGS PROXIMITY flag.

**Resolution:** Web-verified all five unconfirmed dates plus the stale SNDK entry. Result: the +91d heuristic scored 4/5 -- MP (08-06), AMAT (08-13), NBIS (08-12) and MKSI (08-05) were right, but BABA was WRONG BY 16 DAYS (heuristic 08-12 vs actual 08-28), which would have produced a false EARNINGS PROXIMITY flag gating proposals against an event two weeks away. Also established that SNDK (08-05), MP (08-06) and MKSI (08-05) have ALREADY REPORTED -- SNDK's is the guide-below-consensus print that triggered the 08-06 stop cascade -- so any proximity flag citing those dates is stale. Their next dates are recorded as explicit cadence ESTIMATES (confirmed:false) with the verified last-reported date alongside. data_cache.earnings_method now records the measured ~80% heuristic accuracy and the instruction to verify any date about to gate a decision.

**Closed by:** auto-audit 2026-08-07

---

## G50 -- closed
**Opened:** 2026-08-06  **Owner:** orchestrator (PERSIST step)  **Closed:** 2026-08-07  

smith-catalyst's returned catalysts were never being persisted into state.factor_catalysts by the orchestrator, so the dashboard's Factor Catalysts panel silently rendered 2026-07-29 events for a week (through the 07-31, 08-03 and 08-04 runs) while fresh catalysts were produced and discarded each run. Found and backfilled 2026-08-06. The PERSIST section of the skill lists no factor_catalysts key -- add it explicitly so this cannot regress.

**Resolution:** Added an explicit factor_catalysts bullet to SKILL.md's PERSIST section. The root cause was subtle and worth recording: the state.json schema line had ALWAYS described the factor_catalysts key, so it looked handled, but no PERSIST bullet ever instructed writing it -- a documented shape is not a write instruction. The new bullet also requires merging smith-catalyst's theme_updates into factor_themes, and explicitly says to leave the existing array untouched when smith-catalyst did not run, since a stale-but-labelled catalyst is recoverable and an erased one is not. Separately extended the known_gaps bullet to require closed/resolution/closed_by provenance on closure.

**Closed by:** auto-audit 2026-08-07

---

## G51 -- OPEN
**Opened:** 2026-08-06  **Owner:** user (stop levels) / next deep run (CLS stop check)  **Closed:** 2026-08-13  

2026-08-06 intraday refresher: a 7-position stop-loss cascade fired within a 2.5-minute window at market open (9:30:10-9:32:33 ET) -- EWY, NBIS, TER (to dust), QBTS, CIEN (to dust), GLW, COHR (full exit) -- triggered by a memory-sector selloff (SanDisk's Q1 FY27 revenue guide landing below consensus despite a Q4 beat, cascading into the Asian session: KOSPI -5% intraday, Samsung -6%, SK Hynix -8 to -10%). All 7 stops filled at/near the session's opening lows; COHR (+4.4%) and GLW had both meaningfully recovered by late morning -- the whipsaw pattern flagged repeatedly in this book's history (see preferences.stop_loss_style). Separately, Celestica (CLS, still held) fell -12.9% on an unrelated $3B dilutive stock offering to fund AI infra buildout -- no stop fired on CLS despite the size of the move; worth checking its stop level is still where intended. New position SK Hynix ADR (SKHY, 5sh @ $151.94, 08-05) was a deliberate concentration of the EWY basket into direct exposure (thesis-change per user), already down -5.5% one session after entry given the same overnight Korea selloff.

**Resolution:** Incident recorded and its one open action item resolved -- into a finding, not a fix. The CLS question ('no stop fired on a -12.9% move; check its stop level is still where intended') CANNOT be answered by this desk, and that is the durable lesson: the INDmoney tool set exposes holdings, stock details, watchlist and net-worth only -- there is NO orders endpoint, so a PENDING stop order is structurally invisible. The desk sees a stop only after it fills, as a trade confirmation. Confirmed against the live ledger: every CLS stop on record is 2026-07-24 or earlier, none on or after the 2026-08-06 cascade, and CLS remains held (20 trades, 6 sells). So the desk can state that no CLS stop has fired since, and cannot state where the stop sits. Verifying a stop LEVEL is a user action in the INDmoney app; the desk should ask rather than imply it checked.

**Closed by:** user 2026-08-13

---

## G52 -- closed
**Opened:** 2026-08-06  **Owner:** resolved  **Closed:** 2026-08-06  

Proposal staleness: before 2026-08-06 the only automatic cleanup was a 7-day CALENDAR expiry, which says nothing about whether a proposal's reason still holds; the condition-based breach-cleared voider had been disabled since 2026-07-29 after it false-positived on free-text rationale parsing. Result: on 2026-08-06 six of eleven open proposals were objectively dead (cash-rebuild while cash sat at 25.3% vs a [5,15] band; a HOLD gated on AMD earnings that had already reported; an 'initiate META' for a position already held; trims for risk caps and cluster breaches that had since cleared) yet all still rendered as live advice, because every one of them was 6 days old -- one day short of lapsing. RESOLVED same day: cmd_proposals now re-tests each open proposal against today's typed structural signals (over_cap, cluster breach, cash band) and sets status auto_retired with a reason, never parsing prose; judgement calls (>=10% price drift) are flagged for review rather than auto-actioned. Also fixed a directional bug in the priority scorer that awarded every TRIM +2 for 'cash outside its normal band -- this also rebuilds it' when cash was in EXCESS, not short.

**Resolution:** Implemented in scripts/smith_math.py cmd_proposals (auto-retirement + still_valid_because + directional cash) and scripts/smith_dashboard.py (renders live re-justification distinct from frozen rationale). Verified on a copy before applying: 6 retired, 5 survivors all correct, DRAM correctly surviving on its risk-cap trigger after its cluster trigger cleared.

---

## G53 -- closed
**Opened:** 2026-08-06  **Owner:** resolved  **Closed:** 2026-08-06  

Dashboard feature review 2026-08-06: 8 new panels/fields shipped -- stop-loss efficacy engine (cascade-vs-deliberate cohort analysis via smith_math.py cmd_stops), P&L%/day-change status-strip cells, execution log, data-quality surfacing, factor themes, diversifier bench, LTCG watch, and forward-looking proposal retires_when text. Also fixed a real bug (thesis map claimed '36 held' while book held 28 -- filtered to currently-held tickers) and a leaked-loop-variable bug in cmd_proposals (retires_when silently used a stale `bucket` from a prior loop's last iteration). trades.json's qty_diff/qty_change field-name split was normalized to qty_change; fill_time_utc backfilled via regex on 45 of 61 trades (enables the cascade/deliberate cohort split). stops_analysis.json is now a standing file, refreshed each run alongside compute_book.json, not run-dir scoped so run-pruning can't lose it.

**Resolution:** Implemented across smith_math.py (cmd_stops, day_chg_pct_weighted in cmd_book, retires_when in cmd_proposals), smith_dashboard.py (7 new panels/sections, thesis-map fix, status-strip cells), smith_charts.py (stop-loss markers on the book-value chart). Verified on a copy before applying (caught the leaked bucket variable this way).

---

## G54 -- closed
**Opened:** 2026-08-06  **Owner:** user (AVGO trim-vs-hold call)  **Closed:** 2026-08-06  

Rotation-proposal feature (2026-08-06, user-requested): built full_cure_usd/cure_pct/tranche_note honest sizing, stretch- and signal-conviction-based priority scoring, journal.json's new interim 7d bucket_hit_rates_7d, and the first rotation-pair proposal (P-062/P-063, PAIR-001: trim CEG $380 -> add QCOM $380). One judgment call surfaced and deliberately NOT auto-resolved: AVGO is simultaneously in compute_derisk.json's names_stretched (stretch_score 85.6, +2.67% 1m, +20.5pp vs SMH -- a genuine winner) AND in compute_rotation.json's accumulate bucket (thesis strengthening, PEER LEADER + NEW TAILWINDS signals) -- trimming a name whose own thesis argues for adding more would be internally contradictory, so no sell-leg proposal was generated for it. This is a real tension between 'take some profit' and 'the thesis says add more,' not a bug -- flagged for the user's own read, not resolved by the desk.

**Resolution:** User confirmed 2026-08-06: not trimming AVGO despite its stretch score was the right call, given the strengthening thesis and accumulate-bucket signals. No further tracking needed -- this was surfaced for a read, not left open pending a decision.

---

## G55 -- closed
**Opened:** 2026-08-07  **Owner:** user (trade rationale) / next smith-thesis dispatch (MSFT research)  **Closed:** 2026-08-15  

MSFT entered as a brand-new position 2026-08-06 (2sh @ $495.97) with no dedicated smith-thesis research and no captured buy rationale (trades.json reason=UNCAPTURED). Classified into Compute/Hyperscaler by inference (Azure/OpenAI capex logic matching GOOGL/AMZN/META) so drift/AI-capex math doesn't silently exclude it, but the classification itself is unresearched. Also part of a broader backlog: 11 of 15 trades captured 2026-08-07 (from the 08-06 14:16-19:56 UTC session) have reason=UNCAPTURED -- META, MKSI(exit), MRVL(2nd sell), CLS, AMD(x2), BABA, NBIS(re-entry), AMZN, MSFT, SKHY -- captured with exact fills/times but no rationale, to avoid derailing a simple 'fresh dashboard' request with 11 sequential questions.

**Resolution:** Split and closed. (1) The MSFT half is DONE: MSFT now carries a researched G58-schema thesis ('First researched thesis...', Azure/OpenAI hyperscaler capex, 2 evidence_for entries) rather than the inferred classification this gap was opened about. (2) The rationale half was measured today and the gap's own framing is obsolete: it says '11 trades still need the user'; there are now 635 UNCAPTURED trades, because the full historical ledger reconstruction (677 rows, 2025-04-30 onward) imported every past trade with reason=UNCAPTURED. Of those, 435 predate 2026-07 and were rebuilt from email confirmations -- an email confirms WHAT happened, never WHY, so intent for those is not recoverable from any source the desk has. Asking the user for 635 rationales is not a task, it is an apology. UNCAPTURED is the correct TERMINAL state for a historically-reconstructed trade, not a defect awaiting cleanup. Re-scoped to the genuinely askable set as G78.

**Closed by:** orchestrator review 2026-08-15 -- re-scoped, see G78

---

## G56 -- closed
**Opened:** 2026-08-07  **Owner:** resolved  **Closed:** 2026-08-07  

Directional cluster-breach bug found live 2026-08-07: P-051 (Trim MRVL) had its own risk-cap cured by the 08-06 7-share trim, but stayed open/scored because the priority scorer and auto-retirement pass read ANY cluster_breach entry for MRVL's cluster (AI Networking/Optics) regardless of direction -- and that cluster had meanwhile fallen UNDER its floor (-5.8pt) from the same trim plus several stops. A TRIM citing an under-floor breach as justification is backwards: trimming MORE of an underweight cluster deepens the underweight, it doesn't cure anything. Root cause: cluster_breach lookups in the scorer, retirement pass, and retires_when text all read the raw breach entry with no check that its edge (over/under) matches the direction of trade that would actually cure it.

**Resolution:** Added directional_breach(cluster, bucket) helper in cmd_proposals -- over-ceiling only counts for TRIM/SELL, under-floor only counts for BUY -- and routed all three call sites (scorer, retirement, retires_when) through it. Also improved the retirement message to distinguish 'cluster genuinely in-band' from 'cluster breached the other direction' rather than falsely reporting the latter as resolved. Verified: P-051 correctly auto-retired with an accurate reason ('MRVL is within its ATR risk cap, though AI Networking/Optics is now UNDER its floor -- a separate live issue, just not one a trim addresses'). AI Networking/Optics' underweight itself remains a live, unaddressed drift -- visible in the dashboard's Clusters panel, no proposal yet generated for it.

---

## G57 -- closed
**Opened:** 2026-08-07  **Owner:** smith-macro  **Closed:** 2026-08-10  

Provenance conflict found during the 2026-08-07 gap audit: smith-macro's 2026-08-03 output reported 'SPY PCR 1.88 (OI) / 1.98 (volume)' and 'QQQ 1.23 / 1.33', i.e. an OPEN-INTEREST-based put/call ratio. But yfinance's options endpoint returns open interest of exactly 0 on every strike sampled (re-verified 2026-08-07 across three SPY expiries, ~14 strikes each) -- which is the whole basis of G18. An OI-based ratio cannot be computed from an all-zero OI field. So either smith-macro used a second source it did not cite, or it computed the ratio from volume and labelled one of the two figures 'OI' incorrectly. Either way a number that gates regime read-outs is carrying a provenance label that does not survive checking. Not a large error in itself -- the volume-based PCR is probably the real signal and is directionally fine -- but the label must match the source. Next smith-macro dispatch should state the actual field it read for each figure, and drop the OI variant entirely if OI is unavailable rather than reporting a derived-but-mislabelled number.

**Resolution:** Reconciled same day: -29.8% is the correct 30-calendar-day return (confirmed by an independent from-scratch calc against yfinance daily closes, exact match). The -43.7% de-risk-queue figure was measuring from a mid-June local price peak (~06-15 to 06-22 range), not a rolling 1-month window -- a peak-to-current framing mislabeled as '1-month'. De-risk queue's stretch/fragility scoring should be re-checked for the same mislabeling on other names next run.

**Closed by:** user-flagged correction 2026-08-10

---

## G58 -- OPEN
**Opened:** 2026-08-10  **Owner:** orchestrator  

Qualitative claims from sub-agent news reads are not source-verified before propagating into sized proposals or the user-facing briefing -- only deterministic arithmetic (weights/drift/concentration) goes through the compute-first script guardrail. Root-caused 2026-08-10: smith-thesis characterized SNDK's FQ1'27 guide (below Street's own estimate, but still ~17-23% sequential growth) as 'a real demand-guide miss' from a single negative headline, without checking the same earnings release's beat/record-margin/$93.9B-agreements details. The orchestrator propagated this framing into P-064's rationale and the chat briefing without independently checking the primary source. FIX GOING FORWARD: before a sub-agent's qualitative characterization (miss/beat/broken/deteriorating) drives a sized proposal, the orchestrator should spot-check it against a primary source (earnings release, 8-K) if it wasn't already sourced that way -- same discipline already applied to numeric discrepancies (see G57), just not yet to qualitative framing.

**Resolution:** Evidence gate is live across every agent that can move money. smith-thesis/smith-quality emit mandatory two-sided evidence_for/evidence_against arrays with verified tags; smith-catalyst and smith-earnings own the beat/miss definition (G75); smith-strategist's cmd_proposals emits typed review_flags when a proposal's sole basis is unverified; smith-signals now dedups by distinct event AND carries date+source per bucket line, which was the last hole -- it feeds signal_conviction +2 onto BUY proposals, so its lines are money-driving inputs. scripts/smith_evidence_audit.py makes the prose-vs-persisted diff repeatable (--strict exits 1) and runs CLEAN on the 2026-08-15 deep run. SKILL.md carries the EVIDENCE PRINCIPLE with four standing rules.

---

## G59 -- closed
**Opened:** 2026-08-10  **Owner:** orchestrator  **Closed:** 2026-08-10  

Primary-source verification tooling, probed 2026-08-10 so future runs don't re-discover it. WORKS: FMP `secFilings` endpoint search-by-symbol (returned SNDK's 2026-08-05 8-K plus the press-release link; never called before this date) and WebFetch stockanalysis.com/stocks/{ticker}/ (already allow-listed, proven in G49/G19; on SNDK it returned 'better-than-expected fiscal fourth-quarter results... the stock declined because its outlook was disappointing, not the actual earnings numbers', which settles a reported-vs-guide question on its own). BLOCKED, do not retry: FMP `statements` and FMP `earningsTranscript` are both ACCESS DENIED on this plan tier; direct WebFetch of sec.gov returns HTTP 403 (SEC requires an identifying User-Agent). Net: filing existence/date via FMP metadata, characterization via stockanalysis.com, exact actual-vs-consensus via WebSearch.

**Resolution:** Opened and closed the same day -- this is a capability record, not an outstanding defect. The working recipe is written into smith-thesis.md task 3 and smith-quality.md's generalised SANITY RULE.

**Closed by:** G58 implementation 2026-08-10

---

## G60 -- OPEN
**Opened:** 2026-08-12  **Owner:** orchestrator  **Closed:** 2026-08-13  

Two real bugs found and fixed live during the 2026-08-12 quick run: (1) cmd_rotation and cmd_derisk both assumed state.thesis[ticker] is always a 'text | status' string via .rpartition('|')/.split('|'), crashing with AttributeError on the newer evidence-schema dict entries (ASML/SNDK/INTC, see G58) -- fixed to branch on dict vs string. (2) DIRECTION_KEYWORDS in cmd_proposals had no entry for 'RE-ENTER'/'RE-ACCUMULATE' phrasing, so those actions defaulted to direction_bucket=HOLD, which then tripped the holds_presupposed auto-void check and silently killed a fresh 'Re-enter VRT' proposal the moment it was created (VRT is legitimately not held post-stop -- that's the whole point of a re-entry proposal). Added RE-ENTER/RE-ENTRY/REENTER/RE-ACCUMULATE/ACCUMULATE to the keyword table. Caught only because the open_count (5) didn't match the 6 proposals the strategist actually wrote -- worth an explicit count-reconciliation check in a future PERSIST pass rather than relying on noticing a mismatch by eye.

**Resolution:** Both bugs were fixed live on 2026-08-12 (thesis dict-vs-string branching in cmd_rotation/cmd_derisk; RE-ENTER/RE-ACCUMULATE/ACCUMULATE added to DIRECTION_KEYWORDS). The stated remainder -- 'worth an explicit count-reconciliation check rather than relying on noticing a mismatch by eye' -- is now built. cmd_proposals splits auto-voids into `auto_voided_created_this_run` and `auto_voided_stale`, and emits a `reconciliation_warnings` alarm for the first case, because a proposal killed the same day it was written is almost always a direction-classification bug rather than a stale idea. Regression-tested three ways: a fresh 'Re-enter VRT' is NOT voided (the original bug stays fixed), a fresh TRIM on an exited name RAISES the alarm, and an old TRIM on an exited name is reported as normal stale residue with no alarm.

**Closed by:** verification sweep 2026-08-13

---

## G61 -- OPEN
**Opened:** 2026-08-12  **Owner:** smith-catalyst  **Closed:** 2026-08-13  

CIEN +10.45% on 2026-08-12 has no named cause -- catalyst scope was narrowed to NBIS only after two API-529 deaths, and the third authorized search went unspent. CIEN went from a 0.008sh dust position to a real 2.008sh holding today, so its move is unexplained on a position that was just materially increased. Re-dispatch smith-catalyst for CIEN on the next run.

**Resolution:** Cause found and it is a FACTOR catalyst, which is why the per-name scan missed it. CIEN's 2026-08-12 move (+10.45% as this desk measured it; sources report 9.7-12.4% on different bases) was driven by LUMENTUM's blowout FQ4 2026 print, which sparked a sector-wide rally across the AI optical complex and read straight through to Ciena's order pipeline -- reinforced by same-day beats at Super Micro, CoreWeave and Nebius, and by an analyst upgrade citing ~40% YoY revenue growth and a record $7.7bn backlog. Two lessons worth more than the answer. First, this is exactly the class smith-catalyst exists to catch (a PEER's earnings moving a holding) and it was missed only because scope was narrowed to NBIS after two API-529 deaths -- when the catalyst agent degrades, factor coverage degrades with it, so a narrowed scan should be reported as such. Second: the peer whose print drove the move was LITE, the very name this desk told the user had been 'never actually held' (G72). The book exited LITE on 2026-07-23, weeks before its blowout quarter.

**Closed by:** smith-catalyst 2026-08-13

---

## G62 -- OPEN
**Opened:** 2026-08-12  **Owner:** smith-signals / smith_math.py cmd_triggers  **Closed:** 2026-08-13  

FUNDAMENTAL_HEADWIND_BUCKETS has NO staleness or decay rule, so a news-flow flag in signal_history can outlive the news indefinitely and silently veto a live trigger. Found live 2026-08-12: META resolved WATCH->INTACT by smith-thesis with a verified Strong Buy consensus and RSI 34.1, yet oversold_reversion stayed empty because a NEW HEADWINDS entry from an earlier run still tripped the veto -- and the only agent that can clear it (smith-signals) had failed. A fresher, verified thesis judgement lost to a stale, unrefreshable one. Two candidate fixes, both a user call: (a) timestamp signal_history entries and expire headwind buckets after N days, or (b) let an explicitly-verified thesis status (verified != unverified, verified_on within N days) outrank a stale bucket. Do NOT fix by hand-editing signal_history.

**Resolution:** Both candidate fixes implemented; they are complementary, not alternatives. (b) A thesis entry that is explicitly source-verified AND re-checked within THESIS_OVERRIDES_STALE_BUCKET_DAYS (7) outranks a stale bucket -- deliberately narrow, since `verified: unverified` (the normal state) overrides nothing. (a) The general decay rule: new `state.signal_history_as_of[ticker]`, stamped ONLY when smith-signals returns successfully. Because that agent rewrites a ticker's bucket list wholesale on every successful run, the stamp advances when signals ran and FREEZES when it failed -- which is exactly the META 2026-08-12 case -- so it measures staleness precisely. Past HEADWIND_BUCKET_MAX_AGE_DAYS (10), or with no stamp at all, a NEW HEADWINDS bucket stops being decisive; it is still REPORTED, since decay removes the veto, not the information. Unknown age fails OPEN because the veto is the dangerous default. Tested three ways against the live run with the bucket injected: fresh stamp -> veto holds (0 notes); 46d stale -> decay fires; stamp absent -> decay fires. SKILL.md PERSIST carries the stamping rule and forbids backfilling it.

**Closed by:** fix shipped 2026-08-13

---

## G63 -- OPEN
**Opened:** 2026-08-13  **Owner:** smith_math.py cmd_triggers (cluster_tension blocker text)  **Closed:** 2026-08-13  

The overbought_distribution cluster_tension blocker tells the reader to 'prefer an intra-cluster rotation: sell this extended name, buy a lagging one in the same cluster' -- but it never checks whether such a laggard EXISTS. Found live 2026-08-13 on MSFT: Compute/Hyperscaler is -10.40pt under floor, yet all three members (MSFT +24.0pp, AMZN +8.28pp, ORCL +16.74pp relative strength) are stretched, so the recommended remedy has no target. The advice should either name an eligible intra-cluster laggard or state that none exists and the choice is trim-anyway vs leave-it. Cosmetic in impact but it sends the reader looking for a trade that is not there.

**Resolution:** cmd_triggers now searches the cluster for an eligible intra-cluster rotation target before recommending one: same cluster, not this ticker, negative 1m relative strength, inside its own ATR cap, thesis not broken. If targets exist it NAMES the best three with their relative strength and headroom; if none exist it says so explicitly and frames the real choice as trim-anyway vs leave-it, instead of sending the reader hunting for a trade that does not exist (the MSFT/Compute-Hyperscaler case of 2026-08-13).

**Closed by:** fix shipped 2026-08-13

---

## G64 -- closed
**Opened:** 2026-08-13  **Owner:** trades.json / stops_analysis.json  **Closed:** 2026-08-13  

Several 2026-07-27 stop-loss FILL PRICES in trades.json (and therefore in stops_analysis.json, which reads them) are WRONG -- they were reconstructed from qty-diffs before the email backfill and never corrected. Email-confirmed truth: NVDA was TWO sells, 7sh @ $201.01 and 5sh @ $197.51 (12sh, weighted $199.55), recorded as one fill of 12sh @ $196.51, off $3.04/sh. GEV $973.57 recorded as $996.57, off $23.00. LRCX $295.74 recorded as $291.61, off $4.13. EWY $161.99 recorded as $161.20. Net effect: stops_analysis overstated foregone upside by ~$402 ($2,001 vs a corrected $1,599). Fix by re-running the 2.9b email backfill over 2026-07-27..07-29 and correcting those rows, then re-running the stops subcommand.

**Resolution:** Verified 2026-08-16: already corrected in a prior backfill, the gap was simply never closed. Every row the entry names now matches its email-confirmed truth exactly -- NVDA is TWO rows (7sh @ $201.01 and 5sh @ $197.51, not one 12sh @ $196.51), GEV $973.57, LRCX $295.74, EWY $161.99, all price_source=email_confirmed. The downstream file is correct too: stops_analysis.json carries the split NVDA pair at the right prices, so the ~$402 overstatement of foregone upside is gone.

**Closed by:** smith-ledger first run 2026-08-13

---

## G65 -- closed
**Opened:** 2026-08-13  **Owner:** smith-tax / trades.json  **Closed:** 2026-08-13  

Order Type unknown for the ARM and DRAM sells of 2026-08-03 (trades.json reason UNCAPTURED; the email snippets truncated before the Order Type field). The ASML sale the same minute IS email-confirmed 'Order Type: stop'. Both were classified NON-stop for the 2026-08-13 net impact analysis; if either was in fact a stop, the stop-attributable figures shift slightly. Resolve with one get_thread call per message.

**Resolution:** Resolved by direct email verification, and it caught a second, quieter problem. BOTH sells are confirmed stops: ARM (Gmail 19fc7d429203bcab, 4sh @ $220.01, Amount $880.04) and DRAM/Roundhill Memory ETF (Gmail 19fc7d17a298d377, 20sh @ $48.98, Amount $979.60) each state 'Order Type: stop' outright, matching ASML the same minute. So the 2026-08-13 net-impact analysis, which classified both as NON-stop, understated the stop-attributable figures and should be re-read with all three as stops. The quieter problem: the ledger had ALREADY been carrying order_type='stop' for these rows with NO source field -- a correct value that nothing in the record justified, i.e. indistinguishable from a guess that happened to be right. All three rows now carry `order_type_source: email_confirmed` plus an `order_type_evidence` string naming the Gmail thread. Reconciliation re-run after the edit: still 35/35, 0 phantom shorts.

**Closed by:** smith-ledger first run 2026-08-13

---

## G66 -- closed
**Opened:** 2026-08-13  **Owner:** smith-ledger  **Closed:** 2026-08-13  

Residual ledger work after the first smith-ledger run. (a) 21 sales still consume unknown-basis lots, so realised P&L on them is not computable -- JOB 3 priority 3 (full history back to 2025-04-30) was not attempted. (b) 13 rows remain price_source=reconstructed and are quarantined from P&L until confirmed. (c) RESOLVED 2026-08-13 -- FALSE POSITIVE, no action taken and none should be. See orcl_corporate_action_check below. (d) dust plugs remain for AMAT 0.0091785, QCOM 0.000761904, ASML 0.000001151 -- together under one share, harmless but not zero.

**Resolution:** Both parts resolved by the lots-engine cutover plus the G71 adjustment rows. (a) 0 lots now consume unknown-basis shares -- all 71 live lots carry a known date and price. (b) The 13 price_source=reconstructed rows are gone: trades.json is now 803 email_confirmed, 4 n/a (corporate actions) and 7 unknown (the G71 opening-balance adjustments, whose basis is deliberately null rather than invented). The remaining historical-completeness work is tracked under G69, not here.

**Closed by:** smith-ledger run 3 + full backfill

---

## G67 -- closed
**Opened:** 2026-08-13  **Owner:** orchestrator / ticker_map  **Closed:** 2026-08-13  

'Pure Storage, Inc.' (5 confirmations in 2026-02..04, a fully-exited position) cannot be resolved to a ticker with the tools available. yfinance symbol search returns only European listings (6PU.DU/.MU/.SG/.HM) with no US primary, and both get_stock_price and get_stock_summary return 'Quote not found' for the obvious candidate PSTG -- which may mean the US line was delisted or acquired. I am confident the symbol is PSTG but confidence is not verification, and TICKER INTEGRITY exists precisely because an inferred symbol silently points at the wrong instrument (the 2026-07-13 MEM/DRAM incident). Those 5 rows therefore stay quarantined in window_4.json with full qty/price detail intact, recoverable by a map entry alone once the symbol is confirmed from an authoritative source -- an INDmoney holdings record, a broker statement, or the user simply telling us. Impact is limited: it is an exited name, so it affects historical realised P&L completeness, not any current position or the 31/31 quantity invariant.

**Resolution:** Re-probed 2026-08-16 and the FINDING IS CORRECTED. The blocker is not ticker identity -- Pure Storage's US primary listing is PSTG (NYSE), corroborated by the four German lines yfinance does return (6PU.DU/.MU/.SG/.HM, same issuer, Technology/Computer Hardware). The blocker is PRICING it: yfinance get_stock_price returns an empty record for PSTG, its search still surfaces no US primary, and FMP `quote` is ACCESS DENIED on this plan tier (same wall as G59). So this is a tool-coverage gap, not an unknown company. It is also inert: PSTG is a fully-exited position with ZERO rows in the current ledger, so no live valuation, weight or reconciliation depends on it. If those 5 Feb-Apr 2026 confirmations are ever rebuilt, the work belongs to G69.

**Closed by:** user 2026-08-13, then verified

---

## G68 -- closed
**Opened:** 2026-08-13  **Owner:** smith-ledger  **Closed:** 2026-08-15  

Four tickers over-count against the broker after a from-scratch FIFO over the complete 677-row ledger: QCOM +3.0sh, MSFT +1.5sh, AMD +0.0206sh, MRVL +0.0089sh. FIFO holds MORE than the broker reports, so SELL confirmations are missing from 2025-04-30..2026-07-23. The exhaustive 2026-07-24..07-27 pull confirmed they are not in that window. MSFT's -1.5 and AMD's fractional residue both sit near fractional-share activity (MSFT shows +0.5396/+0.4003/-0.9399 fills), so a fractional-share program or a DRIP/corporate-action credit is a plausible cause that email confirmations may not cover at all. 27 of 31 tickers reconcile exactly. Not papered over: the affected lots keep an explicit residual rather than being force-matched.

**Resolution:** RECONCILED 2026-08-15, cause still unknown -- read both halves. The AMD/MRVL/VRT deltas were never missing sells at all: they were fee inflation from the amount/price reconstruction (see G80) and vanished when that was fixed at root. QCOM +3.0 and MSFT +1.5 survived the fix as clean, non-dust numbers and are genuine missing disposals -- a complete pull of every INDmoney confirmation for both shows no such sell, so the shares left through a channel that does not email. Both are now closed to broker truth with sourced corporate_action `adjustment` rows rather than force-matched lots, so the ledger reconciles 35/35 while the delta and its unknown cause stay permanently visible in trades.json.

**Closed by:** orchestrator 2026-08-15

---

## G69 -- OPEN
**Opened:** 2026-08-13  **Owner:** orchestrator (schema design)  **Closed:** 2026-08-13  

116 correctly-extracted historical confirmations were LOST because the `unresolved` schema the orchestrator specified for the parallel window agents was {ticker, ts_utc, missing} with NO qty or price fields. The agents complied exactly, so they logged that the trades existed and discarded the numbers -- unrecoverable without a re-pull. Entirely an orchestrator design error, not an agent fault. All 24 securities involved are exited/never-held, so the 31/31 invariant, current cost basis and LTCG are unaffected; the loss is historical realised P&L on closed positions. FIX for any future fan-out: the quarantine schema MUST carry the full extracted payload (qty, price, amount, order_type) so a later map entry alone recovers the row.

**Resolution:** PREVENTION half CLOSED; the 116 lost rows are NOT recovered and that is stated plainly rather than implied. The rule this gap itself prescribed is now a HARD RULE in SKILL.md: a quarantine schema carries the FULL extracted payload (qty, price, amount, order_type, ts_utc) and never a bare pointer -- generalised past ledgers as 'a schema for unresolved items defines what survives failure, so preserve the expensive part (the extracted data) and discard only the cheap part (the resolution)'. So this cannot recur. What remains is pure data recovery: re-pulling 116 confirmations across 24 securities, all of them exited or never-held. Deliberately NOT attempted here -- it is a large standalone email job whose entire effect is historical realised P&L on closed positions. It touches no live holding: reconciliation is 35/35, all 71 open lots carry a known basis, and the LTCG clock is unaffected. Worth doing only if closed-position P&L is wanted.

**Closed by:** recovery fan-out 2026-08-13

---

## G70 -- closed
**Opened:** 2026-08-13  **Owner:** orchestrator  **Closed:** 2026-08-15  

Trade-time vs present-day ticker divergence. 'Pure Storage, Inc.' trades in Feb-Apr 2026 were executed around its February 2026 rename to Everpure and its move to ticker P, so the symbol in force AT TRADE TIME may have been PSTG while the same security is P today. ticker_map is a flat name->symbol dict with no effective-date dimension, so it cannot express this. Low impact right now (exited position, 5 rows, and a rename changes neither share count nor basis) but the pattern will recur -- SNDK's own separation from WDC is a live example in this book. If a renamed name is ever held again, the map needs an effective-date form.

**Resolution:** Verified resolved in practice. ticker_map carries BOTH display names -- 'Pure Storage, Inc.' AND 'Everpure, Inc.' -- and both map to the SAME current symbol P. All 5 trade rows are recorded under P, and neither PSTG nor P is held. The working convention is therefore already correct and is worth stating explicitly: map every historical display name to the security's CURRENT symbol. That works because a rename changes neither share count nor cost basis, so a ledger keyed on the security needs no effective-date dimension to stay accurate. RESIDUAL RISK, named rather than pretended away: this convention breaks only if a symbol is REUSED by a different security over time (ticker recycling), where one symbol would legitimately need two mappings separated by date. That has not occurred in this book. Re-open with a concrete example if it ever does -- do not pre-build the effective-date machinery for a case that may never arrive.

**Closed by:** orchestrator review 2026-08-15

---

## G71 -- closed
**Opened:** 2026-08-13  **Owner:** orchestrator / smith-ledger  

SHARE-CLASS CONVERSIONS ARE INVISIBLE TO THE LEDGER. GOOG's FIFO runs NEGATIVE (-2.9919sh): it sold ~3 more shares than it ever bought, across a complete 13-row history whose first buy is the account's own first trade (2025-04-30). The cause is a GOOG->GOOGL share-class conversion -- already evidenced by the earlier finding that a row logged 'GOOG 8.441sh @ $325.79' was really GOOGL 8sh @ $327.45. A conversion moves shares between symbols WITHOUT generating a BUY/SELL confirmation, so an email-sourced ledger cannot see it and FIFO reports a phantom short. Note the sign: a conversion OUT produces a short (GOOG), a conversion IN would produce an over-count -- which is a candidate explanation for the G68 over-counts on QCOM/MSFT/AMD/MRVL, though unproven and not assumed. Any fix needs a conversion/corporate-action row type that FIFO understands, not another email pull -- the data is simply not in email.

**Resolution:** DIAGNOSIS IN THE ORIGINAL ENTRY WAS WRONG and is corrected here. The stated cause -- an invisible GOOG->GOOGL share-class conversion -- is disproven: GOOG's balance goes flat 2025-09-18, the phantom sells are 2026-02-03 and 2026-02-11, and GOOGL's ledger history does not begin until 2026-05-13, AFTER them. The specific row the entry cites (GOOG 8.441sh @ $325.79) does not exist; GOOGL holds 8.000000 @ $327.45, already corrected earlier. Nor is it shares transferred in at account opening: every affected ticker has a buy before its first sell. The real cause is MISSING BUY-SIDE RECORDS mid-history -- e.g. NVDA's 2026-02-03 row sells 10sh against 7sh ever recorded, with clean fill timestamps ruling out same-day ordering. A complete confirmation pull contains no such buys, so the shares arrived through a channel that does not email. Resolved by recording 7 sourced opening-balance `adjustment` rows (NVDA 3, GOOG 3.009384, TSM 2, AMD 0.998336, SMCI 0.005202) with NULL basis -- quantity from the shortfall FIFO measured, price genuinely unknown and NOT invented. Also fixed the detector itself: its 1e-9 threshold reported float noise as a 'shortfall_qty: 0.0' phantom short; now SHARE_EPS = 1e-6, below any quantity a broker records. Phantom shorts 7 -> 0, reconciliation holds at 35/35, cost basis on those tickers is now defined rather than silently missing.

---

## G72 -- closed
**Opened:** 2026-08-13  **Owner:** orchestrator  

ORCHESTRATOR TOLD THE USER SOMETHING FALSE ABOUT A HOLDING. On 2026-08-12, asked to compare Lumentum (LITE) against Corning and Amphenol, I stated LITE was 'never actually held -- only a stray TARGET GAP signal tag, no thesis, no position history.' The recovered ledger shows LITE was traded 22 TIMES between 2026-05-15 and 2026-07-23, cycling in and out repeatedly and closing flat on 07-23 for a realised LOSS of $54.18 -- six days before the user asked about it. Root cause: I checked state.thesis and state.signal_history, which are seeded from CURRENT holdings, and treated their silence as proof of absence. It is the same structural blind spot as the ticker_map defect -- current-holdings-derived state cannot answer questions about exited positions. STANDING RULE: before asserting a name was never held, query trades.json, which is the only record of the full history. Absence from thesis/signal_history proves nothing.

**Resolution:** Fixed in both halves. CODE: new `smith_math.py history --ticker X[,Y]` answers was-this-ever-held from trades.json -- the only file that records positions which no longer exist -- returning trade count, first/last dates, buys/sells, peak quantity and live status. Verified on the exact failure: LITE now returns 'WAS held and is now EXITED -- 22 trades between 2026-05-15 and 2026-07-23', cross-checked against lots.json alongside NVDA/COHR (live) and an unknown ticker (never held). RULE: SKILL.md EVIDENCE PRINCIPLE #4 -- state.thesis and state.signal_history are seeded from CURRENT holdings, so an exited name is silent in both BY CONSTRUCTION and the original check could only ever have returned 'never held' whatever the truth was. Generalised: before citing an absence as fact, confirm the source checked is one where a present item would have appeared.

---

## G73 -- closed
**Opened:** 2026-08-15  **Owner:** orchestrator  **Closed:** 2026-08-15  

cmd_book attached trade rationales to qty_changes via a bare ticker->reason map built by LAST-WRITE-WINS over the entire trade history, with no date and no direction check. Any ticker whose newest fill was not yet in trades.json inherited its most recent PRIOR, unrelated trade's reason. On 2026-08-15 that stamped four positions OPENING from zero (IREN, VRT, BE, GLW) with 'stop-loss' -- categorically impossible, not merely stale -- and labelled a genuine AMAT stop-loss sale 'deploy-excess-cash'. Found by smith-ledger, which correctly declined to fix it as outside its write surface.

**Resolution:** Fixed in scripts/smith_math.py: reason matching now requires (a) DIRECTION agreement -- a qty increase only accepts a buy-side row, a decrease only a sell-side row -- and (b) RECENCY, only rows dated at/after the previous run's ts. No match now emits 'UNMATCHED' rather than borrowing another event's reason. First cut of the fix still defaulted every row to sell because cmd_book's rows carry prior_qty/current_qty rather than qty_diff; corrected to derive direction from whichever shape is present. Verified: all six buys now read UNCAPTURED with correct dates, AMAT reads stop-loss, and an explicit regression assert confirms no opening is tagged stop-loss.

---

## G74 -- closed
**Opened:** 2026-08-15  **Owner:** orchestrator  **Closed:** 2026-08-15  

The orchestrator omitted sector_map from smith-thesis's embed for the second time (also 2026-08-10). Without the current map the agent classifies from scratch using its own natural taxonomy (GPU/Accelerator, Foundry, Memory, Optical/Interconnect) instead of policy.json's cluster_targets strings (AI Semis/Fabs, AI Memory/Storage, AI Networking/Optics). Because compute_drift does an EXACT string match against policy.json, merging a renamed map would silently drop every renamed cluster out of drift tracking. Caught at merge both times and the rename rejected, so no drift damage occurred -- but the agent wasted a task's effort on a map that was discarded, and a less careful merge would have broken drift outright.

**Resolution:** SKILL.md section 3 now requires the current sector_map to be embedded alongside the thesis map on every smith-thesis dispatch, with the exact-string-match reason stated. The agent's own file already tells it to reuse policy cluster names; it could not comply with a map it was never given.

---

## G75 -- closed
**Opened:** 2026-08-15  **Owner:** smith-catalyst  **Closed:** 2026-08-15  

smith-catalyst reported Coherent's 2026-08-13 fall as an earnings MISS. Primary reporting shows the opposite: a BEAT on revenue and EPS with a stronger-than-expected FY27 outlook -- the stock fell DESPITE the beat ('Coherent Stock Drops Despite Earnings Beat and Strong Outlook'). This is the SAME failure class as G58 (SanDisk, smith-thesis, 2026-08-10): inferring a fundamental verdict from a price move. It recurred in a DIFFERENT agent, one week after the G58 rules were written -- and smith-catalyst's file was never given the G58 verdict-vocabulary block, only smith-thesis, smith-quality and smith-signals were. The book had added 1sh of COHR the day after the print, so the false framing reached a live position. It was caught this run by the strategist's new evidence gate before it drove a sizing decision, which is the gate working as designed; the underlying rule gap is what remains open.

**Resolution:** Ported as process step 5 of smith-catalyst.md ('A PRICE MOVE IS NOT A FUNDAMENTAL VERDICT'), placed between classification and magnitude-scaling because that is where the inference actually happens, plus a HARD RULES one-liner. The rule is written against the specific failure: the source headline said 'Drop After Earnings' and the agent wrote 'miss'. Four clauses -- beat/miss means reported actuals vs consensus only; a stock can fall on a beat and rise on a miss so price direction carries no information about the quarter; reported quarter and forward guide are separate signals; escalating words need a magnitude and a source. Cheapest correction named explicitly (one WebFetch of stockanalysis.com, already an allowed domain) with the fallback stated: an honest 'fell 12% after reporting, beat/miss not established' beats an unverified verdict.
AUDIT of the rest of the fleet (the second half of this gap's next_step): smith-scout, smith-macro, smith-rebound, smith-cycle and smith-book never characterise earnings -- no exposure, no rule added, deliberately not padded. Two did need it and got tailored versions: smith-earnings, which OWNS the words beat/miss as its literal product and had an example verdict blending a surprise figure with a price move, now carries the airtight definition before it is built out; and smith-watchlist, whose 'earnings highlights' output line could drift from reporting a DATE into characterising a RESULT, now bounded to dates only.

VERIFICATION CAVEAT (2026-08-15): a regression replay was run against the exact 08-13 entry. It succeeded on outcome -- the agent judged its own entry non-compliant, fetched the real figures (non-GAAP EPS $1.74 vs $1.65 consensus, revenue $2.045B vs $2.025B, guidance RAISED), named the inference mechanically ('Drop after earnings' -> 'earnings miss'), correctly preserved the decoupling observation as separately sound, and surfaced a real new finding: the -12% magnitude this desk had been carrying is the least-corroborated of four conflicting figures (-4.57% to -12.4%, window unclear). All of that was persisted. BUT the agent's own step citations were off by one against the edited file -- it cited step 5 for MAP and step 6 for SCALE, which is the PRE-edit numbering. It read a cached definition. **Sub-agent definitions are loaded at session start, not re-read from disk per dispatch, so a rule edited mid-session cannot be regression-tested in that same session.** The correction therefore came from the pre-existing 'scale the claim to the evidence' rule plus an explicit prompt instruction, NOT from the new step 5. The new rule is written and synced but its behavioural effect is UNVERIFIED until a fresh session loads it. Do not treat this gap's test as proof the rule fires; re-run the same replay at the start of a later session to actually confirm it.

**Closed by:** orchestrator 2026-08-15

---

## G76 -- closed
**Opened:** 2026-08-15  **Owner:** orchestrator  **Closed:** 2026-08-15  

The strategist had no accountability loop. SKILL.md section 7 had instructed the desk to score past proposals at 30d/90d with outcome_pct and an aggregate scorecard since the file was written, and NO CODE EVER DID IT -- `outcome_pct` appeared nowhere in smith_math.py. As of this build: 96 proposals produced, 9 actually executed/fulfilled/filled, ZERO scored. The scorecard field was loaded and written back null every run, its `note` grown into a five-entry log of 'still zero proposals in the 30d/90d scoring window' dating to 2026-07-18 -- an excuse that expired ~2026-08-12. Meanwhile journal.json had been scoring SIGNALS since July and now carries real 30-day hit rates (TARGET GAP 57.1% n=14). The desk graded its indicators and not its decisions.

**Resolution:** Built `smith_math.py score`. Direction-aware (a TRIM works if price FELL, a BUY if it ROSE, a HOLD if the move stayed inside the +/-2% band), reusing the journal's VERDICT_THRESHOLD_PCT so 'worked' means the same magnitude in both. Orchestrator supplies prices (--prices-json, run against /dev/null first and it names what it needs -- these include EXITED tickers, so it is its own fetch). dismissed_by_user excluded and the exclusion count reported. First real run: 6 graded, overall accuracy 16.7%, buy 33.3% (n=3), hold 0% (n=2). Also added an ANCHOR PLAUSIBILITY GUARD after the first pass produced a 'TRIM TSM missed 39.4%' row off a corrupt $305.87 anchor (TSM traded $386-448 that week, closed $398.37) which on n=7 was setting the entire trim-accuracy figure; rows beyond +/-35% are now quarantined, reported in full, and excluded from the aggregate -- the same rule the charts apply to value_trust!=ok ledger rows.

---

## G77 -- closed
**Opened:** 2026-08-15  **Owner:** orchestrator  **Closed:** 2026-08-15  

P-005's price_at_proposal ($305.87, 2026-07-14) was flagged as a corrupt anchor because TSM traded $386-$448 that week. ROOT CAUSE WAS THE OPPOSITE OF THE DIAGNOSIS: the anchor was always correct and the TICKER was wrong. The action reads 'Re-enter VRT (funded by TSM trim)', and the 2026-07-29 ticker backfill did `.replace('(',' ').replace(')',' ')` -- stripping the BRACKETS but keeping their contents -- then took the LAST all-caps token, which is the funding leg named inside the parenthetical, not the subject. $305.87 is VRT's price on 2026-07-14 (VRT traded $287.53-$317.18 that week). The proposal's own note had recorded that the TSM leg never even happened ('TSM qty unchanged at 6sh').

**Resolution:** Three parts. (1) HEURISTIC: _proposal_infer_ticker now discards parenthetical CONTENT via regex before taking the last symbol, since a parenthetical in this desk's action grammar is always qualifying context ('(funded by X trim)', '(rotation funding leg)'), never the subject. Ten-case regression, all pass. Also needed `import re`, which was absent -- the first cut would have thrown at runtime. (2) DATA: P-005 corrected TSM->VRT and TRIM->BUY (the subject action is a re-entry); the $305.87 anchor was left untouched because it was never wrong. It now scores as a VRT buy, -3.93%, missed -- a defensible small loss instead of a phantom -39.4%. (3) SWEEP, which found a SECOND and worse case: P-010 was stored as ticker 'AI', parsed out of the CLUSTER NAME in 'Trim STM (AI Semis/Fabs + Memory/Storage cluster overage)'. 'AI' is a real ticker (C3.ai), so it pointed at the wrong company silently rather than failing visibly -- the same class as the 2026-07-13 MEM/DRAM incident. Corrected to STM. All 96 proposals now agree with the corrected inference. WORTH NOTING: the anchor guard added hours earlier did its job in a way I did not anticipate -- it was written to stop a bad NUMBER from setting the scorecard, and what it actually surfaced was a 32-day-old ticker error plus a second one nobody had looked for. Quarantining rather than discarding is what made that possible.

**Closed by:** orchestrator 2026-08-15

---

## G78 -- OPEN
**Opened:** 2026-08-15  **Owner:** user (at the next interactive run)  

Trade rationale for the RECENT, still-recallable set only -- the achievable remainder of G55 after its 635-row framing was retired. 32 UNCAPTURED trades dated 2026-08-01 onward, across 24 tickers (AMD, AMZN, ARM, BABA, BE, BX, CLS, COHR, FLTW, GEV, GLW, INTC, IREN, META, MKSI, MRVL, MSFT, MU, NBIS, QCOM, SKHY, SNDK, TER, VRT). These are recent enough that the user plausibly remembers the reasoning, and several sit on positions that are live and over their risk caps, so the 'why' still has decision value. Everything before 2026-07 is deliberately OUT of scope and stays UNCAPTURED permanently.

---

## G79 -- closed
**Opened:** 2026-08-15  **Owner:** smith-ledger / user (brokerage statement)  **Closed:** 2026-08-15  

ORPHANED POSITIONS -- the ledger shows shares still open that the broker does not report at all. Surfaced by the lots-engine cutover, which added a reconciliation check in the opposite direction to G68: the existing check only walked tickers the BROKER reports, so a ticker the LEDGER thinks is open while the broker shows nothing was structurally invisible. Five found, and one is material: PLTR 5.003973sh across FIVE lots (2026-02-25 to 2026-05-13, basis $126-161), META 1.004836sh (2026-08-06 @ $589.84), EWY 0.041075, SMCI 0.014346, WDC 0.0059. This is a bigger miss than G68's over-counts: G68 is a partial shortfall on a held name, whereas these are positions the record believes are entirely open and are not. PLTR at ~5sh and ~$700 of basis is the one that matters. META is notable because it was exited deliberately in the 2026-08-13 session (the narrative records a full close at $581.83) -- so the sell happened, and the record has ~1sh of it missing.

**Resolution:** RECONCILED 2026-08-15, same split as G68. EWY/SMCI/WDC were fee-inflation dust and disappeared with the G80 root-cause fix. PLTR 5.000975sh and META 0.995985sh were real. PLTR's full email history is complete -- 20 transactions, every one matching the ledger, and NO disposal anywhere -- so the position left the account without a sell confirmation. META's residue traces to an Oct-2025 fractional pair never sold; its August fills net to exactly zero, so the recent deliberate close-out is fully accounted and is NOT the cause. Both closed with sourced adjustment rows.

**Closed by:** orchestrator 2026-08-15

---

## G80 -- closed
**Opened:** 2026-08-15  **Owner:** smith-ledger  **Closed:** 2026-08-15  

SYSTEMATIC LEDGER RECONSTRUCTION ERROR, root cause of nearly all the fractional dust in G68 and G79. Rows reconstructed with qty_source='derived_amount_over_price' computed shares as Amount / Price. That is wrong: INDmoney's Amount field INCLUDES SEC/FINRA fees, so Amount is not shares x price. PROVEN against the 2026-06-22 META confirmation -- Amount $563.58 / Price $561.92 = 1.002954, while the email's own Shares field reads exactly 1. The method inflates BUYS and understates SELLS (PLTR's 2026-05-19 sell of 2 was recorded as 1.999926). 30 of the 54 derived rows were within 1% of a clean share count and have been corrected, removing +0.157531 phantom shares and eliminating the VRT/AMD/MRVL mismatches and the EWY/SMCI/WDC orphans outright.

**Resolution:** Three parts. (1) RULE: smith-ledger.md task 2 now FORBIDS deriving a quantity from Amount/Price outright. The email's `Shares:` field is the only acceptable source, and when the search snippet truncates before it -- which it almost always does -- the agent must spend one `get_thread` call rather than divide. The old text permitted the division as a fallback; that was arithmetically invalid, not merely approximate. Worth recording that the SAME FILE already contradicted itself: its TRUST BOUNDARY section told the agent to flag a confirmation when 'amount != price x shares by more than a plausible fee', so it knew fees broke the identity and told itself to divide anyway. The wrong half was the half being executed. The rule also explicitly forbids substituting a modelled fee ratio -- that is the same error one level up, deriving a number you could have read. (2) DETECTOR: `smith_math.py lots` now inspects every row each run and reports two distinct things -- a G80 RELAPSE alarm for any row dated on/after 2026-08-15 using the forbidden method (tested by injection), and a separate informational line for the accepted historical residue. A prose rule is exactly what lapsed here, so the compute layer now carries the check where it cannot quietly stop being true. (3) DATA: 30 of the 54 affected rows were corrected during the G79 work (+0.157531 phantom shares removed). The remaining 24 are genuine dollar-based fractional orders that cannot be snapped to a clean number. They were MEASURED rather than assumed immaterial: ~$29.08 of cost-basis error in total, ~$11.86 of it on live positions (AMD, VRT) = 0.027% of book equity. Re-pulling 24 confirmations to recover twelve dollars is not proportionate, so they are knowingly left, listed by ticker, and reported every run. Verified against two confirmations: 2026-06-22 META (share-based: Amount/Price 1.002954 vs Shares field 1) and 2025-04-30 GOOG (dollar-based: 0.626330953 vs 0.62453024, $0.29 of a $100 order being fees) -- so both order types are affected, not just one.

**Closed by:** orchestrator 2026-08-15

---

## G81 -- OPEN
**Opened:** 2026-08-19  **Owner:** smith-catalyst / orchestrator verification  

PROXIMATE CAUSE OF THE 2026-08-18 SEMIS ROUT IS UNRESOLVED, AND THE FIRST ANSWER WAS WRONG. smith-catalyst returned, as its lead catalyst, that the 30-year UST hit a 19-year high of 5.33% on Tuesday and repriced high-multiple AI hardware. Checked against primary data before it reached sizing: ^TYX CLOSED Tuesday at 5.285%, DOWN 2.4bp from Monday's 5.309%, and ^TNX at 4.706%, DOWN 1.8bp. Long yields FELL on the session semis dropped 4.09%. The 19-year-high LEVEL is real and is standing multiple-compression pressure on long-duration names; a Tuesday rates SHOCK is not supported by the tape and cannot be the proximate cause. Best-evidenced named trigger remains the WSJ $3T off-balance-sheet AI-commitments report dated 08-17, one day prior, which smith-catalyst itself named as the driver of the GEV/BE/VRT behind-the-meter selloff. This is the G58/G75 failure class in a new place: a plausible causal narrative that the primary series contradicts, sourced to a single secondary aggregator. STANDING RULE ADDED: a catalyst that asserts a MARKET-DATA move (a yield, an index, a spread) as its mechanism must cite the series and the two prints, not a news paraphrase -- market data is the one class of claim the desk can always check itself in one call.

---

## G82 -- OPEN
**Opened:** 2026-08-24  **Owner:** orchestrator / user decision  

BX (Blackstone) was re-entered 2026-08-24 (10sh, 3.67% weight) after a full exit on 2026-08-17. smith-thesis classified it into a brand-new satellite cluster 'Financials/Alt-Asset Diversifier' because it does not fit any existing policy.json cluster and is not a clean AI-capex diversifier -- it shares the XPV off-balance-sheet AI-financing tail risk (Blackstone/Apollo funding Anthropic compute) that drove BofA's 08-11 bond downgrade on AVGO. This cluster has NO policy band, so it is invisible to drift math by design until the user sets one. The AI-capex concentration ratio drop from ~89% to 83.7% this run is this reclassification, not real de-risking -- do not read it as improvement without noting the cause.

---

## G83 -- OPEN
**Opened:** 2026-08-24  **Owner:** smith-ledger (next interactive run)  

BX's re-entry lot is dated 2026-08-21 in trades.json/lots.json, but state/G82 and this run's dispatch both stated the re-entry happened 2026-08-24 -- a 3-day discrepancy independently caught by smith-book, smith-tax, and the strategist this run. Immaterial for tax (all lots are short-term regardless), but the record disagrees with itself and should be reconciled against the actual INDmoney confirmation email at the next interactive run.

---

## G84 -- OPEN
**Opened:** 2026-08-29  **Owner:** orchestrator  **Closed:** 2026-08-29  

2026-08-29 deep review: strategist and orchestrator both asserted a nonexistent '8% drawdown warn line' (policy.json's real drawdown_warn_pct is 15) across the ledger narrative and the chat briefing. Root cause: a number lived only in free-text narrative with nothing checking it against policy.json, so it could be typed once and copied forward. Fixed same-day: smith_memory.py's validate command now has validate_policy_narrative_drift(), which flags the MOST RECENT ledger row if it quotes a drawdown warn/risk-off percentage that disagrees with policy.json.

**Resolution:** Corrected the 2026-08-29 ledger row's narrative text in place (a factual error, not a historical value); added validate_policy_narrative_drift() as a standing guard against recurrence.

---

## G85 -- OPEN
**Opened:** 2026-08-19  **Owner:** orchestrator (smith_lifecycle proposals engine)  

SHADOW-SCORED TRIGGER PROPOSALS ARE STRUCTURALLY EXEMPT FROM CONDITION-BASED AUTO-RETIREMENT. Any proposal whose trigger_type is a shadow trigger (profit_ratchet, scale_out_ladder) is written with retires_when = 'n/a -- shadow-scored, tracked in trigger_journal.json rather than lifecycle-managed here', so the §7 retirement pass never tests it and it can never clear itself no matter what happens to the position. The 2026-08-18 stop cascade made three stale at once and all three survived the dedup/retire pass: P-104 (raise MU stop to cost basis) after MU was cut 2.5sh->0.5sh by that very stop; P-114 (TRIM MRVL $550.65, sized on a 1.468x ATR cap) after the stop cut MRVL 7sh->4sh and the cap breach cleared to 0.809x, leaving a $551 trim against an $864 position; P-117 (STOP_RAISE TER) against what is now a $1.10 / 0.00273sh dust residue. The exemption was written so shadow triggers would not be lifecycle-managed on an unmeasured hit rate -- but retirement is not scoring. A proposal whose SUBJECT no longer exists in the form it was written against should retire regardless of whether its trigger has a track record. FIX: give shadow-triggered proposals the same objective retirement tests every other proposal gets (position materially reduced since proposal date, ticker no longer held, size_usd now >50% of remaining position value, position value under the dust threshold), keeping only the SCORING exemption.

---

## G86 -- OPEN
**Opened:** 2026-08-17  **Owner:** orchestrator  

NO email/transaction-confirmation tooling exists in this standalone deployment (Claude Agent SDK + system cron against INDmoney's public MCP server). Step 2.9's scoped-email fallback and smith-ledger's entire confirmation pipeline are therefore UNAVAILABLE, not merely skipped, on every scheduled run here. Consequence: exact fill price / timestamp / order type cannot be recovered for any trade, so new trades.json rows are written price_source='reconstructed' (quantities remain broker truth). This structurally blocks stop-vs-deliberate cohort classification for all future fills and quarantines them out of smith_math.py stops scoring. First hit 2026-08-17 on 5 trades (BX exit, NBIS trim, IONQ entry, BE add, AMZN add). This is the CAUSE; G78 tracks the resulting rationale backlog.

**Resolution:** Closed for INTERACTIVE Claude Code sessions (Gmail connector present; proved 2026-08-19 -- 18 confirmations pulled, 10 of 11 qty_changes resolved to a literal `Order Type: stop`, 5 prior reconstructed rows corrected). REMAINS OPEN for the headless/cron deployment, which still has no email tooling.

---

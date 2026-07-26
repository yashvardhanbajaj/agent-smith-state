# Tier 2 & 3 Enhancements — Status & Implementation Guide

**Created 2026-07-26 as part of architecture audit completion.**

---

## Tier 2 — Analytical Gaps (High value, medium effort)

### 2.1 ✅ HBM Tracker Integration (ready to wire)
**What:** smith-thesis should read `/Users/yb/Claude/HBMTracker/history.json` + `forecast.json` when any Memory-cluster name is held.

**Current state:** One-way only — HBMTracker reads Smith state, Smith never reads tracker.

**Implementation:**
- smith-thesis agent loads tracker on every run if MU/SNDK/DRAM/EWY held
- Compares tracker's `thesis_tensions` (HBM3E ASP -51% from peak) against Smith's "strengthening" verdicts
- Reconciles or contests the tension in output; flags for strategist review

**Benefit:** Friday's 07-24 selloff would have been correctly contextualized: SK Hynix HBM4 delay is margin-mix (DDR5 more profitable), not demand destruction.

---

### 2.2 ✅ AI Capex Cycle Analytics (skeleton: smith-cycle.md)
**What:** NEW AGENT. Reads hyperscaler capex guidance, memory pricing, semicap health → outputs cycle_position (accelerating|mid|late|rolling) + confidence.

**Current state:** Skeleton agent created; data sources not yet wired.

**Implementation roadmap:**
- Manual first run: pull MSFT/GOOGL/AMZN latest capex announcements + HBMTracker data
- Wire FMP or TipRanks for hyperscaler capex guidance (if available)
- Pull SEMI book-to-bill from public SEMI index (if accessible)
- Feed into strategist to distinguish "AI capex is strong" from "already priced"

**Benefit:** For a 100%-AI-capex book, this is the single most valuable new signal.

---

### 2.3 ✅ Sell Discipline Framework (spec: SELL-DISCIPLINE-FRAMEWORK.md)
**What:** Pre-commit a drawdown ladder so de-risking is policy, not panic.

**Current state:** Framework document created; not yet integrated into policy.json or strategist logic.

**Implementation:**
- Add `drawdown_trim_ladder` to policy.json schema
- Strategist checks drawdown on every run; auto-recommends batch if threshold crossed
- Proposal tracker records execution prices; measures hit rate quarterly

**Benefit:** Turns discretionary behavior (07-24 five exits) into repeatable, auditable process.

---

### 2.4 ✅ Volatility-Aware Proposal Sizing (guidance: benchmark_note in drift output)
**What:** Proposals currently sized in round dollars ($700, $900) with no volatility context. SOX 3mo vol is 61.4%; 1-week 1-sigma is 8.5%.

**Current state:** Guidance note added to drift output; not yet implemented in proposal sizing.

**Implementation:**
- Add `realized_vol` to holdings.json (3mo or 1mo realized vol per name)
- Strategist sizes trims/deploys as % of position or in ATR-based tranches, not fixed dollars
- E.g., instead of "$700 trim MRVL," propose "trim 2% of MRVL position (=$712 at current)" → scales with vol

**Benefit:** A $700 trim in a 61%-vol sector is noise; ATR-based sizing is real risk reduction.

---

### 2.5 ✅ Benchmark Mismatch: SOX Primary (guidance: benchmark_note in drift output)
**What:** Book is benchmarked to SPX/NDX but beta is really vs SOX/SMH. SPX beta predicted +0.075% Friday; actual was -5.06%. SOX beta ~1.19.

**Current state:** Guidance note added to drift output; not yet reflected in reporting.

**Implementation:**
- Compute and cache SMH and SOX betas (primary) alongside SPX (secondary)
- Report SMH as peer benchmark in signals section, not QQQ
- Use SOX beta in stress tables, not SPX

**Benefit:** Removes misleading -5% moves; shows the book was roughly in line with sector Friday.

---

### 2.6 ✅ Factor Attribution: Market vs Sector vs Idio (guidance: factor_attribution_note in attribution output)
**What:** Attribution currently lumps FX/flow/residual, but doesn't split residual into market|sector|idiosyncratic.

**Current state:** Guidance note added to attribution output; decomposition not yet implemented.

**Implementation:**
- Fetch SPX return and SOX return from market_inputs.json (or holdings.json)
- market_move = residual × (SPX_return)
- sector_move = residual × (SOX_return - SPX_return)
- idio = residual - market_move - sector_move

**Benefit:** Answers "why did the book move" clearly — can isolate signal from noise.

---

### 2.7 ✅ Tax Lots: Seeded Template (lots.json updated)
**What:** lots.json was an empty shell; now has schema + example. Still needs population from INDmoney order history.

**Current state:** Template with example format; user must seed actual lot dates/prices.

**Implementation:**
- Extract order history from INDmoney account statement CSV
- Parse into lots.json {ticker: [{qty, date, price_usd}]}
- Once seeded, G1 gap is resolved and smith-tax agent can sequence trims

**Benefit:** Unblocks LTCG timing on every trim proposal (currently unavailable).

---

## Tier 3 — New Capabilities (Medium effort, high value)

### 3.1 ✅ smith-cycle Agent (skeleton: smith-cycle.md)
**What:** Deep-mode agent reading hyperscaler capex guidance + memory pricing + semicap health → cycle position read.

**Current state:** Skeleton created; data sources not wired.

**First run:** Manual (pull hyperscaler capex + HBMTracker data); then automate.

---

### 3.2 ✅ smith-earnings Agent (skeleton: smith-earnings.md)
**What:** Owns earnings calendar, option-chain expected moves, historical surprise rates, post-earnings drift.

**Current state:** Skeleton created; yfinance calendar unreliable (G20), option-chain pull not wired.

**First run:** Manual for 07-28/07-29 earnings (TER/QCOM/LRCX/GLW); then evaluate FMP data source.

---

### 3.3 ✅ smith-tax Agent (skeleton: smith-tax.md)
**What:** Sequence trims by tax lot, flag LTCG boundaries, identify wash-sale risks, flag year-end (Jan-Mar) harvesting windows.

**Current state:** Skeleton created; unblocked once lots.json is seeded (currently empty).

**First run:** Once user populates lots.json, run smith-tax on next deep review.

---

### 3.4 Regime-Conditional Diversifier Screening (design needed)
**What:** 07-20 bench ranked DUK and SO as "clean" diversifiers on AI-capex overlap alone, ignoring that they're rate-sensitive.

**Current state:** Not yet implemented. Needs smith-scout enhancement to score candidates against current macro regime.

**Implementation roadmap:**
- Extend smith-scout to compute rate-sensitivity (duration-like metric) per candidate
- Filter by current regime: hiking Fed → exclude utilities, prefer commodities/gold; cutting Fed → diversifiers work

**Benefit:** Prevents rate-trap diversifications into rising-rate environment.

---

### 3.5 Dashboard: Book-Value History (design needed)
**What:** ledger.csv has 13 rows of value/cash history since 07-12, never plotted. Dashboard should show sparklines: total book value + cash %.

**Current state:** Not yet implemented. Needs dashboard.html extension.

**Implementation:**
- Parse ledger.csv (ts, mode, value_usd, wallet_usd)
- Compute rolling value and cash % from each row
- Add SVG sparklines to dashboard header, refresh on each run

**Benefit:** Visual: the 07-24 cash spike (0.06% → 45.8%) becomes obvious at a glance.

---

## Summary

**Status: Tier 2 & 3 blueprints complete**
- Tier 2: 5/7 documented with implementation roadmaps; 2/7 need data-source wiring
- Tier 3: 3 agent skeletons created; 2 features designed but not yet implemented
- All require incremental work, no blocking issues

**Recommended next steps:**
1. Wire HBMTracker integration into smith-thesis (1-2h)
2. Seed lots.json from INDmoney order history (user action)
3. Run smith-cycle and smith-earnings manually first (validate signals before automation)
4. Extend sell-discipline framework into policy.json + strategist logic (4-6h)

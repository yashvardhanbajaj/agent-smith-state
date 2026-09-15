# smith-thesis — 2026-09-15 (WAVE 2, deep, pre-open)

## 1. Thesis table (27 holdings; deep mode, narrow news budget)
No verdict CHANGES this run — all 09-14 calls (GEV/GLW downgraded to WATCH; MRVL/CIEN/TER/AMAT/KLAC/APH/WDC/MSFT strengthening) carry forward unchanged; pre-open, no new session data yet. 3 entries got new evidence appended (ASML, GEV, MU — see below); rest are `reviewed_unchanged`.

WATCH: ASML, GEV, VRT, AVGO, MU, AMD, GLW, STM, NBIS, AMZN
STRENGTHENING: MRVL, CIEN, TER, AMAT, MSFT, WDC, KLAC, APH, CLS, QCOM, TSM, BE, GOOG, COHR, LITE, ALAB, NOW

**ASML** (WATCH) — sole-source EUV; Wave-1 catalyst-scan VERIFIED this run that MSFT/AMZN/GOOGL/ORCL 2026 capex guidance is unchanged (~$660-690bn) since the Amodei essay — corroborates the existing "sentiment/multiple-compression, not demand" read. No status change.
**GEV** (WATCH) — Wave-1 clarifies GLJ Research's $470 Sell PT is the Street's lowest (single boutique outlier, uncorroborated by peers) — this *weakens* the bear case but the separate SEC-EDGAR-verified trailing-NI quality flag (non-operating gains inflating NI 5x op-income) is the more durable reason for WATCH and is untouched by this nuance. No status change.
**MU** (WATCH) — HBM3E price is now FRESH (0-day-stale, was 33-day-stale) and still flat at $9.00/GB mid — confirms the prior flat read wasn't stale-data noise. WATCH remains CXMT-capacity-driven, not ASP-driven; no conflict, no action. See §4.
**COHR/TSM/AMAT/ASML** (per signals) — had positive fundamental news 09-14 while price fell — consistent with sector-beta/multiple-compression read already applied book-wide, not idiosyncratic deterioration. No action.
**GLW→COHR/LITE contagion** — catalyst tail explicitly frames COHR (-11%) and LITE (-9%) 09-14 moves as *read-through* from GLW's $2bn ATM announcement, not their own fundamental events. Both remain STRENGTHENING (status-only tier); leaving their full evidence arrays untouched in state rather than reconstructing a partial version here.
**TER/CIEN open_flags** — TER's 2026-08-19 "dust position" flag is stale (TER is a full 5.02% position; already corrected in TER's thesis note). CIEN is now genuinely dust ($2.74 total, 0.0083% weight) and has no open_flag yet. Both need orchestrator-side open_flags.json maintenance — see data_quality.

All other 22 names: reviewed, no new evidence surfaced by Wave-1 that bears on their verdict. See `reviewed_unchanged` in tail.

## 2. Factor cluster table (% of equity / 27 holdings)
| Cluster | Tickers | % equity |
|---|---|---|
| AI Semis/Fabs | ASML,AMAT,TER,QCOM,TSM,KLAC,AMD | 33.17% |
| AI Networking/Optics | MRVL,AVGO,CIEN,GLW,COHR,LITE,ALAB,APH | 23.65% |
| AI Power/Cooling/DC Infra | GEV,VRT,BE | 16.82% |
| Compute/Hyperscaler | MSFT,GOOG,NBIS,AMZN | 13.25% |
| AI Memory/Storage | MU,WDC | 5.41% |
| Compute/Hyperscaler OEM | CLS | 3.83% |
| Analog/Industrial Semis | STM | 2.17% |
| Enterprise Software | NOW | 1.71% |

**Combined AI-capex chain (all clusters except STM + NOW): 96.12% of equity, ~77.9% of total book (incl. ~19% cash wallet).** Matches catalyst tail's independent 77.47%/book figure.

**Co-movement check (09-14 session):** AI Networking/Optics cluster -8.86% vs SMH -4.75% (~1.9x beta); Power/Cooling names also fell together (GEV -8.30%, VRT -7.04%, BE -6.33%) despite being semis-adjacent, not semis-direct. Confirms the book trades as one factor, not several.

## 3. Single-factor risk verdict
This is, in every practical sense, one bet: AI-capex buildout. 96.1% of equity spans seven clusters that all reprice together the moment SMH moves (confirmed again today — Networking/Optics fell nearly 2x the index). The only genuinely uncorrelated equity sleeve is STM + NOW combined, 3.88% of equity (~3.1% of book) — small enough that it provides no real ballast. The book's actual shock absorber is the ~19% cash wallet (747,939 INR / 3,932,038 INR total book), not diversification within the equity book itself. A datacenter-capex pause (which Wave-1 confirms has NOT happened — hyperscaler capex guidance is unchanged) would hit ~96% of the equity book simultaneously; today's -4.75% SMH day is a live small-scale demonstration of exactly that correlation.

## 4. HBMTracker reconciliation (MU only — EWY/DRAM not currently held)
- **HBM3E, stack-derived basis**: $9.00/GB mid, flat (0.0% trend, 2026-07-19→2026-09-15), price now 0-days-stale (previously 33 days). Per G12, this row is tier2-only (Silicon Analysts single source) despite the file's row-level tier1_corroborated flag misleadingly reading true — treat with appropriate caution, not full tier1 confidence.
- **verdict_conflict**: none. MU's WATCH is explicitly CXMT structural/capacity-risk-driven (qualification-stage HBM3E shipments to Alibaba/Cambricon, ~1yr ahead of 2027 consensus), not ASP-driven — flat ASP neither confirms nor conflicts with that thesis. **direction: no_action.**
- **HBM4**: last priced 2026-08-05, now 41 days stale (exceeds 30-day threshold), [10,14]/GB band flagged suspect (correction C2 — basis splice between stack-derived $10.42/GB and a separate initial-production estimate). Not used to inform MU's verdict. Supply-structure context: MU is NVIDIA-certified for Vera Rubin HBM4 but structurally thin on allocation (SK hynix 60-70%, Samsung 25-30%, Micron the analyst-estimated remainder — single digits to low teens) — a rising HBM4 ASP would not flow through to MU proportionally even once pricing data refreshes.
- **Corrections checked**: C1 (phantom -51% HBM3E decline, resolved — was a basis-splice artifact) and C2 (HBM4 splice) — both read before forming any view.
- **Forward forecast context**: TrendForce (as_of 2026-06-02) expects 2027 HBM contract prices to "surge multiples higher," range cited 80-150%. Note: the "DDR5 profitability crossover, 2026-04-21" reference in the standing task template was NOT found in today's consumer_view.json snapshot (closest dated entry that day is the CXMT downside-risk forecast) — not fabricated here, flagged in data_quality instead.

## 5. Data quality (capped at 6)
- TER/CIEN open_flags.json stale: TER's 08-19 dust-flag is obsolete (now 5.02% full position); CIEN is now genuinely dust ($2.74, 0.0083%) with no flag yet. Needs orchestrator update.
- HBM3/HBM3E 2026-09-15 row is tier2-only per G12 (Silicon Analysts sole source) despite row metadata reading tier1_corroborated=true — a known tracker bug, not this run's error.
- etf_constituents cache: DRAM's `currently_held: true` flag (cached 2026-08-07, now 39 days stale) is wrong — DRAM is not among the 27 current holdings. EWY correctly flagged not-held. No refresh call spent since neither is held/needed for classification this run.
- Task-template reference to a "DDR5 > HBM3E profitability crossover, 2026-04-21 TrendForce" datapoint was not found in this run's HBMTracker snapshot — omitted rather than invented.
- Ticker/name sanity check (task 1): all 27 holdings' `name` fields match their tickers correctly — no mismatches found this run.
- No new precedent-relevant status changes this run, so no `gaps --query` citation required beyond the routine check run (no new hits beyond already-cited G75 on GEV).

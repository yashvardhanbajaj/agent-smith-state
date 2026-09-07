# Thesis & Factor — 2026-09-07 (deep, Wave 2)

## 1. Thesis table

**Status changed / new evidence this run:**

- **GEV** (9.5%, largest position) — strengthening. Thesis: hyperscaler grid/power-gen equipment, gas turbines + grid-electrification AI-DC beneficiary. EVIDENCE_FOR: Q2 FY26 operating income $655M, +73% YoY, on revenue $11.10B +22% YoY; net cash throughout, diluted shares -2.2% YoY (2026-09-07, smith-quality/EDGAR). EVIDENCE_AGAINST: trailing-4Q net income >5x trailing-4Q op income — driven by a Q1 FY26 $4.92B non-operating gain (10-Q pretax $5.10B vs op income $179M that quarter) and a Q4 FY25 $2.57B tax benefit; primary-source EDGAR-confirmed (GEV 10-Q accn 0001996810-26-000064, verified_on 2026-09-07) — trailing NI is not a usable run-rate proxy right now, though the underlying Q2 print is genuinely strong. No insider buying observed during the past 60 days per Form 4 scan (src: SEC Form 4, as_of 2026-09-07) — mild absence-of-confidence, not a formal flag. Verdict unchanged (strengthening); the quality flag is a measurement-quality caveat, not a thesis break.

- **MRVL** (5.07%) — strengthening (upgraded from quiet to a fuller entry this run). Thesis: custom AI ASICs/networking silicon for hyperscalers, AI Networking/Optics cluster. EVIDENCE_FOR: Q2 FY26 EPS $0.94 beat $0.93 consensus; Q3 guide ~4% above consensus (guide_above_consensus); OCF $605.5M vs NI $308.0M = 1.97x cash conversion; interest expense normalized to $81.4M (5.6x op-income coverage) from the Q1 FY26 acquisition-financing spike, confirming the earlier G44 interest-coverage scare is resolved (all 2026-09-07, smith-earnings/smith-quality EDGAR-adjacent). EVIDENCE_AGAINST: diluted shares +5.8% YoY (870.4M→921.2M) and SBC/revenue climbing 6.4%→8.6%→11.9% over 3 consecutive quarters (2026-09-07, yfinance quarterly financials via smith-quality); 3 distinct insiders (Bharathi, Koopmans, CEO Murphy) sold in the last 60 days while the stock sits -32% off its 52-week high — no formal "sell into rally" flag (not near highs) but worth noting as a mild negative tell (src: SEC Form 4, as_of 2026-09-07); the post-earnings drop was attributed to valuation/position-unwind after a 179% YTD run, not a guidance miss. Net: fundamentals genuinely improving, dilution/SBC trend is the thing to watch next quarter.

- **BE** (5.09%) — strengthening, unchanged. New this run: 5 distinct insiders (Chambers, Chitoori, Immelt, Joshi, Soderberg) sold in the last 60 days; stock is -28% off its 52-week high so no formal "sell into rally" flag fires, but the seller count is a new data point worth tracking (src: SEC Form 4, as_of 2026-09-07). No insider buying during the drawdown either.

- **VRT** (4.95%) — watch, unchanged (contested print, see below). New this run: 1 insider sold in the last 60 days (src: SEC Form 4, as_of 2026-09-07); no insider buying during its drawdown.

- **MU** (3.84%) — watch, unchanged. WATCH remains structural/capacity-risk-based (CXMT), not ASP-based — HBM3E is flat within basis, not falling (see HBM reconciliation below). NEW EVIDENCE_AGAINST this run: CXMT reached HBM3E risk production, shipping qualification samples to Alibaba T-Head and Cambricon, ~1 year ahead of the 2027 consensus timeline (src: smith-catalyst scan citing techtimes.com, as_of 2026-09-01/reported 2026-09-07) — qualification-stage volume only, no unit count disclosed, not yet reflected in any supplier contract price. This reinforces the existing structural WATCH; it does not create a status conflict since MU's WATCH was never ASP-premised.

- **SKHY** (2.23%) — strengthening, unchanged, first fuller write-up this run (previously status-only). Thesis: SK Hynix direct position, HBM4 Vera Rubin allocation leader. EVIDENCE_FOR: SK Hynix holds 60-70% of HBM4 Vera Rubin supplier allocation vs Samsung 25-30% and Micron low-single-to-teens — the largest share of the current ramp (src: HBMTracker consumer_view.json supply_structure, as_of 2026-06-05); this is a materially better allocation position than MU carries on the same "HBM4 exposure" language. EVIDENCE_AGAINST: same CXMT HBM3E risk-production catalyst applies to SKHY per smith-catalyst's affected-tickers list (src: smith-catalyst scan, as_of 2026-09-07), qualification-stage only, not yet in pricing.

**Unchanged this run (reviewed, verdict stands — full text in prior state):**
ASML watch (China-DUV risk not resolved, only un-escalated; new: no insider buying observed in 60-day scan, src SEC Form 4 2026-09-07 — mild negative tell only), CLS strengthening, AVGO watch, CIEN strengthening, QCOM strengthening, AMAT strengthening, AMD watch, LRCX strengthening, MSFT watch, INTC watch, STM watch, GOOG strengthening, NBIS watch, KLAC strengthening, LITE strengthening, IREN watch, SMCI watch, FSLR watch, APH strengthening, TER strengthening, TSM strengthening, GLW strengthening, WDC strengthening, COHR strengthening, ALAB strengthening, NVDA strengthening.

## 2. Factor cluster table (% of book, from held weights)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | ASML, TER, INTC, AMD, AMAT, TSM, NVDA, KLAC, LRCX, QCOM | 31.83% |
| AI Power/Cooling/DC Infra | GEV, BE, VRT, FSLR | 21.08% |
| AI Networking/Optics | MRVL, ALAB, COHR, LITE, APH, AVGO, GLW, CIEN | 19.81% |
| Compute/Hyperscaler | NBIS, GOOG, IREN, MSFT | 10.88% |
| AI Memory/Storage | MU, WDC, SKHY | 8.42% |
| Compute/Hyperscaler OEM | CLS, SMCI | 3.36% |
| Analog/Industrial Semis | STM | 4.60% |

**Combined AI-capex chain (all clusters except Analog/Industrial Semis): ~95.4% of the book.** A datacenter-capex pause or sharp derating hits ~95% of the book simultaneously — this is not a diversified equity portfolio, it is a leveraged single-factor bet expressed across ~31 tickers. Co-movement check: market closed today (Labor Day); ret_5d/rel-strength refresh not run (signals data_quality confirms caches held at 7-day TTL). Qualitative read from the week's news flow (AVGO guide reaction, KLAC/STM post-print derates, CXMT catalyst) is that AI-semis/memory names have been trading on idiosyncratic print reactions more than pure SOX beta lately — cannot be confirmed quantitatively this run.

## 3. Single-factor risk verdict

This is effectively one bet. ~95.4% of the book sits inside the AI-capex chain (semis/fabs, power/cooling infra, networking/optics, memory, hyperscaler compute and hyperscaler-OEM), spread across enough tickers to look diversified on a name-count basis but moving on the same underlying driver — hyperscaler capex sustaining at current or higher levels. The only nominally uncorrelated slice is STM (Analog/Industrial Semis, 4.6%), and even STM's own bull case now leans partly on AI-datacenter demand (raised DC revenue targets, per its thesis) — so the genuinely uncorrelated slice of this book is closer to 0% than 4.6%. There is no real diversifier at this point (BX, the last one, was fully exited 2026-08-17 per open_flags). A hyperscaler capex-growth deceleration, not just a rate shock, is the single scenario that would hit nearly the entire book at once.

## 4. HBMTracker reconciliation

Data staleness: `staleness_days`=0 (tracker ran 2026-09-06) but `max_price_staleness_days`=32 — newest priced HBM points are dated 2026-08-05. Per the tracker's own guidance, price data is weighted with reduced confidence given the 32-day gap; qualitative/structural updates (CXMT, supply_structure) are fresher (2026-09-01/09-06) and carried at full weight.

**MU (HBM-sensitive, 3.84% weight):**
- Metric: HBM3E $/GB, stack_derived basis, $9.00/GB mid ($8-10 range), 2026-07-19 → 2026-08-05, trend_pct_within_basis = 0.0% (flat). Cross-basis comparison to the 2025-06-30/2026-01-15 contract_quote series is explicitly refused (cross_basis_change_is_meaningless=true) — the historical "-51%" figure is a corrected artifact (correction C1, closed 2026-08-05), not a real price move.
- Corrections checked: C1 (HBM3E basis-splice, phantom -51% decline — resolved, TrendForce actually reports HBM3E contract prices rising ~20% for 2026), C2 (HBM4 basis-splice, not directly relevant to MU here).
- Forward forecast context: 2027 HBM contract prices forecast +80-150% (TrendForce, as_of 2026-06-02); DDR5>HBM3E profitability crossover flagged 2026-04-21.
- Supply structure: HBM4 Vera Rubin allocation — SK Hynix 60-70%, Samsung 25-30%, Micron low-single-to-teens (as_of 2026-06-05). MU is qualified but structurally thin on this specific ramp, unlike SKHY.
- Verdict conflict: none. MU's WATCH status is explicitly structural (CXMT capacity-share risk), not ASP-premised — flat-within-basis ASP does not conflict with WATCH. Direction: **no_action**. New CXMT risk-production news (qualification-stage, ~1yr ahead of 2027 consensus) reinforces the existing structural rationale for WATCH rather than creating any tension to resolve.

**SKHY (SK Hynix, direct HBM producer, 2.23% weight — not on the named MU/EWY/DRAM list but included as the underlying primary HBM allocation holder):**
- Same HBM3E flat-within-basis read applies. Status is strengthening; flat (not falling) ASP creates no verdict conflict (this would only be a tension if ASP were falling against a strengthening thesis).
- Verdict conflict: none. Direction: **no_action**. The CXMT qualification-stage catalyst is logged as a fresh risk (evidence_against, above) but is not yet reflected in supplier pricing per smith-catalyst's own magnitude note, so no status change is warranted this run.

No EWY or DRAM ETF positions currently held (EWY stopped out 2026-08-06 per open_flags; still watchlisted).

## 5. Data quality
- FMP `valuation` ref not present in this run's slice — no ROIC/WACC forensic override applicable this run.
- HBM price data is 32 days stale (last priced point 2026-08-05); structural/supply data (CXMT, allocation) is fresh (2026-09-01/09-06) and weighted accordingly.
- No fresh SOX/SMH co-movement check possible — market closed (Labor Day), signals' rel-strength refresh skipped this run (caches within TTL).
- Insider-cluster check (GEV/ASML/BE/MRVL/VRT) was a small inline finding handed in-run, not independently re-verified via secFilings this pass — treated as sourced but unaudited beyond the Form 4 citation given.
- 10 status-only tickers (thesis_tiering) retain prior full text in state.json; only GEV/MRVL/BE/VRT/MU/SKHY/ASML got fresh evidence this run per the Wave-1 handoffs and insider findings.

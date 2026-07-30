# Thesis & Factor — 2026-07-30 quick sweep

## 1. Thesis table — status CHANGES only (quick mode)

| TICKER | Thesis | Verdict | Evidence (post 2026-07-29) |
|---|---|---|---|
| BE | On-site fuel-cell power for AI datacenters (Oracle/Brookfield partnerships, $20B backlog) | STRENGTHENING (new classification, was Unclassified) | Q2 beat 07-28: rev $1.07B, EPS $0.78 vs est, FY guide raised, JPM PT hike; stock +25.6% today on the print, part of broad relief rally |
| GLW | Optical fiber/connectivity + specialty glass for AI datacenter interconnect and hyperscaler supply deals (Nvidia partnership) | WATCH (new classification, was Unclassified; had a prior thesis before 07-24 exit — not carried forward, treated as fresh re-entry) | Q2 beat (core EPS +30%) but weak Q3 guidance drove a >50% drawdown from June peak (07-28); today's +5.4% is a bounce off that guide-down, not new confirming news |
| MKSI | Semicap vacuum/laser/photonics & process-control tools — picks-and-shovels on leading-edge + memory fab capex | INTACT (new classification, was Unclassified; no news since Feb-2026 earnings beat) | No news in the watermark window; +12% today tracks the broad SOX/SMH relief rally, not name-specific evidence |

**Rest of book (23 names): unchanged.** No verdict changes for NVDA/ASML/GEV/CLS/DRAM/VRT/AVGO/MRVL/EWY/CIEN/QCOM/TER/TSM/MU/SNDK/AMAT/COHR/ARM/AMD/ORCL/GOOGL/NBIS/IREN. ASML/MU/SNDK/EWY/DRAM remain WATCH — see Q6 answer below; today's rally is not treated as thesis-confirming evidence.

**Data quality note:** LRCX appears in the prior thesis/sector map but is NOT in today's 26-name holdings snapshot — position appears closed. Recommend orchestrator prune LRCX from persistent maps if confirmed exited.

## 2. Factor cluster table (26-name book, weights sum ≈100% of equity; cash hedge ~45.8% is separate/not shown here)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | NVDA, ASML, TER, AMAT, QCOM, TSM, ARM, AMD, MKSI | 32.46% |
| AI Memory/Storage | MU, SNDK, EWY, DRAM | 24.90% |
| AI Networking/Optics | MRVL, AVGO, CIEN, COHR, GLW | 17.96% |
| Compute/Hyperscaler | GOOGL, ORCL, CLS, NBIS, IREN | 15.61% |
| AI Power/Cooling/DC Infra | GEV, VRT, BE | 9.08% |
| **Combined AI-capex chain** | all 26 names | **~100%** |

Co-movement check: SMH +6.91% intraday; ASML +6.6%, MU +14.0%, SNDK +21.0%, MKSI +12.0%, GLW +5.4%, BE +25.6% (idiosyncratic earnings on top of the beta move) — nearly every cluster name moved with the SOX/SMH tape today, confirming this is a single, broadly-correlated factor bounce, not stock-specific dispersion.

## 3. Single-factor risk verdict

This is effectively one bet. 100% of the equity sleeve sits inside the AI-capex chain (semis/fabs, memory, optics, hyperscaler compute, power/cooling) — a datacenter-capex pause or a memory-pricing air-pocket hits the entire book at once, not a diversifiable slice of it. The only structurally uncorrelated capital is the ~45.8% cash hedge sitting outside the equity sleeve (per last known state) — there is no uncorrelated equity slice; even the "power infra" (GEV/VRT/BE) and "hyperscaler" (GOOGL/ORCL) legs are AI-capex demand-side and supply-side exposures to the same cycle, just at different points in the value chain.

## 4. HBMTracker reconciliation (Memory-cluster names held: MU, SNDK, EWY, DRAM)

**Tension 1 — HBM3E ASP decline vs Memory verdicts.** Latest HBM3E ASP (2026-07-19 row, HBMTracker/history.json): $8–10/GB (mid $9), down from H1-2025 peak $17–20/GB (mid $18.5, 2025-06-30 row) — a **-51% decline**. No verdict conflict currently exists: MU/SNDK/EWY/DRAM are already WATCH, not strengthening, so the book's stated verdicts are consistent with the ASP damage. Reconciliation: HBM2e/HBM3/HBM3e capacity is reported **sold out through 2026** (volume, not price, is doing the work — MU printed +345.7% revenue growth 07-29 on record shipments), and TrendForce (2026-06-02) forecasts 2027 HBM contract prices to surge **80–150%** as tight supply hands Samsung/SK Hynix/Micron pricing power back — an asymmetric, timing-dependent upside if it lands, but not yet priced or contracted (2027 negotiations were "stalled" as of the bulletin). CXMT's domestic HBM3 ramp remains the standing downside risk keeping these at WATCH rather than STRENGTHENING; its timeline is disputed (2026 vs 2027) and unresolved by today's rally.

**Tension 2 — DDR5/HBM3e profitability crossover (2026-04-21, TrendForce).** Server DDR5 contract-price profitability exceeded HBM3e for the first time — a structural first. Combined with the HBM3e:DDR5 price-ratio narrowing from 4-5x (2Q25) toward 1-2x (end-2026 forecast), this signals commoditization pressure on the HBM segment specifically, separate from the CXMT threat. No immediate verdict action — flagged for the next deep review to check whether it starts showing up in MU/SNDK segment margins.

## 6. Does today's rally undo the ASML/MU/SNDK "watch" thesis (CXMT/China DRAM)?

No — read this as a technical relief bounce, not a thesis reversal. Nothing in the post-07-29 news for ASML, MU, or SNDK addresses or resolves the CXMT/China-DRAM threat: ASML's 07-29 item still flags "strategic risks in China," and MU/SNDK news is earnings- and demand-driven (Musk/Tesla allocation, record revenue) with no update on CXMT's IPO ramp or DUV mass-production timeline. The move is consistent with SMH's broad +6.91% snap-back after a 3-day, VIX-elevated selloff (20.66→18.23) — high-beta names (MU +14%, SNDK +21%, ASML +6.6%) simply moved hardest in both directions. Verdicts held at WATCH deliberately; upgrading to strengthening would require actual news that shrinks the CXMT/DUV threat, not just a price recovery.

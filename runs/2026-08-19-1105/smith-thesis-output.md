# smith-thesis — 2026-08-19 (quick)

## 1. Thesis table — CHANGES ONLY (28 held; rest unchanged, "intact/as-carried, no new evidence")

**EXITED (7, remove from active thesis map, archive):** ARM, SNDK, DRAM, IONQ, NBIS, ORCL, SKHY — none appear in current holdings; IONQ's 2026-08-17 unbanded-cluster flag is now moot (position fully closed) and can be closed.

**MU — Micron Technology** — thesis: Memory (DRAM/HBM); WATCH is CXMT structural/capacity-driven, NOT ASP-driven. Status: **WATCH (unchanged)**. verified: unverified (no new discrete corporate event this run).
- evidence_for: [1] "HBM3E stack-derived $9.00/GB flat 07-19→08-05 (0.0% trend_within_basis); corrected -51% figure (C1) stays dead" (HBMTracker, 2026-08-05); [2] "2027 HBM contract prices forecast +80-150%; DRAM tight supply favors Samsung/SK Hynix/Micron" (HBMTracker/TrendForce, 2026-06-02)
- evidence_against: [1] "CXMT projected to close DRAM wafer-capacity gap to ~25k WSPM by end-2026 vs Micron 375k; Q1'26 share 8% vs ~3% YoY" (smith-catalyst 2026-08-16); [2] "HBM4 Vera Rubin allocation: SK Hynix 60-70%, Samsung 25-30%, Micron single-digit-to-low-teens residual — MU is qualified but structurally thin on the live ramp even as pricing rises" (HBMTracker supply_structure, as_of 2026-06-05)
- Position cut 2.5sh→0.5sh (dust-level) was a **stop-loss/sizing event**, not a thesis downgrade.

## 2. Factor cluster table (% of equity)
| Cluster | Tickers | % |
|---|---|---|
| AI Semis/Fabs | NVDA,TSM,ASML,QCOM,LRCX,AMD,AMAT,INTC,TER | 40.51 |
| AI Power/Cooling/DC Infra | GEV,BE,VRT,CEG | 14.91 |
| AI Networking/Optics | COHR,MRVL,CIEN,AVGO,GLW | 12.81 |
| Compute/Hyperscaler | AMZN,MSFT,IREN | 12.82 |
| Compute/Hyperscaler OEM | CLS | 4.15 |
| AI Memory/Storage | MU | 1.57 |
| **AI-capex chain total** | | **86.77 (≈86.8)** |
| Analog/Industrial Semis | STM,TXN | 6.22 |
| Diversified/Regional ETF | FLTW | 3.33 |
| Enterprise Software | NOW | 2.79 |
| China Internet/Diversifier | BABA | 0.86 |

Co-movement check: no numeric SMH multi-day series available this run (quick-mode budget); qualitatively, KOSPI's Wed -5.48% memory-led fall is consistent with sector-beta selling across the AI-capex complex broadly, but this is unverified against SMH specifically — flagged as a gap, not asserted as fact.

## 3. Single-factor risk verdict
This is effectively one bet. AI-capex exposure is 86.8% of equity across six clusters that all draw from the same capex cycle (fabs, memory, optics, power/cooling, hyperscaler compute, hyperscaler OEM) — a datacenter-capex pause hits ~87% of the book at once regardless of the sector labels. The largest genuinely uncorrelated slice is Analog/Industrial Semis (STM+TXN, 6.22%) — TXN is explicitly the lowest-beta name in the book (0.599 vs SMH) — but even this pair carries general semis-cyclical correlation, not true independence. FLTW (3.33%) is nominally "diversified" but is a Taiwan-tech index proximate to TSM/AI-semis, not a real diversifier. BABA (0.86%) is the only position built as an intentional uncorrelated diversifier, and it's under 1% of book. With BX (the last sizeable genuine non-AI-capex sleeve) exited 2026-08-17, there is no meaningful counterweight left.

## 4. HBMTracker reconciliation — THE STRUCTURAL QUESTION
**Verdict: stopped out, not broken.** MU's live thesis status was never ASP-driven — its WATCH is explicitly CXMT-competitive/capacity risk. The last verified pricing point (2026-08-05, HBMTracker consumer_view.json, **14 days stale as of today, still <30d threshold**) shows HBM3E **flat** within the stack-derived basis (0.0% trend 07-19→08-05, not falling), the earlier -51% "decline" remains a dead basis-splice artifact (correction C1, checked), and the 2027 forecast is +80-150% higher contract prices (TrendForce, DDR5>HBM3E profitability crossover 2026-04-21). Nothing in the tracker supports a broken thesis. What actually happened: EWY and DRAM (ETF) were fully stopped out in the 2026-08-06 cascade (G51, price-driven, not thesis-driven) and MU was cut to dust alongside broad book de-risking — a sizing/stop event, consistent with this book's tight-SL discipline, not a fundamental call.

Caveat (do not skip): Wednesday's KOSPI -5.48% memory-led fall **postdates** the 08-05 snapshot and is an **equity-index** move, not a HBM contract $/GB datapoint — I cannot attribute it to new negative contract-pricing information without a tracker refresh. Treated as a data gap, not a basis for a thesis change this run (branch (c) considered explicitly).

Re-entry implication: if HBM/memory exposure is re-added, note the allocation-share fact from supply_structure — SK Hynix (60-70%) and Samsung (25-30%) capture most of the Vera Rubin HBM4 ramp; Micron's share is residual/single-digit-to-low-teens. MU is not the highest-torque vehicle for this thesis even though the underlying pricing case is intact; EWY (Samsung+SK Hynix ~43.6% combined) was structurally closer to the ramp but is also currently stopped out.

## Data quality
- HBMTracker snapshot 14 days stale (last_run 2026-08-05 vs today 2026-08-19); within threshold but weight accordingly, esp. vs the un-reconciled KOSPI move.
- HBM4 $12.00/GB point is a source-spread splice (correction C2, suspect_band=true) — not a genuine price move.
- EWY/DRAM not currently held (exited 08-06 cascade); scope limited HBM reconciliation to MU only per task rules.
- Quick-mode news budget: spent zero new fetches this run — relied on carried-forward evidence sufficient to answer the structural question.
- Ticker/name cross-check: 28/28 holdings match sector_map, no mismatches found.
- IONQ's open unbanded-cluster flag (2026-08-17) is moot — position fully exited this run.

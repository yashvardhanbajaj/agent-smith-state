# Thesis & Factor — Quick Sweep, 2026-07-27 (pre-open, STABILIZING)

## Retired (exited 2026-07-24, reconciled today — historical record kept, not deleted)
- GLW — Optical fiber/connectivity for DC interconnect | was strengthening
- NBIS — Emerging AI-cloud/neocloud GPU-as-a-service | was watch
- IREN — Bitcoin-mining infra pivoted to AI/GPU cloud | was strengthening
(No fresh "why sold" news pulled — accepted gap G26, this is the persisted book catching up to a known event, not new activity.)

## Thesis table — status changes only (quick mode)
- **MU — Micron Technology, Inc.** — Memory (DRAM/HBM) re-buy — **STRENGTHENING → WATCH** — HBM3E ASP down 51% from H1'25 peak ($18.5/GB) to latest read ($9/GB, 2026-07-19, Silicon Analysts); DDR5 contract profitability crossed above HBM3E for the first time (TrendForce, 2026-04-21). Sold-out-through-2026 capacity is a real volume offset, but a 51% ASP move is too large to still call "strengthening." See HBM reconciliation below.

Rest unchanged (19 names, name field verified against holdings row — no mismatches found): NVDA, ASML, GEV, CLS, DRAM, VRT, AVGO, MRVL, EWY, CIEN, QCOM, LRCX, TER, TSM, SNDK, AMAT, COHR, ARM, AMD, ORCL. Only ORCL (07-26: $7B DoD contract, still "poor S&P performer" amid debt/AI-capex-spend concerns) and SNDK (07-26: ~40% pullback but Strong Buy consensus, AI demand cited) had news after the 2026-07-24 watermark — both reaffirm existing WATCH framing, no verdict change.

## Factor cluster table (% of invested equity; source: compute_drift.json, exact policy cluster names)
| Cluster | Tickers | % of book | Band | Status |
|---|---|---|---|---|
| AI Semis/Fabs | NVDA,ASML,LRCX,AMAT,TER,QCOM,TSM,AMD,ARM | 38.7% | 25-35 | BREACH high |
| AI Memory/Storage | MU,SNDK,DRAM,EWY | 26.3% | 15-25 | BREACH high |
| AI Networking/Optics | MRVL,AVGO,CIEN,COHR | 15.2% | 15-25 | in-band |
| AI Power/Cooling/DC Infra | GEV,VRT | 13.0% | 10-20 | in-band |
| Compute/Hyperscaler OEM | CLS | 4.4% | 0-10 | in-band |
| Compute/Hyperscaler | ORCL | 2.4% | 5-15 | BREACH low (lone name since GLW/NBIS/IREN exit) |

Combined AI-capex chain (all six clusters) = **100.0% of invested equity / 56.8% of total book** (cash 43.2%, itself a policy breach vs 3-15% band).

Flag: every invested dollar sits in the AI-capex chain. A datacenter-capex pause hits 100% of equity at once — 56.8% of the total book including cash. Co-movement check: 2026-07-25 session — GEV -1.6%, MRVL -7.2%, EWY -6.3%, ARM -8.1%, ORCL -4.2%, SNDK -10.8%, CIEN -4.1% — all five clusters fell together same day, consistent with one shared macro driver (AI-capex sentiment) rather than idiosyncratic moves.

## Single-factor risk verdict
Effectively one bet wearing six cluster labels. Semis/Fabs, Memory/Storage, Networking/Optics, Power/Infra, and both Hyperscaler sleeves all key off the same variable — hyperscaler AI-capex continuing at pace — and the 2026-07-25 lockstep decline is the tell. The only genuinely uncorrelated slice is the 43.2% cash position (above policy band), which is the real diversifier right now, not any equity holding. Within equities, EWY (Korea/FX-specific) and ORCL (balance-sheet/credit-risk-driven) are the closest things to a second factor, but both still resolve to the same AI-capex demand variable one step removed.

## HBMTracker reconciliation (Memory-cluster names held: MU, SNDK, DRAM, EWY)
- **Metric: HBM3E ASP.** Current: $8-10/GB (mid $9), as of 2026-07-19 (Silicon Analysts). Peak: $17-20/GB (mid $18.5), as of 2025-06-30 (H1'25 peak). **Decline: -51%.**
- **Verdict conflict:** MU held "strengthening" against a 51% ASP collapse — downgraded to WATCH above.
- **Reconciliation:** (a) Demand offset is real and documented — HBM2e/HBM3/HBM3e capacity "sold out through 2026, fully allocated to AI GPU/ASIC customers" (2026-07-19), plus HBM4 ramp from ~Q3 2026 (some estimates put 2026 mix near 55% HBM4/45% HBM3E) — volume may be cushioning revenue even as ASP falls. (b) Forward catalyst: TrendForce (2026-06-02) forecasts 2027 HBM contract prices to surge **80-150%** as tight DRAM supply hands Samsung/SK Hynix/Micron pricing power back — but 2027 negotiations were described as "stalled" as of that bulletin; timing-dependent, not banked.
- **Profitability crossover:** TrendForce (2026-04-21) confirmed server DDR5 contract-price profitability surpassed HBM3E for the first time — structurally pressures the HBM premium DRAM makers have relied on.
- **Net:** SNDK and EWY were already WATCH (consistent with the ASP data). DRAM (Roundhill Memory ETF) stays INTACT — its thesis is volume/demand-based, not ASP-based — but flag for next-run review alongside MU. MU: downgraded to WATCH this run; the size of the ASP move outweighs the sold-out-capacity offset until FQ4 numbers confirm the mix shift is protecting margin.

## Data quality
- HBM3E figures are analyst-estimate ranges (no exchange spot market exists) — directional, not precise.
- G19 (ETF-constituent tool blocked) carried forward — EWY/DRAM classified by prior sector_map, not fresh constituents.
- G1, G26, G3 carried forward unchanged, no new gaps this run.
- Budget: 3 tool calls used (1 news batch + 2 local reads), well under cap.

```json
{"thesis":{"changed":{"MU":"Memory (DRAM/HBM), real re-buy after dust period | watch"},"unchanged_count":20},
 "retired":{"GLW":"exited 2026-07-24, reconciled 2026-07-27, was strengthening","NBIS":"exited 2026-07-24, reconciled 2026-07-27, was watch","IREN":"exited 2026-07-24, reconciled 2026-07-27, was strengthening"},
 "sector_map":{"changed":{},"unchanged_count":21},
 "etf_constituents_updates":{},
 "ai_capex_pct":100.0,
 "factor_flags":["AI Semis/Fabs 38.7% breach vs [25,35]","AI Memory/Storage 26.3% breach vs [15,25]","Compute/Hyperscaler 2.4% under-band vs [5,15], lone name ORCL post-exit","100% of invested equity / 56.8% of total book in AI-capex chain"],
 "thesis_tensions":[{"metric":"hbm3e_asp_usd_per_gb","current_value":9,"peak_value":18.5,"peak_as_of":"2025-06-30","current_as_of":"2026-07-19","decline_pct":-51,"verdict_conflict":"MU held as strengthening while HBM3E ASP down 51% from H1'25 peak","reconciliation":"Downgraded MU to WATCH this run; sold-out-through-2026 capacity + HBM4 mix ramp offer a volume offset, and TrendForce forecasts 80-150% 2027 contract price surge, but the 2026-04-21 DDR5-over-HBM3E profitability crossover structurally pressures the near-term HBM premium"}],
 "data_quality":["HBM3E figures are analyst-estimate ranges, not exchange spot — directional only","G19 ETF-constituent tool still blocked, EWY/DRAM classified by carried-forward sector_map"]}
```

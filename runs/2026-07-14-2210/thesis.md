# Thesis & Factor — Quick Sweep 2026-07-14

## 1. Thesis table — CHANGED names only (quick mode)

| Ticker | Thesis | Verdict | Evidence |
|---|---|---|---|
| VRT | Thermal/power management (cooling, UPS) for AI datacenters | STRENGTHENING (RE-ENTERED) | Prior run's "EXITED 07-14" was mechanical/technical, not a thesis break, as noted. Position is back (3sh). Since then: named top data-center stock (77% Buy ratings, $353-416 targets, 07-10), Nvidia collaboration on datacenter power systems, ThermoKey acquisition closed, Malaysia plant opened for AI-infra demand (07-01/07-02). Re-open confirmed, thesis reaffirmed. |
| MU | Memory (DRAM/HBM) — AI/HBM demand | STRENGTHENING (RE-BUY) | Prior "dust remainder, closed in substance" (0.0004sh) is stale — now a real 2.0sh position. Record Q3 earnings (+346% rev), $250B US investment plan through 2035, Ford automotive-memory supply deal, stock +5.72% today on demand/upgrades. Brief 07-08 "bear market" dip (-27% off highs, valuation/oversupply concerns) was noise, not thesis-breaking — no fundamental deterioration. |
| SNDK | NAND memory, AI memory optionality | WATCH (RE-EXITED) | Prior run (07-13/07-14) called this "a real 7.4% position after sustained accumulation" — now back to dust (0.008sh), exited again intraday. WHIPSAW FLAG: built up over weeks, 07-13 earnings beat (+251% rev) produced a -12.6% intraday whiplash despite the beat, followed by this exit. No bearish fundamental news — pattern reads as position-sizing/technical churn around an intact-to-strong thesis, not a thesis break. Treat future re-entries cautiously pending a stable holding period. |

**Rest unchanged (19 names, no material change since last run):** TSM, LRCX, NOW, QCOM, AVGO, DRAM, CQQQ, MRVL, CIEN, ASML, CLS, GEV, AMAT, STM, NBIS, CRDO, NVDA, GLW, TER — all intact/strengthening/watch as previously assessed, no new evidence found in narrow news check that changes verdicts. Note: CIEN (AI PoC win w/ Telefónica, strong AI-driven fiber demand — strengthening), NBIS (Meta cloud competition weighing on stock 07-01 but Nasdaq-100 inclusion + Nvidia/Microsoft partnerships intact — still watch), NOW (still down hard YTD on AI-cannibalization fear narrative vs. its own $1.5B Now Assist AI-revenue target — still watch, unresolved tension), EWY (bouncing +5.61% today off the Korea selloff lows — still watch, one day of recovery doesn't clear the drawdown flag). ETN, ANET, DLR remain absent from book — left as EXITED, no change.

## 2. Factor cluster table

| Cluster | Tickers | % of book |
|---|---|---|
| Compute/Hyperscaler (foundry, GPU, custom silicon, diversified semis) | TSM, NVDA, AVGO, QCOM, STM | 25.05% |
| Semicap (fab/test equipment) | LRCX, ASML, AMAT, TER | 18.11% |
| Semi-memory (DRAM/NAND/HBM) | MU, SNDK, DRAM | 15.76% |
| Optical/interconnect | CIEN, MRVL, CRDO, GLW | 13.27% |
| Power-infra (cooling, UPS, grid) | VRT, GEV | 10.77% |
| Regional memory-adjacent ETF (Samsung/SK Hynix via Korea) | EWY | 6.37% |
| Neocloud/AI-cloud infra | NBIS | 4.47% |
| EMS/AI hardware assembly | CLS | 1.23% |
| Enterprise SaaS (AI-monetization angle, not capex chain) | NOW | 3.00% |
| China tech/internet diversifier | CQQQ | 1.97% |

**Combined AI-capex chain (compute+semicap+memory+optics+power+neocloud+EMS+EWY): ~95.0% of book.**

Co-movement check: MU (+5.7%), SNDK (+6.5%), EWY (+5.6%) all moved up together today alongside broad chip-sector strength — consistent with a single macro/sector factor (AI-capex sentiment) driving most of the book at once, not idiosyncratic stories.

## 3. Single-factor risk verdict

This book is effectively one bet. ~95% of holdings sit somewhere in the AI-datacenter capex chain — compute silicon, the equipment that makes the silicon, the memory that feeds it, the optics that connect it, and the power/cooling that runs it — plus a regional ETF (EWY) whose real exposure is Samsung/SK Hynix memory and a neocloud name (NBIS) that only exists because of the same capex cycle. A pause or disappointment in hyperscaler AI capital spending would hit nearly the entire book simultaneously, as today's synchronized up-move in MU/SNDK/EWY illustrates the reverse case. The only genuinely uncorrelated slice is NOW + CQQQ at ~5.0% of the book combined — and even NOW carries its own AI-disruption narrative risk (software-margin cannibalization fear), so the true diversifying sliver is closer to CQQQ alone (~2%). There is no meaningful hedge against a capex-cycle drawdown currently in this book.

```json
{"thesis":{"changed":{"VRT":"Thermal/power management (cooling, UPS) for AI datacenters | strengthening","MU":"Memory (DRAM/HBM), real re-buy after dust period, AI/HBM demand | strengthening","SNDK":"NAND memory, AI memory optionality -- re-exited to dust after 07-13 earnings-beat whipsaw (+251% rev, -12.6% intraday); whipsaw pattern flagged, no fundamental break | watch"},"unchanged_count":19},
 "sector_map":{"changed":{},"unchanged_count":23},
 "etf_constituents_updates":{},
 "ai_capex_pct":95.0,"factor_flags":["Combined AI-capex chain (compute/semicap/memory/optics/power/neocloud/EMS/EWY) = ~95% of book -- a datacenter-capex pause or sentiment reversal hits nearly the whole book at once","Only ~5% of book (NOW+CQQQ) sits outside the AI-capex chain, and even NOW carries its own AI-disruption narrative risk"],"data_quality":["SNDK whipsaw: built to 'real position' status then back to dust twice within 24-48h with no bearish fundamental news -- likely position-sizing/technical churn, flagged for future re-entry caution","VRT/MU/SNDK/CIEN/NBIS/EWY were the only names given fresh news checks this run per narrow news budget; remaining 17 defaulted to 'no new evidence -- intact/unchanged'"]}
```

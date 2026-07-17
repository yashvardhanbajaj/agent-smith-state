# Thesis & Factor — Quick Sweep, 2026-07-15

## Thesis table (quick mode — status CHANGED names only; watermark 2026-07-14)

- **SNDK** — NAND memory, AI memory optionality — **WATCH** — Third position flip in 48h (real 1.008sh -> dust 0.008sh -> real 1.008sh re-buy today). No post-watermark news explains the re-entry specifically; latest dated news is the 07-13 earnings beat (+251% rev, -12.6% intraday whipsaw) already known. Today's price is +5.01% (pre-mkt +5%, then -1.99% ext-hrs), consistent with continued technical churn riding memory-sector momentum (SK Hynix Nasdaq debut 07-10, EWY +5.3% today) rather than a fresh fundamental catalyst. Treat as technical whipsaw, not re-conviction — flag for strategist as unstable, do not size up.

**Rest unchanged (22 names):** NVDA, ASML, GLW, GEV, STM, CLS, DRAM, NOW, VRT, AVGO, MRVL, EWY, CIEN, QCOM, LRCX, TER, CRDO, TSM, CQQQ, MU, AMAT, NBIS — no evidence crossing the watermark that changes verdict. Checked news for NOW/CIEN/EWY/NBIS (prior WATCH + today's movers): NOW -5.76% today but most recent news is 07-13 (AI Now-Assist optimism) — no new negative catalyst, stays WATCH. CIEN news is all pre-watermark (07-07 Telefónica AI PoC, positive) — stays WATCH, no fresh evidence. NBIS -7.8% today but news is pre-watermark (Meta competition, 07-01) — stays WATCH, no new catalyst. EWY +5.33% today (SK Hynix Nasdaq-debut-adjacent bounce) but no news items returned and the underlying KOSPI/Hormuz downgrade thesis is unaddressed — stays WATCH, bounce is not thesis repair.

## Factor cluster table (% of book, 23 holdings)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | TSM, NVDA, ASML, LRCX, QCOM, TER, STM, AMAT | 39.27% |
| AI Memory/Storage | DRAM, MU, SNDK, EWY | 26.82% |
| AI Networking/Optics | GLW, MRVL, CIEN, CRDO, AVGO | 13.77% |
| AI Power/Cooling/DC Infra | GEV, VRT | 10.12% |
| Compute/Hyperscaler OEM | NBIS, CLS | 5.36% |
| Diversified/Regional ETF | CQQQ | 1.85% |
| Enterprise Software | NOW | 2.82% |

**Combined AI-capex chain (Semis+Memory+Optics+Power-infra+Hyperscaler-OEM): 95.33% of book.** Only 4.67% (CQQQ + NOW) sits outside the AI-capex chain, and even those two carry AI-adjacent exposure (CQQQ holds China AI-semi names Hua Hong/Cambricon/NAURA; NOW's bull case is AI-agent monetization).

The two clusters named in this run's brief — AI Semis/Fabs (39.27%) + AI Memory/Storage (26.82%) — sum to **66.09% of book alone**, before adding optics/power/hyperscaler. Note also literal name overlap, not just factor overlap: EWY (in Memory/Storage) and DRAM ETF both hold SK Hynix + Samsung Electronics directly — two "different" tickers, same underlying memory-cycle bet.

Co-movement check: SMH +2.51%, SOXX +2.58% today. Memory-heavy names outperformed the index move (SNDK +5.01%, EWY +5.33%, both riding SK Hynix's Nasdaq-listing momentum) — consistent with the cluster trading as one beta, amplified. The two names that moved against the grain (NOW -5.76%, NBIS -7.8%) are exactly the two names classified outside the core Semis/Memory clusters, on idiosyncratic news (AI-software-disruption fear for NOW, Meta-competition fear for NBIS) rather than SOX-linked moves — reinforcing that the cluster/non-cluster split is the real fault line in today's dispersion.

## Single-factor risk verdict

This book is effectively one bet. 95.3% of holdings sit somewhere in the AI-datacenter-capex chain (chips, memory, optics, power, and the OEMs/hyperclouds that assemble it), and the two largest clusters alone (Semis/Fabs + Memory/Storage) already account for two-thirds of the book — with direct underlying-name duplication between EWY and DRAM compounding it further. A pause or air-pocket in hyperscaler AI capex spending would hit the large majority of this portfolio simultaneously and with correlated severity, not a diversified spread of idiosyncratic outcomes. The largest genuinely uncorrelated slice is CQQQ (1.85%, China-tech/internet demand and regulatory cycle, though it still carries some China-semi capex exposure) — practically negligible as a hedge. NOW (2.82%, enterprise SaaS) is the next-most-independent name but is increasingly narrating itself as an AI-monetization story too, so its diversification value is eroding, not improving. There is no meaningful non-AI-capex ballast in this book at current sizing.

```json
{"thesis":{"changed":{"SNDK":"NAND memory, AI memory optionality -- THIRD flip in 48h (real->dust->real, re-bought today ~1.008sh); no post-watermark fundamental catalyst found, price +5.01% tracks memory-sector momentum (SK Hynix Nasdaq debut) not new news; treat as unstable technical churn, not re-conviction | watch"},"unchanged_count":22},
 "sector_map":{"changed":{},"unchanged_count":23},
 "etf_constituents_updates":{},
 "ai_capex_pct":95.33,"factor_flags":["Combined AI-capex chain (Semis/Fabs+Memory/Storage+Networking/Optics+Power-infra+Hyperscaler-OEM) = 95.33% of book -- effectively a single-factor bet","AI Semis/Fabs + AI Memory/Storage alone = 66.09% of book","EWY and DRAM hold overlapping underlying names (SK Hynix, Samsung Electronics) -- factor overlap understates true concentration"],"data_quality":["SNDK 3rd flip in 48h: no news item post-watermark (2026-07-14) directly explains today's re-buy; price-momentum inference only, not confirmed catalyst","EWY: no news items returned by get_us_stocks_details despite +5.33% move; move attributed qualitatively to SK Hynix Nasdaq-listing spillover, unconfirmed by text","Ticker/name sanity check: all 23 holdings' resolved names matched expected companies/funds this run -- no mismatch flags needed (per G-incident 2026-07-13 protocol)"]}
```

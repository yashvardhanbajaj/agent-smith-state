# smith-thesis — 2026-09-22-0926Z (quick, pre-open)

## 1. Thesis table

### Changed / first-look this run

**STM** — WATCH (unchanged). Analog/industrial semis; Q2 beat but Q3 guide_below_consensus WATCH stands. Position increased +5sh to 20sh (2.74% of equity, src: holdings_trim, as_of 2026-09-21) — a sizing decision, not new thesis evidence; no fresh company-specific catalyst found this run beyond the known Q2 print.
- FOR: Q2 2026 rev $3.49B beat $3.47B, EPS $0.31 beat $0.27 (2026-07-23, stockanalysis.com); peer-laggard flag resolved, rel_sigma -0.9 (2026-09-14, smith-signals); Q2 print calls out an AWS-partnership-linked datacenter revenue line, not previously captured (2026-09-22, smith-catalyst/Yahoo Finance).
- AGAINST: Q3 guide $3.7B is guide_below_consensus vs Street $3.78B, stock -15-17% post-print (2026-07-23, stockanalysis.com); position increased same window no fresh catalyst found — same add-ahead-of-resolution pattern flagged on AMZN/AMD/NBIS (2026-09-21/22, holdings_trim + smith-catalyst).
- verified: primary (stockanalysis.com/stocks/STM, 2026-08-12, carried forward).

**LLY** — INTACT (first read; new position, 0.5sh, 1.54%, src: holdings_trim as_of 2026-09-21). Non-AI-capex pharma diversifier: GLP-1 franchise (Mounjaro, Zepbound).
- FOR: Q2 2026 revenue +48% YoY, FY26 guidance raised to $85-87B (2026-09-09/08-31, INDmoney news); analyst consensus 90.5% Buy (n=21), mean target $1,325.39 vs $1,164.89 close, +12.1% upside (2026-09-22, INDmoney); multiple FDA approvals/pipeline advances and a $6.5bn Houston manufacturing expansion in the two weeks before purchase (2026-08-26 to 09-21, INDmoney news).
- AGAINST: GLP-1 competitive intensity and pricing pressure repeatedly cited Aug-Sep, stock pulled back from record highs multiple times on rival/market news (2026-09-07/08, INDmoney news); rich valuation (PE ~38.5x, no independent quality check run this cycle) (2026-09-22, INDmoney); one day of history on this book — next earnings 2026-10-29 is the first real test (2026-09-22).
- verified: secondary (INDmoney news+analyst / stockanalysis.com/stocks/LLY, 2026-09-22). peer_map corrected to XLV by smith-signals this run (was defaulting to SMH).

### Rest unchanged (25 of 27)
Live price triggers fired on **AMD, COHR, GLW, LITE, MU, SKHY** — all checked against this run's catalyst/signals tails and held unchanged: AMD watch (09-21 breakout is momentum, guide_below_consensus/08-12 refusal unresolved), COHR strengthening, GLW watch (ATM usage still undisclosed), LITE strengthening, MU watch (CXMT structural, not ASP), SKHY watch (HBM4 leader but starting-share, not moat). Gate's SMH +4.02% is Monday's already-priced close-to-close bar (premarket flat -0.69%, smith-catalyst gate check) — not treated as fresh evidence for any of them. Remaining 19 quiet names (ASML, GEV, VRT, AMAT, MSFT, AMZN, NBIS, CLS, WDC, AMZN-cluster peers, KLAC, COHR-peers, ALAB, APH, NOW, QCOM, TER, TSM, BE, GOOG, MRVL, CIEN) carried forward from 09-21, no new evidence found.

## 2. Factor cluster table (% of invested equity, holdings_trim snapshot)
| Cluster | Tickers | % |
|---|---|---|
| AI Semis/Fabs | TSM, ASML, TER, AMAT, KLAC, QCOM, AMD | 34.78 |
| Compute/Hyperscaler | GOOG, MSFT, NBIS, AMZN | 16.67 |
| AI Networking/Optics | APH, MRVL, ALAB, LITE, COHR, GLW, CIEN | 16.29 |
| AI Power/Cooling/DC Infra | GEV, VRT, BE | 11.81 |
| AI Memory/Storage | MU, SKHY | 6.91 |
| Compute/Hyperscaler OEM | CLS | 3.55 |
| AI Storage/HDD | WDC | 3.49 |
| Analog/Industrial Semis | STM | 2.74 |
| Enterprise Software | NOW | 2.22 |
| **Pharma/GLP-1 (new)** | **LLY** | **1.54** |

**AI-capex chain (Semis/Fabs+Memory+Optics+Power+Hyperscaler+OEM+Storage) = 93.5% of invested equity.** Sanity check: cluster co-movement to SMH is dispersed, not synchronized — AMD rel_sigma +2.93 vs SMH today while ASML -1.23 and AMAT -1.42 (smith-signals vol_normalization); same tailwind, different day-to-day beta.

## 3. Single-factor risk
This remains effectively a single macro bet on AI-capex continuing: 93.5% of invested equity sits across seven clusters that all live or die on the same hyperscaler/AI-datacenter spending cycle, and today's biggest apparent tailwind (SMH +4.02%) is confirmed stale, not fresh confirmation. The only genuinely uncorrelated slice is new and small: LLY (1.54%, GLP-1 pharma, XLV-benchmarked) plus STM (2.74%, analog/industrial — still semis-cyclical but a different end market) and NOW (2.22%, enterprise SaaS) sum to ~6.5% outside the AI-capex chain. A datacenter-capex pause hits roughly 19 of 20 dollars in this book at once; the STM/LLY adds are a real but marginal diversification step, not a hedge.

## 4. HBMTracker reconciliation (MU, SKHY)
Tracker unchanged since the 2026-09-20 run (generation prices up to 5 days stale); no new datapoint this run — carried forward, not re-derived.
- **MU**: HBM3E $12.4/GB and HBM4 $16.0/GB (both 2026-09-20, contract_quote, tier1-corroborated) are each single points in their basis — `cross_basis_change_is_meaningless=true`, no within-basis trend exists. Verdict conflict: thesis WATCH (CXMT structural share risk) vs. no ASP signal either way. **direction: no_action** — WATCH rests on CXMT qualification-sample progress and HBM4 allocation thinness, not price. HBM3 stack-derived flat 0.0% (07-19→09-15) is a *different generation*, not evidence for HBM3E. Corrections C1/C2 checked (both resolved basis-splice artifacts). Next hard datapoint: FQ4 print 2026-10-01.
- **SKHY**: HBM4 (SKHY's 60-70% Vera Rubin share) prints a ~29% per-GB premium over HBM3E on the same date/basis (16.0 vs 12.4, 2026-09-20) — a real, dated allocation-capture fact. Verdict conflict: thesis WATCH (Samsung/Micron now also HBM4-certified, so 60-70% is a starting share, not a moat) vs. a positive price/allocation fact. **direction: no_action** — both prints are single points, so this is a level comparison, not a price move; the WATCH is about durability past this ramp, which the price level doesn't resolve either way. Corrections C1/C2 checked.
- Forward context (unchanged): DDR5 > HBM3E profitability crossover (2026-04-21, TrendForce); 2027 HBM contract prices forecast +70-140% (2026-08-25, TrendForce) — directional tailwind, not yet in any contract print.

Output file: /Users/yb/Claude/AgentSmith/runs/2026-09-22-0926Z/smith-thesis-output.md
JSON tail: /Users/yb/Claude/AgentSmith/runs/2026-09-22-0926Z/out_thesis.json

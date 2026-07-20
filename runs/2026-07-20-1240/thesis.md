# Thesis & Factor — 2026-07-20 (deep) — watermark 2026-07-18

## Thesis table (full, deep mode; news budget narrow — 8 WATCH names checked)
| Ticker | Thesis | Verdict | Evidence |
|---|---|---|---|
| SNDK | AI NAND/enterprise-SSD supercycle bet | STRENGTHENING | No news post-07-18; sector (SMH/SOXX) down ~5-6% last wk on rotation, not idiosyncratic. |
| GLW | Optical fiber/connectivity for DC interconnect buildout | STRENGTHENING | No new evidence — intact by default. |
| DRAM | Thematic memory ETF (Samsung/SK Hynix/Micron/WDC/SNDK/Kioxia + swaps) | INTACT | Confirmed genuine memory basket; note: ~45% notional is T-bill/cash collateral backing TRS swaps — leveraged structure, not spot. |
| NVDA | Core AI GPU/accelerator platform leadership | STRENGTHENING | No new evidence — intact by default. |
| TSM | Foundry monopoly manufacturing leading-edge AI chips | STRENGTHENING | No new evidence — intact by default. |
| ASML | Sole-source EUV lithography gating leading-edge fab capacity | STRENGTHENING | No new evidence — intact by default. |
| MU | Memory (DRAM/HBM) re-buy | STRENGTHENING | No new evidence — intact by default. |
| EWY | Regional Korea ETF, semis/memory (Samsung, SK Hynix) exposure | WATCH | Constituent check: SK Hynix 23.2%+Samsung Elec 21.7%=44.9% of fund; remaining ~55% is broad Korea equity (financials/autos/chem) — see data quality. |
| LRCX | Semicap WFE geared to leading-edge/memory capex | STRENGTHENING | No new evidence — intact by default. |
| CLS | EMS building Broadcom/OpenAI custom ASICs + AI servers | STRENGTHENING | No new evidence — intact by default. |
| VRT | Thermal/power mgmt for AI datacenters | STRENGTHENING | No new evidence — intact by default. |
| MRVL | Custom AI silicon + optical interconnect for hyperscalers | WATCH | Selloff (07-16) on hyperscaler-capex fear despite record Q1 rev + raised guidance; fundamentals intact, sentiment/capex-headline risk is the live issue. No post-07-18 news. |
| META | Llama models + aggressive AI-capex hyperscaler | STRENGTHENING | No new evidence — intact by default. |
| CIEN | Optical networking for AI DC/telco backbone | WATCH | Insider selling flagged (07-15); Q2 beat but soft FY outlook (06-23) still the live overhang. No post-07-18 news; today's -3.7% tracks broad SOXX weakness. |
| NBIS | Neocloud GPU-as-a-service infra | WATCH | $775M debt financing for AI-cloud expansion (07-17, pre-watermark); Meta cloud competitive threat unresolved. No post-07-18 news. |
| AMAT | Semicap deposition/etch for AI fabs | STRENGTHENING | No new evidence — intact by default. |
| QCOM | Diversifying handsets→AI/datacenter CPU, auto | STRENGTHENING | No new evidence — intact by default. |
| AMD | GPU/CPU compute, direct NVDA accelerator competitor | STRENGTHENING | No new evidence — intact by default. |
| TER | Semicap ATE geared to AI chip test volume | STRENGTHENING | No new evidence — intact by default. |
| IREN | Bitcoin-mining infra pivoted to AI/GPU cloud | WATCH | Microsoft/Nvidia AI contracts + Jefferies buy init (late Jun, pre-watermark) vs governance concerns (07-02) unresolved. No post-07-18 news; today's -3.5% tracks sector. |
| COHR | Photonics/optical components for DC interconnect | STRENGTHENING | No new evidence — intact by default. |
| AVGO | Custom AI ASICs (XPUs) + networking silicon for hyperscalers | STRENGTHENING | No new evidence — intact by default. |
| LITE | Optical transceivers for AI DC interconnect | STRENGTHENING | No new evidence — intact by default. |
| GOOG | Google Cloud/TPU/Gemini hyperscaler | WATCH | No news items returned; today's -2.2% tracks broad tech/semis-adjacent selloff, not stock-specific. No post-07-18 evidence either way. |
| STM | Diversified semis, emerging AI/DC power exposure | STRENGTHENING | No new evidence — intact by default. |
| ARM | Chip architecture/IP licensing powering AI silicon | WATCH | Mixed analyst calls (HSBC cut vs KeyBanc raise, 07-14), Cramer trust exit (07-08); FQ1 earnings 07-29 is the next real catalyst. No post-07-18 news. |
| ORCL | OCI — hyperscaler cloud/AI-capex beneficiary | WATCH | Debt/credit-downgrade concerns persist alongside record $638B RPO backlog (07-14/15, pre-watermark). No post-07-18 news. |
| NOW | Enterprise SaaS + AI-agent monetization angle | WATCH | Q2 earnings 07-22 is the pending catalyst; no post-07-18 news. |
| GEV | (dust — cut 07-16, weight 0.002%) | CLOSED | Effectively closed; excluded from thesis/factor tracking going forward. |

## Factor cluster table (% of book, cluster names match policy.json exactly)
| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | NVDA,ASML,LRCX,AMAT,TER,STM,QCOM,TSM,AMD,ARM | 34.33% |
| AI Memory/Storage | MU,SNDK,EWY,DRAM | 25.81% |
| AI Networking/Optics | MRVL,AVGO,CIEN,GLW,LITE,COHR | 20.15% |
| Compute/Hyperscaler | ORCL,IREN,GOOG,META | 8.57% |
| Compute/Hyperscaler OEM | CLS,NBIS | 6.62% |
| AI Power/Cooling/DC Infra | VRT | 3.72% |
| Enterprise Software | NOW | 0.80% |
| (dust, unclassified) | GEV | 0.00% |

Combined AI-capex chain (all clusters above except Enterprise Software + dust) = **99.20%** of book — unchanged from last run (holdings identical since 07-17). Confirmed breach of the 90% cap, still the worst/highest reading logged. Practical meaning: a datacenter-capex pause or hyperscaler guidance cut hits ~99% of the book simultaneously — there is effectively no diversification against that single macro event. AI Semis/Fabs at 34.33% sits at the top edge of the [25,35] policy band, technically still inside it but with zero room left.

Co-movement sanity check: SMH -4.97% and SOXX -5.74% over the 07-13→07-17 window (yfinance daily). Today's (07-20 pre-open) moves in book names — CIEN -3.7%, IREN -3.5%, GOOG -2.2% down; ARM +2.0%, NBIS +3.5%, ORCL +1.8% up — are a mixed bag, consistent with broad factor/rotation noise rather than a coordinated single-name breakdown. No thesis in this book broke on the week; the drawdown is macro/factor-driven, which is precisely the risk the AI-capex concentration figure is meant to capture.

## Single-factor risk verdict
This book is, in every load-bearing sense, one bet: ~99.2% of assets sit somewhere in the AI-capex value chain (chip design, foundry, memory, semicap, optics, power/cooling, or hyperscaler capex itself), and the largest single cluster (AI Semis/Fabs, 34.3%) is already pressed against its policy ceiling. The only genuinely uncorrelated slice is NOW (0.8%, enterprise SaaS with its own idiosyncratic AI-monetization risk, not capex-cycle risk) — economically negligible as a hedge. EWY nominally sits in "AI Memory/Storage" but only ~45% of its NAV (SK Hynix + Samsung Electronics) is true memory exposure; the rest is broad Korean-economy beta (autos, financials, chemicals) — a partial, accidental diversifier rather than a designed one, and not large enough to change the concentration picture. Bottom line: a hyperscaler capex pause, a memory-price air-pocket, or a broad semis de-rating (as happened 07-13→07-17, -5 to -6% on SMH/SOXX) moves nearly the entire book together. There is no meaningful uncorrelated ballast in this portfolio today.

## Data quality
- EWY: only SK Hynix (23.2%) + Samsung Electronics (21.7%) = 44.9% of fund NAV is genuine memory/semis; remaining ~55% is broad Korea equity beta. Full-weight cluster tagging overstates pure memory exposure by ~2.3pp of book. Not reclassifying — flagging per ticker/name sanity-check protocol.
- DRAM: uses total-return swaps on MU/Samsung/SK Hynix + ~45% T-bill/cash collateral (negative "Cash & Other" line) — a leveraged/synthetic structure. Nominal 6.78% book weight may understate effective price-swing exposure to memory names.
- News budget: only the 8 prior-WATCH names got a news fetch (ARM, CIEN, NBIS, MRVL, IREN, GOOG, ORCL, NOW); all 21 INTACT/STRENGTHENING names default to "no new evidence" per budget rule — smith-signals covers full-book news separately.
- No news item for any of the 8 checked names post-dates the 07-18 watermark; all cited evidence is pre-watermark context carried forward, and today's price moves are treated as macro/factor noise, not thesis signal.
- G3 (INDmoney feed staleness) and G11 (Compute/Hyperscaler cluster line added to draft policy unconfirmed) both still open — see known_gaps registry.
- Holdings/weights unchanged since 07-17 run; AI-capex-chain % (99.2%) and AI Semis/Fabs % (34.3%) re-confirmed via fresh cluster-sum recompute, not just carried forward.

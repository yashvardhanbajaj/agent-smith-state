# Thesis & Factor — 2026-07-14 quick sweep (watermark 2026-07-13)

## 1. Thesis table — CHANGES ONLY (18 of 21 unchanged, see note)

| Ticker | Thesis | Verdict | Evidence |
|---|---|---|---|
| CLS (NEW, 1.4%) | EMS/contract manufacturer building Broadcom/OpenAI custom AI ASICs (Jalapeno program) + AI server hardware | STRENGTHENING | 24 Jun: shares +5% on Jalapeno reveal naming Celestica as build partner; 10 Jun: 2026 guide raised (sales +53.8%, EPS +67.9%); stock +191% TTM. First-run thesis, no red flags. |
| SNDK (7.4%, was 0.0%) | NAND memory, AI memory optionality — grown from dust to a real 7.4% position via sustained accumulation | WATCH (was intact) | 13 Jul: Q3 FY26 revenue +251% YoY (strong beat) yet stock -12.63% intraday (recovered +7% after-hours) — earnings-day whipsaw + hedge-fund profit-taking on a name up 635-858% YTD. Fundamental demand thesis intact/strengthening; flagging on valuation/volatility risk now that size is real. |
| MU (0.001%, dust) | Memory (DRAM/HBM) | CLOSED IN SUBSTANCE | 0.000365 sh after user's large sale — no longer economically meaningful; dropping from active watch tracking. |

**Escalation note (verdict unchanged):** EWY (7.3%, was WATCH) — KOSPI selloff continued, EWY -8.45% today (07-14) on top of the -8.95% 07-13 Iran/Hormuz-driven crash. Position has grown 6→10 sh despite the open watch flag; concentration risk is now material at this weight. Remains WATCH.

**Rest unchanged (16 names, intact/strengthening/watch per prior run, no new evidence crossing the watermark):** NVDA, ASML, GLW, GEV, STM, NOW (still WATCH — note: -8% after-hours today, likely earnings reaction, consistent with prior AI-agent-monetization watch flag), CIEN (still WATCH, soft-guidance concern unresolved), QCOM, LRCX, TER, CRDO, TSM, CQQQ, AMAT, NBIS (still WATCH, Meta-competition risk open), AVGO (STRENGTHENING — 09 Jul: Apple deal extended to 2031 ($30B) + Jalapeno AI chip launch w/ OpenAI reinforces thesis and partly offsets the Google-diversification watch note).

**Exits (no longer held, removed from thesis tracking):** ETN, ANET, DLR, VRT — all 4 were STRENGTHENING/no-flag names pre-exit; no news/technical trigger found for a coordinated exit. Flagged as orchestrator/user action, not thesis-driven.

## 2. Factor cluster table (% of invested book, sums to ~100%)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | NVDA, ASML, LRCX, AMAT, TER, STM, QCOM, TSM | 44.1% |
| AI Memory/Storage | MU, SNDK, EWY, DRAM | 24.8% |
| AI Networking/Optics | CIEN, CRDO, GLW, AVGO | 12.1% |
| AI Power/Cooling/DC Infra | GEV | 8.5% |
| Compute/Hyperscaler OEM | NBIS, CLS | 4.8% |
| Diversified/Regional ETF | CQQQ | 2.3% |
| Enterprise Software | NOW | 3.4% |

**Combined AI-capex chain (Semis+Memory+Networking+Power+OEM) = 94.3% of book vs 90% policy cap — BREACHED.** A datacenter-capex pause or AI-capex growth deceleration hits ~94% of the book at once. AI Semis/Fabs alone (44.1%) breaches its own [25,35] policy band — the ETN/ANET/DLR/VRT exits gutted Power/Infra (was 4 names, now just GEV at 8.5%, under band) and Networking (lost ANET, now 12.1%, under band), mechanically inflating Semis/Fabs' share without any new semis buying.

**Co-movement check:** on 07-13 (KOSPI/Iran-Hormuz selloff day), SMH fell with the broader tape and every AI Semis/Fabs holding sold off in tandem (NVDA, LRCX, AMAT, TER, TSM, STM, QCOM all down that session) — cluster trades as one instrument, confirming the concentration is real, not diversified-in-name-only.

**Look-through overlap flag:** DRAM ETF (10.1% of book) is swap/T-bill structured with ~25% Samsung + ~22% SK Hynix notional exposure plus direct SNDK/MU/WDC/STX/Kioxia stakes; EWY (7.3%) is ~47% Samsung+SK Hynix directly. These two "different" sleeves move on the same underlying names — true Korea-memory exposure exceeds the headline 24.8% Memory cluster weight.

## 3. Single-factor risk verdict

This is effectively a single-factor book. 94.3% of invested value sits somewhere in the AI-capex chain (chips, memory, networking, power, compute OEM), and the 07-13 session showed the AI Semis/Fabs cluster (44.1% alone) moving as one correlated block with SMH — there is no internal hedge here, only concentration. The 4 recent exits (ETN/ANET/DLR/VRT) removed the closest things to internal diversification the book had (grid/power-infra, REIT-adjacent datacenter names) and mechanically pushed Semis/Fabs over its policy band. The largest genuinely uncorrelated slice is NOW (Enterprise Software, 3.4%) — and even that name's narrative is tied to AI-agent monetization sentiment, so it's a weak hedge at best. CQQQ (2.3%, "Diversified/Regional") also carries meaningful China-semicap/component exposure internally, so it is not a clean diversifier either. Net: a genuine datacenter-capex pause or a memory-pricing/China-demand shock would hit the large majority of this book simultaneously.

```json
{"thesis":{"changed":{"CLS":"EMS/contract manufacturer building Broadcom/OpenAI custom AI ASICs (Jalapeno) + AI server hardware | strengthening","SNDK":"NAND memory, AI memory optionality — now a real 7.4% position after sustained accumulation, earnings-day whipsaw | watch","MU":"Memory (DRAM/HBM), dust remainder (0.000365 sh) after large user sale | closed in substance"},"unchanged_count":18},
 "sector_map":{"changed":{"CLS":"Compute/Hyperscaler OEM"},"unchanged_count":20},
 "etf_constituents_updates":{"DRAM":{"constituents":["T-Bill 07/14/26 27.5%","T-Bill 09/08/26 26.0%","Samsung Electronics 15.8%","SK Hynix 15.5%","First American Govt Oblig 14.8%","Micron swap 14.3%","Samsung swap 9.4%","Micron swap 9.0%","SK Hynix swap 6.6%","SNDK 4.9%"],"checked":"2026-07-14"},"EWY":{"constituents":["SK Hynix 25.1%","Samsung Electronics 22.2%","SK Square 4.0%","Samsung Electro-Mechanics 3.0%","KB Financial 2.1%","Hyundai Motor 1.8%","Shinhan Financial 1.5%","Hana Financial 1.2%","Kia Corp 1.2%","Doosan Enerbility 1.1%"],"checked":"2026-07-14"},"CQQQ":{"constituents":["PDD Holdings 9.7%","Meituan 9.4%","Tencent 9.3%","Baidu 8.1%","Kuaishou 4.4%","Hua Hong Semiconductor 4.4%","Kingboard Laminates 2.4%","Cambricon Tech 2.3%","Hygon Info Tech 2.2%","NAURA Tech 1.5%"],"checked":"2026-07-14"}},
 "ai_capex_pct":94.3,
 "factor_flags":["Combined AI-capex chain = 94.3% of book vs 90% cap — breach; a capex-pause hits ~94% of book at once","AI Semis/Fabs alone = 44.1% vs [25,35] band — breach, caused mechanically by ETN/ANET/DLR/VRT exits gutting Power/Infra and Networking, not fresh semis buying","AI Power/Cooling/DC Infra down to GEV alone (8.5%) — under band post-exits","AI Networking/Optics down to CIEN/CRDO/GLW/AVGO (12.1%) post-ANET exit — under band","DRAM ETF (10.1%) look-through is ~25% Samsung + ~22% SK Hynix swap exposure, correlating it with EWY (7.3%, 47% Samsung+SK Hynix) — real Korea-memory exposure exceeds headline weights","EWY -8.45% today on top of 07-13 KOSPI crash, position grown to 7.3% while still WATCH-flagged"],
 "data_quality":["CLS is a new holding, not in prior maps — verified ticker/name resolves to Celestica Inc. (EMS/AI-ASIC manufacturer), no mismatch found; classified Compute/Hyperscaler OEM by best fit (approximate — differs from NBIS's neocloud model)","ETF constituent sanity check passed for DRAM/EWY/CQQQ — resolved holdings match expected fund identity, no ticker mislabeling detected","4 exits (ETN/ANET/DLR/VRT) have no supporting news/technical trigger found — flagged as orchestrator/user action, not thesis-driven","News budget limited to prior-WATCH names (NOW, CIEN, NBIS, EWY, AVGO) + new name (CLS) + grown position (SNDK); remaining 15 'intact' names assumed unchanged per smith-signals coverage"]}
```

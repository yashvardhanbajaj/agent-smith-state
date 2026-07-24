# Thesis & Factor — 2026-07-24 QUICK sweep

## 1. Thesis table — status changes only (5 full exits)

| Ticker | Thesis | Verdict | Evidence |
|---|---|---|---|
| LITE | Optical transceivers/components for AI datacenter interconnect | EXITED 2026-07-24 | Full exit today, wallet-cash reconciled; prior status was strengthening — exit is a book decision, not a thesis break |
| META | Llama models + aggressive AI-capex hyperscaler | EXITED 2026-07-24 | Full exit today; prior status strengthening, no adverse news found |
| GOOG | Google Cloud/TPU/Gemini hyperscaler | EXITED 2026-07-24 | Full exit today; resolves standing open_flag on GOOG's 07-17 exit / 07-18 re-entry flip-flop — now cleanly out |
| BABA | China AI/cloud recovery: Alibaba Cloud + Qwen-Apple integration | EXITED 2026-07-24 | Full exit today; was the book's only non-AI-capex, non-ETF diversifier (China Consumer/Cloud) |
| STM | Diversified semis with emerging AI/datacenter power exposure | EXITED 2026-07-24 | Full exit today, coincides with -18.67% intraday crash (prev_close 65.77 -> 53.49) on/around its Q2 report (guided for 23-Jul); fetched news feed tops out 20-Jul (pre-earnings, still positive) so the crash trigger itself is unconfirmed by name — earnings miss/guide-down is the strong prior given timing |

**Rest of book (24 names): unchanged, "intact/strengthening/watch by default, no new evidence" — no status flips this run.**

### Trim-severity read (positions cut, not exited)
- **AMD** (2sh -> 1sh, -50%): Partial de-risking, not a thesis change. News flow is uniformly positive/strong (Anthropic $5B/2GW deal, Microsoft Azure partnership, Helios launch, analyst target raises) through 23-Jul. Reads as profit-taking into strength, not doubt. Verdict unchanged: strengthening.
- **QCOM** (14.0008sh -> 6.0008sh, -57%): Larger proportional cut than AMD. News is mixed — bullish long-term AI/data-center diversification (Meta CPU collab, $40B non-handset 2029 target) but also flags a "significant EPS decline" expected at the 29-Jul earnings print. Cut reads as de-risking ahead of a binary earnings event more than a thesis reversal. Verdict unchanged: strengthening, but earnings-date watch warranted.

## 2. Factor cluster table (24 remaining positions, ticker-count basis — no per-ticker $ weights in this run's input)

| Cluster | Tickers | Count |
|---|---|---|
| AI Semis/Fabs | NVDA, ASML, LRCX, AMAT, TER, QCOM, TSM, ARM, AMD | 9 |
| AI Memory/Storage | MU, SNDK, EWY, DRAM | 4 |
| AI Networking/Optics | MRVL, AVGO, CIEN, GLW, COHR | 5 |
| AI Power/Cooling/DC Infra | GEV, VRT | 2 |
| Compute/Hyperscaler OEM | CLS, NBIS | 2 |
| Compute/Hyperscaler | ORCL, IREN | 2 |

**Combined AI-capex exposure: 100.0% of the book** (policy.json compute, orchestrator-supplied, worst reading to date). Every one of the 24 remaining names sits in an AI-capex-chain cluster; the BABA exit removed the last non-AI-capex sleeve. Practical meaning: a datacenter-capex pause or AI-spend digestion scare hits 100% of the invested book at once — there is no offsetting sleeve to cushion that scenario.

Co-movement sanity check (qualitative, budget-constrained — no direct SOX/SMH pull this run): Thursday's broad tape was risk-off (SPX -1.21%, NDX -2.15%); pre-open AMD -2.29% and QCOM -2.57% both tracked that weakness before paring in extended hours, consistent with semis moving with the index rather than idiosyncratically.

## 3. Single-factor risk verdict

This is now, by construction, a single-bet book. With GOOG, META, BABA, LITE and STM all exited today, the last genuine diversifier (BABA's China Consumer/Cloud sleeve) is gone and the Compute/Hyperscaler cluster has shrunk to ORCL and IREN — both still AI-capex-chain names, not a different macro factor. Every remaining position — semis/fabs, memory, optics, power infra, and hyperscaler-adjacent compute — is a leveraged expression of the same thesis: AI datacenter capex keeps accelerating. The only genuinely uncorrelated slice left in the account is uninvested cash (wallet ~$5,657 post-exits), which is not a position, just dry powder. This is a meaningful concentration event worth flagging plainly to the strategist: any AI-capex digestion, hyperscaler guidance cut, or China/export-control shock now has no offset anywhere in the book.

```json
{"thesis":{"changed":{"LITE":"Optical transceivers/components for AI datacenter interconnect | EXITED 2026-07-24","META":"Llama models + aggressive AI-capex hyperscaler | EXITED 2026-07-24","GOOG":"Google Cloud/TPU/Gemini hyperscaler | EXITED 2026-07-24","BABA":"China AI/cloud recovery: Alibaba Cloud + Qwen-Apple integration, $53B AI/cloud capex pledge | EXITED 2026-07-24","STM":"Diversified semis with emerging AI/datacenter power exposure | EXITED 2026-07-24"},"unchanged_count":29},
 "sector_map":{"changed":{},"unchanged_count":29},
 "etf_constituents_updates":{},
 "ai_capex_pct":100.0,"factor_flags":["100% of remaining 24 positions sit in AI-capex-chain clusters (semis/fabs, memory, optics, power-infra, hyperscaler/OEM) after BABA exit removed the last diversifier sleeve","Compute/Hyperscaler cluster reduced to ORCL + IREN post GOOG/META exit — both still AI-capex-adjacent, not a distinct factor","QCOM trimmed 57% ahead of 29-Jul earnings (largest proportional cut this run) — earnings-date watch"],
 "data_quality":["STM's -18.67% crash exit coincides with its Q2 report window but fetched news tops out 20-Jul (pre-earnings, still positive) — exact trigger unconfirmed by name","Sector_map data shows IREN also tagged exact 'Compute/Hyperscaler' alongside ORCL; run brief stated cluster 'now only holds ORCL' — flagging the discrepancy rather than silently editing either the brief's claim or the map","No per-ticker $ weight table was in this run's input; cluster sizing above is ticker-count only, not portfolio-weight; the 100.0% ai_capex_pct figure is taken as orchestrator-supplied (policy.json compute), not independently recomputed","SOX/SMH co-movement check done qualitatively from SPX/NDX context only — no direct index pull this run (budget)","G19 carried forward unchanged: FMP etfAndMutualFunds still blocked on plan tier, EWY/DRAM ETF-constituent cache stale"]}
```

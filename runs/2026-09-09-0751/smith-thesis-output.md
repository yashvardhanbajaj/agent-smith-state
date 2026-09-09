# smith-thesis — 2026-09-09-0751 (quick)

## 1. Thesis table (changed only; rest unchanged)
- **VST** (NEW, 5sh @$153.25, 09-08) — AI-power/IPP: nuclear+gas generation monetizing hyperscaler DC electricity demand. **WATCH**.
  FOR: Peter Thiel disclosed $59M stake framed as AI-power-market position (src: INDmoney news, 2026-09-03); consensus Strong Buy, 16 analysts, mean target $217.42 = +30.2% upside (src: INDmoney analyst consensus, as_of 2026-09-09); Q2 JV with Helix strengthens market position (src: INDmoney news, 2026-08-16).
  AGAINST: Q2 2026 revenue ~$4B came in below expectations — reported-quarter signal, kept separate from guide (src: INDmoney news, 2026-08-24); stock -31% from 52-wk high $219.82 to $151.72 (src: INDmoney live quote, as_of 2026-09-09); officer disclosed $6.7M stock sale (src: INDmoney news, 2026-09-08); premium-P/E valuation concern despite strong Q2 (src: INDmoney news, 2026-08-16).
  verified: secondary (INDmoney news+analyst aggregation, as_of 2026-09-09). Sector: **AI Power/Cooling/DC Infra** (new sector_map entry).
- **NBIS** (trimmed 7→5sh, -2sh, 09-08) — status unchanged (WATCH). Added evidence: the trim partially resolves the 09-03 "sized up while WATCH unresolved" conviction/thesis tension flagged last run (src: holdings.json qty_changes, 2026-09-08); structural dilution/data-center concerns still unresolved.
- **INTC** (trimmed 15→11sh, -4sh, 09-08) — status unchanged (WATCH). Added evidence_against: trim is consistent with, not contradicting, the standing loss-making/valuation concerns (src: holdings.json qty_changes, 2026-09-08).
- **IREN** — fully exited 2026-09-08 (stop-loss, 20sh@$47.01). No thesis or sector_map entry existed for it in the current map; nothing to archive here. The 2026-08-12 open_flags "standing re-entry interest REMAINS OPEN" line is now stale post-exit — flagged for orchestrator/watchlist archival.
- **MU / BE**: qty changes noted (MU +0.5sh, BE -2sh) — both sub-share/minor relative to position size, no read-changing evidence found this run; theses unchanged.
- Rest of book (27 names): unchanged, no new evidence past 2026-09-08 watermark.

reviewed_unchanged this run: MU, NBIS, INTC (evidence re-examined, verdicts stand).

## 2. Factor cluster table (% of book, from holdings_trim weights)
| Cluster | Tickers | % |
|---|---|---|
| AI Semis/Fabs | NVDA,ASML,AMAT,TER,QCOM,TSM,AMD,LRCX,INTC,KLAC | 32.15 |
| AI Power/Cooling/DC Infra | GEV,VRT,BE,FSLR,**VST** | 21.14 |
| AI Networking/Optics | MRVL,AVGO,CIEN,GLW,COHR,LITE,ALAB,APH | 19.81 |
| AI Memory/Storage | MU,WDC,SKHY | 9.14 |
| Compute/Hyperscaler | MSFT,GOOG,NBIS,META | 9.44 |
| Compute/Hyperscaler OEM | CLS,SMCI | 4.06 |
| Analog/Industrial Semis | STM | 4.29 |

## 3. Single-factor risk
AI-capex chain (all clusters except Analog/Industrial) = **95.7%** of book; STM (4.29%) is the only genuinely uncorrelated slice, and even its thesis partly cites AI-datacenter optics demand. A datacenter-capex pause hits ~96% of the book at once. Co-movement check (qualitative, no fresh fetch this run): cluster names have historically tracked SOX/SMH beta; STM remains the book's worst SMH-relative laggard (-15.48pp, 08-12 read).

## 4. HBMTracker reconciliation
HBM-sensitive holdings currently held: **MU only** (EWY not held; DRAM ETF cache says currently_held:true but is NOT in this run's holdings_trim — flagging as stale cache, data_quality). max_price_staleness_days=33 (>30) — treating price read as stale, weighting reconciliation with caution.
- Metric: HBM3E $/GB, stack_derived basis, latest 9.0 (2026-08-05), trend_within_basis_pct 0.0 (2026-07-19→08-05) — **flat**, not the phantom -51% figure (see corrections C1/C2, checked).
- Verdict conflict: **none**. MU's WATCH is explicitly CXMT structural/capacity risk, not an ASP call — flat-within-basis ASP does not contradict it. Direction: no_action.
- Supply structure: MU is qualified but structurally thin on HBM4 Vera Rubin allocation (SK Hynix 60-70%, Samsung 25-30%, Micron residual single-digit-to-low-teens) — a rising HBM4 ASP does not flow to MU proportionally.
- Forward context: DDR5 > HBM3E profitability crossover (2026-04-21 TrendForce); 2027 HBM contract prices forecast +80-150% (2026-06-02 TrendForce).

## Data quality
- DRAM ETF cache (as_of 2026-08-07) marked currently_held:true but absent from this run's holdings_trim — stale, needs refresh/correction next ETF-cache touch.
- IREN open_flags "standing re-entry interest" (opened 2026-08-12) is stale post full-exit 2026-09-08; recommend archival.
- TXN (STM/TXN provisional-cluster open_flag, 2026-08-12) no longer appears in holdings_trim — likely exited; the "smith-thesis owes a first thesis" ask on TXN is probably moot, unconfirmed.
- No fresh SOX/SMH co-movement fetch this run (quick-mode budget); qualitative carry-forward only.

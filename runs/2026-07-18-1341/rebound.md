AI-capex 99.2% total-book (99.3% stock-only, cap 90%) — gate: ESCALATING

| Ticker | Δ% | Support | Action | Size | Gate | Tag |
|---|---|---|---|---|---|---|
| META | -2.79% | $637.31 ($613.57) | average | $500 | stage_in | MACRO_DRIVEN |
| VRT | -1.55% | $239.61 ($239.61) | extend | $600 | stage_in | IDIO_WEAK |
| TSM | -2.77% | $391.56 ($350.02) | average | $300 | stage_in | MACRO_DRIVEN |
| GLW | -2.39% | $131.61 ($131.61) | average | $350 | stage_in | IDIO_WEAK |
| AVGO | -0.97% | $361.81 ($361.81) | average | $250 | stage_in | MACRO_DRIVEN |

STAY-OUT: GOOG[WATCH_THESIS] ORCL[WATCH_THESIS] NOW[WATCH_THESIS] MRVL[WATCH_THESIS] ARM[WATCH_THESIS] IREN[WATCH_THESIS] SNDK[WATCH_THESIS] AMAT[INSIDER_SELL] GEV[WATCH_THESIS] EWY[WATCH_THESIS] CIEN[WATCH_THESIS] NBIS[WATCH_THESIS] MU[CLUSTER_FULL] LRCX[CLUSTER_FULL] CLS[THIN_DIP] STM[CLUSTER_FULL] CQQQ[IDIO_WEAK]

```json
{"basis":{"total_book_usd":44873.02,"stock_usd":44849.74,"wallet_usd":23.28,"ai_capex_pct_total_book":99.23,"ai_capex_pct_stock":99.28,"ai_capex_cap_pct":90},
 "gate":{"classification":"escalating","vix_chg_pct":12.2,"es_pct":-1.06,"nq_pct":-1.55,"news_call_used":false},
 "sl_forensics":[
   {"ticker":"CQQQ","action":"exit","qty_change":-10,"est_price":53.01,"current_price":50.32,"delta_pct":-5.07,"cluster_peer_median_delta_pct":-1.21,"classifier":"idio_weak"},
   {"ticker":"STM","action":"trim","qty_change":-5,"est_price":62.77,"current_price":62.06,"delta_pct":-1.13,"cluster_peer_median_delta_pct":-1.13,"classifier":"macro_driven"}
 ],
 "proposals":[
   {"ticker":"META","action":"average","size_usd":500,"current_price":646.01,"support_usd":637.31,"secondary_support_usd":613.57,"support_source":"live","headroom_usd_total_book":4132,"gate":"stage_in","tags":["macro_driven"],"rationale":"deepest dip of the eligible set, tracked Compute/Hyperscaler peer median (-2.17%) within 0.6pp, strengthening thesis, no flag"},
   {"ticker":"VRT","action":"extend","size_usd":600,"current_price":289.56,"support_usd":239.61,"secondary_support_usd":239.61,"support_source":"live","headroom_usd_total_book":3779,"gate":"stage_in","tags":["idio_weak"],"rationale":"cluster hugely underweight (3.58% vs 10-20% band) but only in-book peer is GEV, a dust position -- IDIO_WEAK read is low-confidence"},
   {"ticker":"TSM","action":"average","size_usd":300,"current_price":398.37,"support_usd":391.56,"secondary_support_usd":350.02,"support_source":"live","headroom_usd_total_book":1319,"gate":"stage_in","tags":["macro_driven"],"rationale":"tracked Semis/Fabs peer median (-1.13%) within 1.7pp, cluster near ceiling so sizing capped small"},
   {"ticker":"GLW","action":"average","size_usd":350,"current_price":154.61,"support_usd":131.61,"secondary_support_usd":131.61,"support_source":"live","headroom_usd_total_book":1761,"gate":"stage_in","tags":["idio_weak"],"rationale":"borderline 2.6pp worse than Networking/Optics peer median, just outside macro band, thesis still strengthening"},
   {"ticker":"AVGO","action":"average","size_usd":250,"current_price":370.83,"support_usd":361.81,"secondary_support_usd":361.81,"support_source":"live","headroom_usd_total_book":1804,"gate":"stage_in","tags":["macro_driven"],"rationale":"tracked Networking/Optics peer median within 1.2pp, shares cluster headroom with GLW"}
 ],
 "considered_excluded":[
   {"ticker":"MU","reason":"cluster_full"},
   {"ticker":"LRCX","reason":"cluster_full"},
   {"ticker":"CLS","reason":"thin_dip"}
 ],
 "data_quality":[
   "policy.json confirmed:false, as_of 2026-07-12 -- cluster bands/caps used as-is, not yet user-confirmed",
   "Compute/Hyperscaler cluster (GOOG/META/ORCL/IREN, 7.95% of book) has no band defined in policy.json cluster_targets -- META's headroom computed on the 12% single-position cap only, no cluster ceiling to check against",
   "VRT/GLW/AVGO: only one Barchart MA (the 200-day) sits below live price, so secondary_support_usd = support_usd per rule G -- low-confidence, thin technical cushion",
   "CLS trades below all 5 Barchart MAs (broken trend) -- support computed as price-2xATR ($251.34); per rule G this is a soft stay-out for rebuy despite a strengthening thesis and no open flag, so it was swapped out of the top-5 for AVGO",
   "CQQQ has no surviving in-book cluster peer (Diversified/Regional ETF cluster now empty after this exit) -- classifier fell back to SPX/NDX median (-1.21%) as a mismatched proxy; literal read is IDIO_WEAK but the -5.07% move plausibly reflects Asia/Hormuz-linked regional risk-off (same theme separately flagged for EWY's thesis), not company/ETF-specific weakness",
   "STM's 5sh trim (~$310 notional) closely matches the ~$400 partial trim the strategist explicitly proposed on 2026-07-17 for cluster-full/laggard reasons, and its -1.13% Friday move tracked the Semis/Fabs peer median (-1.13%) almost exactly -- reads as executed deliberate rebalancing, not a stop-loss cascade",
   "AI Semis/Fabs (32.06% vs [25,35] band) and AI Memory/Storage (27.93% vs [15,25] band, over ceiling) both sit at or over policy limits -- MU and LRCX were attractive dips but excluded from sizing as CLUSTER_FULL",
   "Real buys this session (not exits/trims, out of rule A scope): SNDK +1sh, GLW +4sh, CLS +2sh, VRT +2sh, CIEN +0.39sh, IREN +10sh, META +1sh, plus GOOG re-entered 0->2sh (was exited 07-17) -- all already reflected in current holdings/weights used above",
   "Wallet is de minimis this run ($23.28, 0.05% of book) -- total-book and stock-only bases are nearly identical",
   "AMD and STM's cluster peer-median for the classifier used AI Semis/Fabs (NVDA,ASML,LRCX,AMAT,TER,QCOM,AMD,ARM), correctly excluding MU which sits in AI Memory/Storage per sector_map"
 ]}
```

AI-capex 75.5% total-book (100.0% stock-only, cap 100%) — gate: ESCALATING, no SL activity vs last snapshot

| Ticker | Δ% | Support | Action | Size | Gate | Tag |
|---|---|---|---|---|---|---|
| AMD | -8.15% | $390.18 ($306.65) | average | $400 | stage_in | IDIO_WEAK |
| AMAT | -7.82% | $457.11 ($367.65) | average | $300 | stage_in | IDIO_WEAK |
| VRT | -6.27% | $244.20 ($244.20) | average | $65 | stage_in | MACRO_DRIVEN,THIN_DIP |
| GEV | -5.34% | $827.41 ($827.41) | average | $250 | stage_in | MACRO_DRIVEN |
| TER | -4.22% | $284.79 ($284.79) | average | $300 | stage_in | MACRO_DRIVEN |

STAY-OUT: ASML[WATCH_THESIS,OVERBOUGHT] DRAM[WATCH_THESIS,OVERBOUGHT] MRVL[WATCH_THESIS,OVERBOUGHT] SNDK[WATCH_THESIS,OVERBOUGHT] COHR[OVERBOUGHT] EWY[WATCH_THESIS] CIEN[WATCH_THESIS] MU[WATCH_THESIS] ARM[WATCH_THESIS] ORCL[WATCH_THESIS] NBIS[WATCH_THESIS] IREN[WATCH_THESIS] GOOGL[WATCH_THESIS]

```json
{"basis":{"total_book_usd":38373.64,"stock_usd":28982.27,"wallet_usd":9391.37,"ai_capex_pct_total_book":75.527,"ai_capex_pct_stock":100.0,"ai_capex_cap_pct":100},
 "gate":{"classification":"escalating","vix_chg_pct":-0.05,"es_pct":0.27,"nq_pct":0.04,"news_call_used":false},
 "sl_forensics":[],
 "proposals":[
   {"ticker":"AMD","action":"average","size_usd":400,"current_price":454.62,"support_usd":390.18,"secondary_support_usd":306.65,"support_source":"live","headroom_usd_total_book":4150.22,"gate":"stage_in","tags":["idio_weak"],"rationale":"deepest dip -8.15% vs AI Semis/Fabs peer median -4.22%, thesis strengthening, no open flag"},
   {"ticker":"AMAT","action":"average","size_usd":300,"current_price":476.46,"support_usd":457.11,"secondary_support_usd":367.65,"support_source":"live","headroom_usd_total_book":4124.48,"gate":"stage_in","tags":["idio_weak"],"rationale":"-7.82% vs Semis/Fabs peer median -4.22%, thesis strengthening"},
   {"ticker":"VRT","action":"average","size_usd":65,"current_price":269.56,"support_usd":244.20,"secondary_support_usd":244.20,"support_source":"live","headroom_usd_total_book":3257.04,"gate":"stage_in","tags":["macro_driven","thin_dip"],"rationale":"-6.27% close to Power cluster median -5.81%; only $137 room to constant-risk position cap, sized small"},
   {"ticker":"GEV","action":"average","size_usd":250,"current_price":943.38,"support_usd":827.41,"secondary_support_usd":827.41,"support_source":"live","headroom_usd_total_book":3656.79,"gate":"stage_in","tags":["macro_driven"],"rationale":"-5.34% close to Power cluster median -5.81%, thesis strengthening"},
   {"ticker":"TER","action":"average","size_usd":300,"current_price":320.65,"support_usd":284.79,"secondary_support_usd":284.79,"support_source":"live","headroom_usd_total_book":4283.31,"gate":"stage_in","tags":["macro_driven"],"rationale":"-4.22% in line with Semis/Fabs peer median, thesis strengthening"}
 ],
 "considered_excluded":[
   {"ticker":"COHR","reason":"risk_cap_breach"},
   {"ticker":"QCOM","reason":"earnings_today_rank_cutoff"}
 ],
 "data_quality":[
   "MU qty 1.000365376->2.000365376 (ratio 1.9996) flagged likely_corporate_action by compute_book.json; excluded from SL forensics, not treated as a buy or an exit/trim.",
   "GOOGL carries an open_flags entry (ticker-swap identity confirmation, opened 2026-07-28) -- tagged WATCH_THESIS as closest vocabulary fit though the flag is administrative (confirm intentional vs broker substitution), not a thesis break; stay-out applied per rule C's letter.",
   "COHR tagged OVERBOUGHT as closest vocabulary fit for a risk-cap breach (1.18-1.19x its 0.5%-of-book constant-risk position cap per open_flags RISK-CAPS note, and -10.31% vs AI Networking/Optics peer median -7.43% = IDIO_WEAK by rule B), not a technical overextension signal -- excluded from rebuy despite deepest dip in book.",
   "QCOM (Delta -4.21%, earnings today alongside FOMC) narrowly missed the Top-5 cutoff behind TER (Delta -4.22%); excluded by rank/binary-event timing, not a stay-out flag.",
   "policy.json confirmed:false -- cluster/position figures used as-is per skill rules.",
   "Support levels from live Barchart fetch this run; rebound_prime.json cache dated 2026-07-17 (not today), so not reused per step-0 staleness rule.",
   "VRT/GEV/TER: only the 200-day MA sits below live price (5/20/50/100-day all above) -- secondary_support_usd set equal to primary per rule G single-MA-below case.",
   "networth_holdings/networth_snapshot skipped this run per dispatch instruction -- runs/2026-07-29-1435/holdings.json (yfinance, cross-validated vs INDmoney aggregate to 0.212%) used as ground truth; INDmoney per-position feed flagged stale up to 39% this run.",
   "Gate classification ESCALATING taken as given from dispatch/market_inputs.json (v2 rule: SMH -3.45% + KOSPI -5.98%); this differs from the VIX/ES/NQ-only v1 threshold in this agent's own D rule, which alone would have read STABILIZING (VIX -0.05%, ES +0.27%, NQ +0.04%) -- known v1-vs-v2 divergence per state.json G30, v2 (orchestrator-supplied) takes precedence."
 ]}
```

AI-capex 55.1% total-book (79.1% stock-only, cap 100%) — gate: ESCALATING

| Ticker | Δ% | Support | Action | Size | Gate | Tag |
|---|---|---|---|---|---|---|
| NVDA | -2.1% | $206.63 ($205.97) | stay_out | — | wait | MACRO_DRIVEN |
| NBIS | -4.3% | — | stay_out | — | wait | WATCH_THESIS,IDIO_WEAK |
| SKHY | -4.3% | $149.62 ($149.62) | rebuy | $1,500 | stage_in | MACRO_DRIVEN |
| MRVL | -3.6% | — | stay_out | — | wait | INSIDER_SELL |
| AMAT | -2.0% | $394.75 ($394.75) | extend | $900 | stage_in | MACRO_DRIVEN |
| BE | +2.6% | — | stay_out | — | wait | CLUSTER_FULL |
| GLW | -3.0% | $140.23 ($140.23) | average | $1,200 | stage_in | MACRO_DRIVEN |
| LRCX | -2.3% | $253.05 ($253.05) | average | $1,000 | stage_in | MACRO_DRIVEN |
| MU | -6.2% | — | stay_out | — | wait | WATCH_THESIS |

STAY-OUT: NVDA[MACRO_DRIVEN] NBIS[WATCH_THESIS,IDIO_WEAK] MRVL[INSIDER_SELL] BE[CLUSTER_FULL] MU[WATCH_THESIS]

```json
{"basis":{"total_book_usd":40929.38,"stock_usd":28498.36,"wallet_usd":12431.02,"ai_capex_pct_total_book":55.09,"ai_capex_pct_stock":79.12,"ai_capex_cap_pct":100},
 "gate":{"classification":"escalating","vix_chg_pct":5.02,"es_pct":-0.33,"nq_pct":-1.02,"worst_asia_pct":null,"worst_asia_index":"unspecified (this morning's pre-market baseline term, session closed, not re-fetched)","smh_pct":-2.64,"orchestrator_gate":"escalating","downgrade_blocked":false,"news_call_used":false},
 "sl_forensics":[
  {"ticker":"NVDA","action":"exit","qty_change":-15,"est_price":214.72,"current_price":210.18,"delta_pct":-2.11,"cluster_peer_median_delta_pct":-2.40,"classifier":"macro_driven"},
  {"ticker":"NBIS","action":"exit","qty_change":-7,"est_price":219.13,"current_price":209.60,"delta_pct":-4.35,"cluster_peer_median_delta_pct":1.40,"classifier":"idio_weak"},
  {"ticker":"SKHY","action":"exit","qty_change":-5,"est_price":163.41,"current_price":156.31,"delta_pct":-4.34,"cluster_peer_median_delta_pct":-5.89,"classifier":"macro_driven"},
  {"ticker":"MRVL","action":"trim","qty_change":-6,"est_price":237.04,"current_price":228.58,"delta_pct":-3.57,"cluster_peer_median_delta_pct":-2.99,"classifier":"macro_driven"},
  {"ticker":"AMAT","action":"trim","qty_change":-2.0,"est_price":492.32,"current_price":482.54,"delta_pct":-1.99,"cluster_peer_median_delta_pct":-2.40,"classifier":"macro_driven"},
  {"ticker":"BE","action":"trim","qty_change":-2,"est_price":201.45,"current_price":206.71,"delta_pct":2.61,"cluster_peer_median_delta_pct":-1.49,"classifier":"macro_driven"},
  {"ticker":"GLW","action":"trim","qty_change":-3,"est_price":149.84,"current_price":145.36,"delta_pct":-2.99,"cluster_peer_median_delta_pct":-3.57,"classifier":"macro_driven"},
  {"ticker":"LRCX","action":"trim","qty_change":-1,"est_price":314.00,"current_price":306.65,"delta_pct":-2.34,"cluster_peer_median_delta_pct":-2.40,"classifier":"macro_driven"},
  {"ticker":"MU","action":"trim","qty_change":-1.0,"est_price":966.78,"current_price":906.76,"delta_pct":-6.21,"cluster_peer_median_delta_pct":-4.96,"classifier":"macro_driven"}
 ],
 "proposals":[
  {"ticker":"NVDA","action":"stay_out","size_usd":0,"current_price":210.18,"support_usd":206.63,"secondary_support_usd":205.97,"support_source":"live","headroom_usd_total_book":4911.53,"gate":"wait","tags":["macro_driven"],"rationale":"macro-driven exit in line with Semis peers, but 08-26 earnings in 2 days -- an earnings gap easily exceeds the stop's 2xATR distance, making same-week re-entry a near-certain re-stop regardless of print outcome; wait for post-print or a confirmed gate downgrade"},
  {"ticker":"NBIS","action":"stay_out","size_usd":0,"current_price":209.60,"support_usd":0,"secondary_support_usd":0,"support_source":"live","headroom_usd_total_book":0,"gate":"wait","tags":["watch_thesis","idio_weak"],"rationale":"idiosyncratic weak vs Compute/Hyperscaler peers (AMZN/MSFT both up today); dilutive convertible + Vineland DC concerns still open per WATCH thesis"},
  {"ticker":"SKHY","action":"rebuy","size_usd":1500,"current_price":156.31,"support_usd":149.62,"secondary_support_usd":149.62,"support_source":"live","headroom_usd_total_book":2686.48,"gate":"stage_in","tags":["macro_driven"],"rationale":"macro-driven, in line with Memory cluster peers; STRENGTHENING thesis (best-positioned HBM4 allocation), clean stop on broad weakness not a company event"},
  {"ticker":"MRVL","action":"stay_out","size_usd":0,"current_price":228.58,"support_usd":0,"secondary_support_usd":0,"support_source":"live","headroom_usd_total_book":0,"gate":"wait","tags":["insider_sell"],"rationale":"CEO insider selling flagged 08-18 ahead of the 08-27 print, position already stop-cut 75% today -- company-specific caution, not a dip to buy 3 days before earnings"},
  {"ticker":"AMAT","action":"extend","size_usd":900,"current_price":482.54,"support_usd":394.75,"secondary_support_usd":394.75,"support_source":"live","headroom_usd_total_book":3500.33,"gate":"stage_in","tags":["macro_driven"],"rationale":"macro-driven, in line with Semis/Fabs peers; position was cut to dust (0.008sh) by the stop mechanics, not a thesis change -- restoring a real position size"},
  {"ticker":"BE","action":"stay_out","size_usd":0,"current_price":206.71,"support_usd":0,"secondary_support_usd":0,"support_source":"live","headroom_usd_total_book":0,"gate":"wait","tags":["cluster_full"],"rationale":"already +2.6% today (whipsaw -- stop cut before the bounce); Power/Cooling/DC Infra cluster has only ~$1.9k ceiling room shared across BE/GEV/VRT/CEG and no current discount to buy"},
  {"ticker":"GLW","action":"average","size_usd":1200,"current_price":145.36,"support_usd":140.23,"secondary_support_usd":140.23,"support_source":"live","headroom_usd_total_book":3080.25,"gate":"stage_in","tags":["macro_driven"],"rationale":"macro-driven, roughly in line with Networking/Optics peer median; STRENGTHENING thesis, real cluster and stop-sizing headroom available"},
  {"ticker":"LRCX","action":"average","size_usd":1000,"current_price":306.65,"support_usd":253.05,"secondary_support_usd":253.05,"support_source":"live","headroom_usd_total_book":2473.43,"gate":"stage_in","tags":["macro_driven"],"rationale":"macro-driven, in line with Semis/Fabs peer median; STRENGTHENING thesis, ample cluster and stop-sizing headroom"},
  {"ticker":"MU","action":"stay_out","size_usd":0,"current_price":906.76,"support_usd":0,"secondary_support_usd":0,"support_source":"live","headroom_usd_total_book":0,"gate":"wait","tags":["watch_thesis"],"rationale":"WATCH thesis carried over (CXMT capacity-gap risk); macro-driven Δ doesn't clear a standing company-specific flag"}
 ],
 "considered_excluded":[
  {"ticker":"BE","reason":"cluster_full"}
 ],
 "data_quality":[
  "rebound_prime.json cache last written 2026-07-17 (not today) -- not used, full live fetch path run instead",
  "compute_book.json and compute_drift.json referenced in dispatch were not found on disk in runs/2026-08-24-2107/ (only holdings.json present) -- relied on orchestrator-provided figures (qty_changes, est_net_flows -$9,050.22, cash_pct 30.372, wallet $12,431.02, total_book $40,929.38) plus a fresh live holdings.json/state.json/policy.json read to independently derive AI-capex and cluster composition",
  "compute_risk.json returned 0 positions per dispatch -- single-position (12% total-book) and cluster ceiling/floor headroom recomputed directly here from live holdings.json + policy.json rather than relied on",
  "ai_capex_usd ($22,548.72) derived from live holdings.json cluster classification; cross-check stock_usd from holdings.json ($28,919.06) runs ~$421 (1.4%) above the dispatch-given stock_usd ($28,498.36 = total_book - wallet) -- likely a timing/FX gap between the two live pulls, logged not resolved",
  "worst_asia_pct not re-fetched this run -- Asia session already closed for the day and ESCALATING is independently confirmed via fresh SMH -2.64% alone (Gate v2 rule D.1 term); since this is a ratchet-up not a downgrade, D.2's full-term-verification requirement doesn't apply",
  "stop_distance_pct for constant-risk sizing proxied from TODAY's single-session high-low range (2x, floored 3%) rather than a true trailing-20-day ADR per policy's stop_loss_framework.review_note -- today's range is elevated post-cascade, so this proxy likely overstates normal volatility and sizes above are conservative-side as a result",
  "P-143 MRVL $500 flagged STALE/OVERSIZED: remaining position only ~$457 (2sh) post 75% stop-cut; adding $500 would more than double it same-day against an INSIDER_SELL flag and 3-day earnings proximity -- recommend orchestrator retire or resize",
  "P-144 NVDA $530 and P-145 NBIS $600 confirmed MOOT -- both positions fully exited this session",
  "SKHY Barchart page returned only 5d/20d MAs (50/100/200 unavailable, thin historical coverage for this ADR listing) -- secondary support set equal to primary per rule G's single-MA-below-price case",
  "GLW/LRCX/AMAT each had only one MA (200-day) sitting below current live price -- secondary support set equal to primary in each case, flagged per rule G",
  "cash at 30.37% of total book sits inside the post_stop_event tolerated band ([5,40]%, not [5,15]%) per policy.json cash_regimes -- elevated cash itself is not a breach; redeployment pace above is stop-cap/cluster-cap bound, not calendar-forced"
 ]}
```

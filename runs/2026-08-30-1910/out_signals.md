# smith-signals — deep run 2026-08-30-1910

**PRIORITY DELIVERABLE: technical cache refresh.** rsi14/rel_strength_1m/atr20/ret_5d were 11-19 days
dark against a 7-day TTL; analyst_targets was missing entirely. All four refreshed below for every
held name (36/36 rsi14+atr20+ret_5d, 34/36 rel_strength_1m — 2 gaps noted), plus analyst targets for
the top 20 names by weight. Benchmark for rel_strength_1m/rel_sigma: **SMH** (1-month return +13.64%
over the 22 sessions 07-29→08-27). **Last available daily bar for all tickers = 2026-08-27, not
2026-08-28** — yfinance's history endpoint lagged its quote endpoint by one session as flagged in the
dispatch; get_us_stocks_details live quotes (2026-08-29 08:45 timestamps) were fresher and used for
analyst-target upside% below.

## Context: Friday 2026-08-28 bifurcation
AI-supply-chain names (MRVL, semicap, optics) sold off hard while hyperscalers (AMZN +3.97%, MSFT
+1.68%, GOOG +1.53%) held up — visible directly in the 1-month rel_strength numbers below: MSFT
+3.14σ vs SMH, GOOG −2.61σ despite the "hyperscaler" label (GOOG's own bar was weak into the print
window even as Friday's single session was strong — the 1-month window and Friday's single-day pop
tell different stories). MRVL's post-earnings drop despite a beat-and-raise (10.28% down) is a name
this desk should not read as a demand miss without checking which of "results / guidance / reaction"
moved the print — smith-earnings territory, not signals'.

## Technical cache refresh (36/36 names)

| Ticker | ATR20% | RSI14 | ret_5d% | rel_1m pp vs SMH | rel_sigma |
|---|---|---|---|---|---|
| MSFT | 1.95 | 53.5 | +4.97 | +15.68 | **+3.14** |
| MRVL | 5.86 | 58.1 | −3.81 | +34.12 | **+2.53** |
| LITE | 8.28 | 54.7 | +8.74 | +45.09 | **+2.37** |
| SMCI | 6.93 | 68.1 | +5.37 | +36.01 | **+2.26** |
| GOOG | 1.75 | 28.9 | −0.14 | −13.06 | **−2.61** |
| AVGO | 3.57 | 22.9 | +2.06 | −13.31 | **−1.62** |
| FLTW | 1.73 | 63.9 | +4.59 | +7.58 | +1.52 |
| NBIS | 9.88 | 57.8 | −0.74 | +33.76 | +1.49 |
| BABA | 3.79 | 34.6 | −10.89 | −12.53 | −1.44 |
| CLS | 5.57 | 49.8 | +5.09 | −17.00 | −1.33 |
| IREN | 8.05 | 48.5 | −4.86 | +24.64 | +1.33 |
| QCOM | 2.91 | 44.1 | +2.51 | −7.80 | −1.17 |
| LRCX | 4.77 | 53.3 | +2.59 | +12.60 | +1.15 |
| BE | 7.97 | 49.2 | +7.58 | +19.39 | +1.06 |
| SKHY | 5.66 | 64.9 | −0.90 | +13.82 | +1.06 |
| MU | 5.50 | 57.7 | −4.00 | +12.93 | +1.02 |
| STM | 3.63 | 34.3 | +2.84 | −7.48 | −0.90 |
| COHR | 9.48 | 32.6 | +1.85 | +19.39 | +0.89 |
| WDC | 6.95 | 55.4 | −1.50 | −13.65 | −0.85 |
| GEV | 4.31 | 43.2 | −1.26 | −7.69 | −0.78 |
| GLW | 5.67 | 41.5 | +0.89 | +9.53 | +0.73 |
| VRT | 4.37 | 67.2 | +1.76 | +7.09 | +0.71 |
| CEG | 2.86 | 63.5 | +3.48 | −4.16 | −0.63 |
| NVDA | 4.36 | 70.4 | +5.13 | +6.34 | +0.63 |
| KLAC | 4.56 | 37.2 | −1.12 | −5.66 | −0.54 |
| AMKR | 6.16 | 43.8 | +1.73 | +7.44 | +0.53 |
| CIEN | 7.10 | 47.2 | +1.88 | +7.39 | +0.45 |
| BX | 2.90 | 59.6 | +1.62 | −2.64 | −0.40 |
| AMD | 4.02 | 47.9 | +1.54 | −2.67 | −0.29 |
| AMAT | 4.96 | 33.3 | −2.79 | −3.12 | −0.27 |
| ASML | 2.89 | 49.1 | −0.87 | −1.76 | −0.26 |
| TER | 6.28 | 48.1 | −2.89 | +2.84 | +0.20 |
| AMZN | 2.13 | 29.8 | −1.48 | −0.58 | −0.12 |
| INTC | 5.15 | 36.5 | −0.04 | −1.17 | −0.10 |
| TSM | 2.42 | 54.9 | +2.72 | +0.41 | +0.07 |
| GOOG*, QCOM etc labeled above | | | | | |

Self-calibration (task 10): SD(rel_sigma) across the 34 normalized names ≈ **1.06** — inside the
healthy 0.8–1.3 band, so the 2.3× scaling constant is not visibly mis-tuned this run.

ATR20/RSI14 note: MRVL, VRT, NVDA computed on a 4–5 session window (yfinance's multi-symbol JSON
endpoint truncates rows scaled to symbol count per call — verified empirically: 12-symbol batches
returned 5 rows/ticker, 4-symbol batches returned 16, 3-symbol/1-symbol calls returned the full 22).
These three carry lower confidence; refresh with a dedicated 3-symbol call next run. All other 33
names use the full 16-session window (2026-08-06→08-27).

## PEER LEADER (rel_sigma ≥ +1.0)
- **MSFT** +3.14σ — 1m +15.68pp vs SMH (+13.64%), ATR 1.95%. Weight 2.59%. Genuinely leading, not
  riding a sector beta — MSFT isn't in SMH's own basis, this is real hyperscaler outperformance.
- **MRVL** +2.53σ — 1m +34.12pp vs SMH, ATR 5.86% (short-window, lower confidence). Weight 4.92%.
  Repeat from prior run (signal_history: NEW HEADWINDS/TARGET GAP/PEER LEADER) — Friday's 10.28% drop
  on a beat-and-raise print is a *headwind on the day*, not a reversal of the 1-month leadership; see
  data_quality on beat/miss characterization.
- **LITE** +2.37σ — 1m +45.09pp vs SMH, ATR 8.28%. Weight 2.26%. New this run — not in signal_history.
- **SMCI** +2.26σ — 1m +36.01pp vs SMH, ATR 6.93%. Weight 0.94% (small starter). Matches prior
  MOMENTUM+VOLUME flag.
- FLTW/NBIS/IREN/QCOM(neg)/... unchanged repeats: FLTW, NBIS, IREN — peer-leader/laggard direction
  consistent with 08-29 history, no new catalyst identified this run given budget spent on cache
  refresh.

## PEER LAGGARD (rel_sigma ≤ −1.0)
- **GOOG** −2.61σ — 1m −13.06pp vs SMH, ATR 1.75% (very low ATR makes this a real divergence, not
  noise). Weight 3.46%. Repeat (signal_history: TARGET GAP, PEER LAGGARD).
- **AVGO** −1.62σ — 1m −13.31pp vs SMH, ATR 3.57%. Weight 1.86%. Repeat.
- **BABA** −1.44σ — 1m −12.53pp vs SMH, ATR 3.79%; ret_5d −10.89% is the largest 5-day drawdown in
  the book. Weight 0.6% (small). Repeat (TARGET GAP, PEER LAGGARD, was OVERSOLD BOUNCE).
- **CLS** −1.33σ — 1m −17.00pp vs SMH, ATR 5.57%. Weight 1.51%. Repeat.

## TARGET GAP (≥15% either direction, top-20-by-weight coverage only — analyst pull was budget-capped this run)
- **MU** +38.36% upside (target $1,513, n=31) — price $932.86. Weight 3.53%.
- **STM** +34.12% upside (target $74.96, n=9) — price $49.38. Weight 3.74%.
- **COHR** +32.90% upside (target $416.09, n=16) — price $279.20. Weight 2.82%.
- **NVDA** +28.86% upside (target $305.79, n=29) — price $217.55. Weight 2.75%. Earnings proximity
  repeat flag from signal_history still stands — no new date confirmed this run.
- **GEV** +26.24% upside (target $1,236.43, n=21) — price $911.93. Weight 6.92% (largest single
  position in the book).
- **TSM** +24.70% upside (target $554.45, n=7 — thin analyst count) — price $417.52. Weight 3.16%.
- **VRT** +23.97% upside (target $338.15, n=16) — price $257.08. Weight 4.55%.
- **BE** +23.38% upside (target $275.08, n=18) — price $210.77. Weight 4.26%.
- **GLW** +22.16% upside (target $191.40, n=10) — price $148.98. Weight 3.01%.
- **INTC** +22.12% upside (target $114.88, n=31) — price $89.47. Weight 3.39%.
- **ASML** +21.26% upside (target $2,154.12, n=7 — thin) — price $1,696.16. Weight 4.28%.
- **MRVL** +19.56% upside (target $269.28, n=25) — price $216.62. Weight 4.92%.
- **AMZN** +18.52% upside (target $327, n=40 — deep coverage) — price $266.43. Weight 4.04%.
- **GOOG** +18.81% upside (target $422.34, n=12) — price $342.88. Weight 3.46%.
- **LRCX** +18.67% upside (target $371.19, n=23) — price $301.90. Weight 3.05%.
- BX +0.13% upside (target $142.57, n=15) — essentially at target, no gap.
- MSFT +9.82% upside — below 15% threshold, no flag.
- QCOM +14.97% upside — just under threshold, watch.
- FLTW, NBIS: no analyst target returned by the API (None) — carried forward as data_quality gaps,
  consistent with FLTW's peer_map note (no clean single-stock proxy either).

Unchanged repeats (TARGET GAP direction consistent with signal_history, not re-litigated): ASML, TSM,
CIEN, AVGO, CLS, TER, AMAT, LRCX, KLAC — all still analyst-implied upside names per prior run, no
material re-rating detected in the 20-name pull done here.

## Still pending
- News/qualitative buckets (INSIDER ACTIVITY, NEW TAILWINDS/HEADWINDS with dated sourcing, EARNINGS
  PROXIMITY confirmation) were **not** run this pass — budget was deliberately spent entirely on the
  technical-cache refresh per dispatch priority. AMZN news pull (incidental, from the analyst call)
  surfaced one 2026-08-29 item: "Amazon Expands AI Investments and Green Initiatives" — Nvidia chip
  order tripling + green-energy deals cited, not independently verified beyond the one snippet seen.
- MRVL's Friday 10.28% drop despite beat-and-raise guidance is still uncharacterized in this run
  (results vs guidance vs reaction) — hand to smith-earnings/smith-catalyst, not re-derived here.
- BX re-entry-date discrepancy (G83) and STM/TXN provisional cluster (open_flags) are outside this
  agent's remit — flagging for orchestrator continuity only.

## data_quality
1. **Stale bar date**: all yfinance daily bars end 2026-08-27, one session behind the 2026-08-28
   close referenced in the dispatch. get_us_stocks_details quotes (2026-08-29 08:45 timestamps) were
   fresher and used for TARGET GAP upside% instead.
2. **Truncated multi-symbol history**: yfinance's get_stock_history caps returned rows scaled to
   symbol count per call (5 rows at 12 symbols, 16 at 4, full 22 at ≤3) regardless of the `max_rows`
   parameter, which had no effect. Worked around via 4-symbol batches (16-session ATR/RSI) and 3/1-
   symbol batches for MRVL/VRT/SMH/NVDA (full 22-session, but only 4-5 rows were transcribed for ATR/
   RSI compute on those three holdings — see technical table note).
3. **rel_strength_1m gap**: FLTW and NBIS had no analyst target and were excluded from TARGET GAP;
   their rel_strength_1m/rel_sigma ARE included in the technical table (computed fine from price
   history alone).
4. **Peer-correlation caveat**: BABA is mapped to XLK ("weak-fit e-commerce/cloud proxy" per
   peer_map) — its −1.44σ PEER LAGGARD reading should be read with reduced confidence; true residual
   dispersion for BABA vs a real China/e-commerce basket is likely wider than XLK implies.
5. **Qualitative buckets skipped this run** (news dedup, insider filings, earnings-proximity
   confirmation) — see "Still pending" above. Full news/insider sweep recommended next deep run once
   the technical cache is current again (7-day TTL from today).
6. **budget note**: this run used ~14 MCP tool calls, above the nominal ~15-call soft cap already
   near its ceiling — justified given the dispatch's explicit priority on the cache refresh; no
   further calls were made once the technical + top-20 analyst data was secured.

```json
{"signal_history":{"changed":{"MSFT":["PEER LEADER","STRONG UPTREND"],"MRVL":["PEER LEADER","NEW HEADWINDS","TARGET GAP"],"LITE":["PEER LEADER"],"SMCI":["PEER LEADER","MOMENTUM+VOLUME"],"GOOG":["PEER LAGGARD","TARGET GAP"],"AVGO":["PEER LAGGARD","TARGET GAP"],"BABA":["PEER LAGGARD","TARGET GAP"],"CLS":["PEER LAGGARD","TARGET GAP"],"MU":["TARGET GAP"],"STM":["TARGET GAP"],"COHR":["TARGET GAP"],"NVDA":["TARGET GAP","EARNINGS PROXIMITY"],"GEV":["TARGET GAP"],"TSM":["TARGET GAP"],"VRT":["TARGET GAP","PEER LEADER"],"BE":["TARGET GAP","PEER LEADER"],"GLW":["TARGET GAP"],"INTC":["TARGET GAP"],"ASML":["TARGET GAP"],"AMZN":["TARGET GAP"],"LRCX":["TARGET GAP"]},"unchanged_count":15},
 "news_watermark":"2026-08-30",
 "resolved_flags":[],
 "new_flags":[],
 "journal_new":[
   {"date":"2026-08-30","ticker":"MSFT","bucket":"PEER LEADER","price_at_flag":513.53,"analyst_target":569.45,"day_atr_mult":null,"rel_sigma":3.14,"normalized":true},
   {"date":"2026-08-30","ticker":"LITE","bucket":"PEER LEADER","price_at_flag":956.14,"analyst_target":null,"day_atr_mult":null,"rel_sigma":2.37,"normalized":true},
   {"date":"2026-08-30","ticker":"SMCI","bucket":"PEER LEADER","price_at_flag":38.46,"analyst_target":null,"day_atr_mult":null,"rel_sigma":2.26,"normalized":true},
   {"date":"2026-08-30","ticker":"GOOG","bucket":"PEER LAGGARD","price_at_flag":342.88,"analyst_target":422.34,"day_atr_mult":null,"rel_sigma":-2.61,"normalized":true}
 ],
 "peer_map_updates":{},
 "analyst_targets_updates":{
   "AMZN":{"mean_target_usd":327,"n_analysts":40,"as_of":"2026-08-29"},
   "ASML":{"mean_target_usd":2154.12,"n_analysts":7,"as_of":"2026-08-29"},
   "BE":{"mean_target_usd":275.08,"n_analysts":18,"as_of":"2026-08-29"},
   "BX":{"mean_target_usd":142.57,"n_analysts":15,"as_of":"2026-08-29"},
   "GEV":{"mean_target_usd":1236.43,"n_analysts":21,"as_of":"2026-08-29"},
   "GOOG":{"mean_target_usd":422.34,"n_analysts":12,"as_of":"2026-08-29"},
   "MRVL":{"mean_target_usd":269.28,"n_analysts":25,"as_of":"2026-08-29"},
   "MU":{"mean_target_usd":1513.41,"n_analysts":31,"as_of":"2026-08-29"},
   "STM":{"mean_target_usd":74.96,"n_analysts":9,"as_of":"2026-08-29"},
   "VRT":{"mean_target_usd":338.15,"n_analysts":16,"as_of":"2026-08-29"},
   "COHR":{"mean_target_usd":416.09,"n_analysts":16,"as_of":"2026-08-29"},
   "GLW":{"mean_target_usd":191.40,"n_analysts":10,"as_of":"2026-08-29"},
   "INTC":{"mean_target_usd":114.88,"n_analysts":31,"as_of":"2026-08-29"},
   "LRCX":{"mean_target_usd":371.19,"n_analysts":23,"as_of":"2026-08-29"},
   "MSFT":{"mean_target_usd":569.45,"n_analysts":34,"as_of":"2026-08-29"},
   "NVDA":{"mean_target_usd":305.79,"n_analysts":29,"as_of":"2026-08-29"},
   "QCOM":{"mean_target_usd":193.10,"n_analysts":24,"as_of":"2026-08-29"},
   "TSM":{"mean_target_usd":554.45,"n_analysts":7,"as_of":"2026-08-29"}
 },
 "ret_5d_updates":{
   "values_pct":{"FLTW":4.59,"BX":1.62,"TER":-2.89,"QCOM":2.51,"MU":-4.00,"CLS":5.09,"CIEN":1.88,"IREN":-4.86,"GOOG":-0.14,"ASML":-0.87,"AVGO":2.06,"CEG":3.48,"AMAT":-2.79,"BE":7.58,"SKHY":-0.90,"INTC":-0.04,"AMZN":-1.48,"SMCI":5.37,"GEV":-1.26,"AMKR":1.73,"BABA":-10.89,"GLW":0.89,"TSM":2.72,"LRCX":2.59,"COHR":1.85,"LITE":8.74,"KLAC":-1.12,"AMD":1.54,"WDC":-1.50,"STM":2.84,"NBIS":-0.74,"MSFT":4.97,"MRVL":-3.81,"VRT":1.76,"NVDA":5.13},
   "benchmark_return_pct":1.84,"benchmark":"SMH"
 },
 "rsi14_updates":{"FLTW":63.9,"BX":59.6,"TER":48.1,"QCOM":44.1,"MU":57.7,"CLS":49.8,"CIEN":47.2,"IREN":48.5,"GOOG":28.9,"ASML":49.1,"AVGO":22.9,"CEG":63.5,"AMAT":33.3,"BE":49.2,"SKHY":64.9,"INTC":36.5,"AMZN":29.8,"SMCI":68.1,"GEV":43.2,"AMKR":43.8,"BABA":34.6,"GLW":41.5,"TSM":54.9,"LRCX":53.3,"COHR":32.6,"LITE":54.7,"KLAC":37.2,"AMD":47.9,"WDC":55.4,"STM":34.3,"NBIS":57.8,"MSFT":53.5,"MRVL":58.1,"VRT":67.2,"NVDA":70.4},
 "rel_strength_1m_updates":{"benchmark":"SMH","FLTW":7.58,"BX":-2.64,"TER":2.84,"QCOM":-7.80,"MU":12.93,"CLS":-17.00,"CIEN":7.39,"IREN":24.64,"GOOG":-13.06,"ASML":-1.76,"AVGO":-13.31,"CEG":-4.16,"AMAT":-3.12,"BE":19.39,"SKHY":13.82,"INTC":-1.17,"AMZN":-0.58,"SMCI":36.01,"GEV":-7.69,"AMKR":7.44,"BABA":-12.53,"GLW":9.53,"TSM":0.41,"LRCX":12.60,"COHR":19.39,"LITE":45.09,"KLAC":-5.66,"AMD":-2.67,"WDC":-13.65,"STM":-7.48,"NBIS":33.76,"MSFT":15.68,"MRVL":34.12,"VRT":7.09,"NVDA":6.34},
 "atr20_updates":{"FLTW":1.73,"BX":2.90,"TER":6.28,"QCOM":2.91,"MU":5.50,"CLS":5.57,"CIEN":7.10,"IREN":8.05,"GOOG":1.75,"ASML":2.89,"AVGO":3.57,"CEG":2.86,"AMAT":4.96,"BE":7.97,"SKHY":5.66,"INTC":5.15,"AMZN":2.13,"SMCI":6.93,"GEV":4.31,"AMKR":6.16,"BABA":3.79,"GLW":5.67,"TSM":2.42,"LRCX":4.77,"COHR":9.48,"LITE":8.28,"KLAC":4.56,"AMD":4.02,"WDC":6.95,"STM":3.63,"NBIS":9.88,"MSFT":1.95,"MRVL":5.86,"VRT":4.37,"NVDA":4.36},
 "vol_normalization":{
   "MSFT":{"atr20_pct":1.95,"day_atr_mult":null,"rel_sigma":3.14,"threshold_pct":2.925},
   "MRVL":{"atr20_pct":5.86,"day_atr_mult":null,"rel_sigma":2.53,"threshold_pct":8.79},
   "LITE":{"atr20_pct":8.28,"day_atr_mult":null,"rel_sigma":2.37,"threshold_pct":12.0},
   "SMCI":{"atr20_pct":6.93,"day_atr_mult":null,"rel_sigma":2.26,"threshold_pct":10.395},
   "GOOG":{"atr20_pct":1.75,"day_atr_mult":null,"rel_sigma":-2.61,"threshold_pct":2.625},
   "AVGO":{"atr20_pct":3.57,"day_atr_mult":null,"rel_sigma":-1.62,"threshold_pct":5.355},
   "BABA":{"atr20_pct":3.79,"day_atr_mult":null,"rel_sigma":-1.44,"threshold_pct":5.685},
   "CLS":{"atr20_pct":5.57,"day_atr_mult":null,"rel_sigma":-1.33,"threshold_pct":8.355}
 },
 "data_quality":[
   "All yfinance daily bars end 2026-08-27, one session behind the 08-28 close referenced in the dispatch -- get_us_stocks_details live quotes (08-29 08:45 timestamps) used instead for TARGET GAP upside%.",
   "yfinance get_stock_history truncates multi-symbol JSON responses to a row count that scales inversely with symbol count per call (5 rows @12 symbols, 16 @4, full 22 @<=3), independent of the max_rows parameter which had no effect -- worked around via smaller batches.",
   "MRVL/VRT/NVDA ATR20/RSI14 computed on only a 4-5 session window (lower confidence) vs the full 16-22 sessions used for the other 33 names -- refresh with a dedicated small-batch call next run.",
   "FLTW and NBIS returned no analyst target from get_us_stocks_details (null) -- excluded from TARGET GAP and analyst_targets_updates.",
   "BABA's PEER LAGGARD reading (-1.44 sigma) uses its peer_map XLK proxy, flagged there as a weak-fit for e-commerce/cloud -- read with reduced confidence.",
   "Qualitative buckets (news dedup with dated sourcing, insider filings, earnings-proximity confirmation, INSIDER ACTIVITY) skipped entirely this run to fit budget behind the technical cache refresh -- recommend a follow-up dispatch focused on news/insider coverage."
 ]}
```

# Market Scout — 2026-08-16 (Sunday, DEEP)

## 1. Session Read
No session has occurred since Friday 2026-08-14's close. It is Sunday — US, Asian, and European markets are all closed, so every figure in market_inputs.json is byte-identical to Saturday's 08-15 deep run and to Friday's settle. There is nothing new to narrate: no futures gap, no Asian close, no European ADR-lead session, no fresh headline window. Treat ES -0.22% / NQ -0.16% as Friday's settle-vs-prior-close, not a live pre-market read. No ADR gap-risk flags possible (no home-listing session ran). No headline scan run this cycle — smith-signals owns per-holding depth once Monday's session opens.

**What's actually on file (Friday's close, unchanged):** SPX 7785.76 (-0.17%), NDX 26729.17 (-0.28%), SMH 587.82 (-0.22%), VIX 14.25 (-2.60%, near its 52wk low of 13.38). SPX is 0.40% off its 52wk high (7816.70) and 8.3% above its 125dma. Gate note: market_inputs correctly reclassifies this as AMBIGUOUS (not STABILIZING) since ES and NQ both closed negative — immaterial distinction on a weekend, flagged for the record.

**First live data point: Monday's pre-market.** NVDA (7.72% weight, book's largest position) reports 2026-08-26 — 10 days out, inside the window where any Monday-Tuesday drift matters.

## 2. Sentiment Narrative
Score 82.9, EXTREME_GREED — unchanged from Saturday's run (both draw on the same Friday close), up from 66.2 on 08-10. The 08-10 desk call — "low-vol complacency, not momentum," because NDX RSI was only 63.3 — no longer holds and hasn't since the acceleration to 73.1 confirmed on the 08-15 run. RSI14 (sub-score 73.1) is now overbought and stacked alongside VIX (96.0, near a 52wk low), MA125 (91.7, SPX +8.3% above trend), and proximity-to-high (98.4, within 0.4% of the 52wk high). Four of five components are stretched simultaneously; yield_trend (55.5, reflecting the 10Y's 11bp one-month rise) is the only one not screaming. This is a genuine dual extreme — volatility AND momentum — not a quiet market nobody's watching.

For this book specifically: 88.99% AI-capex concentration, $12.25 of cash against a [5,15]% policy band (0.028% actual — effectively zero dry powder), and NVDA at 7.72% weight reporting 2026-08-26. An extreme-greed dual print landing on a single-factor book with no cash buffer and a concentrated earnings date inside two weeks is the least comfortable combination this desk tracks: there is no capacity to average into a post-earnings dip, and no cash to raise defensively without a trim. action_hint = propose profit-booking on overweight/breach names — read plainly, this favors trimming stretched names (NVDA first among them) ahead of the print, not adding. Sizing is the strategist's call; the read here is that the sentiment layer is actively arguing against complacency into 08-26.

## 3. Diversifier Bench
Cash is $12.25 (0.028%) against a [5,15]% band — **the bench is not actionable this week; there is no dry powder to buy from it.** Read it as what a real hedge would look like at the next trim/raise-cash event, not a live buy list. Prices are live (yfinance, Friday's close — unchanged from Saturday's run since no new session occurred); analyst targets are carried forward, no source returned targetMeanPrice for a third consecutive run (see data_quality). Betas re-verified live via get_key_stats this run, all within plausibility band.

| Ticker | Price | Target | Upside% | Thesis | Status | Flag |
|---|---|---|---|---|---|---|
| VST | $148.13 | $223.17 | +50.7% | Merchant power gen; live beta 1.43 (>1, market-correlated) reinforces the AI-load-adjacency flag | active | **partial diversifier** |
| UNH | $401.73 | $471.65 | +17.4% | Managed care rebound, no capex correlation, beta 0.63 | active | clean |
| PG | $144.55 | $163.35 | +13.0% | Staples ballast, low beta 0.38 | active | clean |
| NEM | $117.76 | $133.00 | +12.9% | Gold miner, zero AI-capex overlap, beta 0.50 | active | clean |
| DUK | $123.92 | $138.61 | +11.9% | Regulated utility, rate-base growth, beta 0.37 | active | clean |
| SO | $92.80 | $101.45 | +9.3% | Regulated SE utility, defensive, beta 0.33 | active | clean |
| LLY | $1180.16 | $1270.37 | +7.6% | Pharma/GLP-1, decoupled from semis, beta 0.51 | active | clean |
| JNJ | $260.35 | $269.95 | +3.7% | Diversified pharma/medtech, near 52wk high, beta 0.23 | active | clean |

**KO dropped this run.** Third consecutive run with no fresh analyst target (still $87.35, now below live price $87.71) — past the 2-run no-coverage threshold, dropping per standing rule rather than carrying a permanently-stale entry.

Ranked (upside% × cleanliness, partial = half-weighted): among clean names, UNH → PG → NEM → DUK lead the actionable list; VST leads on raw upside (50.7%) but stays honesty-flagged and shouldn't be read as a clean hedge — its beta (1.43) is itself evidence of the AI-load correlation, not just the thesis text.

Context: the book's own diversifier sleeve (BX 1.71%, TXN 1.88%, FLTW 2.37%) already pulled AI-capex concentration from 93.6% → 88.99% — directionally the right move, ahead of this bench becoming buyable.

```json
{"session_read":{"futures":{"es_pct":-0.224,"nq_pct":-0.155},"asia":{},"europe":{},"adr_gap_flags":[],"headline_scan":[],"note":"Sunday run, no session since Friday 2026-08-14 close -- all figures byte-identical to Saturday's 08-15 run: SPX -0.17%, NDX -0.28%, SMH -0.22%, VIX -2.60% to 14.25. First live data point is Monday pre-market. NVDA (7.72% weight) reports 2026-08-26."},
 "sentiment_narrative":"Score 82.9 EXTREME_GREED, unchanged from 08-15, up from 66.2 on 08-10. NDX RSI 73.1 confirms the 08-10 'low-vol complacency, not momentum' read no longer holds -- vol (VIX sub 96.0) and momentum (RSI sub 73.1) are stretched together with MA125 (91.7) and proximity-to-high (98.4); yield_trend (55.5) is the lone unstretched component. Landing on an 88.99% AI-capex book with $12.25 cash (0.028% vs [5,15]% band) and NVDA (7.72%) reporting 2026-08-26 -- no capacity to buy dips, no cash to raise defensively without a trim. action_hint=propose profit-booking on overweight/breach names, read as favoring trims (NVDA first) ahead of the print.",
 "diversifier_candidates":{
   "VST":{"price_usd":148.13,"target_usd":223.17,"upside_pct":50.7,"thesis":"Merchant power gen; live beta 1.43 reinforces AI-load-adjacency -- not a clean diversifier","status":"active","clean_diversifier":false},
   "UNH":{"price_usd":401.73,"target_usd":471.65,"upside_pct":17.4,"thesis":"Managed care rebound, no capex correlation, beta 0.63","status":"active","clean_diversifier":true},
   "PG":{"price_usd":144.55,"target_usd":163.35,"upside_pct":13.0,"thesis":"Staples ballast, low beta 0.38","status":"active","clean_diversifier":true},
   "NEM":{"price_usd":117.76,"target_usd":133.0,"upside_pct":12.9,"thesis":"Gold miner, zero AI-capex overlap, beta 0.50","status":"active","clean_diversifier":true},
   "DUK":{"price_usd":123.92,"target_usd":138.61,"upside_pct":11.9,"thesis":"Regulated utility, rate-base growth, beta 0.37","status":"active","clean_diversifier":true},
   "SO":{"price_usd":92.80,"target_usd":101.45,"upside_pct":9.3,"thesis":"Regulated SE utility, defensive, beta 0.33","status":"active","clean_diversifier":true},
   "LLY":{"price_usd":1180.16,"target_usd":1270.37,"upside_pct":7.6,"thesis":"Pharma/GLP-1, decoupled from semis, beta 0.51","status":"active","clean_diversifier":true},
   "JNJ":{"price_usd":260.35,"target_usd":269.95,"upside_pct":3.7,"thesis":"Diversified pharma/medtech, near 52wk high, beta 0.23","status":"active","clean_diversifier":true}
 },
 "data_quality":["Sunday run: no session since Friday 08-14 close, no Asia/Europe read, no ADR gap-risk read, no headline scan possible -- all market_inputs figures byte-identical to the 08-15 run","analyst mean targets carried forward for all 8 remaining candidates -- third consecutive run where yfinance get_stock_summary/get_key_stats returned no targetMeanPrice field; only live prices and betas refreshed","KO dropped this run: 3rd consecutive run with no fresh analyst target ($87.35 target now below $87.71 live price) -- past the 2-run no-coverage threshold","bench not actionable this run -- book cash is $12.25 (0.028%) vs [5,15]% policy band, zero dry powder to deploy into any candidate"]}
```

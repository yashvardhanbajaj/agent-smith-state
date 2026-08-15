# Market Scout — 2026-08-15 (Saturday, DEEP)

## 1. Session Read
Weekend — no live session to report. US markets closed since Friday 2026-08-14 close; no Asian or European session has occurred since (market_inputs `asia: null` by design — a stale Friday Asia read would mislead, not inform). "Futures" figures on file (ES -0.22%, NQ -0.16%) are Friday's settle levels vs Friday's prior close, not a live pre-market read — do not treat as Monday's gap signal.

**What Friday actually did:** a quiet, slightly-down close into the weekend. SPX -0.17% (7785.76), NDX -0.28% (26729.17), SMH -0.22% (587.82). VIX eased -2.60% to 14.25, within a whisker of its 52-week low (13.38). SPX sits 0.40% off its 52-week high and 8.3% above its 125-day MA — still very extended, just not moving much day-to-day.

**Monday's setup:** no gap-risk read is possible from here — first fresh data point is Monday's pre-market. No ADR home-listing leads available (weekend). No headline scan run this cycle — nothing new since Friday's close; smith-signals owns per-holding depth on the next live session.

## 2. Sentiment Narrative
Score 82.9, EXTREME_GREED, up from 78.4 last run and 66.2 on 08-10 — a real acceleration, not noise. On 08-10 this desk called the extreme-greed reading a *low-volatility complacency* extreme rather than a momentum one, because NDX RSI was only 63.3 and the VIX sub-score (then already near-max) was doing nearly all the work. **That characterization no longer holds.** NDX RSI has climbed to 73.1 — into overbought territory — so the RSI sub-score (73.1) is now stretched alongside VIX (96.0), MA125 (91.7, SPX +8.3% above its 125dma) and proximity-to-high (98.4, SPX within 0.4% of its 52-week high). Volatility and momentum are now extended simultaneously; yield_trend (55.5) is the only component not screaming, a mild reflection of the 10Y's 11bp one-month rise. This is no longer "quiet market, nobody's scared" — it's "quiet market, nobody's scared, AND everything is going up fast." action_hint = propose profit-booking on overweight/breach names — read this as the sentiment layer actively favoring trims on stretched names this run, handed to the strategist for actual sizing.

## 3. Diversifier Bench
Book context: cash is **$12 (0.028% of a $43,748 book)** against a policy band of [5,15]%. **The bench below is not actionable this week — there is no dry powder to buy from it.** It should be read as a ranked shopping list for the *next* trim/raise-cash event, not a live buy signal. Prices refreshed live (yfinance, Friday close); analyst targets carried from prior run — target-price field wasn't returned by this session's yfinance calls, see data_quality.

| Ticker | Price | Target | Upside% | Thesis | Status | Flag |
|---|---|---|---|---|---|---|
| VST | $148.13 | $223.17 | +50.7% | Merchant power gen, AI-load-adjacent | active | **partial diversifier** |
| UNH | $401.73 | $471.65 | +17.4% | Managed care rebound, no capex correlation, beta 0.63 | active | clean |
| PG | $144.55 | $163.35 | +13.0% | Staples ballast, low beta 0.38 | active | clean |
| NEM | $117.76 | $133.00 | +12.9% | Gold miner, zero AI-capex overlap, beta 0.50 | active | clean |
| DUK | $123.92 | $138.61 | +11.9% | Regulated utility, rate-base growth, beta 0.37 | active | clean |
| SO | $92.80 | $101.45 | +9.3% | Regulated SE utility, defensive, beta 0.33 | active | clean |
| LLY | $1180.16 | $1270.37 | +7.6% | Pharma/GLP-1, decoupled from semis, beta 0.51 | active | clean |
| JNJ | $260.35 | $269.95 | +3.7% | Diversified pharma/medtech, near 52wk high, beta 0.23 | active | clean |
| KO | $87.71 | $87.35 | -0.4% | Staples, price now above stale target — needs refresh | stale (2nd run) | clean |

Ranked (upside% × diversification cleanliness, partial = half weight): VST (partial, 50.7%→25.3 weighted) leads on raw upside but is honesty-flagged; among clean names UNH, PG, NEM, DUK lead the actionable list.

Note: book just added its first genuine non-AI-capex names in this book's history (BX financials, TXN diversified analog, FLTW Taiwan ETF), pulling AI-capex concentration from 93.6% to 88.96% of equity — directionally the right move even before this bench becomes buyable.

```json
{"session_read":{"futures":{"es_pct":-0.224,"nq_pct":-0.155},"asia":{},"europe":{},"adr_gap_flags":[],"headline_scan":[],"note":"weekend run, no live session -- Friday close only: SPX -0.17%, NDX -0.28%, SMH -0.22%, VIX -2.60% to 14.25"},
 "sentiment_narrative":"Score 82.9 EXTREME_GREED (up from 78.4 last run, 66.2 on 08-10). NDX RSI rose to 73.1 from 63.3 -- the 08-10 'low-vol complacency, not momentum' read no longer holds; volatility (VIX sub 96.0) and momentum (RSI sub 73.1) are now stretched together, alongside MA125 (91.7) and proximity-to-high (98.4). yield_trend (55.5) is the only unstretched component. action_hint=propose profit-booking on overweight/breach names.",
 "diversifier_candidates":{
   "NEM":{"price_usd":117.76,"target_usd":133.0,"upside_pct":12.9,"thesis":"Gold miner, zero AI-capex overlap, beta 0.50","status":"active","clean_diversifier":true},
   "VST":{"price_usd":148.13,"target_usd":223.17,"upside_pct":50.7,"thesis":"Merchant power gen, AI-load-adjacent -- not a clean diversifier","status":"active","clean_diversifier":false},
   "UNH":{"price_usd":401.73,"target_usd":471.65,"upside_pct":17.4,"thesis":"Managed care rebound, no capex correlation, beta 0.63","status":"active","clean_diversifier":true},
   "PG":{"price_usd":144.55,"target_usd":163.35,"upside_pct":13.0,"thesis":"Staples ballast, low beta 0.38","status":"active","clean_diversifier":true},
   "LLY":{"price_usd":1180.16,"target_usd":1270.37,"upside_pct":7.6,"thesis":"Pharma/GLP-1, decoupled from semis, beta 0.51","status":"active","clean_diversifier":true},
   "DUK":{"price_usd":123.92,"target_usd":138.61,"upside_pct":11.9,"thesis":"Regulated utility, rate-base growth, beta 0.37","status":"active","clean_diversifier":true},
   "SO":{"price_usd":92.80,"target_usd":101.45,"upside_pct":9.3,"thesis":"Regulated SE utility, defensive, beta 0.33","status":"active","clean_diversifier":true},
   "JNJ":{"price_usd":260.35,"target_usd":269.95,"upside_pct":3.7,"thesis":"Diversified pharma/medtech, near 52wk high, beta 0.23","status":"active","clean_diversifier":true},
   "KO":{"price_usd":87.71,"target_usd":87.35,"upside_pct":-0.4,"thesis":"Staples, price now above stale target -- needs refresh","status":"stale","clean_diversifier":true}
 },
 "data_quality":["weekend run: no Asian/European session, no ADR gap-risk read, no headline scan possible -- first fresh data point is Monday pre-market","analyst mean targets carried from prior run for all 9 candidates -- this session's yfinance get_stock_summary/get_key_stats calls did not return a targetMeanPrice field; only live prices were refreshed","KO target ($87.35) is now below live price ($87.71) -- second consecutive stale run, needs a real target refresh or drop next run per 2-run stale rule","bench is not actionable this run -- book cash is $12 (0.028%) vs [5,15]% policy band, no dry powder to deploy into any candidate"]}
```

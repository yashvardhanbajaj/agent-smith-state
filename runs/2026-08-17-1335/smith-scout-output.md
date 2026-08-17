# Market Scout — Deep Review, 2026-08-17 (Monday pre-open, gate AMBIGUOUS)

## 1. Session Read

**US futures:** ES +0.17%, NQ +0.56% — mildly positive open implied, tech (NQ) leading. Futures do not corroborate the VIX pop; this reads as a headline-driven vol spike, not a risk-off signal.

**VIX:** 14.93, +4.77% on the day — but still just above the 52-week low (13.38) and far from the 35.3 stress ceiling. The move is real (it's what disqualified STABILIZING and produced the AMBIGUOUS gate) but the level is unremarkable in a 1-year context.

**Asian session (closed):**
- Nikkei +0.74% — unremarkable.
- KOSPI +2.42% — notable, driven in large part by SK hynix's own +3.26% move (see ADR flag below); relevant to the SKHY holding (4.28% wt).
- TAIEX +0.10% — flat; no signal for TSM (5.79% wt) or FLTW (2.31% wt).
- Hang Seng proxy (9988.HK, BABA's HK-listed shares) +2.42% — notable for the small BABA position (0.56% wt).

**European session (open during this run) — home-listing leads for ADR holdings:**
- ASML.AS +3.0% overnight (€1579.6 → €1627.2) — **expect ASML to gap up at the US open** (4.24% wt, a top-5 position).
- STMPA.PA +3.7% overnight (€46.655 → €48.385) — **expect STM to gap up at the US open** (2.52% wt).
- STOXX50 +0.47% — broad European tape unremarkable outside these two single names.

**ADR gap-risk summary — holdings carrying overnight gap risk today:** ASML (+3.0% home listing), STM (+3.7% home listing), SKHY (+3.3% home listing / SK hynix), BABA (+2.4% HK listing, minor weight). All four should be expected to open notably above Friday's US close.

**Headline scan:** No dedicated news/headline tool was used this run (budget + tool-scope guardrail) — flagging is done via price-action proxies (the home-listing gaps above) rather than text-headline confirmation. No overnight US-market headline was independently verified for any holding; smith-signals owns per-holding depth and should confirm the driver behind the ASML/STM/SKHY moves before the strategist sizes anything off them.

## 2. Sentiment Narrative

The compute script has the composite at 81.8, still in **extreme_greed** (unchanged band vs the prior run). The score is being driven by a market that is technically stretched even though today's tape looks calm: SPX (7785.76) sits within 0.4% of its 52-week high (7816.7) and 7.8% above its 125-day moving average (7221.58); NDX RSI14 is at 73.1, deep into overbought territory. The VIX sub-component still scores 92.9/100 toward greed because the *level* (14.93) is near a 1-year low even though today's daily change is a +4.77% pop — the score reacts to the regime, not the day's headline move. Yield trend is the only middling component (55.5, US10Y +11.1bps over the month — a mild headwind, not a shock). **Action_hint is non-null: "propose profit-booking on overweight/breach names."** Plainly, this run's data supports the strategist actively looking for trims on names that are overweight-vs-policy or that have breached risk bands — this is not a signal to add risk, and it is not the strategist's call to size, only to act on if the drift/breach tables independently support it.

## 3. Diversifier Bench (ranked: clean diversifiers by upside%, partial diversifiers discounted to the bottom)

| Ticker | Price (USD) | Target | Upside % | Mini-thesis | Status | Diversifier flag |
|---|---|---|---|---|---|---|
| UNH | $401.73 | $471.65 | 17.4% | Managed care rebound, no capex correlation, beta 0.63 | active | clean |
| PG | $144.55 | $163.35 | 13.0% | Staples ballast, beta 0.38 | active | clean |
| NEM | $117.76 | $133.00 | 12.9% | Gold miner, zero AI-capex overlap, beta 0.50 | active | clean |
| DUK | $123.92 | $138.61 | 11.9% | Regulated utility, beta 0.37 | active | clean |
| SO | $92.80 | $101.45 | 9.3% | Regulated SE utility, beta 0.33 | active | clean |
| LLY | $1,180.16 | $1,270.37 | 7.6% | Pharma/GLP-1, decoupled from semis, beta 0.51 | active | clean |
| JNJ | $260.35 | $269.95 | 3.7% | Diversified pharma/medtech, beta 0.23 | active | clean |
| VST | $148.13 | $223.17 | 50.7% | Merchant power gen; live beta 1.43 confirms AI-load adjacency | active | **partial — not a clean diversifier, ranked last despite raw upside** |

Notes: all 8 candidates re-priced live via yfinance this run; every price matched the prior state snapshot exactly (market is still pre-open, so "live" = last close, as expected). Analyst target/upside figures are carried forward unchanged from state since price didn't move and no fresher target-price field was available from this run's yfinance calls (get_stock_summary/get_key_stats/get_recommendations expose PE, dividend, and buy/hold counts but not targetMeanPrice directly — see data_quality). Analyst breadth check via get_recommendations confirms all 8 still carry active coverage (no stale-candidate drops this run).

```json
{"session_read":{"futures":{"es_pct":0.17,"nq_pct":0.56},"asia":{"nikkei_pct":0.74,"kospi_pct":2.42,"taiex_pct":0.10,"sk_hynix_home_pct":3.26,"baba_hk_pct":2.42},"europe":{"asml_as_pct":3.01,"stmpa_pa_pct":3.71,"stoxx50_pct":0.47},"adr_gap_flags":["ASML.AS +3.0% overnight -- expect ASML (4.24% wt) to gap up at the US open","STMPA.PA +3.7% overnight -- expect STM (2.52% wt) to gap up at the US open","000660.KS (SK hynix) +3.3% overnight -- expect SKHY (4.28% wt) to gap up at the US open","9988.HK (BABA-W) +2.4% overnight -- expect BABA (0.56% wt) to gap up at the US open"],"headline_scan":[]},
 "sentiment_narrative":"Composite 81.8, extreme_greed (unchanged band). SPX within 0.4% of 52w high, 7.8% above 125dma, NDX RSI14 73.1 overbought; VIX sub-score high (92.9) because the level (14.93) is still near its 1yr low despite today's +4.77% daily pop. Yield trend mild headwind (55.5). action_hint non-null: propose profit-booking on overweight/breach names -- strategist should look for trims, not adds, though sizing is the strategist's call.",
 "diversifier_candidates":{"UNH":{"price_usd":401.73,"target_usd":471.65,"upside_pct":17.4,"thesis":"Managed care rebound, no capex correlation, beta 0.63","status":"active","clean_diversifier":true},"PG":{"price_usd":144.55,"target_usd":163.35,"upside_pct":13.0,"thesis":"Staples ballast, beta 0.38","status":"active","clean_diversifier":true},"NEM":{"price_usd":117.76,"target_usd":133.0,"upside_pct":12.9,"thesis":"Gold miner, zero AI-capex overlap, beta 0.50","status":"active","clean_diversifier":true},"DUK":{"price_usd":123.92,"target_usd":138.61,"upside_pct":11.9,"thesis":"Regulated utility, beta 0.37","status":"active","clean_diversifier":true},"SO":{"price_usd":92.8,"target_usd":101.45,"upside_pct":9.3,"thesis":"Regulated SE utility, beta 0.33","status":"active","clean_diversifier":true},"LLY":{"price_usd":1180.16,"target_usd":1270.37,"upside_pct":7.6,"thesis":"Pharma/GLP-1, decoupled from semis, beta 0.51","status":"active","clean_diversifier":true},"JNJ":{"price_usd":260.35,"target_usd":269.95,"upside_pct":3.7,"thesis":"Diversified pharma/medtech, beta 0.23","status":"active","clean_diversifier":true},"VST":{"price_usd":148.13,"target_usd":223.17,"upside_pct":50.7,"thesis":"Merchant power gen; live beta 1.43 confirms AI-load adjacency -- NOT a clean diversifier","status":"active","clean_diversifier":false}},
 "data_quality":["Live yfinance prices for all 8 diversifier candidates matched prior state exactly (pre-open session, last close = prior close, as expected)","No targetMeanPrice field surfaced from get_stock_summary/get_key_stats/get_recommendations this run -- target_usd/upside_pct carried forward unchanged from state rather than re-derived; flag for future run if a target-bearing tool becomes available","No dedicated news/headline search tool used for the overnight US-holdings headline scan -- ADR gap flags are price-action-derived (home-listing % moves), not headline-confirmed; smith-signals should confirm drivers before the strategist sizes off these moves"]}
```

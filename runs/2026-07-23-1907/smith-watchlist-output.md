# Watchlist & Market Context — 2026-07-23 (quick sweep)

## 1. Watchlist scan (US only, entry setups) — slice: cursor 30→45 (ITA, APA, UHS, LLY, FIG, ODD, NET, MKSI, SNPS, ROBO, WDC, IBM, RMBS, UMC, MCHP)

- watchlist | SNPS | OVERSOLD BOUNCE | pos 0.03 (near 52w low $366 vs $374.48) | mean target $563.99 (23 analysts) | upside +33.6% | news: Benchmark initiated Buy $570 PT (16 Jul); Strong Buy reiterated despite Russell index removal (09 Jul); Piper Sandler upgrade to Overweight $550 (23 Jun)
- watchlist | UHS | OVERSOLD BOUNCE | pos 0.09 | mean target $206.18 (22 analysts) | upside +27.4% | news: shares rose on proposed 2.4% CMS payment rate increase (02 Jul)
- watchlist | IBM | OVERSOLD BOUNCE | pos 0.01 (sitting at 52w low $204.44) | mean target $273.75 (24 analysts) | upside +24.8% | news: stock plunged ~25% on Q2 miss/guidance (14 Jul); JPMorgan Overweight $291 PT (24 Jun); Morgan Stanley PT $267 (27 Jun) — mixed: fundamental miss vs. analyst support, treat as higher-risk bounce
- watchlist | FIG | OVERSOLD BOUNCE (partial) | pos 0.04 | mean target N/A (INDmoney analyst_forecast empty for FIG) | news: BofA upgraded to Buy, $30 PT (07 Jul); institutional buying + AI optimism (13 Jul) — no consensus upside figure available, flagged in data_quality
- watchlist | MCHP | TARGET GAP | pos 0.63 | mean target $113.38 (32 analysts) | upside +25.2% | news: AI-driven data-center product growth, earnings-beat setup (13–16 Jul)
- watchlist | RMBS | TARGET GAP | pos 0.38 | mean target $149.00 (12 analysts) | upside +29.8% | news: Q1 adj. EPS beat ($0.63 vs $0.59 y/y), margin softened to 42% (28 Apr, stale — no newer catalyst this slice)

No setups: APA (upside 14.3%, just under threshold), UHS-adjacent ITA/ROBO (ETFs, no analyst data), ODD (deep oversold pos 0.11 but analyst mean target $10.25 is BELOW price — bearish, not a bounce), NET (upside -5.9%), UMC (upside -31.4% despite mid-range pos), WDC (upside 12.3%, under threshold).

## 2. Earnings calendar (next 7 days, quick mode)
- yfinance get_earnings_calendar (2026-07-23 to 2026-07-30) returned empty again — G20 reconfirmed, not a new finding.
- Holdings rows / earnings_calendar cache were not embedded in this run's dispatch; without them I cannot identify which held tickers fall inside the 7-day window without guessing. No dates fabricated. Recommend orchestrator include the cache slice next run so only unconfirmed/stale names need re-checking.

## 3. Data quality
```json
{"watchlist_setups":[
  {"ticker":"SNPS","type":"oversold_bounce","upside_pct":33.6,"pos":0.03},
  {"ticker":"UHS","type":"oversold_bounce","upside_pct":27.4,"pos":0.09},
  {"ticker":"IBM","type":"oversold_bounce","upside_pct":24.8,"pos":0.01},
  {"ticker":"FIG","type":"oversold_bounce","upside_pct":null,"pos":0.04},
  {"ticker":"MCHP","type":"target_gap","upside_pct":25.2,"pos":0.63},
  {"ticker":"RMBS","type":"target_gap","upside_pct":29.8,"pos":0.38}],
 "earnings_calendar_updates":{},
 "watchlist_scan_cursor":45,
 "data_quality":[
   "G20 reconfirmed: yfinance get_earnings_calendar returned empty for 2026-07-23..2026-07-30 (second consecutive empty result).",
   "Earnings section skipped in full: holdings rows / earnings_calendar cache not embedded in this dispatch, so 7-day window against held tickers could not be checked — no dates guessed.",
   "FIG: analyst_forecast block empty on INDmoney (no consensus mean target) despite deep oversold position (pos 0.04) and a BofA Buy upgrade ($30 PT, single-analyst) — reported without upside_pct.",
   "IBM oversold-bounce is mixed signal: pos 0.01 driven partly by a post-earnings ~25% guidance-miss plunge (14 Jul), not pure technical oversold — flagged as higher risk.",
   "ITA and ROBO (ETFs in this slice) carry no analyst_forecast data on INDmoney — excluded from setup scan by design (no target price to gap-check)."
 ]}
```

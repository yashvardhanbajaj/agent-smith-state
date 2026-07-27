# Watchlist & Market Context — 2026-07-27 (quick sweep)

## 1. Watchlist Setups (US only, entry setups — shopping list, not holdings review)
Scan slice: watchlist indices 60-81 (cursor rotation), holdings-overlap tickers excluded.

**OVERSOLD BOUNCE (pos≤0.3 + positive news/upside>15%)**
- CRWV (CoreWeave): pos 0.09 (52w 63.80-153.20, px 71.88). No formal analyst mean target in feed (analyst_forecast empty), but news flow strongly positive — one analyst cited ~79% upside. Headlines: "CoreWeave Stock Rallies on Analyst Upgrades and AI Demand" (07-22); "CoreWeave Secures Major Financing for AI Growth" ($8.5B DDTL, 07-21); "ARK Invest Expands Stake in CoreWeave" (07-19). Caveat: -11.4% today, high volatility name.
- PATH (UiPath): pos 0.154 (52w 9.20-19.84, px 10.84). Mean target $13.25, upside 18.2%. Headline: "UiPath Reports Strong Q1 Earnings Driven by AI Demand" (raised FY guidance).
- ADBE (Adobe): pos 0.188 (52w 190.12-376.16, px 225.11). Mean target $269.61, upside 16.5%. Mixed but recent positive: +6.1% today; HSBC upgrade to Buy $308 offset by Morgan Stanley downgrade on leadership risk.
- AEM (Agnico Eagle): pos 0.172 (52w 122.32-255.24, px 145.13). Mean target $220.12, upside 34.1%. Headline: "Agnico Eagle Reports Strong Cash Flow Growth" (Q1 FCF +23% YoY).
- SHOP (Shopify): pos 0.224 (52w 94.00-182.19, px 113.75). Mean target $148.39, upside 23.3%. Headline: "Jefferies Upgrades Shopify, Boosts Price Target Significantly" ($160 PT, AI-commerce thesis).

**NEARING BREAKOUT (pos≥0.90 with catalyst)**
- AAPL (Apple): pos 0.985 (52w 201.50-334.99, px 333.02), near all-time high. Catalyst: fiscal Q3 earnings 07-30, China AI approval, $100B buyback. Note: mean target $318.81 is actually below spot (-4.5%) — momentum/breakout thesis, not value.

**TARGET GAP ≥15% upside**
- AMZN: mean $313.13, upside 25.9%, pos 0.44.
- APLD: mean $73.05, upside 62.8% (widest gap scanned), pos 0.43 — speculative AI-datacenter name, wide loss profile per news.
- GLW: mean $215.47, upside 31.9%, pos 0.42 — note: exited from holdings 07-24, this is a re-entry candidate only. Earnings 07-28.
- INTC: mean $115.65, upside 20.2%, pos 0.59.
- MCHP: mean $113.08, upside 30.3%, pos 0.53.
- CORZ: mean $33.36, upside 31.8%, pos 0.57.
- GOOG: mean $421.79, upside 24.4%, pos 0.60 (earnings already reported 07-22).
- NEM: mean $129.46, upside 28.0%, pos 0.43.

No setups found in: UMC (analyst upside is -19.9%, overvalued — excluded).

## 2. Earnings Calendar (holdings, next 7 days — quick mode window)
All three confirmed dates already cached and still future; no re-fetch needed.
- LRCX: 2026-07-29, confirmed (cache, prior source).
- TER: 2026-07-28, confirmed (cache, prior source).
- QCOM: 2026-07-29, confirmed (cache, prior source).
- GLW: cache entry retired — GLW no longer held (exited 07-24). Corning's 07-28 date remains valid for watchlist tracking only (see GLW target-gap note above), not as a portfolio earnings-risk item.
- No newly-confirmed dates found for other current holdings this run (out of 7-day window scope).

## 3. Rolling Performance
Per compute_attribution.json: 1m/3m/6m/12m rolling windows are null — only 14 ledger rows exist, insufficient history. Reporting as-is, not estimated.

## Data Quality
- CRWV: analyst_forecast segment returned empty from get_us_stocks_details — no formal mean target/upside; oversold call rests on price-position + news tone only.
- GLW retained on watchlist for re-entry tracking despite full exit; orchestrator should drop it from the earnings_calendar cache per instructions.
- G20 (earnings source reliability), G19 (ETF-constituent tool blocked), G3 (net worth lag ~12%) — carried from known_gaps, no new evidence this run.
- Full watchlist has ~93 unique US entries (3 lists, 1 null slot); this run covered slice [60,81]; ~11 names remain before a full wrap (next slice starts at 82: PENG onward).

```json
{"watchlist_setups":[
  {"ticker":"CRWV","type":"oversold_bounce","upside_pct":null,"pos":0.09},
  {"ticker":"PATH","type":"oversold_bounce","upside_pct":18.19,"pos":0.15},
  {"ticker":"ADBE","type":"oversold_bounce","upside_pct":16.51,"pos":0.19},
  {"ticker":"AEM","type":"oversold_bounce","upside_pct":34.07,"pos":0.17},
  {"ticker":"SHOP","type":"oversold_bounce","upside_pct":23.34,"pos":0.22},
  {"ticker":"AAPL","type":"nearing_breakout","upside_pct":-4.46,"pos":0.99},
  {"ticker":"AMZN","type":"target_gap","upside_pct":25.87,"pos":0.44},
  {"ticker":"APLD","type":"target_gap","upside_pct":62.78,"pos":0.43},
  {"ticker":"GLW","type":"target_gap","upside_pct":31.94,"pos":0.42},
  {"ticker":"INTC","type":"target_gap","upside_pct":20.17,"pos":0.59},
  {"ticker":"MCHP","type":"target_gap","upside_pct":30.26,"pos":0.53},
  {"ticker":"CORZ","type":"target_gap","upside_pct":31.80,"pos":0.57},
  {"ticker":"GOOG","type":"target_gap","upside_pct":24.35,"pos":0.60},
  {"ticker":"NEM","type":"target_gap","upside_pct":28.02,"pos":0.43}
],
 "earnings_calendar_updates":{},
 "watchlist_scan_cursor":82,
 "data_quality":["CRWV analyst_forecast empty from feed — no formal target/upside","GLW retired from earnings_calendar cache (no longer held)","G20/G19/G3 known gaps unchanged this run","~11 watchlist names remain before full-list wrap"]}
```

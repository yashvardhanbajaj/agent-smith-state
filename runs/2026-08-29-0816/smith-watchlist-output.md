# Watchlist & Market Context — 2026-08-29 (deep, weekend)

## Watchlist setups (scan slice: index 45-59 of 139 deduped US watchlist names)

- **BWXT** — OVERSOLD BOUNCE: pos 0.05 (152.85 vs 52wk 147.74-241.82), JPMorgan overweight initiation (27-Jul) + nuclear isotope expansion news. Mean target $234.45, upside 34.8%.
- **MKSI** — TARGET GAP: mean target $411.31 vs $255.76, upside 37.8%. pos 0.45 (not oversold).
- **STM** — TARGET GAP: mean target $74.96 vs $49.38, upside 34.1%. Mixed news (Q3 guide-down 27-Jul offset by strong Q2 print 14-Aug raising data-centre revenue targets). pos 0.47.
- **SNPS** — TARGET GAP: mean target $560.17 vs $442.61, upside 21.0%. Baird upgrade post strong Q3 print (27-Aug). pos 0.31 (borderline oversold).
- **GLNG** — TARGET GAP: mean target $63.94 vs $50.29, upside 21.4%. pos 0.67 (thin coverage, 3 analysts).
- **LRCX** — TARGET GAP: mean target $371.19 vs $301.90, upside 18.7% (23 analysts, Strong Buy). Note: LRCX is also a held position (3.02% weight) — flagging per instructions since it also sits on the watchlist, not a new entry idea.
- **FIG** — OVERSOLD BOUNCE: pos 0.22 (28.82 vs 52wk 16.60-72.11), BofA upgrade to Buy (07-Jul, $30 target) on AI optimism. Upside to consensus target ~7.6% (below 15% threshold — flagged on the upgrade trigger, not target gap).

No setups on APA, LLY, NET, UHS (upside <15%, no oversold trigger), ODD (oversold but negative news — guide-down).

## Earnings calendar (holdings, next 14 days: through 2026-09-12)

- **AVGO** — 2026-09-02, confirmed (cached, indmoney-news reconfirmed 2026-08-24). No re-check needed.
- **CIEN** — 2026-09-03, confirmed (cached, smith-watchlist 2026-08-26). No re-check needed.
- No other holdings report in this window. (NVDA 08-26 and MRVL 08-27 already passed.)

## Data quality
- Watchlist has 3 separate lists totaling 139 deduped US tickers; this run covered indices 45-59 (BWXT, STM, GLNG, ITA*, APA, UHS, LLY, FIG, ODD, NET, CIEN*, MKSI, SNPS, LRCX, EWY*) — *ITA/EWY skipped (ETFs, no single-name setup logic), CIEN skipped (already a holding + earnings-only relevance, no target-price entry check run).
- FIG has no target_price object returned by the API (only consensus target_prc); upside computed manually from consensus figure, treat as approximate.

```json
{"watchlist_setups":[
  {"ticker":"BWXT","type":"oversold_bounce","upside_pct":34.8,"pos":0.05},
  {"ticker":"MKSI","type":"target_gap","upside_pct":37.8,"pos":0.45},
  {"ticker":"STM","type":"target_gap","upside_pct":34.1,"pos":0.47},
  {"ticker":"SNPS","type":"target_gap","upside_pct":21.0,"pos":0.31},
  {"ticker":"GLNG","type":"target_gap","upside_pct":21.4,"pos":0.67},
  {"ticker":"LRCX","type":"target_gap","upside_pct":18.7,"pos":0.60},
  {"ticker":"FIG","type":"oversold_bounce","upside_pct":7.6,"pos":0.22}
],
 "earnings_calendar_updates":{},
 "watchlist_scan_cursor":60,
 "data_quality":["Watchlist scan covered indices 45-59 of 139 deduped names; full-list coverage accrues over several runs.","ITA and EWY skipped as ETFs (no single-name entry-setup logic applies).","FIG upside_pct approximated from consensus target_prc (no target_price object returned by API).","LRCX and STM/CIEN watchlist entries overlap existing holdings; flagged per shopping-list rule regardless."]}
```

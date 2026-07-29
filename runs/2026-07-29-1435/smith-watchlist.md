# Watchlist & Market Context — 2026-07-29 (quick, ESCALATING gate)

## 1. Watchlist setups (US only, cursor 75→90 slice: CORZ,AAPL,AEM,NEM,ASML,ADBE,AVGO,SHOP,PENG,PLTR,TSLA,NVDA,QCOM,OLED,AMD + semicap cross-check LRCX,KLAC,AMAT,MU,TSM,MRVL,SNPS)

- **AEM** — watchlist, OVERSOLD BOUNCE. pos 0.16 (143.71 vs 52w range 122.68–255.24). Mean target 220.12, upside 34.7%. News: "Agnico Eagle Reports Strong Cash Flow Growth" (positive, 30 Jun).
- **PLTR** — watchlist, OVERSOLD BOUNCE. pos 0.17 (123.53 vs 106.37–207.52), down -6.1% today. Mean target 182.20, upside 32.2%. News: "Mixed Sentiment Ahead of Earnings" (neutral) — qualifies on upside, not on news tone.
- **OLED** — watchlist, OVERSOLD BOUNCE. pos 0.07 — only 6.7% above 52w low (77.15), price 82.29. Mean target 125.89, upside 34.6%. No recent news (last item stale, Nov-2025); flagging on price position + target gap only.
- **CORZ** — watchlist, TARGET GAP. Mean target 33.36, upside 37.8%, pos 0.46. No fresh news this window.
- **NEM** — watchlist, TARGET GAP. Mean target 129.27, upside 29.2%, pos 0.41. Mixed news (target cut 15-Jul vs upgrade 14-Jul).

No setups on: AAPL, ASML, ADBE, AVGO, SHOP, TSLA, NVDA, QCOM, AMD, LRCX, KLAC, AMAT, MU, TSM, MRVL, SNPS this slice (several of these are book holdings, not shopping-list candidates — excluded from setups by design).

**Support-level watch (context only, not setups):** SMH -3.45% pre-market is dragging the whole semicap/AI-capex complex — AMAT -7.8%, AMD -8.2%, MRVL -7.8%, LRCX -7.5%, MU -8.9%, KLAC -6.2%, QCOM -4.2%, ASML -4.4% pre-open. None are testing 52-week lows yet (all still 20%+ above their lows) — this is a sentiment/momentum air-pocket, not a support break so far. OLED (watchlist, see above) is the one name genuinely close to its 52-week low. Worth re-checking at the open if SMH weakness persists.

## 2. Earnings calendar (holdings, ≤7d window, quick mode)

- **LRCX — 2026-07-29 (TODAY), confirmed** (fmp-calendar). Unchanged.
- **QCOM — 2026-07-29 (TODAY), confirmed** (fmp-calendar). Unchanged.
- **VRT — 2026-07-29 (TODAY), confirmed** — CORRECTED from cached 07-30. Verified via stockanalysis.com/stocks/VRT/ ("Earnings Date Jul 29, 2026", Q2 report). Source: web.
- **CLS — already reported.** Verified via stockanalysis.com/stocks/CLS/: Q2 2026 results out ~07-27/07-28, beat expectations. Cached date was directionally right; marking confirmed. Source: web.
- **COHR — 2026-08-05, still unconfirmed** (cadence). 4.19% book weight, ≥3% threshold — qualifies for a web check but budget was spent on VRT/CLS (higher urgency, same-day/passed). Carry to next run.

**Flag: three holdings (LRCX, QCOM, VRT) now confirmed reporting the SAME DAY as the FOMC decision (2026-07-29)** — a materially higher-vol day than the calendar previously showed (VRT was thought to be 07-30).

```json
{"watchlist_setups":[{"ticker":"AEM","type":"oversold_bounce","upside_pct":34.71,"pos":0.16},{"ticker":"PLTR","type":"oversold_bounce","upside_pct":32.2,"pos":0.17},{"ticker":"OLED","type":"oversold_bounce","upside_pct":34.63,"pos":0.07},{"ticker":"CORZ","type":"target_gap","upside_pct":37.8,"pos":0.46},{"ticker":"NEM","type":"target_gap","upside_pct":29.2,"pos":0.41}],
 "earnings_calendar_updates":{"VRT":{"date":"2026-07-29","confirmed":true,"source":"web"},"CLS":{"date":"2026-07-28","confirmed":true,"source":"web"}},
 "watchlist_scan_cursor":90,
 "data_quality":["COHR (4.19% weight, ≥3% threshold) still unconfirmed after INDmoney+yfinance; WebFetch budget spent on VRT/CLS instead — carry to next run","yfinance get_earnings_calendar returned empty for 2026-07-28→08-05 window (tool limitation, not a data signal)","OLED news feed stale (last item Nov-2025) — oversold flag rests on price position + target gap only, not corroborating news","Support-level check limited to 52w high/low (no moving-average data available) — 'approaching support' read is directional, not a technical breakdown call","AMAT/MRVL/QCOM/AVGO/TSM/ASML/AMD/MU/LRCX excluded from watchlist setups — confirmed as existing book holdings via holdings.json, not shopping-list candidates"]}
```

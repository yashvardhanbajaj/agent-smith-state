# Watchlist & Market Context — Quick Sweep 2026-07-24

## 1. Watchlist Setups (rotation slice idx 45-59, cursor was 45)

- SNPS — watchlist — OVERSOLD BOUNCE: pos=0.03 (near 52w low $366 vs $373.52), mean target $563.99, upside +33.8%. Benchmark initiated Buy (16 Jul); Piper Sandler upgraded to Overweight (23 Jun). 42% rev growth reported.
- FIG — watchlist — OVERSOLD BOUNCE: pos=0.03 (near 52w low $16.60). No analyst consensus target available (upside N/A). BofA upgraded to Buy w/ $30 PT (07 Jul); shares +11.9% on institutional buying (13 Jul).
- RMBS — watchlist — TARGET GAP: mean target $149.00, upside +30.7%. pos=0.36. No fresh catalyst news this cycle (last item 28 Apr).
- CIEN — watchlist (also held) — TARGET GAP: mean target $565.71, upside +28.0%. AI PoC w/ Telefónica Deutschland boosting growth read (07 Jul); insider sales flagged (15 Jul, neutral).
- GLW — watchlist (also held) — TARGET GAP: mean target $214.07, upside +27.1%. Q2 earnings 28 Jul imminent; Amazon fiber-optics supply deal (25 Jun).
- BABA (exited today) — watchlist re-entry candidate — OVERSOLD BOUNCE: pos=0.22, mean target $190.47, upside +40.1%. Apple Qwen AI integration rally (+27% this month per news), but ongoing securities-fraud investigation and Pentagon military-company designation are live overhangs.
- CLS — watchlist (also held) — TARGET GAP: mean target $448.00, upside +25.3%. Broadcom/OpenAI Jalapeño chip contribution lifted shares (24 Jun); AI datacomm demand strong.
- LITE (exited today) — watchlist re-entry candidate — TARGET GAP: mean target $1104.89, upside +24.6%. Nvidia optical-interconnect tailwind cited (03 Jun); no fresh news since 10 Jun.
- GOOG (exited today) — watchlist re-entry candidate — TARGET GAP: mean target $430.07, upside +26.0%. Q2 earnings already reported 22 Jul; today's -6.89% move is the post-earnings reaction (matches cached earnings date).
- COHR — watchlist (also held) — TARGET GAP: mean target $391.45, upside +20.0%. Datacenter segment revenue +40.6% YoY (12 Jul); Sherman facility $650M expansion.
- IBM — watchlist — TARGET GAP (mixed signal): pos=0.06 (near 52w low), mean target $262.85, upside +21.4%. CAUTION: Q2 stock plunged -25% on 14 Jul after revenue/EPS miss and lowered guidance — this is a post-crash value setup, not a clean oversold bounce; news flow since is negative-to-neutral.
- STM (exited today, -18.67%) — watchlist re-entry candidate — TARGET GAP: mean target $73.36, upside +27.1%. pos=0.54 (52w range still elevated, not a 52w-low bounce). News confirms Q2 2026 results reported 23 Jul — today's crash is the earnings reaction, consistent with why the book exited.
- META (exited today) — watchlist re-entry candidate — TARGET GAP: pos=0.31 (borderline oversold), mean target $826.01, upside +26.6%. Q2 earnings news dated 21-23 Jul conflicting on whether already reported — treat earnings status as unclear.
- MKSI — watchlist — TARGET GAP (borderline): mean target $406.92, upside +15.1%.

No setup: NET (upside -1.3%), ODD (negative guidance, upside -51.5%), WDC (upside +11.9%, <15%), LRCX (upside +13.2%, <15%, held), ROBO (ETF, no analyst coverage).

**watchlist_scan_cursor advances to 60** (next slice starts at GLW in the de-duplicated 129-name combined watchlist).

## 2. Earnings Calendar (holdings, next 7 days — quick mode, through 2026-07-31)

- LRCX — 2026-07-29 — confirmed (cache, unchanged)
- GLW — 2026-07-28 — confirmed (source: news, "Corning...report Q2 earnings on July 28")
- TER — 2026-07-28 — confirmed (source: web, stockanalysis.com — 3.12% book weight, both INDmoney news and yfinance calendar were silent so spent the one WebFetch)
- QCOM — 2026-07-29 — confirmed (source: news, "set to release its Q3 2026 earnings on July 29")

Already reported this cycle (outside window, no action): TSM, ASML, SNDK, NVDA, AVGO, GOOG, STM, MU (per news; MU's next report is FY26 Q4, ~September).

## 3. JSON Tail

```json
{"watchlist_setups":[
 {"ticker":"SNPS","type":"oversold_bounce","upside_pct":33.8,"pos":0.03},
 {"ticker":"RMBS","type":"target_gap","upside_pct":30.7,"pos":0.36},
 {"ticker":"CIEN","type":"target_gap","upside_pct":28.0,"pos":0.58},
 {"ticker":"GLW","type":"target_gap","upside_pct":27.1,"pos":0.47},
 {"ticker":"BABA","type":"oversold_bounce_reentry","upside_pct":40.1,"pos":0.22},
 {"ticker":"CLS","type":"target_gap","upside_pct":25.3,"pos":0.55},
 {"ticker":"LITE","type":"target_gap_reentry","upside_pct":24.6,"pos":0.74},
 {"ticker":"GOOG","type":"target_gap_reentry","upside_pct":26.0,"pos":0.60},
 {"ticker":"COHR","type":"target_gap","upside_pct":20.0,"pos":0.64},
 {"ticker":"IBM","type":"target_gap_postcrash","upside_pct":21.4,"pos":0.06},
 {"ticker":"STM","type":"target_gap_reentry","upside_pct":27.1,"pos":0.54},
 {"ticker":"META","type":"target_gap_reentry","upside_pct":26.6,"pos":0.31},
 {"ticker":"MKSI","type":"target_gap","upside_pct":15.1,"pos":0.72}],
 "earnings_calendar_updates":{
 "GLW":{"date":"2026-07-28","confirmed":true,"source":"news"},
 "TER":{"date":"2026-07-28","confirmed":true,"source":"web"},
 "QCOM":{"date":"2026-07-29","confirmed":true,"source":"news"}},
 "watchlist_scan_cursor":60,
 "data_quality":[
 "yfinance get_earnings_calendar returned empty again (4th consecutive run) -- persistent tool/data gap (G20), not zero earnings.",
 "MU (5.49% weight) 7-day earnings window unconfirmed: stockanalysis.com returned a stale/past estimated date (2026-06-24) -- discarded as implausible (out of band); news confirms MU already reported this quarter, next report likely Sept FY26 Q4.",
 "FIG has no analyst_forecast/target-price coverage from INDmoney -- oversold setup (pos 0.03, BofA upgrade) reported without upside% since target unavailable.",
 "get_us_stocks_details caps at 10 symbols/call (undocumented) -- required more batched calls than planned.",
 "Watchlist cursor built by de-duplicating 3 INDmoney watchlists into one 129-name ordered list; index alignment assumes stable API ordering across runs."]}
```

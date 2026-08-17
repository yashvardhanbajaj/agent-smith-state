# Watchlist & Market Context — 2026-08-17 (deep)

## 1. Watchlist setups (US only, entry-scan slice: index 75-89 of consolidated watchlist, cursor advanced 75→90)

- **AMZN** — TARGET GAP: mean target $327.00 vs current $262.65, upside 19.68%, pos 0.73 (52w range $196.00–$287.20)
- **GOOG** — TARGET GAP: mean target $421.79 vs current $343.54, upside 18.55%, pos 0.71 (52w range $197.46–$404.47)
- **ASML** — TARGET GAP: mean target $2176.09 vs current $1844.08, upside 15.26%, pos 0.88 (52w range $716.20–$1999.96)
- **MU** — TARGET GAP: mean target $1501.98 vs current $971.66, upside 35.31%, pos 0.75 (52w range $113.46–$1255.00)
- **AVGO** — TARGET GAP: mean target $527.88 vs current $392.99, upside 25.55%, pos 0.52 (52w range $281.87–$495.00); note -5.94% pre-open move today, worth a signals-side look
- **CORZ** — TARGET GAP: mean target $37.12 vs current $20.18, upside 45.64%, pos 0.41 (52w range $13.14–$30.46); thin coverage (8 analysts)

No OVERSOLD BOUNCE or NEARING BREAKOUT setups in this slice — nothing at pos≤0.3 with positive catalyst, nothing at pos≥0.90 with catalyst (ASML closest at 0.88, no breakout catalyst confirmed).

Silence on: ADBE, PLTR, SHOP, AAPL, AEM, NEM, INTC, CRWV, PENG — no threshold met (CRWV, PENG have no analyst target data).

Prior-run existing setups could not be re-scanned this pass — no prior JSON tail was supplied in the slice; recommend orchestrator include it next run so open setups get freshness checks.

## 2. Earnings calendar — holdings within 14 days (2026-08-17 to 2026-08-31)

Confirmed, cached, no re-check needed:
- **NVDA** — 2026-08-26, confirmed (web, stockanalysis.com; checked 2026-08-16)
- **MRVL** — 2026-08-27, confirmed (indmoney-news; checked 2026-08-16)
- **BABA** — 2026-08-28, confirmed (web-verified; checked 2026-08-16)

Just outside the 14-day window: AVGO — 2026-09-02 (confirmed, cached, no action needed).

Checked and confirmed already-reported (no action, not in window): ARM (Q1 FY27 reported 2026-07-29, per news; next date not yet announced), CIEN (news references a recent earnings beat as of 2026-08-13 — already reported this cycle, next date unannounced).

Unconfirmed: **IREN** — no next earnings date found in INDmoney news; fiscal Q4 (June-end) typically reports late Aug/early Sept in prior years, but nothing confirms 2026 timing. IREN is 2.05% of book (below the 3%-weight threshold that would mandate a dedicated web check), so left as unconfirmed rather than guessed.

yfinance get_earnings_calendar returned an empty result for both 2026-08-17→08-31 and 2026-08-17→09-05 windows — likely unavailable/broken in this environment, not a true "no earnings" signal. Flagged below.

```json
{"watchlist_setups":[
  {"ticker":"AMZN","type":"target_gap","upside_pct":19.68,"pos":0.73},
  {"ticker":"GOOG","type":"target_gap","upside_pct":18.55,"pos":0.71},
  {"ticker":"ASML","type":"target_gap","upside_pct":15.26,"pos":0.88},
  {"ticker":"MU","type":"target_gap","upside_pct":35.31,"pos":0.75},
  {"ticker":"AVGO","type":"target_gap","upside_pct":25.55,"pos":0.52},
  {"ticker":"CORZ","type":"target_gap","upside_pct":45.64,"pos":0.41}
],
 "earnings_calendar_updates":{},
 "watchlist_scan_cursor":90,
 "data_quality":["yfinance get_earnings_calendar returned empty for 08-17→08-31 and 08-17→09-05 — likely broken/unavailable this session, not confirmation of no earnings","No prior JSON tail supplied in slice, so existing open setups from prior runs were not re-scanned for freshness this run","IREN next earnings date unconfirmed (below 3%-weight threshold for mandatory web verification)","get_us_stocks_details hit a 15-calls/min rate limit mid-run on the second batch; one retry succeeded"]}
```

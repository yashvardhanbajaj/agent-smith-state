# Watchlist & Market Context — Quick Sweep, 2026-07-15

## 1. Watchlist Setups (US only, entry candidates — not held)
Scanned rotating slice: watchlist indices 45-66 (SNPS, ROBO, WDC, IBM, COHR, LITE, RMBS, UMC, MCHP, PATH, APLD, AMZN, CRWV, INTC, GOOG), holdings excluded from scan (LRCX, CLS, GLW, TSM, SNDK, TER, GEV, MU skipped as already-held).

- **APLD** (Applied Digital) — TARGET GAP, mean target $73.36, upside 61.2%, pos 0.46. News: two hyperscaler lease deals since Jun ($5.2B + $12.7B rev potential), stock up on each.
- **RMBS** (Rambus) — TARGET GAP, mean target $144.57, upside 27.1%, pos 0.38.
- **LITE** (Lumentum) — TARGET GAP, mean target $1111.29, upside 26.7%, pos 0.73. News: Nvidia optical-interconnect partnership tailwind.
- **IBM** — OVERSOLD BOUNCE, mean target $294.94, upside 26.4%, pos 0.04 (52wk low $212, now $217). CAUTION: pos this low is from a -25.2% crash on 14-Jul Q2 miss (rev/EPS miss, hardware spending shift) — this is a post-earnings-gap oversold read, not a clean dip-buy; treat target upside with skepticism until guidance settles.
- **SNPS** (Synopsys) — OVERSOLD BOUNCE / TARGET GAP overlap, mean target $563.74, upside 24.5%, pos 0.18. News: Russell index removal + product discontinuation (neutral/negative) vs. Piper Sandler upgrade to $550 (23-Jun, positive) — mixed.
- **MCHP** (Microchip) — TARGET GAP, mean target $114, upside 23.6%, pos 0.67. News: AI datacenter product growth (PCIe Gen6 switch), fiscal Q4 net sales +35.1%.
- **AMZN** — TARGET GAP, mean target $312.91, upside 20.9%, pos 0.62. News: AWS +28% rev growth, strong Q2 setup.
- **COHR** (Coherent) — TARGET GAP, mean target $387.36, upside 19.8%, pos 0.64. News: Datacenter segment +40.6% YoY.
- **GOOG** — TARGET GAP (borderline), mean target $428.54, upside 16.6%, pos 0.79.

No setup: ROBO (ETF, no analyst target), WDC (upside only 7.1%), UMC (analyst target below price, -46.7%), CRWV (no analyst forecast data), INTC (target below price, -3.2%), PATH (pos 0.26 oversold but upside only 9.9%, no strong recent catalyst — below bar).

## 2. Earnings Calendar (holdings, next 7 days — quick mode window)
- **TSM — 2026-07-16 (TOMORROW), CONFIRMED** (cached, source prior run). 8.49% position — largest single-name earnings risk in the book this week.
- GLW — 2026-07-28, confirmed (cached) — outside 7-day quick window, no action.
- QCOM — 2026-07-29, confirmed (cached) — outside 7-day quick window, no action.
- All other 20 holdings: no confirmed earnings date found inside the 2026-07-15 to 2026-07-22 window; yfinance get_earnings returns historical EPS/quarter data only, not an explicit next-report date, so these are left "unconfirmed" rather than guessed.

## Data Quality
- yfinance get_earnings_calendar returned empty for the 07-15/07-22 date range; fell back to get_earnings (historical) which lacks an explicit next-report-date field — cannot positively confirm/deny earnings-in-window for non-cached holdings this run.
- get_us_stocks_details caps at 10 symbols/call (hard API limit) — batched into 2 calls of 8+7, not a violation of single-symbol looping.
- CRWV and ROBO have no analyst_forecast block from INDmoney — target/upside unavailable, excluded from setup scoring.
- No prior watchlist-setup tail was supplied this run, so "always re-scan existing setups" carryover could not be applied — first-available baseline starts now.

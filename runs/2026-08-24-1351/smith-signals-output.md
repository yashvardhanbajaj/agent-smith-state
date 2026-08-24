# Signal Scanner — Deep Review, 2026-08-24 pre-open (13:51 IST / 04:xx ET)

DEGRADATION NOTICE: atr20/rel-strength cache is STALE (last refreshed 2026-07-31/08-12, past 7d TTL, not refreshed this run — cost tradeoff on a 33-name book). Every move-based bucket below (STRONG UPTREND/DOWNTREND, MOMENTUM+VOLUME, PEER LEADER/LAGGARD) fell back to LEGACY ABSOLUTE thresholds (±4% day move, ±8pp relative strength), tagged **[unnormalized]**. day_atr_mult/rel_sigma are null throughout.

## MOMENTUM+VOLUME / STRONG DOWNTREND (move-based) [unnormalized]
- **BABA** — Fri -8.57%, pre-mkt -3.47% (2.1x legacy 4% bar). 0.6% weight (dust-adjacent, post stop-cascade). 2 distinct events: (1) "Alibaba Reports Mixed Earnings Amid AI Investment Surge" — 2026-08-20 — Q2 miss/AI-capex margin concern; (2) "Alibaba Raises $10.2 Billion for AI Expansion" — 2026-08-23 — dilutive capital raise. Mean target $189.61, +37.06% upside (TARGET GAP persists). NEW HEADWINDS (same 2 events). Journal already opened MOMENTUM+VOLUME today, $119.34.
- **MRVL** — Fri -5.57%, pre-mkt -3.43% (1.4x legacy bar). 4.77% weight. News flow is net POSITIVE in-window (Google partnership, 08-19/21) — reads as profit-taking after the pop, not a fundamental break; avoid the SanDisk-style trap. Real caution: 2 distinct insider-selling mentions — "Marvell Expands Google Partnership Amid Insider Selling" 2026-08-19, "Marvell Faces Insider Selling Amid Strong Growth Prospects" 2026-08-18 → INSIDER ACTIVITY (news-derived, see data_quality). TARGET GAP RESOLVED OUT this run: upside now only 7.87% (target $257.29 vs $237.04), was ≥15%. PEER LEADER +16.86pp vs SMH despite Friday's drop.
- **HOOD** — Fri +13.7%, pre-mkt -1.28% (3.4x legacy bar). 1.39% weight, starter-sized. Driver: "Robinhood Stock Surges Amid Bitcoin Rally and Regulation Hopes" — 2026-08-21 — crypto rally + regulatory-tailwind speculation. No dated catalyst found for the pre-market giveback — ordinary profit-taking, not a new story. Mean target $120.01, only 9.9% upside — richly valued post-spike.

## STRONG DOWNTREND (pos-based)
- **META** — pos 0.110 (near 52wk low $520.26, live $549.90). Unchanged since this morning's 08:55 touch. PEER LAGGARD -14.01pp vs XLK. 2.87% weight. NEW HEADWINDS: (1) "Meta Faces Lawsuit Amid Strong Advertising Growth" — 2026-08-22; (2) "Meta Faces Trials and AI Spending Challenges" — 2026-08-21 (trillion-dollar trial exposure + capex concern). Mean target $754.14, +27.08% upside — TARGET GAP persists.

## STRONG UPTREND
- **FLTW** — pos 0.821, 2.58% weight, no peer proxy (Taiwan ETF, no clean fit). No analyst target (ETF). Unchanged repeat.

## TARGET GAP
- **TXN** — NEW this run. Mean target $324.45, +18.52% upside, 2.03% weight. Consensus is HOLD (56% buy/36% hold/8% sell) — weakest conviction in the book; gap is price-depression (-10.1% 1m), not analyst enthusiasm.
- **SKHY** — mean target $245.5, ~50% implied upside. DATA QUALITY CAVEAT: 52wk-low returned $0.00 (implausible) — pos/BREAKOUT calc suppressed for SKHY this run per guardrail; target field kept as it looks internally consistent.
- Unchanged repeats (no material pos/news shift since this morning's 08:55 pass): MU, TSM, CIEN, AMD, STM, NVDA, AVGO, GEV, QCOM, CEG, AMZN, MSFT, VRT, AMAT, BE, GLW, GOOG, WDC, INTC, BABA, META.
- **NBIS** — target data unavailable this run (analyst_forecast.target_price null) — cannot confirm TARGET GAP status.
- **BX** — mean target $142.38 vs live $143.38 = -0.7% (price now trades ABOVE its own consensus target, doesn't meet the 15% either-direction bar, but worth flagging as a first for this new position).

## PEER LEADER / LAGGARD [unnormalized]
- **NOW** — +32.91pp vs XLK (NOW +34.6% vs XLK +1.69%, 1m). 2.35% weight. Confirms existing bucket.
- **MSFT** — +22.11pp vs XLK (MSFT +23.8% vs XLK +1.69%). 3.78% weight. New journal entry (not previously scored).
- **BX** — +14.19pp vs XLF (BX +16.74% vs XLF +2.55%). 3.73% weight, re-entered 2026-08-24. Confirms open_flags/journal read.
- **MRVL** — +16.86pp vs SMH (see above).
- **STM** — -18.62pp vs SMH (STM -23.13% vs SMH -4.51%). 3.89% weight. Confirms open_flags -1.61σ read (provisional Analog/Industrial Semis cluster, still unbanded).
- **WDC** — -12.96pp vs SMH (WDC -17.47% vs SMH -4.51%). 2.33% weight. NEW.
- **AMD** — -9.81pp vs SMH (AMD -14.32% vs SMH -4.51%). 2.42% weight. NEW.
- **META** — -14.01pp vs XLK (see above).
- Near-miss, not flagged: INTC -7.72pp vs SMH — just under the 8pp bar, watch item.

## NEW TAILWINDS
- **GEV** — 4.93% weight. 2 distinct positive events: (1) "GE Vernova Sees Significant Revenue Growth in 2026" — 2026-08-23 — data-center power revenue $5B in H1, >2x YoY, $176B backlog; (2) "GE Vernova Reports Mixed Q2 Results with Positive Outlook" — 2026-08-21 — EPS miss, revenue beat, raised cash-flow outlook. Mean target $1,239.46, +22.8% upside.
- **INTC** — 3.46% weight. 2 distinct positive events: (1) "Intel Gains Institutional Confidence Amid AI Push" — 2026-08-20; (2) "Intel Raises Capital Amid Revenue Growth and Losses" — 2026-08-17 (large capital raise). Still net loss-making — sentiment tailwind, not fundamental confirmation.

## NEW HEADWINDS
- **AVGO** — 3.80% weight. 3 distinct negatives outweighing 1 positive: (1) "Druckenmiller and Loeb Exit Broadcom for AI Investments" — 2026-08-23 (both fully exited, rotated to Alphabet); (2) "D.E. Shaw Cuts Stake Amid Strong Broadcom Performance" — 2026-08-22 (-58.3% stake); (3) "Broadcom Faces Pressure Amid AI Market Dynamics" — 2026-08-19 (Google-Marvell competitive threat). Offset: "Broadcom's AI Growth and Financing Strategies Highlighted" — 2026-08-21 (BMO outperform). Mean target $527.88, +30.2% upside. Same off-balance-sheet AI-financing tail risk flagged in G82 (now shared with BX).
- BABA, META — see move-based section above (same events double as headwinds).

## INSIDER ACTIVITY [news-derived proxy — FMP insiderTrades/form13F ACCESS DENIED this run]
- **TSM** — "Insider Purchase Signals Confidence in TSMC" — 2026-08-22 (positive-framed buying). 6.46% weight. Confirms existing bucket.
- **MRVL** — 2 distinct selling mentions, 2026-08-18/19 (see above). New addition.
- **AMD** — "AMD Insider Sale and Board Changes Amid Market Watch" — 2026-08-22. 2.42% weight. New addition.
- **STM** — buyback program 2026-08-10 is stale (pre-window), folded in as context only, not a fresh flag.

## EARNINGS PROXIMITY
- **NVDA** — 8.39% weight (largest single holding). "Nvidia's Earnings and AI Pricing Impact Market Sentiment" — 2026-08-24 — imminent print, exact date/time unconfirmed from this feed. pos 0.699, only +1.25% over trailing month (no aggressive run-up into the print), Fri day% -0.98%. Options-implied-move data not accessible this run (FMP plan-gated) — skipped.

## Still pending (no fresh news since watermark, prior story unresolved)
- ASML: US export-control risk to China lithography sales (14 Jul) — unresolved, no new news.
- GLW: 15% polysilicon tariff tailwind (07 Aug) — still the backdrop, nothing fresh.
- QCOM: handset-margin-pressure narrative (06 Aug); only 1 negative item this window (08-20) — insufficient alone for a fresh NEW HEADWINDS flag.
- CEG: mixed Q2 (06 Aug, beat EPS/miss revenue) — no fresh news since.
- TER: Baird downgrade to Neutral (21 Aug, "no catalysts until 2028") — dust position (~0% weight, stop-cascade residual), low priority.

## data_quality
1. atr20/rel-strength cache STALE (12+ days past 7d TTL, not refreshed this run) — every move-based bucket degraded to legacy absolute thresholds (±4% day, ±8pp relative), tagged [unnormalized]; day_atr_mult/rel_sigma null throughout, do not treat any line as volatility-calibrated.
2. FMP insiderTrades, form13F, and news (search-stock-news) ACCESS DENIED this run (plan tier restriction) — deep-mode's Form-4/13F task degraded to the news-derived proxy quick mode normally uses. TSM/MRVL/AMD insider lines are headline-derived, not filing-verified.
3. SKHY 52wk-low returned $0.00 (implausible) — fails PLAUSIBILITY BANDS guardrail; pos/BREAKOUT suppressed for SKHY, target field kept.
4. NBIS analyst_forecast.target_price null — TARGET GAP skipped for NBIS.
5. yfinance batched 1mo-history call (38 symbols, 1 call) truncated each series to 1 displayed row (23 total) — stats block (returnPct etc.) appears computed over the full window regardless, but truncation blocks path auditing; MSFT (+23.8%) and NOW (+34.6%) 1m returns are large enough to warrant a clean single-symbol spot-check next run.
6. Repeat suppression applied broadly: ~21 TARGET GAP names already refreshed by an earlier same-day (08:55) pass per signal_history_as_of — this 13:51 review found no material shift, collapsed to the unchanged-repeats line above.

```json
{"signal_history":{"changed":{
  "MRVL":["INSIDER ACTIVITY","MOMENTUM+VOLUME","PEER LEADER"],
  "AMD":["TARGET GAP","PEER LAGGARD","INSIDER ACTIVITY"],
  "GEV":["TARGET GAP","NEW TAILWINDS"],
  "BABA":["TARGET GAP","STRONG DOWNTREND","MOMENTUM+VOLUME","NEW HEADWINDS"],
  "INTC":["INSIDER ACTIVITY","TARGET GAP","NEW TAILWINDS"],
  "TXN":["TARGET GAP"],
  "WDC":["TARGET GAP","PEER LAGGARD"],
  "SKHY":["TARGET GAP (data-quality flagged, 52wk-low=0)"]
},"unchanged_count":25},
 "news_watermark":"2026-08-24","resolved_flags":["MRVL TARGET GAP (upside fell to 7.87%, below 15% bar)"],"new_flags":[],
 "journal_new":[
  {"date":"2026-08-24","ticker":"MRVL","bucket":"MOMENTUM+VOLUME","price_at_flag":237.04,"analyst_target":257.29,"day_atr_mult":null,"rel_sigma":null,"normalized":false},
  {"date":"2026-08-24","ticker":"MRVL","bucket":"PEER LEADER","price_at_flag":237.04,"analyst_target":257.29,"day_atr_mult":null,"rel_sigma":null,"normalized":false},
  {"date":"2026-08-24","ticker":"MSFT","bucket":"PEER LEADER","price_at_flag":483.24,"analyst_target":569.56,"day_atr_mult":null,"rel_sigma":null,"normalized":false},
  {"date":"2026-08-24","ticker":"AMD","bucket":"PEER LAGGARD","price_at_flag":473.25,"analyst_target":612.84,"day_atr_mult":null,"rel_sigma":null,"normalized":false},
  {"date":"2026-08-24","ticker":"WDC","bucket":"PEER LAGGARD","price_at_flag":459.44,"analyst_target":662.12,"day_atr_mult":null,"rel_sigma":null,"normalized":false},
  {"date":"2026-08-24","ticker":"AMD","bucket":"INSIDER ACTIVITY","price_at_flag":473.25,"analyst_target":612.84,"day_atr_mult":null,"rel_sigma":null,"normalized":false},
  {"date":"2026-08-24","ticker":"TXN","bucket":"TARGET GAP","price_at_flag":264.36,"analyst_target":324.45,"day_atr_mult":null,"rel_sigma":null,"normalized":false}
 ],
 "peer_map_updates":{},
 "vol_normalization":{
  "HOOD":{"atr20_pct":5.62,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":4.0},
  "BABA":{"atr20_pct":3.28,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":4.0},
  "MRVL":{"atr20_pct":9.88,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":4.0},
  "NOW":{"atr20_pct":5.65,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":8.0},
  "MSFT":{"atr20_pct":3.12,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":8.0},
  "BX":{"atr20_pct":3.47,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":8.0},
  "STM":{"atr20_pct":4.17,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":8.0},
  "WDC":{"atr20_pct":9.51,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":8.0},
  "AMD":{"atr20_pct":8.34,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":8.0},
  "META":{"atr20_pct":4.74,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":8.0}
 },
 "data_quality":[
  "atr20/rel-strength cache stale (12+ days past 7d TTL) -- all move-based buckets degraded to legacy absolute thresholds [unnormalized]",
  "FMP insiderTrades/form13F/news tools ACCESS DENIED (plan tier) -- insider activity is news-derived proxy only, not filing-verified",
  "SKHY 52wk-low returned $0.00 (implausible) -- pos/BREAKOUT calc suppressed, discarded per guardrail",
  "NBIS analyst target null -- TARGET GAP unconfirmed",
  "yfinance batched 38-symbol 1mo call truncated display rows to 1 of 23 -- MSFT/NOW returnPct outliers warrant a clean spot-check",
  "~21 TARGET GAP names unchanged vs this morning's 08:55 pass -- collapsed to repeat line"
 ]}
```

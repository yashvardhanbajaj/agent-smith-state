# US Macro Desk — 2026-07-31 Deep Review

## 1. Fed Funds & Stance
- Effective Fed funds target: 3.63% (upper bound), per cache — 07-29 FOMC held rates, matching this run's cache.
- Stance: HAWKISH (cached — no new FOMC meeting since last check; next_check_date 2026-09-17 not yet reached).
- Cache reused verbatim, no re-search performed.

## 2. Options Sentiment — Market Level
- SPY (Barchart put-call page): put/call OI ratio 1.98, put/call volume ratio 1.43, total OI 17.49M (11.63M puts / 5.86M calls).
- QQQ (Barchart put-call page): put/call OI ratio 1.22, put/call volume ratio 1.11, total OI 11.17M (6.13M puts / 5.03M calls).
- Read: both ratios sit above the neutral 1.0 line, more so on SPY — options market is carrying meaningfully more put open interest/volume than call, consistent with active downside hedging rather than outright bullish positioning, even as VIX (16.86, -1.35% on the day) sits calm in the lower half of its 52-week range [13.6, 31.05]. That combination — elevated PCR + low VIX — reads as "hedged complacency": realized vol is low and the tape just ripped higher, but participants are still buying/holding puts, likely a residual of the 07-28/07-29 CXMT-driven selloff and against the AMD (08-04) and broader earnings-season binary risk sitting immediately ahead.
- Max pain: NOT COMPUTABLE this run. yfinance `get_options` returned `openInterest: 0` across every strike and every expiry for both SPY and QQQ (checked nearest nine expiries) — the field is not populated by the current feed. This reconfirms known gap G18. No fallback PCR needed since Barchart succeeded.

## 3. Calendar
- Next FOMC decision: 2026-09-16 (cache-implied; next_check_date 2026-09-17 is the day after).
- Next CPI print: 2026-08-12 (July 2026 CPI, per BLS schedule).
- Next NFP (jobs report): 2026-08-07 (first Friday of August, standard BLS cadence; July 2026 employment situation).
- Mega-cap ("Mag-7"-adjacent) earnings season window: ACTIVE — today (07-31) falls inside the mid-Jul-through-end-of-month window.
- Within-5-trading-days flag: YES — AMD reports 2026-08-04, ~2 trading days from this run (07-31 → Mon 08-03 → Tue 08-04). NFP (08-07) is just outside the 5-trading-day band; CPI (08-12) is well outside. AMD is the near-term binary catalyst that matters for portfolio volatility risk.

## 4. Regime Read
The FOMC hold is now a known, priced event — it did not resolve the macro cross-current. The 10-yr has kept climbing (4.663%, +24.5bps over the trailing month) *despite* the hold, meaning long-end duration pressure is a separate, ongoing headwind independent of Fed policy — a hawkish hold caps near-term cut hopes without capping the bond selloff. Layered on top: a violent memory-sector whipsaw (CXMT-driven selloff 07-28/29, SMH +6.9% relief rally 07-30, KOSPI +17.9% overnight melt-up 07-31) has produced a market that is up sharply (NDX +2.78%, SPX +1.66%) with low realized vol (VIX 16.86) but still-elevated put positioning (SPY PCR 1.98) — a fragile, hedged-into-strength tape rather than clean risk-on conviction. Call it neutral-tilting-risk-on but fragile, largely unchanged in kind from 07-27 but with the FOMC uncertainty now resolved (hawkish, as expected) and replaced by acute single-stock/AI-capex-cycle event risk (AMD 08-04) sitting inside a 100%-AI-capex book with only ~5.4% cash cushion.
- AI-capex chain: near-term tailwind from the relief/melt-up rally, but AMD's 08-04 print is a binary event risk directly inside the book's dominant factor, arriving before the dust from the CXMT whipsaw has settled — treat the current rally as unconfirmed until AMD prints.
- Rate-sensitive / long-duration growth: pressured — the 10-yr's persistent climb despite the Fed hold means duration cost keeps rising regardless of policy stance; this is the disconnect the book should not ignore under the "hold = relief" narrative.
- Defensives/diversifier bench: not currently favored by the tape (low VIX, growth-led melt-up), but they remain the natural release valve if the AMD print or a renewed memory-sector leg down breaks the relief rally — worth keeping live given the thin cash buffer.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":1.98,"spy_max_pain":null,"qqq_pcr":1.22,"qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-08-12","next_nfp":"2026-08-07","earnings_season_window":true},
 "regime":"neutral","regime_note":"FOMC hold now priced/resolved (hawkish, as cached) but 10yr keeps climbing (4.663%, +24.5bps/mo) independent of Fed action; low VIX + elevated SPY/QQQ put positioning post CXMT whipsaw + KOSPI melt-up reads as hedged-into-strength, not clean risk-on. AMD earnings 08-04 is the live binary catalyst for this 100%-AI-capex book with thin (~5.4%) cash buffer.",
 "cluster_impact":{"ai_capex_chain":"near-term tailwind from relief rally, but AMD 08-04 print is unresolved binary risk directly inside the book's core factor","rate_sensitive":"pressured by 10yr's continued climb despite the FOMC hold - duration cost keeps rising regardless of policy stance","defensives":"currently unfavored by the growth-led melt-up tape but remain the release valve if AMD or renewed memory-sector stress breaks the rally"},
 "data_quality":["SPY/QQQ max-pain unavailable - yfinance get_options returns openInterest=0 across all strikes/expiries for both symbols (G18 reconfirmed still true this run)","next_fomc date (2026-09-16) inferred from cached next_check_date (2026-09-17 = day after decision), not independently re-confirmed via search per caching rule","next_nfp (2026-08-07) derived from standard first-Friday BLS cadence, not an explicit BLS calendar hit in search results - CPI date (2026-08-12) was explicitly confirmed via search"]}
```
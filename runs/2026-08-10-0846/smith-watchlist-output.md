# Watchlist & Market Context — 2026-08-10 (deep, pre-open)

## Watchlist Setups (rotation idx 15-29 + explicit re-entry checks: IREN/EWY/GLW/COHR)

- **IREN** [watchlist] TARGET GAP — mean target $81.73 (13 analysts, 92% buy), upside +49.6% vs $41.23. pos 0.40 (52w $17.22-$76.87), +8.7% today on $2.8B AI cloud contract backlog. Standing re-entry candidate (G51) — cleanest setup of the four post-cascade names.
- **VST** [watchlist] OVERSOLD BOUNCE — pos 0.09 (52w $132.66-$219.82), mean target $222.11, upside +36.7%. Q2 reported 08-07: EBITDA +31% YoY but revenue missed; guidance reaffirmed.
- **ORCL** [watchlist] OVERSOLD BOUNCE / TARGET GAP — pos 0.14, mean target $247.17, upside +40.5%. CAUTION: already held (2.51% wt), thesis flagged BROKEN across 3 prior deep reviews with an unexecuted exit recommendation — this signal conflicts with the standing strategist view, not a clean fresh-money case.
- **CEG** [watchlist] OVERSOLD BOUNCE — pos 0.22, mean target $351.24, upside +23.2%. Already held (2.29% wt); Q2 (08-06) beat EPS, missed revenue, debt overhang persists.
- **LEU** [watchlist] OVERSOLD BOUNCE — pos 0.15 (52w $142-$464), mean target $260.87, upside +26.6%. Recent news skews negative (Oklo HALEU deliveries delayed to 2029); +7.5% today.
- **SMR** [watchlist] OVERSOLD BOUNCE — pos 0.05 (52w $7.21-$57.42), mean target $13.37, upside +26.6% (mixed 60/30/10 buy/hold/sell split).
- **FLEX** [watchlist] TARGET GAP — mean target $160.50, upside +24.4%, pos 0.62.
- **LNG** [watchlist] TARGET GAP — mean target $304.95, upside +16.0%, pos 0.61.

No setup (checked, didn't clear threshold): MRVL (upside 14.9%, just under 15%), NOW (11.0%), ARM (1.5%), GLW (13.4%, near-miss), EWY (no analyst target data, pos 0.63 mid-range), SPCX/CBRS/EEMA/EFNL/EVER (no qualifying combination).

**G51 re-entry read (Friday SMH +1.96% risk-on):** IREN clears TARGET GAP cleanly (+49.6% upside, fresh contract catalyst). COHR is close but doesn't cross the bar — pos 0.83 (52w $84.35-$440), +13.4% today on China-restriction tailwind ahead of 08-12 earnings, upside only +3.9% (target already close to price). EWY has no computable setup (ETF, no analyst target). GLW's upside is 13.4%, just under the 15% TARGET GAP cutoff despite a strong week (+18% per its own news feed).

## Earnings Calendar (14-day deep-mode window, through 2026-08-24)

- **COHR** 2026-08-12 — confirmed (Zacks Q4 FY26 preview: ~$2.0bn rev est, $1.62 EPS est). Not currently held — lower priority.
- **VST** 2026-08-07 — now CONFIRMED as reported. Cache had it unconfirmed/cadence; Q2 print (EBITDA +31%, rev miss, guidance reaffirmed) is in the news feed. Updating cache.
- **MRVL** 08-26 (unconfirmed, cadence) — outside the 6-trading-day refresh window (through 08-18); yfinance calendar endpoint returned no rows for 08-10..08-26, no new confirmation found.
- **AVGO** 09-02 (unconfirmed, cadence) — outside window, no update.
- **NVDA** 08-26 (unconfirmed, cadence) — outside window, no update.
- No newly-scheduled earnings surfaced for any held or watchlist name inside the 6-trading-day window.

## Data Quality

- yfinance get_earnings_calendar(2026-08-10..08-26) returned an empty list — endpoint not populated for this range; relied on get_earnings + news cross-checks instead.
- MRVL/AVGO/NVDA dates remain cadence-based estimates, unconfirmed by INDmoney or yfinance; all fall outside this run's 6-trading-day window so no WebFetch was spent (the LRCX-style direct-source check is reserved for in-window names ≥3% weight).
- EWY/CBRS/SPCX/EEMA/EFNL returned no analyst_forecast block — cannot compute TARGET GAP for these; treat as data gap, not "no upside."
- ORCL and CEG setups both point at currently-held names with open strategist flags (ORCL thesis BROKEN/unexecuted exit; CEG fresh post-earnings, watch) — flagging the conflict rather than resolving it; that call belongs to the strategist.

```json
{"watchlist_setups":[
  {"ticker":"IREN","type":"TARGET GAP","upside_pct":49.55,"pos":0.40},
  {"ticker":"VST","type":"OVERSOLD BOUNCE","upside_pct":36.7,"pos":0.09},
  {"ticker":"ORCL","type":"OVERSOLD BOUNCE","upside_pct":40.52,"pos":0.14},
  {"ticker":"CEG","type":"OVERSOLD BOUNCE","upside_pct":23.16,"pos":0.22},
  {"ticker":"LEU","type":"OVERSOLD BOUNCE","upside_pct":26.64,"pos":0.15},
  {"ticker":"SMR","type":"OVERSOLD BOUNCE","upside_pct":26.55,"pos":0.05},
  {"ticker":"FLEX","type":"TARGET GAP","upside_pct":24.39,"pos":0.62},
  {"ticker":"LNG","type":"TARGET GAP","upside_pct":16.01,"pos":0.61}
],
 "earnings_calendar_updates":{
   "VST":{"date":"2026-08-07","confirmed":true,"source":"reported"},
   "COHR":{"date":"2026-08-12","confirmed":true,"source":"zacks-preview"}
 },
 "watchlist_scan_cursor":30,
 "data_quality":[
   "yfinance get_earnings_calendar(08-10..08-26) returned empty; used get_earnings+news instead",
   "MRVL/AVGO/NVDA still cadence-based/unconfirmed, outside 6-trading-day window, no update this run",
   "EWY/CBRS/SPCX/EEMA/EFNL lack analyst_forecast data -- TARGET GAP not computable, not 'no upside'",
   "ORCL and CEG setups conflict with existing holding/thesis flags (ORCL BROKEN, CEG fresh watch) -- flagged not resolved",
   "COHR pos 0.83, +13.4% today -- close to breakout bar but doesn't cross 0.90, not listed as a formal setup",
   "GLW upside 13.4% -- near-miss on the 15% TARGET GAP cutoff despite a strong week"
 ]}
```

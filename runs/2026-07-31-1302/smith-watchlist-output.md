# Watchlist & Market Context — 2026-07-31 (deep)

## 1. Watchlist setups (US only; rotating slice, cursor 105-119 scanned)

- **VST** (watchlist) — OVERSOLD BOUNCE: pos 0.18 (52wk $132.66-$219.82, now $148.62), mean target $222.83, upside 33.3%. Positive news: Q2 earnings expected +138.6% YoY, PPAs with Meta/AWS, $600M shareholder returns.
- **NRG** (watchlist) — TARGET GAP: pos 0.20, mean target $197.71, upside 32.2%. News neutral (Texas fleet expansion); flagged on gap size, not sentiment.
- **VRT** (watchlist) — TARGET GAP: pos 0.42, mean target $376.15, upside 39.5%. Post-Q2 miss-on-revenue dip (29-Jul) despite EPS beat — gap widened; UBS/analysts still Strong Buy.
- **ONTO** (watchlist) — TARGET GAP: pos 0.54, mean target $369.60, upside 32.2%. Morgan Stanley Overweight, $371 PT (15-Jun).
- **CORZ** (watchlist) — TARGET GAP: pos 0.52, mean target $34.17, upside 36.2%. No recent headline news in this pull.
- **NVDA** (watchlist + held) — TARGET GAP: pos 0.43, mean target $302.83, upside 35.6%. Mixed near-term news (OpenAI financing-guarantee concerns) vs. long-term bullish consensus (63 analysts, 92% buy).
- **DELL** (watchlist) — TARGET GAP: pos 0.82, mean target $502.78, upside 19.5%. Strong AI-server demand news, Citi/Evercore/Goldman PT raises; approaching but not yet breakout territory (pos<0.90).

No setups: RTX (upside 6.7%), GTLB (1.2%), PANW (3.3%), TLN/CCEC (no analyst forecast data), SIL/URNM/GDX (ETFs, no target).

## 2. Earnings calendar

Within 14 days of 2026-07-31:
- **AMD** — 2026-08-04, CONFIRMED (source: fmp-calendar; corroborated by 29-Jul news: "poised to report fiscal Q2 results on Aug. 4"). EARNINGS PROXIMITY flag — currently held, 5 trading days out.
- **CEG** — updated to 2026-08-06, CONFIRMED (source: web, stockanalysis.com) — supersedes prior cadence estimate of 2026-08-10. New position (added today), so this closes a gap immediately.
- **VST** — cached 2026-08-07, unconfirmed (watchlist name, not a holding — no re-check spent per budget).
- **ETN** — cached 2026-08-04, unconfirmed (watchlist name only).

No other holdings have earnings inside the 14-day window per cache.

## 3. Data quality
- RTX/GTLB/PANW/CCEC/TLN/SIL/URNM/GDX show upside <15% or no target — correctly excluded, not a coverage gap.
- CEG earnings date changed source (cadence→web) and date shifted 4 days (08-10→08-06); orchestrator should overwrite, not merge.
- Full watchlist has ~143 entries across 3 lists (with duplicates); this run covered index 105-119 only — CEG/VST/DELL/etc. appear multiple times across lists but were only priced once.

```json
{"watchlist_setups":[
  {"ticker":"VST","type":"oversold_bounce","upside_pct":33.3,"pos":0.18},
  {"ticker":"NRG","type":"target_gap","upside_pct":32.24,"pos":0.20},
  {"ticker":"VRT","type":"target_gap","upside_pct":39.52,"pos":0.42},
  {"ticker":"ONTO","type":"target_gap","upside_pct":32.22,"pos":0.54},
  {"ticker":"CORZ","type":"target_gap","upside_pct":36.17,"pos":0.52},
  {"ticker":"NVDA","type":"target_gap","upside_pct":35.59,"pos":0.43},
  {"ticker":"DELL","type":"target_gap","upside_pct":19.49,"pos":0.82}
],
 "earnings_calendar_updates":{
   "CEG":{"date":"2026-08-06","confirmed":true,"source":"web"},
   "AMD":{"date":"2026-08-04","confirmed":true,"source":"fmp-calendar"}
 },
 "watchlist_scan_cursor":120,
 "data_quality":["CEG earnings date corrected from cadence est. 2026-08-10 to confirmed 2026-08-06 via stockanalysis.com","NRG/CORZ target-gap setups have thin or no recent news corroboration — gap is analyst-consensus-driven, not sentiment-driven","VST/ETN (watchlist-only, not held) earnings dates remain unconfirmed — not re-checked, low priority vs. held names"]}
```

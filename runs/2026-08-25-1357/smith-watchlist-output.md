# Watchlist & Market Context — 2026-08-25 (deep)

## 1. Watchlist entry setups (US only; slice = index 15-29 of 138 deduped names, cursor 15)

OVERSOLD BOUNCE (pos≤0.3 + positive news/upgrade/upside>15%):
- **ORCL** — pos 0.12, mean target $246.43, upside 42.2%. Cloud revenue +47% (24-Aug); stock hammered on debt/cash-burn worry, not fundamentals.
- **CEG** — pos 0.24, mean target $348.45, upside 21.5%. Q2 EPS beat/revenue miss (06-Aug); still Strong Buy consensus.
- **LEU** — pos 0.11, mean target $257.33, upside 31.2%. Stock down on delayed HALEU deliveries; upside alone clears bar.
- **SMR** — pos 0.04, mean target $12.63, upside 28.4%. Thin news flow; deeply oversold vs 52w range.
- **VST** — pos 0.03, mean target $221.28, upside 38.7%. Q2 revenue miss (24-Aug) but Strong Buy consensus intact.

TARGET GAP ≥15% upside (no proximity trigger required):
- **FLEX** — upside 33.6%, pos 0.49. Raised FY27 revenue guidance on AI/CPI growth (19-Aug).
- **IREN** — upside 51.3%, pos 0.38. First AI data center delivered to Microsoft, Nvidia Exemplar Cloud status (13/18-Aug).
- **AEP** — upside 15.9%, pos 0.47. Guidance raised despite Q2 EPS miss; AI-datacenter power tailwind.
- **DLR** — upside 15.5%, pos 0.68. Q2 beat, TD Cowen upgrade to Buy (24-Jul).

No NEARING BREAKOUT setups in this slice (nothing at pos≥0.90 with a catalyst).

Skipped: CBRS (52w-low read as $0 — implausible, discarded, see data_quality), SPCX (pos 0.25 but no target-price/upside data returned, news mixed).

## 2. Earnings calendar (holdings within 14 days, i.e. by 2026-09-08)

- **NVDA** — 2026-08-26, confirmed (cache, indmoney-news reconfirmed 08-24).
- **MRVL** — 2026-08-27, confirmed (cache, indmoney-news reconfirmed 08-24).
- **AVGO** — 2026-09-02, confirmed (cache, indmoney-news reconfirmed 08-03).
- **CIEN** — 2026-09-03, confirmed (NEW — was uncached; web-verified via stockanalysis.com, company press release 08-06: FQ3 results before market open).

All other holdings' next reports fall outside the 14-day window per cache (already reported: AMD, AMZN, QCOM, LRCX, TER, CEG, BABA) or are quarterly-cadence names unlikely to report before 09-08 (INTC, KLAC, MU, COHR, BX, VRT, STM, GLW, WDC — not re-checked this run, no evidence of near-term report).

Dates only — no beat/miss verdicts reported here (that belongs to smith-earnings).

## Data quality
- CBRS 52-week-low returned as $0 in get_us_stocks_details — outside plausibility band, discarded from pos calc.
- SPCX: no analyst mean-target/upside field returned by get_us_stocks_details (consensus sentiment only); excluded from TARGET GAP scoring for lack of a number.
- Rotating scan covered only 15 of 138 deduped watchlist names this run (idx 15-29); remainder pending over future runs.

```json
{"watchlist_setups":[
 {"ticker":"ORCL","type":"oversold_bounce","upside_pct":42.2,"pos":0.12},
 {"ticker":"CEG","type":"oversold_bounce","upside_pct":21.5,"pos":0.24},
 {"ticker":"LEU","type":"oversold_bounce","upside_pct":31.2,"pos":0.11},
 {"ticker":"SMR","type":"oversold_bounce","upside_pct":28.4,"pos":0.04},
 {"ticker":"VST","type":"oversold_bounce","upside_pct":38.7,"pos":0.03},
 {"ticker":"FLEX","type":"target_gap","upside_pct":33.6,"pos":0.49},
 {"ticker":"IREN","type":"target_gap","upside_pct":51.3,"pos":0.38},
 {"ticker":"AEP","type":"target_gap","upside_pct":15.9,"pos":0.47},
 {"ticker":"DLR","type":"target_gap","upside_pct":15.5,"pos":0.68}
],
 "earnings_calendar_updates":{"CIEN":{"date":"2026-09-03","confirmed":true,"source":"web"}},
 "watchlist_scan_cursor":30,
 "data_quality":["CBRS 52w-low=$0 from get_us_stocks_details (implausible), discarded","SPCX missing target-price/upside field, excluded from target-gap scoring"]}
```

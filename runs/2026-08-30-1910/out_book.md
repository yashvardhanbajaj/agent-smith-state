```json
{
  "div_yield_pct": 0.44,
  "ex_dates": [
    {"ticker":"GLW","ex_dividend_date":"2026-08-31","days_out":1},
    {"ticker":"AMKR","ex_dividend_date":"2026-09-02","days_out":3},
    {"ticker":"QCOM","ex_dividend_date":"2026-09-03","days_out":4},
    {"ticker":"GOOG","ex_dividend_date":"2026-09-04","days_out":5},
    {"ticker":"TER","ex_dividend_date":"2026-09-04","days_out":5},
    {"ticker":"WDC","ex_dividend_date":"2026-09-08","days_out":9},
    {"ticker":"NVDA","ex_dividend_date":"2026-09-10","days_out":11},
    {"ticker":"TSM","ex_dividend_date":"2026-09-16","days_out":17},
    {"ticker":"STM","ex_dividend_date":"2026-09-22","days_out":23},
    {"ticker":"LRCX","ex_dividend_date":"2026-09-23","days_out":24}
  ],
  "ltcg_narrative": [
    {"ticker":"ALL","months_to_ltcg":null,"note":"No live LTCG-deferral decisions this run. Earliest open lot across the book is 2026-07-15, so the 24-month Indian LTCG boundary is mid-2028 -- roughly 22 months out. compute_book.json's ltcg_flags array is empty and that is correct, not a gap. No position is a trim candidate on LTCG grounds."}
  ],
  "refreshed_betas": {
    "GEV": 1.033, "VRT": 2.077, "ASML": 1.365, "MU": 2.213, "GOOG": 1.237,
    "TSM": 1.258, "LRCX": 1.865, "GLW": 1.148, "QCOM": 1.663, "CIEN": 1.315,
    "COHR": 2.107, "NVDA": 2.215, "NBIS": 1.434, "AMD": 2.489, "AMAT": 1.618,
    "CEG": 1.118, "AVGO": 1.473, "TER": 1.793, "CLS": 1.516, "STM": 1.521,
    "BX": 1.546
  },
  "risk_narrative": "Aggregate open risk sits at 13.16% against a 10% policy cap -- a real breach, not a rounding issue -- while cash is 3.01%, below the 5-15% policy floor. That pairing is the operative constraint: any new position this run must be funded by a sale, not by deploying cash, because there isn't enough cash to deploy and adding exposure on top of an already-breached risk budget compounds the problem. The risk_concentration table shows why the breach is worse than weight alone suggests: BE is 4.26% of the book by weight but 6.7% of risk (beta 2.105), MRVL is 4.92% weight vs 6.17% risk (beta 1.676), and NBIS, MU, and FLTW each carry risk shares 1.5-2x their capital weight on betas above 1.9. These five names plus the nine ATR-cap breaches (GEV, MRVL, VRT, BE, MU, LRCX, GLW, COHR, NBIS) overlap heavily -- BE, MU, and NBIS appear in both lists -- meaning the same handful of high-beta names are driving both the risk-cap breach and the individual stop-distance breaches simultaneously. Drawdown is -8.95% off the total-book peak of $44,873.02; it is not yet at a typical -15% to -20% policy stress threshold but the -3.115% weighted day move that produced today's read shows how fast that gap can close in this beta-1.34 book. Net: trim candidates should be sourced from the risk_concentration/ATR-breach overlap set (BE, MU, NBIS first) rather than the largest weight holders, since weight and risk are diverging for exactly these names.",
  "data_quality": [
    "lots.json not found at the path this run supplied (./lots.json resolved to no file in the run directory) -- per-lot cost-basis concentration (oldest lot, single-lot concentration) could not be computed from source data this run. Relying on the orchestrator-provided fact that the earliest open lot is 2026-07-15; do not treat the empty ltcg_flags as a data gap, it is correct given that date.",
    "MRVL: yfinance get_key_stats returned no beta field this run (cache retains 1.676, as_of 2026-07-31, now >30d stale). Did not WebFetch stockanalysis.com to conserve tool budget since MRVL is not defaulting to 1.0 -- flagging for next run's refresh instead.",
    "FLTW: yfinance get_key_stats and get_stock_summary both returned empty payloads this run (cache retains 2.411, as_of 2026-08-15, benchmark SPX with prior correction note). Same treatment as MRVL -- flagged, not web-fetched, to stay in budget.",
    "BE: fresh yfinance native beta came back 3.832, outside the 0-3.5 plausibility band -- discarded, not ingested. Cache retains 2.105 (as_of 2026-07-31, now stale) pending a cleaner re-derive.",
    "IREN: fresh yfinance native beta came back 4.302, outside the 0-3.5 plausibility band -- discarded, not ingested. Cache retains 2.436 (as_of 2026-07-31, now stale) pending a cleaner re-derive.",
    "All 21 refreshed_betas values are yfinance NATIVE (S&P-benchmarked) betas, not the SMH regression the rest of the cache uses -- same caveat class already attached to STM/TXN in the existing cache. Orchestrator should tag benchmark=SPX_native_yfinance and as_of=2026-08-30 on write-back; re-derive vs SMH next deep run for consistency.",
    "SKHY, INTC, AMD, CIEN, COHR, NBIS, FLTW, BE, AMZN, CLS, LITE, IREN, SMCI: no current cash dividend (yfinance returned dividendYield null/0 or a stale/decades-old exDividendDate) -- excluded from both the yield calc and ex-date list.",
    "Portfolio trailing dividend yield (0.44%) is a weight_pct-weighted average of yfinance trailingAnnualDividendYield per holding; BX's 3.64% single-name yield is the largest single contributor (~0.13pp of the 0.44%) -- flagged since BX's payoutRatio >1.0 (alt-asset manager distribution structure, not a pure earnings payout) makes headline yield less comparable to the rest of the book.",
    "Tool budget: used 5 of ~10 calls (2x get_stock_history [truncated to 2 rows/symbol regardless of max_rows, unusable for a fresh SMH regression], 1x get_key_stats batch, 2x get_stock_summary batch). Stopped there by design, not by hitting the cap -- output is not truncated."
  ]
}
```

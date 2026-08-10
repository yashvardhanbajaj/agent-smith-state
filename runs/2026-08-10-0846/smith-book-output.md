# Book & Risk Narrator — 2026-08-10-0846 (deep, US pre-open)

## Income
- Trailing portfolio dividend yield (value-weighted, dividendYield x weight_pct across all 30 holdings): **0.372%**.
- Payers of note: QCOM 2.19%, ORCL 1.36%, TSM 0.90%, BABA 0.82%, MSFT 0.73%, CEG 0.63%, AVGO 0.61%, ASML 0.52%.
- INTC pays no current dividend — yfinance shows a stale exDividendDate of 2024-08-07 with payoutRatio 0 (suspended, consistent with the 2024 dividend cut). Do not treat as an income holding.
- AVGO's last confirmed ex-div (2026-06-22) has already passed; next ex-div not yet published by yfinance, so nothing to report inside the 30-day window despite being a requested check-name.
- TSM ex-div 2026-09-16 is 37 days out — outside the 30-day window, excluded from ex_dates below.

## Upcoming ex-dividend dates (within 30 days of 2026-08-10)
| Ticker | Ex-Div Date | Days Out |
|---|---|---|
| CEG | 2026-08-18 | 8 |
| MSFT | 2026-08-20 | 10 |
| AMAT | 2026-08-20 | 10 |
| QCOM | 2026-09-03 | 24 |
| GOOGL | 2026-09-04 | 25 |

## LTCG narrative
compute_book.json's `ltcg_flags: []` is confirmed correct. Spot-check of lots.json's dated lots: the oldest dated lot in the file is ORCL 4sh @ $126.58 on 2026-07-16, with the bulk of the book re-established 2026-07-28 through 2026-08-07 (post the 07-24/07-27 mass stop-outs). Nothing is within shouting distance of the 24-month Indian LTCG boundary (would need a 2024-08 or earlier purchase date) — the entire dated book is under 4 weeks old.

Residual gap: several tickers carry a null-dated "predates available email history" lot for legacy dust/survivor quantities that are not economically trivial in a few cases — DRAM 5sh, VRT 3sh, AVGO 2sh, GEV 0.395sh, CLS 3.003sh, plus dust amounts in ASML/QCOM/SNDK/AMAT. These predate the 2025-04-30 email-reconstruction window, so true purchase date is unknown and they are excluded from the LTCG flag computation. Not urgent (even a 2025-04-29 purchase is only ~15.5 months old today), but flagging as a standing completeness gap for LTCG monitoring on legacy lots, not a new issue this run.

## Beta cache
No beta refresh needed this run. compute_book.json carries no flagged 1.0-default or TTL-expired entries requiring a fetch, and per the orchestrator's brief, INTC's beta (1.579 vs SMH) and ATR20 (7.588%) were already freshly computed upstream this run. `refreshed_betas` is empty.

## Risk narrative
Portfolio beta is 1.106 vs SMH (primary SOX/SMH benchmark; the 1.491 SPX beta is flagged as misleading and should not drive sizing). Risk-weighted concentration shows a clear divergence between capital weight and risk contribution: SNDK is 4.96% of value but 13.11% of risk-weighted concentration (beta 2.924) — the single largest risk-vs-weight gap in the book. SKHY (4.13% weight / 9.11% risk, beta 2.442) and MU (4.61% weight / 8.14% risk, beta 1.954) follow the same pattern, and DRAM (4.21% weight / 7.89% risk, beta 2.073) rounds out a memory/HBM cluster that punches well above its capital weight on risk. AMD is the outlier moderate-beta name in the top-5 risk list (1.566) but still contributes disproportionately (5.11% weight / 7.24% risk). Drawdown is -5.742% on a total-book basis (peak $44,873.02 -> current $42,296.38) — a moderate pullback, not yet near a severe-drawdown policy threshold, but worth watching given the memory-cluster beta concentration sitting above it. Cash (wallet) is 9.61% of total book, below the elevated post-flow levels seen in recent runs but still a real hedge against the concentrated risk names above.

## Data quality
- Dividend/ex-div data sourced from yfinance batch summary calls (2 calls, 30/34 symbols total); no gaps encountered.
- LTCG completeness gap on null-dated legacy lots (see narrative above) — standing item, not new.
- No beta cache staleness flagged this run; nothing fetched from stockanalysis.com (not needed).

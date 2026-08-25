# smith-book — deep review, 2026-08-25

## Income
- Trailing portfolio dividend yield (market-value weighted, 35 positions): **0.52%**
- Highest-yield contributors: BX 3.65%, QCOM 2.29%, TXN 2.15%, TSM 1.04%, BABA 0.88%
- 12 of 35 names pay no dividend (BE, AMZN, COHR, CIEN, NBIS, FLTW, AMD, NOW, SKHY, HOOD, CLS; INTC's cached ex-date is 2024-08-07 — dividend suspended, treated as non-payer)

## Upcoming ex-dividend dates (within 30 days of 2026-08-25)
| Ticker | Ex-div date | Days out |
|---|---|---|
| GLW | 2026-08-31 | 6 |
| QCOM | 2026-09-03 | 9 |
| GOOG | 2026-09-04 | 10 |
| TSM | 2026-09-16 | 22 |
| STM | 2026-09-22 | 28 |

## LTCG narrative
compute_book.json's `ltcg_flags` is empty, and lots.json confirms why: the earliest lot in the book is GEV at 2026-07-21 — about one month old. No position is within 6 months of the 24-month Indian LTCG boundary; nothing to flag. Note lots.json has no entries yet for the 5 brand-new positions (KLAC, COHR, NBIS, NVDA, SKHY) added around 2026-08-24/25 — smith-ledger reconciliation is pending per this run's dispatch, not a book-agent gap.

## Beta cache refresh
compute_book.json flagged exactly one cache miss: **KLAC** (defaulted to 1.0). Fetched via yfinance `get_key_stats`:
- KLAC beta = **1.458** (yfinance native, SPX-benchmarked — same caveat as the existing STM/TXN cache entries: not the SMH regression used elsewhere in this book; re-derive vs SMH on a future deep run for consistency). Within plausibility band (0–3.5). No stockanalysis.com fallback needed.

## Risk narrative
The book's risk-weighted concentration is running hotter than its dollar weights suggest. BE carries 4.55% of book weight but 8.09% of risk-weighted concentration (beta 2.105) — the single largest risk/weight gap in the book. NBIS is smaller in weight (2.88%) but has the highest beta on the sheet (2.636), contributing 6.42% of risk. MRVL (4.35% wt / 6.15% risk, beta 1.68), MU (3.68% wt / 6.07% risk, beta 1.95) and FLTW (2.62% wt / 5.34% risk, beta 2.41) round out the top-5 risk contributors, which together are ~18% of book weight but ~32% of risk-weighted concentration. Portfolio beta is 1.184 vs. the SOX/SMH primary benchmark (1.19 peer beta) — tracking its true factor closely — but the secondary SPX beta of 1.491 is the more honest read of how this book behaves against the broad market: it is a levered semis/AI-capex bet, not a diversified equity sleeve. Drawdown is -7.94% off the total-book peak ($44,873 → $41,310); wallet/cash sits at 8.47%. Not yet at a typical -10% caution band, but with 11 tickers having changed quantity overnight (5 brand-new adds) and BE/NBIS both flagged as disproportionate risk contributors, this is worth watching rather than shrugging off.

## Data quality
- Portfolio dividend yield and ex-dates sourced from yfinance `get_stock_summary`; skipped silently for any ticker where the field was absent (no separate discard needed — all returned values were in sensible ranges).
- KLAC beta refreshed from yfinance native (SPX) beta, not SMH-regressed — flagged for future re-derivation, consistent with existing STM/TXN cache notes.
- lots.json has no lot history yet for KLAC, COHR, NBIS, NVDA, SKHY (new positions) — out of scope for this agent, reconciliation owned by smith-ledger.
- No LTCG flags to narrate this run; known_gaps G78/G82/G83 (trade-rationale/BX re-entry timing gaps) are outside this agent's scope and not restated here beyond this note.

```json
{"div_yield_pct":0.52,"ex_dates":[{"ticker":"GLW","ex_dividend_date":"2026-08-31","days_out":6},{"ticker":"QCOM","ex_dividend_date":"2026-09-03","days_out":9},{"ticker":"GOOG","ex_dividend_date":"2026-09-04","days_out":10},{"ticker":"TSM","ex_dividend_date":"2026-09-16","days_out":22},{"ticker":"STM","ex_dividend_date":"2026-09-22","days_out":28}],
 "ltcg_narrative":[],
 "refreshed_betas":{"KLAC":1.458},
 "risk_narrative":"BE (4.55% wt) and NBIS (2.88% wt, beta 2.636 highest in book) are the top disproportionate risk contributors -- top-5 risk names are ~18% of weight but ~32% of risk-weighted concentration. Portfolio beta 1.184 tracks SOX/SMH (1.19) closely but SPX secondary beta 1.491 shows this is a levered semis/AI-capex bet vs broad market. Drawdown -7.94% off total-book peak, not yet at a -10% caution band but trending with cash at 8.47% amid 11 overnight qty changes including 5 new adds.",
 "data_quality":["KLAC beta is yfinance native SPX beta, not SMH-regressed -- re-derive vs SMH next run","lots.json has no entries yet for KLAC/COHR/NBIS/NVDA/SKHY (new positions, ledger reconciliation pending, out of scope for this agent)","ltcg_flags empty this run -- earliest lot in book is ~1 month old (GEV 2026-07-21), nowhere near the 24-month LTCG boundary"]}
```

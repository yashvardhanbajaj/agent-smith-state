# Smith Book & Risk — Deep Run 2026-08-16

Market closed since Fri 2026-08-14. Value/weights/concentration/beta/drawdown are unchanged from 2026-08-15 (compute_book.json) — not restated. This run covers only the time-varying and judgment layers: dividends, LTCG, beta-cache upkeep.

## 1. Income
Weighted trailing portfolio dividend yield: **0.447%** (35 names, weight_pct × yfinance trailingDividendYield; essentially flat vs yesterday's 0.451% — no dividend policy changes, small drift from weight/price noise). BX remains the outlier payer at **3.63%** trailing yield (payout ratio 111% — supplemental/variable alt-asset-manager distribution, not a fixed cash dividend, do not treat as guaranteed run-rate). Next-highest: QCOM 2.22%, TXN 2.03%, ORCL 1.33%.

### Ex-dividend dates within 30 days (through 2026-09-15)
| Ticker | Ex-Div Date | Days Out |
|---|---|---|
| CEG | 2026-08-18 | 2 |
| MSFT | 2026-08-20 | 4 |
| AMAT | 2026-08-20 | 4 |
| GLW | 2026-08-31 | 15 |
| QCOM | 2026-09-03 | 18 |

Same five names as yesterday, days_out simply decremented by one — no new ex-div events entered the window. TSM (2026-09-16, 31 days out) remains just outside; noted, excluded. AMD and INTC have no active dividend (INTC suspended 2024; AMD's listed ex-div date, 1995-04-27, is a legacy stub with no active payout).

## 2. LTCG Narrative
compute_book.json's `ltcg_flags` is **empty**, and for the first time this is on a fully reconciled lot base (35/35 tickers reconcile, 0 mismatches/orphans/phantom shorts, 71/71 open lots dated — G1 and G66 closed). Checked lots.json directly: across all held tickers, the **earliest open lot is CLS/DRAM/ORCL on 2026-07-15/16** — about one month old. The 24-month Indian LTCG boundary for that earliest lot doesn't arrive until mid-2028. No position is within remote range of the 6-month pre-boundary window; no LTCG action is due this or any near-term run. (One lot for LLY dated 2026-04-02 is older but LLY is not a current holding — irrelevant to this book.)

No reliability caveat needed this run — the prior G68 over-count flag (QCOM/MSFT/AMD/MRVL) is resolved per the orchestrator's reconciliation note; lots.json is now the trusted source for holding-period math.

## 3. Beta Cache Refresh
Checked all 35 held tickers' `data_cache.betas` timestamps against the 30-day TTL. All properly-timestamped entries are current (oldest 2026-07-31, 16 days old — within TTL; BX/FLTW at 2026-08-15, 1 day old). Two entries — **STM (1.246) and TXN (0.599)** — carry no `as_of`/`benchmark` metadata at all (bare numbers), so freshness can't be verified; treated as effectively expired/malformed and refreshed.

Fetched via yfinance `get_key_stats` (batched, 2 symbols): **STM 1.521**, **TXN 1.325**. Both within the 0–3.5 plausibility band. Note: these are yfinance's native `beta` field (trailing 5Y monthly, S&P500-benchmarked) — a different methodology from the custom SMH-regression used for most other cache entries. Flagging so the orchestrator can decide whether to re-derive vs SMH for consistency next deep run; not blocking the cache write.

No held name defaulted to 1.0 or is missing a cache entry outright this run.

## 4. Risk Narrative
Risk concentration is unchanged from yesterday and still running hotter than weight concentration at the top: MU (5.55% weight, beta 1.954) carries 8.5% of risk-weighted exposure, SKHY (4.17% weight, beta 2.442) carries 7.96%, NBIS (3.81% weight, beta 2.636) carries 7.86%, and DRAM (3.90% weight, beta 2.073) carries 6.34% — four names, all beta >1.9, disproportionate to their dollar weight. Portfolio beta is 1.277 (primary SOX/SMH read 1.19; secondary SPX read 1.491 is the misleading one — size and stress off SOX/SMH). Drawdown is a non-issue at -2.507% off the $44,873.02 total-book peak, well inside the -15% warn rung — no proximity concern. With the market closed all weekend, none of this has moved since Friday's close; nothing here requires action before Monday's open.

## Data Quality
- Dividend yields/ex-dates from yfinance `get_stock_summary` (2 batched calls, all 35 tickers), `dividendYield`/`exDividendDate` fields; 0 used for confirmed non-payers.
- STM/TXN betas refreshed via yfinance `get_key_stats` (1 batched call) — native beta field, not the SMH-regression method used elsewhere; methodology note above.
- LTCG read now unconstrained by any known gap; G68 caveat retired.
- Tool-call budget: 4 calls total, well under the ~10 soft cap.

```json
{"div_yield_pct":0.447,
 "ex_dates":[
   {"ticker":"CEG","ex_dividend_date":"2026-08-18","days_out":2},
   {"ticker":"MSFT","ex_dividend_date":"2026-08-20","days_out":4},
   {"ticker":"AMAT","ex_dividend_date":"2026-08-20","days_out":4},
   {"ticker":"GLW","ex_dividend_date":"2026-08-31","days_out":15},
   {"ticker":"QCOM","ex_dividend_date":"2026-09-03","days_out":18}
 ],
 "ltcg_narrative":[
   {"ticker":"ALL","months_to_ltcg":null,"note":"compute_book.json ltcg_flags empty, confirmed against fully reconciled lots.json (35/35 tickers, 0 mismatches, 71/71 lots dated). Earliest open lot across the book is 2026-07-15/16 (CLS/DRAM/ORCL) -- 24-month LTCG boundary not until mid-2028. No position near the 6-month pre-boundary window. No G68-style caveat needed; lots.json fully trusted this run."}
 ],
 "refreshed_betas":{"STM":1.521,"TXN":1.325},
 "refreshed_betas_meta":{"STM":{"source":"yfinance","field":"native_beta","prior_value":1.246,"prior_benchmark":"unlabeled/no_as_of","note":"cache entry had no as_of or benchmark tag -- treated as expired"},"TXN":{"source":"yfinance","field":"native_beta","prior_value":0.599,"prior_benchmark":"unlabeled/no_as_of","note":"same as STM"}},
 "risk_narrative":"Unchanged from Friday's close (market closed all weekend). MU/SKHY/NBIS/DRAM (all beta >1.9) contribute risk share well above weight share (8.5%/7.96%/7.86%/6.34% risk vs 5.55%/4.17%/3.81%/3.90% weight). Portfolio beta 1.277, primary SOX/SMH read 1.19 vs misleading SPX read 1.491 -- size and stress off SOX/SMH. Drawdown -2.507% off $44,873.02 peak, well inside -15% warn rung -- no proximity concern.",
 "data_quality":["STM and TXN beta cache entries had no as_of/benchmark metadata (bare numbers) -- treated as expired and refreshed via yfinance native beta field, a different methodology (S&P500-benchmarked) from the SMH-regression used for most other cache entries; orchestrator may want to re-derive vs SMH next deep run for consistency","All other 33 betas within 30-day TTL, not refreshed","No held name missing a beta or defaulted to 1.0"]}
```

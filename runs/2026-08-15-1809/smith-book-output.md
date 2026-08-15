# Smith Book & Risk — Deep Run 2026-08-15

## 1. Income
Weighted trailing portfolio dividend yield: **0.451%** (35 names, weights from compute_book.json, dividendYield field from yfinance summary; 0 used for non-payers incl. INTC [dividend suspended 2024], AMD, NBIS, DRAM, SKHY, CLS, AMZN, TER-adjacent names with no field, COHR, IREN, NOW, CIEN, ARM, SNDK, BE, FLTW).

BX standalone trailing yield is **3.63%** — ~8x the book's weighted average and the single highest yield in the portfolio (next-highest: QCOM 2.22%, TXN 2.03%, ORCL 1.33%, TSM 1.02%). Confirmed: this book has never carried a meaningful income component before BX, and BX alone now anchors it. Payout ratio on BX is 111% (dividendRate $5.23 vs trailing EPS-implied payout >1) — a supplemental/variable-distribution alt-asset-manager payout, not a fixed cash dividend; do not treat the 3.63% as guaranteed run-rate.

### Ex-dividend dates within 30 days (through 2026-09-14)
| Ticker | Ex-Div Date | Days Out |
|---|---|---|
| CEG | 2026-08-18 | 3 |
| MSFT | 2026-08-20 | 5 |
| AMAT | 2026-08-20 | 5 |
| GLW | 2026-08-31 | 16 |
| QCOM | 2026-09-03 | 19 |

(TSM ex-div 2026-09-16 is 32 days out — just outside the window, noted but excluded.)

## 2. LTCG Narrative
compute_book.json's `ltcg_flags` returned **empty** — correctly so. The account's earliest trade is 2025-04-30 (per lots.json rebuild note); the 24-month Indian LTCG boundary for that earliest lot doesn't arrive until ~2027-04-30, so no position enters the 6-month pre-boundary window until roughly late Oct 2026. No LTCG action is due this run.

**Reliability caveat (G68):** QCOM, MSFT, AMD, and MRVL lots are known over-counted vs the broker (QCOM +3.0sh, MSFT +1.5sh, AMD +0.0206sh, MRVL +0.0089sh — confirmed by direct lot-sum vs live qty check: QCOM lots sum 13.0008 vs held 10.0008; MSFT lots sum 4.5 vs held 3.0). Any future holding-period read on these four names should not be taken at face value until smith-ledger resolves G68 — do not treat their earliest lot dates as trustworthy purchase dates for LTCG sequencing.

**Standing gaps not directly actionable this run:** G70 (ticker rename, e.g. PSTG→P) and G71 (GOOG share-class conversion running a negative FIFO) both concern tickers not currently held (P/PSTG and GOOG are absent from this book's 35 positions), so they don't distort today's LTCG read, but G71's negative-FIFO mechanism is flagged by smith-ledger as a plausible root cause of the G68 over-counts — not attempting repair here, per dispatch to smith-ledger this run.

## 3. Beta Cache Refresh
No held name is missing a beta or sitting at a defaulted 1.0 (compute_risk.json `missing_beta: []` confirms). All 35 cache entries are within the 30-day TTL (oldest is 2026-07-31, 15 days old).

The one live issue: **BX and FLTW were cached against SMH**, which is the wrong benchmark for a non-semis alt-asset-manager and a diversified regional ETF. Refreshed both vs **SPX** (^GSPC) using 21 daily returns (2026-07-16 to 2026-08-14):

| Ticker | Old (SMH) | New (SPX) | Benchmark Used | Note |
|---|---|---|---|---|
| BX | -0.021 | **1.124** | SPX | Old SMH-relative beta was economically meaningless (BX isn't semis-correlated); 1.124 vs broad market is a plausible alt-asset-manager loading. |
| FLTW | 0.768 | **2.411** | SPX | Thin sample (21 obs) + high realized vol (annualized ~45.5% vs SPX ~13.4%) — within plausibility band (0-3.5) but re-measure next deep run before sizing off it. |

`refreshed_betas` below are raw per-ticker values for the orchestrator to fold into data_cache.betas with today's date and benchmark tag — portfolio-level beta/risk_concentration were NOT recomputed here.

## 4. Risk Narrative
Risk concentration is running hotter than weight concentration at the top: MU is 5.44% of the book by weight but 8.79% of risk-weighted exposure (beta 1.954), SKHY is 4.18% weight vs 8.43% risk (beta 2.442), NBIS is 3.51% weight vs 7.64% risk (beta 2.636), and DRAM is 3.91% weight vs 6.70% risk (beta 2.073) — four names, all beta >1.9, contributing disproportionately to book-level swings relative to their dollar weight. Portfolio beta is 1.21 on the correct SOX/SMH factor benchmark (1.19 primary) vs a misleading 1.49 SPX-relative read — this book moves with semis, not the broad market, and sizing/stress decisions should reference SOX. Separately, compute_risk.json shows aggregate open (stop-distance) risk at 14.29% against a 10% cap, with 10 names individually over their ATR-based cap — this is the more urgent live constraint right now, not drawdown. Drawdown itself is a non-issue at -2.507% off the $44,873.02 peak, well inside the -15% warn / -25% risk-off ladder rungs — no proximity concern this run.

## Data Quality
- Dividend yield sourced from yfinance `get_stock_summary` trailingdividendYield field; treated as 0 where field absent (confirmed non-payers, not a data gap).
- BX/FLTW betas computed in-agent from 21 daily log-simple returns vs ^GSPC (yfinance get_stock_history, 3mo period truncated to last 22 bars) — not a yfinance-native beta field.
- Tool-call budget: used 4 calls (2x get_stock_summary batch, 1x get_stock_history batch, plus this write) — well under the ~10 soft cap.

```json
{"div_yield_pct":0.451,
 "ex_dates":[
   {"ticker":"CEG","ex_dividend_date":"2026-08-18","days_out":3},
   {"ticker":"MSFT","ex_dividend_date":"2026-08-20","days_out":5},
   {"ticker":"AMAT","ex_dividend_date":"2026-08-20","days_out":5},
   {"ticker":"GLW","ex_dividend_date":"2026-08-31","days_out":16},
   {"ticker":"QCOM","ex_dividend_date":"2026-09-03","days_out":19}
 ],
 "ltcg_narrative":[
   {"ticker":"ALL","months_to_ltcg":null,"note":"compute_book.json ltcg_flags empty -- earliest account lot is 2025-04-30, so no position nears the 24-month LTCG boundary until ~Oct 2026. No action due."},
   {"ticker":"QCOM","months_to_ltcg":null,"note":"Lots over-counted +3.0sh vs broker (G68) -- do not trust earliest-lot date for holding-period math until smith-ledger resolves."},
   {"ticker":"MSFT","months_to_ltcg":null,"note":"Lots over-counted +1.5sh vs broker (G68) -- same caveat as QCOM."},
   {"ticker":"AMD","months_to_ltcg":null,"note":"Lots over-counted +0.0206sh vs broker (G68) -- same caveat."},
   {"ticker":"MRVL","months_to_ltcg":null,"note":"Lots over-counted +0.0089sh vs broker (G68) -- same caveat."}
 ],
 "refreshed_betas":{"BX":1.124,"FLTW":2.411},
 "refreshed_betas_meta":{"BX":{"benchmark":"SPX","source":"yfinance","prior_value":-0.021,"prior_benchmark":"SMH"},"FLTW":{"benchmark":"SPX","source":"yfinance","prior_value":0.768,"prior_benchmark":"SMH","caveat":"thin sample (21 obs), high realized vol -- re-measure next deep run"}},
 "risk_narrative":"MU/SKHY/NBIS/DRAM (all beta >1.9) contribute risk share well above their weight share; portfolio beta 1.21 vs SOX/SMH (correct factor) vs a misleading 1.49 vs SPX; aggregate open ATR risk 14.29% vs 10% cap (10 names over cap) is the live constraint, not drawdown, which sits at -2.507% -- well inside the -15% warn rung.",
 "data_quality":["BX and FLTW betas recomputed vs SPX (not SMH) per explicit run instruction -- not a TTL-driven refresh, a benchmark correction","FLTW beta (2.411) thin-sample flagged, within plausibility band but not to be sized off without re-measurement","No held name missing beta or defaulted to 1.0 this run"]}
```

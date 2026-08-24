# smith-book output — 2026-08-24 deep review

## 1. Income
Portfolio trailing dividend yield: **0.53%** (weight-weighted across all 33 US positions using yfinance `dividendYield`; non-payers — BE, AMZN, NBIS, INTC (suspended), FLTW, AMD (no current dividend), NOW, CIEN, HOOD, CLS, ASML-dust-adjacent — contribute 0).
Top yield contributors: BX (3.65% yield, 3.73% weight — REIT/alt-asset payout drags the whole book's yield up disproportionately), TXN (2.15%), QCOM (2.29%), TSM (1.04%).

## 2. Upcoming ex-dividend dates (within 30 days of 2026-08-24)
| Ticker | Ex-div date | Days out |
|---|---|---|
| GLW | 2026-08-31 | 7 |
| QCOM | 2026-09-03 | 10 |
| GOOG | 2026-09-04 | 11 |
| WDC | 2026-09-08 | 15 |
| TSM | 2026-09-16 | 23 |
| STM | 2026-09-22 | 29 |

## 3. LTCG narrative
`compute_book.json.ltcg_flags` is empty — correctly so. lots.json's oldest surviving lot is GEV (2026-07-21), ~34 days old; the book is nowhere near the 24-month Indian LTCG boundary. No flags, no trim candidates on tax grounds this run. lots.json is otherwise reconciled: COHR and IREN have zero remaining lots (correct — full 08-18 exits), and CLS (0.003266) / TER (0.002731) dust lots match live holdings qty almost exactly. One discrepancy: the BX lot in lots.json is dated 2026-08-21, but the orchestrator's stated re-entry date is 2026-08-24 — a 3-day gap worth a smith-ledger reconciliation pass. Immaterial for LTCG either way (both dates are under a week old).

## 4. Beta cache refresh
compute_book.json flagged WDC and HOOD as defaulted to 1.0 (no cache entry). Fetched fresh via yfinance `get_key_stats` (single batched call):
- **WDC: 2.217** (plausibility band 0–3.5, OK)
- **HOOD: 2.321** (plausibility band OK)

Both replace the 1.0 default with real, materially higher betas — the risk_concentration table in compute_book.json will re-rank once these fold in on the next script pass (WDC 2.33% weight, HOOD 1.39% weight, both currently under-counted in risk terms). No cache entries in `data_cache_betas` are past the 30-day TTL (oldest live entry is GOOG at 2026-07-28, 27 days old — still inside window); only WDC/HOOD needed refresh this run.

## 5. Risk narrative
Risk concentration is running hotter than weight concentration at the top: BE carries 5.08% of book weight but 9.4% of risk-weighted exposure (beta 2.105), and NBIS is worse in relative terms — 3.87% weight driving 8.98% of risk (beta 2.636). MRVL (4.77% wt / 7.03% risk, beta 1.676), MU (3.65% wt / 6.27% risk, beta 1.954) and FLTW (2.58% wt / 5.47% risk, beta 2.411) round out a top-5 risk table where every name is running at 1.4–2x its weight in beta-adjusted terms. Portfolio beta is 1.137 on an SPX basis but the script's own primary-benchmark read (1.19 vs SOX/SMH) is the one to size against — SPX's 1.491 secondary beta overstates true factor exposure and should not drive position sizing. Total-book drawdown sits at -6.89% off the 44,873 USD total-book peak, against an ESCALATING pre-open gate classification — the same regime that preceded the 08-18 stop-loss cascade which fully exited COHR/IREN and left CLS/TER as dust. With BE, NBIS and MU sitting at the top of both the risk-concentration table and (per the orchestrator's cascade history) the tight-SL discipline this book runs, further beta-driven stop-outs are a live path if the ESCALATING read persists into the open. Cash buffer (wallet) is 6.63% of total book (2,769 USD) — thin relative to the risk concentration sitting in three single-digit-weight, high-beta names.

## Data quality
- betas defaulted to 1.0 pre-run for WDC, HOOD (no cache entry) — refreshed this run via yfinance, both in-band.
- BX lot in lots.json dated 2026-08-21 vs. orchestrator-stated re-entry date 2026-08-24 — flag for smith-ledger, no LTCG impact.
- SK Hynix ADR (SKHY) returned no dividend fields from yfinance (ADR-level distribution data gap) — treated as 0 yield in the portfolio calc; may modestly understate true trailing yield.
- INTC (ex-div 2024-08-07) and AMD (ex-div 1995-04-27) returned stale ex-dividend dates from yfinance reflecting suspended/no current dividend — correctly excluded from upcoming ex-date list and yield calc.
- ltcg_flags empty this run: book too young (oldest lot 34 days) for any 24-month LTCG boundary proximity — not a data gap, a timing fact.

```json
{"div_yield_pct":0.53,"ex_dates":[{"ticker":"GLW","ex_dividend_date":"2026-08-31","days_out":7},{"ticker":"QCOM","ex_dividend_date":"2026-09-03","days_out":10},{"ticker":"GOOG","ex_dividend_date":"2026-09-04","days_out":11},{"ticker":"WDC","ex_dividend_date":"2026-09-08","days_out":15},{"ticker":"TSM","ex_dividend_date":"2026-09-16","days_out":23},{"ticker":"STM","ex_dividend_date":"2026-09-22","days_out":29}],
 "ltcg_narrative":[],
 "refreshed_betas":{"WDC":2.217,"HOOD":2.321},
 "risk_narrative":"BE (5.08% wt / 9.4% risk, beta 2.105) and NBIS (3.87% wt / 8.98% risk, beta 2.636) are the standout disproportionate risk contributors, followed by MRVL, MU and FLTW -- all top-5 risk names run 1.4-2x their weight in beta-adjusted terms. Portfolio beta is 1.137 (SPX basis) but the true factor read is 1.19 vs SOX/SMH per the primary_benchmark note; the 1.491 SPX secondary beta overstates exposure and should not drive sizing. Total-book drawdown is -6.89% off the 44,873 USD peak under an ESCALATING pre-open gate -- the same regime that preceded the 08-18 stop-loss cascade (COHR/IREN full exits, CLS/TER left as dust). BE/NBIS/MU sitting atop both the risk table and the book's tight-SL discipline makes further beta-driven stop-outs a live risk if ESCALATING persists into the open. Cash buffer is thin at 6.63% of total book (2,769 USD) relative to the risk sitting in these three names.",
 "data_quality":["betas defaulted to 1.0 pre-run for WDC, HOOD -- refreshed via yfinance this run, both in-band (0-3.5)","BX lot dated 2026-08-21 in lots.json vs stated 2026-08-24 re-entry -- reconciliation flag for smith-ledger, no LTCG impact","SKHY (SK Hynix ADR) returned no dividend fields from yfinance -- treated as 0 yield, may understate true portfolio yield modestly","INTC/AMD ex-dividend dates from yfinance are stale (2024/1995) reflecting suspended/no dividend -- correctly excluded","ltcg_flags empty: book too young (oldest lot 34 days) for 24-month LTCG boundary proximity, not a data gap"]}
```

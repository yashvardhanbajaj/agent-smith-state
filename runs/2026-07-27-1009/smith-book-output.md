# Smith Book & Risk — Deep Add-Ons (2026-07-27)

## 1. Dividend income
- Portfolio trailing dividend yield (weighted, equity sleeve only): **~0.35%** (weight_pct x trailing dividendYield across 21 positions; ETFs DRAM/EWY excluded — yfinance stock-summary endpoint returns no dividendYield field for them, flagged as data gap, not assumed zero-yield).
- Per-name trailing yields feeding the calc (top contributors): QCOM 2.20%, ORCL 1.74%, TSM 0.94%, AVGO 0.68%, LRCX 0.34%, NVDA 0.48%, ASML 0.52%, GEV 0.20%. Remaining names (SNDK, CLS, COHR, ARM, AMD, CIEN) pay no dividend currently.
- Book is overwhelmingly a capital-appreciation (AI capex) sleeve — dividend income is immaterial to total return, consistent with the growth-factor policy.

## 2. Ex-dividend dates within 30 days (of 2026-07-27)
- **ASML** — ex-div 2026-07-28 — 1 day out. $9.09/share annual rate.
- **AMAT** — ex-div 2026-08-20 — 24 days out. $2.12/share annual rate.
- (QCOM 2026-09-03 and TSM 2026-09-16 are outside the 30-day window — 38 and 51 days out respectively — noted for awareness only, not flagged as near-term.)

## 3. LTCG narrative
- compute_book.json's `ltcg_flags` is empty because **lots.json is unseeded** (only the schema template/example exists, zero real lot records) — standing gap **G1**.
- No holding-period estimation was attempted from any other source (price history, qty_changes, etc.) per instruction — this would be a guess, not a computed LTCG boundary.
- Action needed to unblock: seed lots.json from INDmoney order-history CSV or manual entry. Until then, LTCG-aware trim sequencing cannot be computed for any of the 21 positions, including the qty-halved names (SNDK, DRAM, TSM, CLS, LRCX, MU, TER, CIEN) that are also active trim/flow candidates from the 07-24/25 de-risking event.

## 4. Beta cache refresh (SNDK, DRAM, ARM)
Computed via real price history — 15 weekly closes (2026-04-20 to 2026-07-24) for each name vs. SMH (SOX/semicap proxy), weekly-return covariance regression (n=14 return observations per name). All results within the 0–3.5 plausibility band; none defaulted or estimated.

| Ticker | Beta (vs SMH) | Corr | N |
|---|---|---|---|
| SNDK | 2.566 | 0.888 | 14 |
| DRAM | 2.202 | 0.915 | 14 |
| ARM  | 1.756 | 0.603 | 14 |

Note: ARM's correlation (0.603) is meaningfully weaker than SNDK/DRAM — its beta estimate is noisier (idiosyncratic name-specific moves, e.g. licensing-deal headlines, dilute the SOX-factor read). Still a real regression output, not a guess — orchestrator should weight confidence accordingly when folding into risk_concentration.

These 3 replace the 1.0-default entries per G15 (guessed-value shortcut reverted 07-26; this run supplies the actual computed replacement). Write to data_cache.betas with today's date (2026-07-27) and a fresh TTL.

## 5. Risk narrative
Portfolio beta (1.608 vs SOX/SMH's own 1.19) confirms the book runs meaningfully hotter than its own primary benchmark — this is a single-factor AI-capex bet, not diversified semi exposure. Three names contribute risk out of proportion to their book weight: NVDA (10.1% weight but 13.9% of risk-weighted concentration, beta 2.211), MRVL (7.1% weight / 9.67% risk, beta 2.197), and VRT (6.7% weight / 8.49% risk, beta 2.029) — together these three account for ~32% of risk-weighted concentration versus ~24% of book weight, meaning a SOX drawdown would hit the book harder than raw weights suggest. EWY (7.67%/6.97%, beta 1.46) is roughly proportional. ASML (7.49% weight / 6.5% risk, beta 1.394) is the one top-5 name that's mildly risk-diversifying. Drawdown is -5.857% off total-book peak ($41,923 to $39,468) — modest and nowhere near a stress threshold; the 46.09% cash wallet (standing hedge, not new) is doing real work muting the beta-1.608 equity sleeve's effective book-level volatility.

## Data quality / gaps
- G1: lots.json unseeded — LTCG flags unavailable (standing).
- G15: SNDK/DRAM/ARM beta defaults replaced this run with computed values (see table above) — resolved for this cycle, re-verify next TTL cycle.
- ETF dividend yields (DRAM, EWY) unavailable via yfinance stock-summary endpoint — not assumed zero, flagged as gap.
- AMD's returned "exDividendDate" (1995-04-27) is a stale/legacy field artifact from yfinance, not a live schedule — AMD pays no current dividend; excluded from ex-date list.

```json
{"div_yield_pct":0.35,
 "ex_dates":[{"ticker":"ASML","ex_dividend_date":"2026-07-28","days_out":1},{"ticker":"AMAT","ex_dividend_date":"2026-08-20","days_out":24}],
 "ltcg_narrative":[{"ticker":null,"months_to_ltcg":null,"note":"lots.json unseeded (only schema template present) -- LTCG flags unavailable, standing gap G1. No estimation attempted from other data sources."}],
 "refreshed_betas":{"SNDK":2.566,"DRAM":2.202,"ARM":1.756},
 "risk_narrative":"Portfolio beta 1.608 vs SOX/SMH benchmark beta 1.19 -- book runs hotter than its own primary factor. NVDA (10.1% wt / 13.9% risk), MRVL (7.1% wt / 9.67% risk) and VRT (6.7% wt / 8.49% risk) contribute disproportionate risk (beta 2.0-2.2 each); ASML (7.49% wt / 6.5% risk, beta 1.394) is mildly diversifying. Drawdown -5.857% off total-book peak is modest, not near a stress threshold. 46.09% cash wallet is the standing hedge muting book-level volatility.",
 "data_quality":["G1: lots.json unseeded, LTCG flags unavailable","G15: SNDK/DRAM/ARM betas computed fresh this run via 15-wk SMH regression, replacing 1.0 defaults","ETF dividend yields (DRAM, EWY) unavailable via yfinance stock-summary, not assumed zero","ARM beta corr only 0.603 -- noisier estimate than SNDK/DRAM, flag confidence to orchestrator","AMD exDividendDate field (1995) is stale yfinance artifact, ignored"]}
```

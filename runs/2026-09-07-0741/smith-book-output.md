# smith-book output — 2026-09-07 (deep)

## Beta cache refresh
Scope per compute_book.json/compute_bookcalc.json: no held name was defaulted to 1.0
(compute_book.json data_quality is empty — every position has a cache hit). The one
actionable flag was bookcalc's `betas_missing: ["STM"]` — STM's cache entry (1.521,
2026-08-16) is on the wrong benchmark (`SPX_native_yfinance`, not the SMH regression
used everywhere else), so bookcalc correctly excluded it from risk-weighted ranking
rather than let it distort the table.

Fetched STM + SMH, 1mo/1d, 23 true-daily bars each (2026-08-05..09-04), not truncated.
OLS beta (cov(STM,SMH)/var(SMH)) over the 22 daily-return pairs = **1.16**.

- Sanity: 0–3.5 band OK. Lower than STM's old SPX-native reading (1.521) — expected,
  since SMH is itself a high-beta index, so a name's loading against it is typically
  smaller than against SPX.
- No ETF/thin-history gap this run (DRAM/EWY/CQQQ/SNDK not held) — stockanalysis.com
  fallback not needed.
- All other held-name cache entries are 5-8 weeks stale (as_of 2026-07-28..08-29) but
  none are flagged missing/wrong-benchmark by the script, and the run's tool budget is
  reserved for the one explicit flag; they stand for the orchestrator's discretion on
  a rolling refresh cadence.

## Risk narrative
The book is concentrated in dollars (top5 = 30.0%, top10 = 50.85% of $39,719 total,
no single name over 10%) but MORE concentrated in risk than dollars would suggest.
BE (5.1% weight, beta 2.105) and NBIS (4.0% weight, beta 2.636) are the clearest risk
hogs — each contributes ~7.6-7.9% of portfolio risk on roughly half that in dollar
weight, a ~2.9-3.8pp risk-minus-dollar gap driven entirely by high beta, not size.
MRVL, TER and MU repeat the same pattern at smaller magnitude (each ~1.2-1.7pp hot).
The mirror case is GEV: the single largest position (9.5% of book) but the quietest
name in the top ranks (beta 0.777), contributing only 5.5% of risk — a full 4.0pp
below its dollar weight — so trimming GEV for "concentration" would cut the least
risky dollar in the book, while BE/NBIS are the names actually driving portfolio
volatility beyond what their ticket size implies. ASML, TSM, NVDA and APH show the
same quiet-size pattern on a smaller scale.

Portfolio beta is 1.419 vs SPX (secondary) / 1.19 vs SOX-SMH (primary, the true
factor per policy). Drawdown is -6.364% off the $42,419 total-book peak — comfortably
inside the 15% policy warn threshold and nowhere near the 25% risk-off line; no
ladder rung is close to triggering. Net: this is a risk story about composition
(BE/NBIS running hot beta relative to ticket size), not a drawdown or aggregate-size
story.

## Data quality
- STM: refreshed via live regression this run (see above); benchmark now consistent
  (SMH) for the first time.
- 27 other held-name betas are 5-8 weeks stale but not flagged by the script this run;
  not refreshed to stay inside tool budget — flagging for a future rolling-refresh pass
  rather than reacting reactively only to explicit-missing/wrong-benchmark flags.
- market_cap_allocation in compute_book.json is entirely "Unclassified" (100.002%) —
  not this agent's scope to fix, but worth the orchestrator's attention since it makes
  that section of compute_book.json non-informative.

```json
{"refreshed_betas":{"STM":1.16},"beta_benchmark":"SMH",
 "risk_narrative":"Book is concentrated in dollars (top5 30.0%, top10 50.85%, no name >10%) but more concentrated in risk than dollars imply: BE (5.1% wt, beta 2.105, 7.95% of risk) and NBIS (4.0% wt, beta 2.636, 7.80% of risk) are the clearest risk hogs, each running 2.9-3.8pp hotter in risk than in weight, with MRVL/TER/MU repeating the pattern at smaller scale. GEV is the mirror case -- largest dollar position (9.5%) but quietest beta (0.777), contributing only 5.47% of risk (-4.03pp), so it is the least risky dollar in the book despite being the biggest. Portfolio beta 1.419 (SPX) / 1.19 (SOX-SMH primary). Drawdown -6.364% off the $42,419 peak is well inside the 15% policy warn threshold and far from the 25% risk-off line -- no ladder rung is close.",
 "data_quality":["STM was the only name flagged (betas_missing / wrong-benchmark) this run and was refreshed vs SMH: 1.16, 23 true-daily bars, not truncated.","27 other held-name cache entries are 5-8 weeks stale (as_of 2026-07-28..08-29) but not flagged missing/wrong-benchmark by the script, so left untouched to stay inside the ~10-call tool budget -- candidate for a rolling-refresh pass.","market_cap_allocation in compute_book.json is 100% Unclassified -- out of this agent's scope but flagged for the orchestrator."]}
```

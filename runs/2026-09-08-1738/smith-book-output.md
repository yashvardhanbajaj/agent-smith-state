# smith-book — 2026-09-08 deep run

## Beta cache refresh (vs SMH, 23 true-daily bars 2026-08-05..09-04)
23 names in the book were past the 30-day TTL (as_of 07-28..08-07). Budget allowed 10 of them —
prioritized by weight and by membership in the six over-ATR-cap names. Remaining 13 expired names
(AMAT, AVGO, CIEN, CLS, GLW, GOOG, IREN, LRCX, NVDA, QCOM, TSM, MSFT, SKHY) still carry stale betas;
flagged for next deep run.

| Ticker | Old beta (as_of) | New beta | Delta |
|---|---|---|---|
| GEV | 0.777 (07-31) | 0.719 | -0.058 |
| ASML | 0.926 (07-31) | 0.758 | -0.168 |
| BE | 2.105 (07-31) | 1.327 | -0.778 |
| MRVL | 1.676 (07-31) | 1.493 | -0.183 |
| VRT | 1.082 (07-31) | 1.108 | +0.026 |
| TER | 1.832 (07-31) | 1.652 | -0.180 |
| NBIS | 2.636 (07-31) | 2.317 | -0.319 |
| MU | 1.954 (07-31) | 1.227 | -0.727 |
| COHR | 1.707 (07-31) | 2.580 | +0.873 |
| AMD | 1.566 (07-31) | 0.875 | -0.691 |

All 10 within 0-3.5 plausibility band. No ETF/thin-history fallback needed this run (no expired
name fell into the DRAM/EWY/SNDK-style no-beta bucket among the 10 refreshed).

**Note for orchestrator:** `compute_bookcalc.json`'s risk_weighted_concentration table (BE, NBIS,
MRVL, TER, MU as risk hogs) was built on the stale betas above — BE and MU in particular were
overstated (2.105→1.327, 1.954→1.227) and COHR was understated (1.707→2.580). Re-run bookcalc with
this refreshed cache before trusting that table's ranking again.

## Risk narrative
The book's -$112.61 move this run is a pure currency effect on unchanged Friday 09-04 prices
(FX +$400.23 vs residual market -$512.83, flow $0.00) — there is no fresh price signal to react to.
Concentration is a dollars-and-risk story that reads differently on each axis. In dollars: GEV alone
is 9.51% of equity (already over its individual ATR cap) and the top 5 names carry roughly a third
of the book — high but not unusual for a 32-name single-factor sleeve. In risk terms, using the
refreshed betas, GEV's own contribution is muted (beta 0.719, among the lowest in the book) — its
concentration risk is real but mostly a sizing problem, not a volatility problem. The two names that
are actually load-bearing on the 9.894%-vs-10% aggregate cap are NBIS (weight 3.969%, beta 2.317,
implied risk contribution ~9.2%) and COHR (weight 3.548%, beta 2.580 — the highest beta in the book
after this refresh, up from 1.707), both already flagged over their individual ATR caps. With the
aggregate cap breached as recently as the last validate run (10.559%) and only ~0.11pp of headroom
left, a gap-down in either NBIS or COHR — both single-day-double-digit-move names historically — is
what would push the aggregate back over 10% fastest; MRVL and TER contribute meaningfully but at
roughly half NBIS/COHR's per-dollar risk. BE's risk profile actually calmed the most in this refresh
(beta 2.105→1.327), so despite being the second-largest of the six over-cap names by weight (5.362%),
it is no longer the aggregate's biggest single swing factor. Drawdown at -0.28% from a $42,429 peak
is nowhere near a policy threshold — not a live concern this run. Cash at 6.39% sits inside the
[5,15] band but with $0 deployable above the floor, so there is no dry powder to react to a gap
without breaching the band. AI-capex concentration (95.42% of equity) is unchanged and remains the
dominant structural risk underneath all of the above — every over-cap name is inside the same factor.

## Data quality
- 13 of 23 TTL-expired betas not refreshed this run (tool-call budget); using stale cache values,
  flag for next deep run: AMAT, AVGO, CIEN, CLS, GLW, GOOG, IREN, LRCX, NVDA, QCOM, TSM, MSFT, SKHY.
- LTCG: all 72 open lots short-term (earliest 2026-07-21, first 24-month crossing 2028-07-21) — no
  live LTCG decision exists; not treated as a constraint this run.
- risk_weighted_concentration in compute_bookcalc.json was computed on pre-refresh betas; ranking
  will shift once folded back in (BE/MU down, COHR up materially).

```json
{"refreshed_betas":{"GEV":0.719,"ASML":0.758,"BE":1.327,"MRVL":1.493,"VRT":1.108,"TER":1.652,"NBIS":2.317,"MU":1.227,"COHR":2.580,"AMD":0.875},
 "beta_benchmark":"SMH",
 "risk_narrative":"Book move this run is a pure FX effect on unchanged 09-04 prices, no new price signal. Dollar concentration (GEV 9.51% of equity, top5 ~1/3 of book) and risk concentration diverge: GEV's refreshed beta (0.719) is low, making it a sizing risk more than a volatility risk. NBIS (wt 3.969%, beta 2.317) and COHR (wt 3.548%, beta 2.580, highest beta in book post-refresh) are the true load-bearing names on the 9.894%-vs-10% aggregate cap, which had breached 10.559% as recently as the last validate -- with only ~0.11pp headroom, a gap in either is what would push it back over. BE's risk cooled sharply this refresh (2.105->1.327) despite being the 2nd-largest of the six over-cap names by weight. Drawdown -0.28% and cash-band position are not live concerns; AI-capex concentration (95.42% of equity) remains the structural risk underneath all six over-cap names.",
 "data_quality":["13 of 23 TTL-expired betas not refreshed this run (budget): AMAT, AVGO, CIEN, CLS, GLW, GOOG, IREN, LRCX, NVDA, QCOM, TSM, MSFT, SKHY -- refresh next deep run","compute_bookcalc.json's risk_weighted_concentration table was built on pre-refresh betas (BE/MU overstated, COHR understated) -- re-fold with this cache before trusting its ranking"]}
```

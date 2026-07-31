# Smith Book & Risk Narrator — 2026-07-31 deep run

## INCOME
- Portfolio trailing dividend yield (weighted on equity book, ex-cash): ~0.28%
- Payers used: ASML 0.59%, NVDA 0.53%, MU 0.07%, AVGO 0.70%, VRT 0.11%, TSM 1.01%,
  GEV 0.22%, CEG 0.66%, QCOM 2.26%, GLW 0.90%, AMAT 0.49%, ORCL 1.70%
- Non-payers (0% yield, excluded): SNDK, GOOGL, DRAM, MRVL, AMD, EWY, COHR, TER, CLS,
  NBIS, ARM, BE, MKSI, IREN, CIEN
- Upcoming ex-dividend within 30 days: **AMAT — 2026-08-20 (20 days out)**
- Just outside the 30-day window: GLW 2026-08-31 (31 days out — flag for next run)
- Already passed this cycle (informational only): ASML 2026-07-28, ORCL 2026-07-10,
  MU 2026-07-06, AVGO 2026-06-22, NVDA 2026-06-04, VRT 2026-06-15, GEV 2026-06-16,
  CEG 2026-05-15

## LTCG NARRATIVE
- compute_book.json returned `ltcg_flags: []` — no positions currently within 6 months
  of, or past, the 24-month Indian LTCG boundary.
- This is expected, not reassuring: lots.json is still effectively unseeded (known gap
  **G1**). Only 4 lots exist (GOOG, AVGO, TSM, ASML), all dated 2026-07-28 — i.e. 3 days
  old — so the empty flag list reflects missing data, not a clean LTCG runway. The true
  holding periods for the other 23+ names (some likely held well over a year given the
  book's age) are unknown and cannot be estimated from price/qty history alone.
- No LTCG estimate attempted for any name outside the 4 seeded lots, per instruction.

## RISK NARRATIVE
Portfolio beta sits at 1.349 against the SOX/SMH benchmark's 1.19 — still running hot,
i.e. the book is structurally more volatile than the semi-index itself, not just riding
it. The risk-weighted concentration table shows the excess isn't spread evenly: SNDK
(6.99% of book) contributes 15.16% of risk-weighted concentration — more than double its
capital weight — on a 2.92 beta, the single largest risk/capital mismatch in the book.
DRAM (6.89% weight -> 10.59% risk, beta 2.07) and MU (6.96% weight -> 10.09% risk, beta
1.95) repeat the same pattern: the memory cluster is now the book's dominant risk driver,
not just a large position. MRVL (6.02% weight -> 7.49% risk, beta 1.68) adds a fourth
name skewing the same way; ASML is the outlier at the other end (8.66% weight but only
5.94% risk, beta 0.93 — a genuine ballast position). Drawdown is -8.35% from the
total-book peak ($44,873 -> $41,126) — not yet at a policy-breach level but a real
give-back after the 07-28 crash, only partly clawed back by the 07-29/30 rally. Cash is
down to 5.4% of total book ($2,222 of $41,126) — the low end of the normal 5-15% band
after weeks of redeploying into the dip. This isn't a breach, but dry powder is now
genuinely thin: another leg down would have to be absorbed mostly by existing positions
rather than fresh buys, and the elevated beta/risk concentration in the memory names
means that leg down would hit disproportionately hard.

## DATA QUALITY
- G1 (lots.json unseeded beyond 4 recent lots) — still open, blocks real LTCG analysis.
- Betas/ATR were pre-refreshed by orchestrator this run — not touched here, per instruction.
- Dividend data via yfinance; skipped silently for names with no dividend history (none
  needed skipping — all 12 candidate payers returned data).

```json
{"div_yield_pct":0.28,"ex_dates":[{"ticker":"AMAT","ex_dividend_date":"2026-08-20","days_out":20}],
 "ltcg_narrative":[{"ticker":null,"months_to_ltcg":null,"note":"lots.json unseeded beyond 4 lots opened 2026-07-28 (3 days old) -- known gap G1, no LTCG flags possible for the other 23+ holdings, none estimated"}],
 "risk_narrative":"Portfolio beta 1.349 vs SOX/SMH benchmark 1.19 -- running hot. Risk-weighted concentration is driven by the memory cluster: SNDK (6.99% weight, 15.16% risk, beta 2.92), DRAM (6.89% weight, 10.59% risk, beta 2.07), MU (6.96% weight, 10.09% risk, beta 1.95), MRVL (6.02% weight, 7.49% risk, beta 1.68) all carry risk shares well above their capital weights; ASML (8.66% weight, 5.94% risk, beta 0.93) is the ballast counterweight. Drawdown -8.35% from total-book peak ($44,873->$41,126), not yet policy-breach but a real give-back post 07-28 crash only partly clawed back by 07-29/30 rally. Cash at 5.4% of total book is low end of the 5-15% band -- thin dry powder if another leg down hits, and it would land hardest on the already risk-heavy memory names.",
 "data_quality":["G1: lots.json unseeded beyond 4 recent lots (2026-07-28) -- LTCG analysis blocked for 23+ holdings","GLW ex-date 2026-08-31 is 31 days out, just outside the 30-day window -- watch next run"]}
```

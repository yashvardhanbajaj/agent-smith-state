# smith-book deep output — 2026-09-06

## Income
Trailing yield computed only over the 5 confirmed dividend payers fetched (APH, AVGO, GLW, MSFT, TSM); other holdings' payer status not checked this run (budget) — do not read as full-book yield.
Weighted contribution: APH 0.0252 + AVGO 0.0132 + GLW 0.0085 + MSFT 0.0092 + TSM 0.0308 = ~0.081 pct-pts of total book.

Ex-dividend dates within 30 days (today 2026-09-06):
- TSM: 2026-09-16 (10 days out) — qty 3, ~$4.08/sh annual rate → ~$1.02 quarterly cash
- AVGO: 2026-09-21 (15 days out) — qty 2, ~$2.60/sh annual → ~$1.30 quarterly cash
- APH: 2026-09-22 (16 days out) — qty 10, ~$1.00/sh annual → ~$2.50 quarterly cash
(GLW ex-date 2026-08-31 and MSFT 2026-08-20 already passed; next cycle not yet posted.)

## LTCG narrative
compute_book.ltcg_flags is empty — correct, not a gap. Earliest open lot in lots.json is dated 2026-07-15, so the earliest 24-month Indian LTCG boundary is ~2028-07. There are NO live LTCG-deferral decisions in this book; nothing is within 6 months of the boundary. Flat statement, not manufactured urgency.

## Beta cache refresh
Cache had no top-level as_of stamp despite per-entry dates. Refreshed the 3 held names missing entirely from data_cache.betas (all true daily bars, period=1mo, ≤3 symbols/call, vs SMH):
- ALAB: 1.634 (23 daily obs, 2026-08-05..09-04)
- APH: 0.539 (new position, 23 daily obs) — low-beta connector name, sits well below book beta of 1.417
- FSLR: 0.170 (23 daily obs) — near-zero SMH correlation, solar/policy-driven not semis-driven

All in plausible band (0–3.5). No stockanalysis.com fallback needed — yfinance returned usable history for all three.

APH lot check: **APH has NO entry in lots.json** despite being a confirmed 10-share position (compute_book qty_changes shows prior_qty 0 → 10, est_cost $827.80, trade_reason UNMATCHED). This is a ledger gap, not a beta gap — flag for smith-ledger.

## Risk concentration read
compute_book.risk_concentration (beta x weight) top-5: BE (5.10% wt, β2.105 → 7.57% of risk), NBIS (3.99% wt, β2.636 → 7.43% of risk), MRVL (5.07% wt, β1.676 → 5.99%), TER (4.50% wt, β1.832 → 5.82%), MU (3.84% wt, β1.954 → 5.30%). BE and NBIS punch far above their capital weight — together ~9.1% of dollars but ~15% of portfolio risk. By contrast GEV, the single largest weight (9.50%), has a sub-1 beta (0.777) and is UNDER-represented in the risk table — it's a size concentration, not a risk concentration. Portfolio beta 1.417 vs SMH confirms the book still runs meaningfully hotter than the semis benchmark. Drawdown is 0.0% (fresh peak $42,418.68) — no proximity to any policy drawdown threshold; cash at 6.39% sits comfortably inside the 5–15% band. Note: the top-3-by-weight figures cited in this run's dispatch (GEV 10.6%/MRVL 5.04%/VRT 4.93%) don't match compute_book.top3 (GEV 9.501%/ASML 5.399%/BE 5.095%) — using the compute_book values as ground truth per instructions; flagging the mismatch for the orchestrator.

## Data quality
- Dividend yield/ex-dates checked for only 5 of 32 names (payers only among APH/AVGO/GLW/MSFT/TSM); remaining book not screened for dividend status this run.
- APH missing from lots.json — ledger gap, needs smith-ledger.
- G18/G81/G82/G83/G85/G86/G69/G78 standing gaps unchanged, not re-derived here.

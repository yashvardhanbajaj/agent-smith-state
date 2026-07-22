# Signal Scan — 2026-07-22 (pre-open, quick mode)
Session: US cash opens ~7pm IST tonight. Prices below use ext_hr_live_price (pre-market, per G3 overlay fix) for pos/day-move reads; "Monday close" = last completed regular session (the AI-capex/memory rally).

## BREAKDOWN
- ORCL — 1.24% wt — pos 0.03 (ext_hr $126.50 vs 52wk low $120.03) — mean $249.24, +49.0% upside. Repeat (open_flag: bought into breakdown 07-17). 21-Jul article adds explicit credit-rating downgrade + possible $7B data-center guarantee. Also newly PEER LAGGARD vs XLK (-8.5%, ORCL 1mo -14.5% vs XLK -5.9%).

## STRONG UPTREND
- AMD — 2.62% wt — pos 0.88 — mean $541.66, upside -0.5% (at target). Monday close +8.1% on Microsoft/Helios AI-rack news. New PEER LEADER (+17.1% vs SMH -12.7%).
- GEV — 2.65% wt — pos 0.82 — mean $1221.48, +11.7% upside. Position rebuilt from dust to a real 1sh; $11B grid-capex plan (21-Jul, positive).
- ASML — 4.36% wt — pos 0.83 — mean $2121.55, ~+15-19% upside. Repeat (STRONG UPTREND/TARGET GAP/POLICY IMPACT unchanged — export-control risk persists, no new development post-07-20). New PEER LEADER (+13.1% vs SMH).

## OVERSOLD BOUNCE
- BABA — 1.42% wt, NEW position (5sh) — pos 0.24 — mean $190.62, +38.1% upside. 21-Jul positive news (Apple AI-partnership integration). Also PEER LEADER vs KWEB (BABA 1mo +24.4% vs KWEB +7.9%, +16.6pp).

## INSIDER ACTIVITY
- CIEN — 1.35% wt — repeat (open_flag: CEO+3 execs cluster-sold, filed 7/17). No new filings since. Position trimmed 3.39→1.39sh this cycle, consistent with the trim-candidate read. New MOMENTUM+VOLUME: Monday close +7.9%.

## MOMENTUM+VOLUME (Monday 07-21 close rally, fading 1-3.5% pre-market)
- SNDK — 11.45% wt (largest) — Monday +14.3%, now $1551 pre-mkt (-2.4%). No analyst target available this run (data gap).
- MU — 4.63% wt — Monday +12.2% — mean $1491.95, +34.9% upside.
- TER — 2.67% wt — Monday +12.1% — mean $426.35, +12.3% upside (gap now <15%, dropped from TARGET GAP).
- CLS — 4.09% wt — Monday +10.5% — mean $448, +24.2% upside.
- LITE — 2.00% wt — Monday +9.4% — mean $1104.89, +24.2% upside.
- DRAM (ETF) — 6.96% wt — Monday +10.9%.
- AMAT — 0.01% wt (cut to dust, 2.009→0.0092sh) — Monday +7.4%, continuing the 07-20 journal flag; position now immaterial.

## TARGET GAP (≥15% upside; mean target cited)
- IREN — 2.48% wt — mean $80.93, +49.0% upside (largest gap in book) — AI-cloud contract tailwind continuing.
- MU, CIEN, CLS, LITE — see above (momentum bucket, also carry TARGET GAP).
- GOOG — 1.71% wt — mean $430.07, +19.5% upside — open_flag (07-17 re-entry flip-flop) still unresolved; new PEER LEADER (+9.4% vs XLK).
- QCOM — 5.84% wt — mean $222.73, +22.1% upside — position increased 6→14sh (near-doubled, now 5.84% wt); PEER LAGGARD tag dropped (now neutral, +4.3% vs SMH).
- NVDA — 6.03% wt — mean $302.31, +31.4% upside — repeat, PEER LEADER (+20.4% vs SMH, unchanged).
- TSM — 6.11% wt — mean $522.82, +18.8% upside — new PEER LEADER (+10.9% vs SMH).
- META — 3.15% wt — mean $822.69, +21.7% upside — repeat, PEER LEADER (+22.9% vs XLK, unchanged).
- MRVL — 3.49% wt — mean $253.69, +18.0% upside — repeat, still PEER LAGGARD (-9.4% vs SMH).
- AVGO — 1.86% wt — mean $524.51, +26.3% upside — new PEER LEADER (+18.6% vs SMH); POLICY IMPACT (EU antitrust/VMware review) unchanged.
- Also ≥15%, unchanged reads: VRT +19.7% ($379), COHR +19.0% ($391), GLW +24.1% ($214, trimmed 19→10sh) — no new catalysts since last run.

Closed/narrowed gaps (now <15%, dropped from bucket): LRCX (12.6%), TER (12.3%), ARM (4.9%), STM (9.4%), AMAT (9.4%), AMD (-0.5%).

## EARNINGS PROXIMITY
None at >5% weight confirmed within 7 days this run. STM (23-Jul) and ARM (29-Jul) report soon but are sub-5% weight (1.6%/1.4%) — not flagged per threshold.

## Unchanged repeats
NVDA (TARGET GAP, PEER LEADER), META (TARGET GAP, PEER LEADER), MRVL (TARGET GAP, PEER LAGGARD), STM (none), LRCX (none) — no material change (news/pos/analyst action) since last run.

Peer-laggard tags resolved to neutral this run (no longer ≤-8%): QCOM, VRT, COHR, IREN, ARM, NBIS.

## Still pending
- ORCL debt/FCF concerns (open_flag 07-17/18) — reinforced by 21-Jul credit-downgrade article; unresolved.
- CIEN insider cluster-sell (open_flag 07-18) — no new filings; user has already trimmed the position.
- SNDK peer-laggard vs SMH (open_flag 07-14) — this run's 1mo calc shows -11.3% relative (SNDK -24.0% vs SMH -12.7%), smaller magnitude than the flagged -38% (likely a longer lookback there) — flagging the discrepancy, not resolving it.
- GOOG re-entry flip-flop (open_flag 07-17/18) — still open; user should review directly.

## Data quality
- SNDK (largest position, 11.4%): analyst_forecast returned empty — no target/upside computable this run.
- NBIS: analyst target unavailable.
- DRAM: feed returned 52week_low=0 (bad data) — pos set to 0.5 per guardrail, not a genuine mid-range read.
- IREN: sector tagged "Financials" in feed (likely misclassification; cosmetic).
- Peer-ETF and holding 1mo returns are same-session yfinance pulls, not pre-market-adjusted — treat peer-relative reads as directional given the ongoing rally/fade.

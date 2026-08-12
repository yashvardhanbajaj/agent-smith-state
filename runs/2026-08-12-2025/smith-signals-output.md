# Signal scan — 2026-08-12 (quick, intraday 10:55 ET)

> **DEGRADED — computed by the orchestrator, not smith-signals.** The sub-agent failed twice on
> API 529 (server-side overload), exhausting its one retry per the SKILL's failure rule. Everything
> below is derived from data already on disk, using smith-signals.md's own thresholds verbatim:
> `strong_move_threshold_pct = clamp(1.5 x atr20_pct, 2.0, 12.0)` and
> `rel_sigma = rel_strength_1m_pp / max(2.3 x atr20_pct, 5.0)`, PEER at |sigma| >= 1.0.
> **NOT COVERED** (needs fetches this fallback did not make): `pos`-based buckets (BREAKOUT,
> BREAKDOWN, pos-gated UPTREND/DOWNTREND, OVERSOLD BOUNCE, OVERBOUGHT PULLBACK), TARGET GAP
> (no analyst targets), NEW TAILWINDS/HEADWINDS and POLICY IMPACT (no news read), EARNINGS
> PROXIMITY, INSIDER ACTIVITY. Those buckets are ABSENT, not empty — do not read their absence
> as 'no signal'. RSI buckets below are computed from the seeded rsi14 cache and are a partial
> substitute for the pos-gated oversold/overbought pair, not the same test.

## STRONG UPTREND
- NBIS +20.61% — 1.61x its 12.82% ATR (thr +12.00%) — 3.50% of book

## MOMENTUM+VOLUME
- NBIS +20.61% (1.61x ATR) — 3.50% of book

## PEER LEADER
- FLTW +6.2% 1m vs SMH +0.73% (+5.5pp, +1.10σ on a 1.89% ATR) — genuinely leading
- ORCL +17.5% 1m vs SMH +0.73% (+16.7pp, +1.33σ on a 5.47% ATR) — genuinely leading
- NOW +20.9% 1m vs SMH +0.73% (+20.2pp, +1.55σ on a 5.65% ATR) — genuinely leading

## PEER LAGGARD
- STM -14.8% 1m vs SMH +0.73% (-15.5pp, -1.61σ) — genuinely lagging

## RSI OVERSOLD (computed)
- META RSI14 34.1 — 2.93% of book

## RSI OVERBOUGHT (computed)
- MSFT RSI14 78.8, +24.7% 1m — 3.72% of book
- BX RSI14 71.1, +16.5% 1m — 1.81% of book

**Unchanged repeats (suppressed):** MSFT (PEER LEADER), AMZN (PEER LEADER), BX (PEER LEADER)

**Self-calibration:** SD(rel_sigma) = 0.95 across n=31 (in the 0.8-1.3 healthy band).

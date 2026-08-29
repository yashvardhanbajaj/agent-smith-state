# Signal Scanner — Weekend Dispatch (2026-08-29, quick, market closed)

Prices/weights below reconstructed via yfinance/INDmoney as Friday 2026-08-28 close (day% = Fri vs Thu 08-27). News scanned for items dated after watermark 2026-08-26 (i.e. 08-27/08-28 only — a 2-day window).

## HEADLINE: MRVL earnings — precise verdict
MRVL fell -10.28% Friday (241.45→216.62) on a session that also saw broad semis weakness (SMH -3.47%). Per the SanDisk-trap discipline: separating the signals —
- **Reported Q2 results: BEAT.** "Marvell Technology exceeded Q2 earnings and revenue estimates" (27 Aug 2026, INDmoney/Zacks-sourced). Company also raised its FY28 revenue forecast.
- **Guidance: company framed Q3 outlook as "strong,"** but it read as light versus elevated buy-side expectations built up over MRVL's 165% YTD run and the Google custom-chip narrative — "outlook disappointed investors" (28 Aug 2026).
- **Price reaction: -10.28%,** consistent with a beat-but-sell-the-news / valuation-reset move on a stock priced for perfection, not a fundamental miss. "Analysts remain cautiously optimistic, with some reiterating buy ratings" (28 Aug 2026).
- Exact reported EPS/revenue-vs-consensus figures were not retrievable this run (yfinance's earnings-history endpoint had not yet posted the Q2 actual as of this scan) — flagged in data_quality; do not treat the "beat" as unsourced, it is corroborated by two independent 27-28 Aug news items, but the numeric magnitude is missing.
- TARGET GAP newly crosses threshold: mean target $269.28, live $216.62 → **+19.56% upside**, not in MRVL's prior signal_history. weight 4.08% of book.

## Bucketed signals (non-empty only)

**STRONG UPTREND**
- MSFT — pos=0.80 (513.53 vs 52wk range 349.20–553.72), day +1.68% (Fri green) — mean target $569.45, +9.82% upside. weight 2.38%. NEW this run (was PEER LEADER only in prior history).
- FLTW (Taiwan ETF proxy) — pos=0.88, day -0.61% — no analyst target (ETF). weight 2.45%. unchanged repeat.

**STRONG DOWNTREND**
- META — pos=0.21 (578.02 vs 520.26–790.80), day +1.21% Friday (green, but position stays deep in the lower range) — mean target $754.72, +23.41% upside. weight 2.76%. unchanged repeat; ongoing legal/child-safety litigation headwind persists (see Still Pending).

**TARGET GAP (≥15% either direction)** — mostly a mechanical widening from Friday's broad semis pullback (prices fell, targets unchanged), not fresh company-specific news. Full list (target mean, upside%): STM $74.96/+34.1%, MU $1513.41/+38.4%, CLS $477.22/+37.4%, BABA $186.99/+36.4%, AVGO $525.97/+29.9%, NVDA $305.79/+28.9%, AMAT $640.31/+27.9%, GEV $1236.43/+26.2%, KLAC $234.35/+25.1%[unnormalized], AMD $613.09/+24.1%, META $754.72/+23.4%, BE $275.08/+23.4%, COHR $416.09/+32.9%, CIEN $557.29/+32.1%, WDC $664.92/+30.9%, GLW $191.40/+22.2%, LITE $1148.30/+22.1%[unnormalized], INTC $114.88/+22.1%, ASML $2154.12/+21.3%, TER $446.47/+20.5%, CEG $348.30/+20.5%, TXN $323.68/+20.1%, VRT $338.15/+24.0%, GOOG $422.34/+18.8%, AMZN $327.00/+18.5%, LRCX $371.19/+18.7%, TSM $554.45/+24.7%, MRVL $269.28/+19.6% (**new**, see headline).
- **unchanged repeats (upside widened mechanically, no material news): ASML, TSM, MU, CIEN, AMD, STM, AVGO, GEV, CLS, BABA, CEG, AMZN, TER, VRT, COHR, AMAT, BE, INTC, TXN, META, GOOG, WDC, GLW, KLAC.**
- **QCOM target gap resolved** — upside now 14.97%, dropped just under the 15% threshold (was flagged with OVERSOLD BOUNCE previously); pos=0.31, news mixed (handset weakness vs edge-AI expansion), no longer clearly oversold-bounce either.

**PEER-RELATIVE (1-month, ATR-normalized, σ = rel_strength / max(2.3×ATR20%, 5%))**
PEER LEADER (σ≥+1.0):
- MSFT +16.1pp vs XLK (+2.24σ) — genuinely leading hyperscaler peers, not just riding the tape. weight 2.38%.
- CEG +13.3pp vs XLU (+1.77σ) — power-infra name outrunning a weak utilities tape (XLU -3.85% 1m). weight 2.02%.
- HOOD +20.1pp vs XLF (+1.55σ) — fintech/brokerage weak-fit proxy, treat with caution. weight 1.36%.
- MRVL +34.1pp vs SMH (+1.5σ) — genuine 1-month outperformance despite Friday's earnings-reaction drop.
- VRT +24.6pp vs XLU (+1.18σ) · NBIS +34.2pp vs XLK (+1.16σ) · BE +36.9pp vs XLU (+1.14σ) · BX +8.9pp vs XLF (+1.11σ).

PEER LAGGARD (σ≤-1.0):
- GOOG -12.7pp vs XLK (-1.98σ) — 1m return only +0.6% vs XLK +13.2%; notable underperformance for a hyperscaler name despite Friday's +1.53% green day. weight 3.33%. **new this run.**
- TXN -15.4pp vs SMH (-2.00σ) — **new.**
- BABA -12.1pp vs XLK (-1.61σ) — **new.**
- META -15.7pp vs XLK (-1.44σ) — unchanged repeat.
- AVGO -13.3pp vs SMH (-1.40σ) — **new.**
- CLS -17.0pp vs SMH (-1.03σ) — **new.**
- **Bucket removals this run** (no longer meet ±1.0σ): AMD (was PEER LAGGARD, now -0.14σ), STM (was PEER LAGGARD, now -0.78σ), WDC (was PEER LAGGARD, now -0.62σ), AMZN (was PEER LEADER, now -0.02σ), NOW (was PEER LEADER, now +0.49σ). AMZN/NOW simply tracked the sector rally rather than leading it once normalized.
- KLAC, LITE, SMCI: no ATR20 in cache → σ not computable this run [unnormalized]; FLTW has no peer-ETF mapping (Taiwan single-country ETF, no clean proxy).

**INSIDER ACTIVITY (news-derived, quick mode)**
- INTC — CEO Lip-Bu Tan's recent share purchases continue to be cited as a confidence signal (28 Aug article), alongside SoftBank/Tiger Global/Duquesne institutional buying through August. No new Form-4 detail available in quick mode.
- BE — Pelosi household disclosed a new equity stake (27 Aug 2026, positive sentiment) — congressional disclosure, not a corporate insider filing; noted for context only.

## No signals fired this run
NEW TAILWINDS / NEW HEADWINDS: no ticker cleared ≥2 distinct post-watermark events in either direction over this 2-day window once syndicated coverage of the same story is deduped (e.g. GEV's two 27/28-Aug items are one LS Electric JV story; NOW's two items are one earnings release). EARNINGS PROXIMITY: no holding >5% weight has a print within 7 days (TSM 6.07% already reported mid-Aug). MOMENTUM+VOLUME / OVERSOLD BOUNCE / OVERBOUGHT PULLBACK / BREAKOUT / BREAKDOWN: none crossed vol-scaled or pos thresholds this run.

## Still pending (from open_flags / prior watermark)
- HOOD — still sits outside the drift/policy cluster (opened 2026-08-20, no resolution this run); same unresolved-precedent risk as IONQ flagged previously.
- Cash 29.09% vs [5,15]% band (opened 2026-08-19) — no fresh data this run (market closed, no holdings pull); orchestrator should revisit at next live run.
- MU/SNDK thesis-text corrections (2026-08-05) — full both-directions reconciliation still smith-thesis's open item, not re-derived here.
- META legal/child-safety litigation — ongoing headwind story, one new item post-watermark (28 Aug, negative) but insufficient alone for a fresh NEW HEADWINDS count; still the dominant news theme on the name.

## Self-calibration (vol normalization)
SD(rel_sigma) = 1.065 across 33 normalized names (target ≈1.0) — the σ scaling is reading correctly calibrated this run, no drift to report.

## Data quality
- MRVL: exact reported EPS/revenue-vs-consensus $ figures unavailable this run (yfinance earnings-history not yet updated with Q2 actual); beat/miss verdict rests on two independent news sources instead of raw numbers.
- SKHY: 52-week-low returned as $0 against a $161 live price — implausible, discarded per plausibility guardrail; pos not computed for SKHY this run.
- KLAC, LITE, SMCI: no ATR20 cache entry → day-move and peer-σ triggers fell back to legacy absolute thresholds [unnormalized]; flagged in vol_normalization/journal_new as applicable.
- FLTW: no peer-ETF mapping exists (Taiwan single-country ETF has no clean sector proxy) — peer-relative skipped by design, not a gap.
- This is a weekend/degraded dispatch: no live INDmoney holdings pull; weights/prices reconstructed from the embedded holdings file, not verified against a fresh networth_holdings call.

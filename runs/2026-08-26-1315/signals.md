# Signal Scan — 2026-08-26 (QUICK) — pre-open, prices = Tue 08-25 regular-close (yfinance-rebuilt)

## EARNINGS PROXIMITY (flagged per dispatch, weight-threshold overridden for these 4)
- NVDA — reports TODAY 08-26 after close. wt 2.58%. Live $213.05, pos 0.68 (mid-range), target $302.83 (+29.65%). NOT run up into print — news flags a 7-session pre-earnings decline (24-Aug) despite bullish sell-side; no implied-move data accessible. Journal: TARGET GAP grade A (n=1, low-conf); MOMENTUM+VOLUME bucket overall grade F (0% hit, n=11) — treat any post-print momentum flag skeptically.
- MRVL — reports 08-27. wt 4.08% (<5% but flagged per dispatch). Live $240.38, +4.84% Tue (0.49x its 9.88% ATR — not outsized), pos 0.67. Google-partnership news (20/21-Aug, pre-watermark) driving the pop. Target $257.29, only +6.57% upside — no TARGET GAP.
- AVGO — reports 09-02 (exactly 7d out). wt 3.46%. Live $356.74, pos 0.35, target $527.88 (+32.42%).
- CIEN — reports 09-03 (8d out, flagged anyway per dispatch). wt 2.83%. Live $387.66, +4.22% Tue, pos 0.55, target $565.71 (+31.47%).

## STRONG UPTREND
- ASML — pos 0.80 (NEW crossing, prior history had TARGET GAP only). Live $1744.16, target $2176.09 (+19.85%, TARGET GAP also fires). Day move only 0.23% (0.05x its 5.11% ATR) — this is a pos-driven flag, not a momentum day. wt 4.23%.
- FLTW (Taiwan ETF) — pos 0.84, unchanged repeat (as_of 08-25). Day +2.03% (1.07x its 1.89% ATR — still under the 2.84% scaled threshold). wt 2.45%. No analyst target (ETF).

## STRONG DOWNTREND
- META — pos 0.18, unchanged repeat. Live $570.05, target $754.14 (+24.41%, TARGET GAP also fires). wt 2.76%. Journal TARGET GAP grade F (0% hit, n=1); OVERSOLD BOUNCE still open (08-20 flag, no outcome yet).

## MOMENTUM+VOLUME (2 unnormalized — ATR20 missing, legacy ±4% day threshold used per guardrail)
- SMCI [unnormalized] — NEW position (10sh, wt 0.93%, starter). Day +9.35%, well past the 4% fallback threshold. Cisco AI-hardware partnership + strong FY27 guidance (25-Aug), independent investigation cleared management (20-Aug). Target $42.38, only +9.25% upside — no TARGET GAP despite the pop. ATR20 not yet cached — flag for next deep run.
- LITE [unnormalized] — NEW position (0.5sh, wt 1.07%). Day +6.67%, past the 4% fallback. Strong Q4 print + FY27 guide (12-Aug, pre-watermark), CEO share-withholding for taxes (not a sale) misreadable as insider selling — it isn't. pos 0.79 (just under STRONG UPTREND's 0.80). Target $1125.93 (+21.35%, TARGET GAP also fires). ATR20 not yet cached.
- HOOD — near-miss, NOT flagged this run under scaled rule. Day +8.17% = 1.45x its 5.62% ATR, just under the 8.43% scaled threshold. Journal entry from 08-24 (open, no outcome) stands; today's print alone doesn't re-trigger under the normalized test — noted for calibration transparency. wt 1.36%.

## OVERSOLD BOUNCE
- QCOM — pos 0.28, upside 17.56% (>15% test). wt 2.72%. Automotive strength/Q4 guide (25-Aug) vs handset weakness (20-Aug) — mixed, not a clean reversal story. Journal: bucket already open since 08-06 (neutral +0.38% at 7d) — this is a continuation, no new journal entry.
- CEG — pos 0.27, upside 20.10%. wt 2.02%. Continuing the open REVERSAL-BUY WATCH thread (07-31 flag, worked +3.43% at 7d) — same underlying setup, not double-counted.
- BABA — pos 0.27, upside 37.01%. wt 0.58% (small). CAUTION: this bucket has failed on BABA twice before (07-22, grade F/0%). Today's move is calm (+0.82%, de-escalated from the prior STRONG DOWNTREND/MOMENTUM print) — flagging for completeness, not conviction.

## TARGET GAP — broad-based, mostly unchanged repeats (upside ≥15% either direction, mean target cited)
Unchanged from signal_history: TSM +23.70% ($547.09) · MU +37.88% ($1501.98) · CIEN +31.47% ($565.71) · AMD +21.81% ($612.84) · STM +30.84% ($71.52) · AVGO +32.42% ($527.88) · GEV +25.23% ($1239.46) · QCOM +17.56% ($194.77, also OVERSOLD BOUNCE above) · CLS +35.16% ($473.24) · BABA +37.01% ($189.61) · AMZN +20.17% ($327) · TER +18.53% ($449.80) · VRT +24.37% ($338.15) · AMAT +24.78% ($638.17) · BE +20.95% ($275.08) · INTC +23.85% ($114.88) · META +24.41% (above) · GOOG +18.60% ($421.79) · WDC +31.92% ($662.12) · GLW +23.11% ($191.40) · KLAC +20.90% ($231.78) · NVDA +29.65% (above) · ASML +19.85% (above, also STRONG UPTREND) · CEG +20.10% (above).
NEW this run: COHR +29.85% ($410.76, was empty in signal_history) · LITE +21.35% (new position, above).
RESOLVED (dropped out): LRCX now +14.71% ($368.94) — compressed just under the 15% threshold, was flagged prior run.
DATA CAUTION: SKHY consensus target $245.50 implies ~+53.9% upside but its 52wk-low field returned $0 (bad data, likely thin history on a recent ADR) — not asserting TARGET GAP off this until the pos/range data is verified. NBIS mean target unavailable (only consensus.target_prc $260.20 returned, no formal target_price block) — implied +17.2% upside not asserted with confidence, flagged in data_quality instead.

## NEW TAILWINDS / NEW HEADWINDS — mostly resolved this run (see below)
News flow has gone quiet against the 2026-08-25 watermark — almost every holding's freshest dated item falls ON 08-25 (1 story) rather than crossing the ≥2-distinct-event bar. Prior flags now insufficient to re-fire:
- BABA NEW HEADWINDS — resolved. Still pending: $10.2B dilutive AI-capex raise (23-Aug), mixed earnings/75% profit plunge (20-Aug).
- GEV NEW TAILWINDS — resolved. Still pending: $5B H1 data-center-power revenue, $176B backlog (23-Aug).
- AVGO NEW HEADWINDS — resolved. Still pending: Druckenmiller/Loeb full exits (23-Aug), D.E. Shaw −58.3% stake cut (22-Aug), debt-financing-concern headline (24-Aug).

## INSIDER ACTIVITY — stale, all pre-watermark, carried as unchanged repeats
TSM (VP Lipen Yuan bought 2,350sh, $174k, 22-Aug) · AMD (EVP Grasby sold shares, 22-Aug) · MRVL (CEO sold ahead of earnings, 18-Aug). Quick mode = news-derived only (no fresh Form-4 pull); no new post-watermark filings surfaced.

## PEER-RELATIVE (STALE CACHE — NOT refreshed this quick run; rel_strength_1m/rsi14 last stamped 08-12 per dispatch)
Carrying forward signal_history entries as unchanged repeats only, NOT re-verified: PEER LEADER — AMZN, NOW, MSFT, BX, MRVL, SKHY(caveat: pos data corrupted, see above). PEER LAGGARD — KLAC, WDC, STM, META, AMD. Fresh sigma cannot be computed honestly this run — emitting null rather than fabricating.

## Data quality
- SKHY 52wk-low returned $0 (recent ADR, thin history) — pos/BREAKOUT/STRONG-DOWNTREND math unreliable this run; prior STRONG DOWNTREND in signal_history is stale, not reasserted.
- ATR20 missing for KLAC, LITE, SMCI — LITE/SMCI MOMENTUM+VOLUME flagged via legacy ±4% fallback per guardrail, tagged [unnormalized].
- NBIS analyst target_price block absent (only consensus.target_prc) — upside not asserted as TARGET GAP.
- rel_strength_1m/rsi14 caches stale since 08-12; all PEER LEADER/LAGGARD lines this run are unverified carry-forwards, not fresh sigma.
- GOOG news segment returned empty (no items) — no news read for GOOG this run.
- Budget: 6 get_us_stocks_details calls used (batch 3 split into two 5-symbol calls after a size overflow); well under the 15-call soft cap.

## Unchanged repeats (buckets unchanged from signal_history, no material move — condensed)
TSM, MU, CIEN, AMD, STM, AVGO(TG only), GEV(TG only), CLS, AMZN, TER, VRT, AMAT, BE, INTC, GOOG, WDC, GLW, KLAC, MSFT, NOW, BX — TARGET GAP / PEER lines as listed above; no new triggers.

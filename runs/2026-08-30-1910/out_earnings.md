# smith-earnings — DEEP — 2026-08-30

## 1. VERIFY SWEEP: PENDING entries at/past reported_date

| Ticker | reported | status | eps_act vs cons | quarter | guide |
|---|---|---|---|---|---|
| NVDA | 2026-08-26 | VERIFIED | 2.22 vs 2.09113 (+6.16%) | **beat** | guide_below_consensus (China DC) |
| MRVL | 2026-08-27 | VERIFIED | 0.94 vs 0.93077 (+0.99%) | **beat** | above consensus (~+4% rev) |

Both already carry real actuals, verdicts and drift. **No re-resolution needed.** Confirmed only.
Remaining PENDING: AVGO, CIEN — legitimately pending, reported_date is in the FUTURE. Not stuck.

Which signal was weighted, stated explicitly:
- **NVDA — the GUIDE, not the quarter.** Quarter beat (+6.16% EPS, 4th straight). The -4.58% Fri /
  -5.3% 2d drift is the $0-China-DC guide + $400M H200 charge. Guide is an *exclusion*, not a cut to
  base case: restoration is pure upside. Quarter verdict stays `beat`.
- **MRVL — NEITHER. The move is not an earnings signal.** Quarter beat, guide ABOVE consensus.
  -10.28% Fri is position unwind after a 179% YTD run. Any agent reading "MRVL -10%" as a bad print
  is reading price, not actuals. Both signals were positive.

## 2. PRE-PRINT: AVGO — 2026-09-02 (after close), 1.86% of book

- **EPS consensus 3.238** (yfinance, FQ3'26). Revenue consensus: **NOT SOURCED → null.**
  stockanalysis overview + forecast pages carry annual only; FMP `analyst/financial-estimates` is
  plan-blocked (new denial, log alongside statements/transcript/quote). No estimate = no number.
- **Implied move ±8.12%** — ATM 370 straddle (29.95 mid) / spot 368.79, 2026-09-04 expiry.
  Cross-check: 08-31 expiry IV ~31% vs 09-04 expiry IV ~80%. The earnings kink confirms the event
  is priced into that expiry. OI 11,371 at the 370 call — liquid, good confidence.
- **Surprise history: +1.6 / +4.38 / +1.32 / +1.74 → avg +2.26%.** Four straight beats, but SMALL
  ones. AVGO is a managed-beat name; it does not clear the bar by much.
- **Drift: 2d avg -4.72%, 5d avg -4.03%, 5d median -5.63%.** Split: +12.9/-16.4/+4.1/-19.5 (2d).
  Two violent down-prints (Dec-11, Jun-03) against two up. High variance, not a reliable direction.
- **Ran DOWN into it.** -0.41% over 1mo but **-13.79% off the 08-07 high of 427.76**. Bounced +4.5%
  on 08-27, then -0.74% Friday to 368.79.
- **Read:** expectations have already been de-rated 14%. A +2% typical beat is worth more here than
  it was on 08-07 because the bar came to it. The risk is not the quarter — it is the guide, which
  is where the last two AVGO down-prints came from.

## 3. PRE-PRINT: CIEN — 2026-09-03 (pre-market), 2.88% of book

- **EPS consensus 1.72756** (yfinance, FQ3'26). Revenue consensus: **NOT SOURCED → null**, same
  reason as AVGO. FY26 revenue forecast $6.33B is ANNUAL and is not a quarterly consensus.
- **Implied move ±12.0%** — 09-04 expiry, K380 straddle 12.25% / K375 11.81%, spot 378.44.
  **LOW CONFIDENCE, ±1.5pp.** Bid/ask 19.4/25.3 (26% wide), OI single-to-double digits at most
  strikes. Directionally "very large expected move"; do not treat 12.0 as a precise number.
- **Surprise history: +27.56 / +18.24 / +15.55 / +12.34 → avg +18.42%.** Four straight, all LARGE,
  but the magnitude is DECAYING every quarter (27.6 -> 18.2 -> 15.6 -> 12.3). The buy-side has been
  re-basing to the real number; the beat cushion is shrinking.
- **Drift: 2d avg -3.54%, 5d avg -0.53%, 5d median -4.57%.** 5d avg is CONTAMINATED by the 09-04-25
  print (+36.95%) — use the median. Last three 5d: -8.09, -1.05, -29.94.
- **Ran UP into it. +14.55% over 1mo**, though -14.99% off the 08-17 high of 445.18 and -5.35% on
  Friday alone.
- **Read:** this is the harder of the two. CIEN carries a ~12% implied move on a name whose beat
  magnitude is halving and which is still up 14.6% on the month. Beating by 12% may already be the
  price. Its two most recent prints BOTH beat and BOTH fell double digits within 2 days.

## 4. CORRECTION TO THE DISPATCH FRAMING

"Four straight beats each, with the last two prints closing sharply lower" — accurate for CIEN
(Mar-05 -12.88%, Jun-04 -13.66%, both on beats). **Not accurate for AVGO**: its last two were
2026-03-04 **+4.80%** and 2026-06-03 -12.59%. AVGO's down-prints are Dec-11 and Jun-03 — alternating,
not consecutive. The pattern is real for CIEN and overstated for AVGO.

## 5. DATA QUALITY

- Revenue consensus unavailable for BOTH names. Emitted null. No estimate was invented.
- FMP `analyst` endpoint (financial-estimates) is ACCESS DENIED on this plan — new, add to the
  do-not-retry list with statements / earningsTranscript / quote.
- CIEN option chain is illiquid; implied move is an estimate with a stated band, not a measurement.
- Weight drift: dispatch says CIEN 3.01% / AVGO 1.85%; holdings_trim says 2.88% / 1.86%. Used holdings.
- No trade recommendation is made here. Both prints are binary inside 5 sessions at 1.86% and 2.88%.

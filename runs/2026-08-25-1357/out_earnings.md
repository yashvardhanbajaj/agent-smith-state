# smith-earnings — 2026-08-25 (deep)

Four held names print inside 14 days. All four dates independently re-confirmed
this run against stockanalysis.com (not carried on cache alone).

## Window

| Ticker | Date | Timing | Days | Weight | Implied move | Basis |
|---|---|---|---|---|---|---|
| NVDA | 2026-08-26 | AMC | 1 | 2.79% | 6.06% | ATM 207.5 straddle, 08-28 exp, spot 208.48 |
| MRVL | 2026-08-27 | AMC | 2 | 4.35% | 10.55% | ATM 230 straddle, 08-28 exp, spot 229.29 |
| AVGO | 2026-09-02 | AMC | 8 | 3.82% | 8.98% | ATM 360 straddle, 09-04 exp, spot 358.76 |
| CIEN | 2026-09-03 | BMO | 9 | 2.95% | 13.30% | ATM 372.5 straddle, 09-04 exp, spot 371.95 — LOW CONFIDENCE |

Combined weight at binary risk inside 9 sessions: **13.91%** of book.
Sizing is the strategist's call, not mine.

## Surprise history (EPS actual vs consensus, last 4 reported quarters)

| Ticker | Q-4 | Q-3 | Q-2 | Q-1 | Avg |
|---|---|---|---|---|---|
| NVDA | +4.10 | +3.46 | +5.32 | +5.54 | +4.61 |
| MRVL | -0.51 | +3.01 | +1.05 | +0.64 | +1.05 |
| AVGO | +1.60 | +4.38 | +1.32 | +1.74 | +2.26 |
| CIEN | +27.56 | +18.24 | +15.55 | +12.34 | +18.42 |

## Post-earnings drift — SEPARATE FIELD, NOT A VERDICT

Cumulative return from last pre-print close. Reaction day = next session for AMC
prints, same session for BMO (CIEN).

| Ticker | Reaction d1 (each qtr) | Drift 2d avg | Drift 5d avg | Median 5d |
|---|---|---|---|---|
| NVDA | (carried from 08-24 run) | -5.30 | -4.84 | n/a |
| MRVL | (carried from 08-24 run) | +3.74 | contaminated | +5.77 |
| AVGO | +9.41 / -11.43 / +4.80 / -12.59 | -4.72 | -4.03 | -5.62 |
| CIEN | +23.31 / +9.25 / -12.88 / -13.66 | -3.54 | -0.53 | -4.57 |

## The finding that matters

**CIEN has beaten EPS consensus by 12-28% in each of the last four quarters and
its last two prints still produced ~-13% same-day reactions.** Q3 FY26 (2026-03-05)
was a +15.55% EPS beat that closed -12.88%; Q2 FY26 (2026-06-04) was a +12.34%
beat that closed -13.66% and -29.94% five days out. The move on this name has not
been made by the reported quarter for two consecutive prints — it has been made by
guidance and by where the bar already sat. The stock is -6.02% today into a 09-03
print at a 49.8%-upside consensus target, which is precisely the elevated-bar
setup that produced the SNDK (G58) and COHR (G75) mislabels.

Whatever happens on 09-03, the quarter verdict and the guide verdict get recorded
as two facts. A -13% print day is not evidence of a miss.

AVGO carries the same shape more mildly: +2.26% average EPS beat, four straight
beats, yet negative average drift at both 2d and 5d, and a -12.59% reaction to its
last beat (2026-06-03). Both June prints (AVGO 06-03, CIEN 06-04) were beats that
sold off hard on the same two sessions — read that as a sector expectations reset,
not as two independent operational misses.

## NVDA — tomorrow

Consensus EPS has drifted up since the 08-24 read: **2.09161** now vs 2.08869 then
(yfinance, +0.14%). Implied move 6.06%, essentially unchanged from the 6.17% stored
on 08-21, and the option market is not pricing an outsized event. NVDA has beaten
EPS four straight quarters (avg +4.61%) and still carries a negative average 2d/5d
drift (-5.30 / -4.84). Position is 5sh / 2.79%, re-entered this morning.

No revenue consensus was sourceable for any of the four names this run — the
stockanalysis overview and forecast pages carry annual figures only, and FMP
`statements` is access-denied on this plan tier. All four `revenue_consensus`
fields are therefore `null`, not estimated.

## Data quality

- **G18 partially contradicted for single names.** Open interest IS populated for
  NVDA / MRVL / AVGO / CIEN when the chain is pulled with an explicit `expiration`
  parameter (NVDA 08-28 ATM put OI 7,254; AVGO 09-04 ATM put OI 1,581). The zeroed
  OI in `chains/nvda_2026-08-28.json` and `chains/mrvl_2026-08-28.json` is an
  artifact of the summary-format pull, not a data outage. G18's SPY/QQQ scope is
  untouched by this.
- **Max-pain not computed.** Per dispatch. The ±4-strike ATM window returned by the
  chain tool is too narrow to feed `smith_math.py maxpain` meaningfully, and
  widening it was not worth the budget. Unavailable, not estimated.
- **CIEN implied move is low confidence.** The 09-04 chain is thin (ATM 372.5 OI:
  2 calls / 22 puts) and last-trade prints are stale — the 375 call last-traded at
  78.56 against a 372.5 call at 28.40, which is not a coherent surface. The 13.30%
  figure is a directional read only; the 365-strike straddle gives 13.3% and the
  370-strike gives 14.6%, so treat the range as 13-15%.
- **AVGO consensus EPS 3.238 is single-source (yfinance) and unverified.** It
  implies +32.7% QoQ off the 2.44 actual reported 2026-06-03. Plausible on the AI
  ramp, but I could not cross-check it, so it is not decision-grade.
- **AVGO implied move is an upper bound.** The 09-04 expiry sits two sessions past
  the 09-02 AMC print and carries residual time value.
- No new prints landed since BABA (2026-08-20). `verified_prints` is empty this run
  by design — nothing to characterise, so nothing characterised.

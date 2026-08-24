# smith-earnings — 2026-08-24 (deep)

Window: 5 trading days from 2026-08-24. **NVDA 08-26 (T+2), MRVL 08-27 (T+3).** AVGO 09-02 is T+7 — outside.
All prices/option prints are **as-of the 2026-08-21 close**. Today is pre-open; no live session exists yet.

## 1. Implied expected move

| | NVDA | MRVL |
|---|---|---|
| Spot (08-21 close) | 214.72 | 237.04 |
| ATM strike | 215 | 237.5 |
| Expiry used | 2026-08-28 | 2026-08-28 |
| ATM call / put (last) | 6.55 / 6.70 | 13.30 / 13.50 |
| Straddle | 13.25 | 26.80 |
| **Implied move** | **±6.17%** | **±11.31%** |
| 1-sigma band | 201.47 – 227.97 | 210.24 – 263.84 |

Control: NVDA's same-day 08-24 straddle prices only 1.62% — the event premium sits in the 08-28 tenor, as it should.

**MRVL is priced for ~1.8x NVDA's move.**

## 2. Data quality — G18 is NOT closed (contradicts my dispatch brief)

My brief stated yfinance open interest "is populated again as of 2026-08-16." **The live pull says otherwise.**
Across both symbols and every expiration: `openInterest` = 0, `bid`/`ask` = 0, and `iv` returns 0.001%–6.25%
annualized (impossible for NVDA into a print). Only `last` and `volume` are real.

Consequences, stated plainly rather than worked around:
- **Max-pain and PCR are not computable.** Both are OI-weighted. `smith_math.py maxpain` independently
  detected the condition and returned `null` with the note "no open interest" — it did not emit a max-pain of 0.
  I did not substitute volume-weighted PCR; that is a different statistic.
- **Implied move is derived from last-trade prints, not bid/ask mids.** Volume supports it
  (NVDA 215C 18,658 / 215P 9,570 contracts) so the prints are recent, but this is one notch below quote-grade.
  Treat ±6.17% / ±11.31% as good to roughly a quarter-point, not to the basis point.

## 3. Surprise history (EPS actual vs consensus — reported quarters only)

| Quarter | NVDA surprise | MRVL surprise |
|---|---|---|
| 2Q2025 | +4.10% | −0.51% |
| 3Q2025 | +3.46% | +3.01% |
| 4Q2025 | +5.32% | +1.05% |
| 1Q2026 | +5.54% | +0.64% |
| **Average** | **+4.61%** | **+1.05%** |

NVDA has beaten EPS four straight quarters with a wide, stable cushion. MRVL's beats are thin and include
one outright miss — roughly a quarter of NVDA's average cushion. MRVL has materially less room for error.

## 4. Post-earnings drift — a separate field from the verdict

Both names report after the close; base = report-date close, so t+1 is the reaction day.

**NVDA — beat every quarter, fell every quarter:**

| Print | Surprise | 2-day | 5-day |
|---|---|---|---|
| 2025-08-27 | +4.10% | −4.09% | −5.47% |
| 2025-11-19 | +3.46% | −4.10% | −3.36% |
| 2026-02-25 | +5.32% | −9.39% | −6.40% |
| 2026-05-20 | +5.54% | −3.64% | −4.13% |
| **Average** | +4.61% | **−5.30%** | **−4.84%** |

This is the G58/G75 failure mode in its purest form: **four consecutive EPS beats, four consecutive negative
drifts.** Any agent reading NVDA's post-print tape and inferring "miss" would be wrong four times out of four.

**MRVL — no stable pattern, and the average is contaminated:**

| Print | Surprise | 2-day | 5-day |
|---|---|---|---|
| 2025-08-28 | −0.51% | −16.35% | −18.00% |
| 2025-12-02 | +3.01% | +5.71% | −4.30% |
| 2026-03-05 | +1.05% | +22.42% | +15.84% |
| 2026-05-27 | +0.64% | +3.17% | **+51.81%** |
| Average | +1.05% | +3.74% | +11.34% |
| Median | | +4.44% | +5.77% |

**Do not use MRVL's +11.34% average 5-day drift as a central estimate.** The 2026-05-27 window's +51.81%
captured a non-earnings catalyst (the early-June melt-up), not drift. Range is −18.0% to +51.8%; median 5-day
is +5.77%. The distribution is too wide and too event-contaminated to forecast from. Reported as raw values.

Implied vs realized: NVDA's 6.17% is **1.16x** its average absolute 2-day move (5.30%) — a modest premium.
MRVL's 11.31% is **0.95x** its average absolute 2-day move (11.91%) — priced at or slightly below what this
name actually does on prints.

## 5. MRVL's recent drop — no pre-announcement, no guidance cut, no downgrade

The dispatch asked whether a pre-announcement or analyst action explains the move. **None of the three.**
Verified sequence from daily bars:

| Date | Close | Move | Driver |
|---|---|---|---|
| 08-18 | 216.00 | — | |
| 08-19 | 237.27 | **+9.85%** | Google custom-silicon/TPU deal announced |
| 08-20 | 251.01 | **+5.79%** | continuation |
| 08-21 | 237.04 | **−5.57%** | give-back / profit-taking into August monthly opex |

The +9.85% on 08-19 matches the reported +9.9% close of $237.27 exactly — independent cross-validation.
The deal: warrant for ~59M shares at $206.58 (~$12.2B), vesting per $500M of cumulative custom-product
revenue across 240 tranches through FY2033. The widely-cited **"$120B" is the warrant's maximum milestone
ceiling, not a firm order** — worth holding the strategist to that distinction.

On the down day itself, **Oppenheimer raised its price target to $300 from $250**. The decline is a reversal
of a two-day, deal-driven +16% rally into monthly expiration — not new negative information about the quarter.

**Unverified:** the dispatch's "further −3.43% pre-market today." I could not confirm it — yfinance returns the
Friday close, and the session is pre-open. Not carried forward as fact.

## 6. Pre-print positioning risk

| | Weight | Implied | 1-sigma book impact |
|---|---|---|---|
| NVDA | 8.39% | 6.17% | 0.518% |
| MRVL | 4.77% | 11.31% | 0.539% |
| Combined, same direction | 13.16% | — | ~1.06% |

**MRVL carries slightly more 1-sigma book risk than NVDA despite being 1.76x smaller.** Both are AI-capex;
the two prints are correlated, not independent, and land one day apart. Sizing is the strategist's call.

Note: dispatch cited NVDA 8.25% / MRVL 4.86%; this run's `holdings_trim` says **8.39% / 4.77%**. Used the file.

## 7. Verdicts

No verdict is issued for NVDA or MRVL — **neither has reported.** `quarter_verdict` and `guide_verdict` are
`null` until actuals exist. Pre-print consensus is locked into `earnings_facts` now so that after the print the
verdict is settled by arithmetic against a number recorded *before* the tape moved.

Consensus EPS locked: **NVDA 2.08869, MRVL 0.92986** (yfinance, live this run). Quarterly *revenue* consensus
was not obtainable — stockanalysis.com's overview and forecast pages carry only annual granularity — so
`revenue_consensus` is `null` for both rather than estimated.

**BABA correction (stored fact was missing the verdict I own):** revenue RMB268.95B vs RMB268.34B = +0.23%
**beat**; EPS RMB8.52 vs RMB10.72 = −20.52% **miss**. A revenue beat and an EPS miss in the same print —
recorded as two separate verdicts so no agent collapses it into one word.

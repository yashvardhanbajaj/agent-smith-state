# Agent Smith — Portfolio Strategist — 2026-08-17 (deep, refresher run)

**Data condition.** US cash market has been closed since Friday 2026-08-14's close; the INDmoney snapshot is
identical to 08-16 to the cent. Gate flipped AMBIGUOUS → STABILIZING purely because ES/NQ futures ticked
positive (+0.074% / +0.221%) overnight — two agents searched independently for a cause and found none. An
unexplained 0.2% futures tick is not a signal and drives none of the sizing below. Zero news dated after the
08-16 watermark across all 36 holdings (verified by batched fetch). Drift, triggers, and rotation tables are
therefore numerically identical to 08-16's, and P-094 (ORCL hard stop @ $139.14) has been reinstated after being
retired in error — a stop level is a standing risk instruction, not hold-fire advice.

**The 12 open proposals (P-082, P-087 through P-091, P-093, P-094, P-097 through P-100) are unchanged and not
restated here per this run's brief.** Quick verdict on whether each still holds: MSFT (P-082) and BX (P-097)
remain overbought — RSI14 78.8 and 71.1 respectively, both still up on the month, retirement conditions not
yet met. MU/SKHY/DRAM/NBIS/SNDK/NVDA (P-087–P-091, P-099) remain over their own ATR risk caps at cap-multiples
1.2x–2.1x, no thesis change. QCOM (P-098) and CEG (P-093) remain unfunded — deployable cash is still $0.00
above the cash-band ceiling, so both stay blocked on their sell legs. MRVL stop-raise (P-100) still applies —
gain-at-risk $70.83 vs. a stop still below breakeven. Nothing here has been cured or invalidated by anything
new today.

## New this run — two items, neither a new trade

**1. Lot-sequencing guidance for the two open trims where it's material (smith-tax, first-ever run).** Lot file
is now fully reconciled (71 open lots, 0 undated/unpriced, 35/35 reconciled) and trusted. Of the 8 open trims,
FIFO-vs-HIFO lot selection only matters for two:

- **P-089 (MU trim, $500)** — HIFO sells the 08-13 half-share bought at $970.36 against a $971.86 mark first,
  leaving the $788.81/$849.49 lots intact. Realised gain **$2.50 instead of $62.98 — $60.48 less taxable gain**
  on this $500 slice. This is deferral, not erasure: the gain migrates into the remaining position, and with the
  earliest LTCG boundary now confirmed at 2028-07-15 (see below), there is no rate arbitrage here — pure
  cross-FY timing.
- **P-090 (NBIS trim, $700)** — HIFO leads with the expensive 08-12 lot ($234.79) ahead of 08-07 ($188.27).
  Realised gain **$178.97 instead of $225.49 — $46.52 less taxable gain**, the cleanest genuine saving in the
  set.
  The other six open trims (NVDA, BX, SKHY, DRAM, MSFT, SNDK) are mathematically identical or differ by ≤$10
  under either method — not worth complicating the execution to chase $11 total. This is execution guidance for
  proposals already under review, not a new sized action.

**2. LTCG boundary confirmed — no live deferrals possible.** Earliest open lot in the book is 2026-07-15
(CLS, fractional). At the policy's 24-month boundary the first LTCG crossing is **2028-07-15**. Every open lot
is short-term; no trim on the current list, or any future one for the next ~23 months, can be deferred into
long-term treatment. This closes the standing "check LTCG before trimming" question with a hard date rather than
a guess.

**Loss-harvesting scan (smith-tax): reviewed, no action recommended.** 13 names sit below basis for a combined
**$283.21** (0.65% of the book, largest single name $47). Five of the thirteen — AMZN, BE, AVGO, IREN, AMAT —
carry a `strengthening` thesis, so harvesting them would sell conviction for a sub-$50 offset each; flagged as
tension, not actioned. The pool is too small and too thesis-conflicted to warrant a proposal, and there is no
Jan–Mar harvesting-window pressure (FY ends 2027-03-31, 226 days out).

**No other new proposals.** With drift, triggers, and rotation numerically unchanged from 08-16 and zero fresh
news or price action, there is nothing new to size today beyond the two execution refinements above. This is the
correct outcome for a closed-market, no-session day — not a gap in coverage.

## Risk-off check

`risk_off_status` = **normal** (drawdown −2.492% vs. an 8% warn / 12% risk-off threshold) — no defensive
posture triggered, no new deployments blocked on that basis. Separately, the cash breach persists: $12.25
(0.028%) against a [5,15]% policy band, unchanged since 08-16, with $0.00 deployable above the band ceiling.
That is a funding constraint on QCOM/CEG, not a risk-off signal — the two are different gates and should not be
conflated.

## Stress table (approximate, deep mode)

**Fallback note: smith-macro did not run this cycle (deep run, but no macro dispatch this pass), so there is no
live 10-yr/Fed regime read to anchor the rate-sensitive rows against.** The figures below use static cluster/beta
assumptions only, labelled accordingly — treat as an order-of-magnitude sketch, not a calibrated model. Portfolio
beta 1.298 (compute_book.json), book $43,754.81.

| Scenario | Est. impact | Most exposed names |
|---|---|---|
| AI-capex pause (hyperscaler guidance cut) | −18% to −25% book (−$7,900 to −$10,900) | NVDA, MU, SKHY, DRAM, NBIS, MSFT — the ~78% of the book sitting in AI-linked clusters (Semis/Fabs 33.3%, Memory 15.5%, Networking 12.5%, Power 10.1%, Hyperscaler+OEM 17.5%) |
| Rates +100bp (static assumption, no live 10-yr read) | −8% to −12% book (−$3,500 to −$5,250) | High-multiple/growth names and debt-financed infra: MSFT, NOW, SNDK, GEV, VRT, CEG |
| Tariff/export-control escalation | −5% to −7% book (−$2,200 to −$3,000), concentrated −15% to −20% in AI Semis/Fabs (33.3% of book) | TSM (Taiwan), ASML (Netherlands/China), AMAT, LRCX (China revenue exposure), BABA, MU (China memory) |
| USD/INR ±3% | ≈0% on the USD-reported book — FX doesn't touch USD P&L | In INR-terms net worth: a weaker rupee (+3% USD/INR) raises the INR-equivalent value of the whole book ~3%; a stronger rupee (−3%) cuts it ~3%. No single name driven. |

## Hit-rate readout (journal, precomputed — buckets with ≥3 scored entries only)

- **MOMENTUM+VOLUME**: n=3, 100.0% hit rate.
- **TARGET GAP**: n=16, 68.8% hit rate.
- OVERSOLD BOUNCE has n=1 — skipped (below the 3-entry floor).
- No bucket is below the 40%-over-≥5-entries de-emphasis threshold; no de-emphasis recommended.

## Scorecard interpretation (stored in proposals.json — not recomputed)

`smith_math.py score` has written: **overall n=7, 14.3% accuracy, avg benefit −3.77%** (1 worked, 4 missed, 2
neutral). By direction: **TRIM/SELL n=1, 0% accuracy** (1 neutral, avg benefit +0.31% — too thin to read
anything into, a single data point); **BUY n=4, 25% accuracy** (1 worked, 2 missed, 1 neutral, avg benefit
−4.49%); **HOLD n=2, 0% accuracy** (both missed, avg benefit −4.38%). 43 proposals remain under 30 days and are
not yet in the scoring window; 9 were excluded as user-dismissed (correctly — a user override isn't a strategist
error); 0 quarantined for anchor corruption this pass.

What this implies: at n=7 scored, this is not yet a statistically reliable read on this desk's calling ability —
treat every number above as provisional. That said, the two readable directions both skew weak: BUY calls have
missed twice as often as they've worked, and both scored HOLD calls underperformed the noise band on the
downside. Read together with 43 proposals still pending, the honest takeaway is "wait for a larger sample before
either doubling down on or discounting this desk's signal quality" — not "the desk is failing" and not "the desk
is working." Every proposal above and in the 12 open should be treated as a suggestion for the user's own
judgment, which is the framing this scorecard argues for, not against.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Specify HIFO lot selection on execution (existing P-089 trim, size/ticker unchanged)","ticker":"MU","size_usd":500,"price_at_proposal":971.8636,"rationale":"smith-tax (first-ever run, lot file 71/71 reconciled, 35/35 matched): HIFO sells the 08-13 half-share at $970.36 first, cutting realised gain from $62.98 to $2.50 -- $60.48 less taxable gain on this slice. Deferral not erasure -- no LTCG boundary is reachable (earliest lot 2026-07-15, first crossing 2028-07-15), so this is pure cross-FY timing, not a rate arbitrage. Does not change the trim's size, ticker, or trigger -- guidance only.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":1,"unverified":0}},
   {"action":"Specify HIFO lot selection on execution (existing P-090 trim, size/ticker unchanged)","ticker":"NBIS","size_usd":700,"price_at_proposal":277.7382,"rationale":"smith-tax: HIFO leads with the expensive 08-12 lot ($234.79) ahead of 08-07 ($188.27), cutting realised gain from $225.49 to $178.97 -- $46.52 less taxable gain, the cleanest genuine saving of the 8 open trims. Does not change the trim's size, ticker, or trigger -- guidance only.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":1,"unverified":0}}
 ],
 "scorecard_read":"n=7 scored (43 still under 30d, 9 user-dismissed excluded, 0 quarantined): overall 14.3% accuracy / -3.77% avg benefit. TRIM n=1 (too thin to read). BUY n=4, 25% accuracy, -4.49% avg benefit -- missed twice as often as worked. HOLD n=2, 0% accuracy, -4.38% avg benefit -- both missed on the downside. Sample too small at n=7 to draw a confident conclusion either way; both readable directions skew weak, which argues for continued caution and user review on every sized proposal rather than either trusting or discounting the desk's calls yet.",
 "deemphasize_buckets":[],
 "data_quality":["Book, drift, triggers and rotation are numerically identical to 08-16 -- closed market, zero news after the watermark. smith-macro did not run this cycle, so the stress table's rate-sensitive rows use static assumptions only, not a live 10-yr/Fed read -- flagged explicitly in that section. Beta used (1.298) is compute_book.json's live figure; the orchestrator's slice header cited 1.277, a minor cache/rounding discrepancy not material to any proposal above."]}
```

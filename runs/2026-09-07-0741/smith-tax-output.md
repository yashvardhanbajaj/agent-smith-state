# smith-tax — 2026-09-07 (DEEP)

**Price source for every $ figure:** INDmoney snapshot `runs/2026-09-07-0741/holdings.json`, ts 2026-09-07T07:41Z.
US session `closed_holiday` (Labor Day) → all prices are the **2026-09-04 close**, one session stale. Lot
basis is `price_source: email_confirmed` throughout.

## 1. Lot file state — TRUSTED
Re-ran `smith_math.py lots --base-dir . --holdings runs/2026-09-07-0741/holdings.json`: **32/32 tickers
reconciled, 0 mismatches, 0 orphans, 0 phantom shorts.** All **72 open lots** carry a known acquisition
date and an email-confirmed basis (0 unknown, 0 reconstructed).
`lots.json` `_rebuilt: 2026-09-07`. ASML residual −1.1e-06 sh is floating-point dust, not a real share.
The file is safe to sequence against. Nothing is imputed anywhere in this report.

## 2. LTCG window — one line, because there is no decision in it
Earliest open lot is **2026-07-21**; the Indian 24-month boundary first bites **2028-07-21**. Every open lot is short-term — **no trim this run can be deferred into long-term treatment.** That is the whole story.

## 3. Trim sequencing — all five deltas are $0.00
From `compute_taxcalc.json` (deterministic; not re-derived). Each name has a single open lot in range, so
**FIFO and HIFO select identical lots on all five.** No lot-selection decision exists this run.

| Prop | Name | Size | Lot sold | Realised (FIFO=HIFO) | Δ tax |
|---|---|---|---|---|---|
| P-214 | FSLR Trim | $182.69 (0.8936 sh) | 2026-08-31 @ $202.15 | **+$2.06** | $0.00 |
| P-228 | FSLR Sell | $300.00 (1.4674 sh) | 2026-08-31 @ $202.15 | **+$3.37** | $0.00 |
| P-224 | MSFT Sell | $600.00 (1.2007 sh) | 2026-08-10 @ $509.86 | **−$10.16** | $0.00 |
| P-234 | NVDA Trim | $287.95 (1.25 sh) | 2026-08-24 @ $210.23 | **+$25.16** | $0.00 |
| P-237 | AMD Sell | $429.81 (0.9000 sh) | 2026-08-12 @ $491.12 | **−$12.19** | $0.00 |

Net realised across all five if executed in full: **+$8.24** — nil. Tax is not an argument for or against
any of these five; decide them on thesis and risk alone.

### Three facts about the proposals (not recommendations)
1. **P-224 MSFT is unfillable as sized.** $600 implies 1.2007 sh; the book holds **1.0000 sh** (one lot,
   2026-08-10 @ $509.86). Shortfall **0.2007 sh**. Max realisable is a full exit: **$499.70 proceeds,
   −$10.16 realised.** Resize to ~$500, or confirm a top-up the ledger has not yet confirmed.
2. **FSLR carries two overlapping open sells** (P-214 $182.69 + P-228 $300) against 3.0 shares. Combined
   2.361 sh = **79% of the position**, both off the same 2026-08-31 lot. Feasible, but approving both
   near-exits FSLR — which may not be what either proposal intended.
3. **AMD P-237 sells 3 days after a buy** (1 sh added 2026-09-04 @ $468.48). FIFO/HIFO both consume the
   older 2026-08-12 lot so the fresh lot survives, but the round trip is real churn.

## 4. Harvest candidates — sized by the engine, tension judged here
Twelve names sit below basis; total harvestable loss **−$337.45**, largest single candidate **−$65.24**.
These are rounding errors, not a harvest programme — and most conflict with something:

| Ticker | Unrealised loss | % | Thesis | Conflict |
|---|---|---|---|---|
| AMAT | −$65.24 | −4.6% | strengthening | **Open BUY P-231 ($400).** Harvesting = selling what the strategist is adding. Hard conflict. |
| STM | −$53.90 | −2.9% | watch | **Cleanest candidate.** No open proposal, thesis not strengthening. Still only $54. |
| MRVL | −$52.15 | −2.5% | strengthening | Selling conviction for $52. No. |
| GEV | −$45.21 | −1.2% | strengthening | Selling conviction. No. |
| ASML | −$30.37 | −1.4% | watch | No open proposal; second-cleanest, but $30. |
| GOOG | −$27.68 | −2.0% | strengthening | **Open BUY P-235.** Hard conflict. |
| AVGO | −$23.26 | −3.2% | watch | No conflict; immaterial size. |
| AMD | −$18.01 | −1.2% | watch | **Open SELL P-237 already realises −$12.19** — the harvest is happening inside the trim. |
| MSFT | −$10.16 | −2.0% | watch | **Open SELL P-224 realises the entire −$10.16** as a full exit. Nothing left to harvest. |
| LRCX | −$10.00 | −1.1% | strengthening | **Open BUY P-240.** Hard conflict. |
| APH | −$1.00 | −0.1% | strengthening | **Open BUY P-239.** Conflict, and $1. |
| CIEN | −$0.47 | −14.6% | strengthening | **Open BUY P-232.** 0.0085 sh of dust. Ignore. |

**Judgement: no harvest is worth initiating this run.** Five of the twelve carry an open BUY on the same
name (AMAT, GOOG, LRCX, APH, CIEN) — harvesting there sells what the strategist is proposing to add; four
more are `strengthening`. The conflict-free candidates (STM −$54, ASML −$30, AVGO −$23) are too small to
trade, and the open MSFT/AMD sells already book $22.35 of loss on their own.

## 5. Wash-sale / repurchase
India has **no US-style 30-day wash-sale rule** on equities — rebuying straight after a harvest is legal,
but it resets basis lower and surrenders downside cushion: an economic trade, not a free option. Directly
relevant to AMAT/GOOG/LRCX/APH/CIEN, where a harvest would be followed within days by the open BUY.

## 6. FY clock
Indian FY runs to **2027-03-31**. Today 2026-09-07 is **not** in the Jan-Mar harvesting window (opens in
~4 months). No urgency to manufacture.

## 7. Data quality
- **P-224 MSFT sized above the position** (1.2007 sh implied vs 1.0000 held) — resize or reconcile.
- **FY-to-date realised gain unavailable.** `state.realised_pnl_closed_positions` (+$608.49, 36 closed
  positions, as of 2026-08-13) is **all-time, not FY-scoped**, and its own note flags GOOG as distorted by
  the unrecorded GOOG→GOOGL conversion (G71). Not imputed, so no offset arithmetic is presented above.
- Prices are the 2026-09-04 close (US holiday); every figure here moves on the 2026-09-08 open. ASML lots_residual −1.1e-06 sh: immaterial.

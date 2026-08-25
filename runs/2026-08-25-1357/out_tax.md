# smith-tax — 2026-08-25 (deep)

## 1. Lot file state

Engine re-run: `smith_math.py lots --base-dir . --holdings runs/2026-08-25-1357/holdings.json`
**35/35 tickers reconciled, 0 mismatches, 0 orphans, 0 phantom shorts. 66 open lots, all
66 carrying a known acquisition date and a real basis (0 null-date, 0 null-price,
all `email_confirmed`).** File is trustworthy for every name below.

**Caveat found, and it matters for anyone else reading `lots.json` this run:** the
ON-DISK `lots.json` is currently STALE — it holds 33 tickers, missing ASML/COHR/KLAC/
NBIS/NVDA/SKHY and carrying an orphaned SNDK. That is smith-ledger mid-flight on its 11
new fills. The engine's in-memory rebuild from `trades.json` is the clean 35/35 set, and
that is what this analysis used. **I verified BX/MSFT/AMD/AVGO are byte-identical between
the stale file and the fresh rebuild**, so the four trim names were unaffected. I did not
write `lots.json`; the rebuild was emitted to a scratchpad copy.

## 2. LTCG window — no live decisions

Earliest open lot in the entire book: **2026-07-21** (not 2026-07-15 as dispatched — that
lot has since been sold). India's 24-month foreign-equity boundary puts the first LTCG
crossing at **2028-07-21**. Every one of the 66 open lots is short-term and will remain so
for ~23 months. **No trim in this run can be deferred into long-term treatment, and there
is nothing to sequence for holding-period reasons.** Reported and set aside.

## 3. Trim sequencing — FIFO vs HIFO

Prices: `compute_book.json`, this run, **2026-08-25 pre-open** (session flagged AMBIGUOUS,
SMH −2.43%). These are pre-open marks — the realised figures move with the open.

| Prop | Ticker | Size | Px | Shares | FIFO lot | HIFO lot | FIFO gain | HIFO gain | Δ |
|------|--------|------|-----|--------|----------|----------|-----------|-----------|---|
| P-142 | BX | $285.00 | 142.82 | 1.9955 | 08-21 @143.49 | same | −$1.34 | −$1.34 | $0 |
| P-155 | MSFT | $434.90 | 486.58 | 0.8938 | 08-06 @495.97 | 08-10 @509.86 | −$8.39 | −$20.81 | **−$12.42** |
| P-157 | AMD | $283.94 | 466.34 | 0.6089 | 08-12 @491.12 | same | −$15.09 | −$15.09 | $0 |
| P-159 | AVGO | $294.75 | 361.49 | 0.8154 | 08-12 @421.73 | same | −$49.12 | −$49.12 | $0 |

**Every one of these four realises a LOSS, not a gain.** Three of the four proposals are
argued on "real profit to take, not just a smaller loss" (P-142, P-155, P-159). That
phrase is about 1-month price momentum versus SMH — it is not a statement about position
basis, and at lot level it is the opposite of what the book shows. All four positions were
established in August at prices above today's. Stated as a fact about the proposals, not
as an argument against them: **the strategist may well be right to trim stretched momentum;
it just should not be described to the user as booking profit.**

**Lot-selection detail:**
- **BX, AMD** — single open lot each. FIFO and HIFO are the same trade. No decision.
- **AVGO** — three lots, but the oldest (08-12 @421.73) is *also* the highest-basis one,
  so FIFO and HIFO coincide by luck. Nothing to choose. Note the 0.8154sh comes entirely
  out of that 2sh lot; the two 08-19 lots @~364 are untouched either way.
- **MSFT — the only live lot decision in the run.** HIFO takes the 08-10 @509.86 lot and
  realises **$12.42 more loss** than FIFO's 08-06 @495.97 lot. **This is not material.**
  $12.42 on a $37.8k book is 0.03%, and it is a timing difference in loss recognition, not
  a permanent tax saving — the basis not consumed now is still there later. **Do not
  complicate the execution for it.** Recorded because you asked for the gap, not because
  it should change anything.

**Bottom line on sequencing: there is no meaningful FIFO/HIFO money in these four trims.**
The largest divergence across the whole set is $12.42, and three of four have zero.

## 4. Loss-harvesting scan

Names below weighted basis, material only (>$20 unrealised loss), all short-term:

| Ticker | Qty | Basis | Px | Unrealised | % | Thesis |
|--------|-----|-------|-----|-----------|---|--------|
| STM | 30.00 | 54.42 | 49.84 | −$137.40 | −8.42% | watch |
| AVGO | 4.00 | 393.17 | 361.49 | −$126.71 | −8.06% | **strengthening** |
| CIEN | 3.01 | 409.56 | 371.00 | −$116.01 | −9.42% | watch |
| VRT | 7.00 | 272.58 | 260.08 | −$87.50 | −4.59% | watch |
| INTC | 15.00 | 95.31 | 89.59 | −$85.76 | −6.00% | watch |
| GEV | 2.01 | 1001.28 | 958.53 | −$85.70 | −4.27% | **strengthening** |
| TXN | 3.00 | 282.62 | 261.30 | −$63.96 | −7.54% | watch |
| AMD | 2.00 | 491.12 | 466.34 | −$49.56 | −5.05% | watch |
| AMZN | 6.00 | 269.87 | 262.76 | −$42.66 | −2.63% | **strengthening** |
| MSFT | 3.00 | 500.60 | 486.58 | −$42.06 | −2.80% | watch |
| WDC | 2.00 | 461.84 | 444.60 | −$34.48 | −3.73% | **strengthening** |
| BABA | 2.00 | 130.71 | 116.79 | −$27.84 | −10.65% | watch |

Book-wide: **−$912.51 unrealised loss, +$438.50 unrealised gain, net −$474.01.**

**Thesis tension — flagged, not recommended:** AVGO, GEV, AMZN and WDC are all
`strengthening`. Harvesting any of them means selling conviction to book a tax loss.
AVGO is the sharp case: it is simultaneously the second-largest harvest candidate
(−$126.71) AND a strengthening thesis AND already carries an open trim (P-159) on a
*catalyst-threat* rationale. Those are three different reasons pointing at one name, and
only one of them is a tax reason. **The tax reason is the weakest of the three and should
not be what carries the decision.**

The cleanest harvest candidates on thesis grounds are **STM (−$137.40)** and **CIEN
(−$116.01)** — largest losses, `watch` thesis, no conviction being sold. Neither has an
open proposal. **I am not recommending them; sizing is the strategist's call.**

## 5. FY clock and repurchase risk

Indian FY ends **2027-03-31**. Today is 2026-08-25 — **outside** the Jan–Mar harvesting
window by ~4 months. No urgency; harvests deferred now lose nothing, and seven more months
of price action will change which names are the candidates.

**India has no US-style wash-sale rule for equities** — there is no 30-day prohibition and
I am not inventing one. But repurchasing a harvested name within days still changes the
economics: you re-enter at a fresh, lower basis, which converts today's realised loss into
a larger *future* realised gain. The harvest is a deferral, not a saving, unless the
position genuinely stays exited. **BX is the live illustration**: re-entered 2026-08-21 on
a 10sh probe, and P-142 now proposes selling ~2sh of it four days later. That round trip
realises $1.34 and resets nothing useful.

## 6. Data quality

- On-disk `lots.json` stale mid-run (6 tickers missing, SNDK orphan) — smith-ledger in
  flight. Engine rebuild used instead. Not a defect in the record, a race in the read.
- **Realised gains booked so far this FY were not supplied** in `slice_tax.json`. Without
  them I cannot size how much of a harvest is actually absorbed by booked gains, so every
  harvest figure above is a gross unrealised loss, not a net tax benefit. Flagged, not
  estimated.
- G83 stands: BX lot dated 2026-08-21 in trades/lots, but state and dispatch say re-entry
  was 2026-08-24. Tax-irrelevant today (both short-term, both far from any boundary), but
  the record still disagrees with itself.
- G80 residue: ~$12 of cost-basis error across live positions (0.027% of book), including
  AMD ×6 and WDC ×2 rows. Below the noise floor of everything above.
- Dispatch named `out_tax.md`; `slice_tax.json` names `smith-tax-output.md`. Wrote to
  `out_tax.md` per dispatch.

# smith-tax — DEEP run 2026-08-30

## 0. Lot file state — TRUSTED
`smith_math.py lots --base-dir . --holdings runs/2026-08-30-1910/holdings.json`
reconciliation: **35/35 tickers, 0 mismatches, 0 orphans, 0 phantom shorts.**
**74 open lots, 74 with a known acquisition date and basis (0 unknown, 0 imputed).**
(Dispatch cited 71 lots as of 2026-08-16; the current file carries 74. Not a defect — buys since.)
Known residue, informational only: G80 accepted ~$29 of Amount/Price basis error across 24 pre-2026-08-15
rows, ~$12 of it on live positions (0.027% of book). Does not touch any of the five names below.

## 1. THE HONEST LIMIT — no LTCG decisions exist this run
Earliest open lot in the entire book: **2026-07-21** (GEV, 0.000782sh).
India's 24-month boundary for foreign equity puts the first LTCG crossing at **2028-07-21**.
`compute_book.json.ltcg_flags` is empty, consistent with that.
**Every one of the 74 open lots is short-term. No trim can be deferred into long-term treatment,
this FY or next.** Nothing downstream should read an LTCG argument into any of these five trims.
(Dispatch stated 2026-07-15 as the earliest lot; that lot has since been sold. 2026-07-21 is current.)

## 2. Trim sequencing — FIFO vs HIFO
Price source: **Friday 2026-08-28 official closes**, supplied by the orchestrator (post-close, 2 sessions old
as of Sunday 2026-08-30). Sizes are the strategist's own, unchanged.

| Prop | Name | Size $ | Sh | FIFO lot | FIFO gain | HIFO lot | HIFO gain | Delta | Material |
|---|---|---|---|---|---|---|---|---|---|
| P-174 | ASML | 520.97 | 0.30715 | 08-24 @1757.32 | **-18.79** | 08-25 @1767.17 | **-21.81** | 3.02 | no |
| P-176 | AMD  | 279.60 | 0.60054 | 08-12 @491.12  | **-15.34** | same (single lot) | -15.34 | 0.00 | n/a |
| P-178 | AMZN | 320.00 | 1.20107 | 07-31 @271.77  | **-6.41**  | 08-06 @271.96 | **-6.64** | 0.23 | no |
| P-179 | MU   | 280.18 | 0.30035 | 08-19 @933.39  | **-0.16**  | same lot | -0.16 | 0.00 | n/a |
| P-180 | IREN | 243.40 | 6.86601 | 08-27 @40.89   | **-37.35** | same lot | -37.35 | 0.00 | n/a |
| | **Total** | 1,644.15 | | | **-78.05** | | **-81.30** | **3.25** | **no** |

**Verdict: run all five FIFO. The entire HIFO advantage across the whole program is $3.25.**
That is not worth a bespoke lot instruction to the broker. On MU, IREN and AMD, FIFO *is* the
tax-optimal sequence — the oldest lot is also the highest-basis one. Only ASML and AMZN diverge,
by $3.02 and $0.23. Every trim is satisfied out of a single lot; none straddles a lot boundary.

## 3. FACT THE STRATEGIST SHOULD SEE: four of five trims realise LOSSES, not profits
P-174's rationale says "book real profit" and P-178's priority reason says "real profit to take."
Those come from 1-month **relative-strength** ranking, not from lot basis. Against Friday's closes:

- ASML $1696.16 vs weighted basis $1762.24 → **-3.75%**. Selling books a **loss**.
- AMZN $266.43 vs $269.87 → **-1.27%**. Selling books a **loss**.
- AMD $465.58 vs $491.12 → -5.20%. Loss. IREN $35.45 vs $38.89 → -8.86%. Loss.
- **MU is the only one above basis** ($932.86 vs $924.76, +0.88%) — and even there FIFO lands on the
  higher-basis 08-19 lot, so the trim realises -$0.16 rather than a gain. Selling the 08-24 lot
  instead would book +$3.73. FIFO is already the better answer.

This does not argue against any trim — the trims are funding, and open risk is 13.16% vs a 10% cap.
It only means the program books a **$78 realised loss, not a gain**. Tax cost of executing all five: **zero**.

## 4. Loss-harvesting — genuinely live, and it has something to offset
FY-to-date realised P&L, FIFO replay of trades.json over 2026-04-01 → 2026-08-28 (my computation,
not the engine's — smith_math.py has no realised-gain stage): **+$2,010.79 net**
($4,479.94 gains less $2,469.14 losses, across 165 sell rows / 51 tickers).
Excluded, not imputed: 0.998336sh of AMD consumed against the null-basis G71 adjustment lot.
Treat the figure as ±, and as a magnitude rather than a filed number.

**So there is a real booked gain for harvested losses to work against.** Eight names carry a
material unrealised loss (prices: compute_book.json INDmoney snapshot, one session lagged, except
the five orchestrator-supplied Friday closes):

| Ticker | Wtd basis | Price | Unreal. loss | Thesis | Tension |
|---|---|---|---|---|---|
| GEV  | 973.86 | 911.93 | **-186.09** | strengthening | harvesting sells conviction |
| STM  | 54.42  | 49.38  | **-151.20** | watch | clean — no thesis conflict |
| MRVL | 229.34 | 216.62 | **-114.52** | strengthening | harvesting sells conviction |
| VRT  | 272.58 | 257.08 | **-108.50** | watch | clean |
| CIEN | 409.56 | 378.44 | **-93.63**  | watch | clean |
| INTC | 95.31  | 89.47  | **-87.56**  | watch | clean |
| IREN | 38.89  | 35.45  | **-68.90**  | watch (contested 3-for/3-against) | already being trimmed (P-180) |
| ASML | 1762.24| 1696.16| **-66.08**  | watch | already being trimmed (P-174) |

Whole-book unrealised loss across all 23 underwater names: **-$1,172.82**. Even a full liquidation
of everything below basis offsets only ~58% of the $2,011 already booked. There is no scenario this
FY where harvesting over-shoots the gain — the constraint is conviction, not capacity.

**The two to look at hardest are STM (-$151) and VRT (-$109): largest losses with no thesis conflict.**
GEV is the single biggest loss in the book and the one I would *not* harvest — thesis is
strengthening and it is a 6.9% position; realising $186 means selling something the book wants to own.
MRVL is the same shape, smaller. I am naming the tradeoff, not recommending the trade — sizing is the
strategist's call.

## 5. Wash-sale / repurchase
**India has no wash-sale rule for listed equities** — a loss realised today is allowed even if the
name is repurchased tomorrow. Do not import the US 30-day prohibition; it does not apply.
The real economics: repurchasing resets basis to the lower price, so a harvest-then-rebuy converts
unrealised loss into a realised offset while keeping exposure — but it also gives up the higher basis
that would have sheltered a future gain. Four of these five are **trims, not exits**, so residual
exposure persists regardless and the repurchase question is mostly moot for them.

## 6. FY clock
FY ends **2027-03-31**. Today 2026-08-30 → **not in the Jan–Mar harvesting window** (7 months out).
One asymmetry worth stating: the $1,173 of unrealised loss is not a stored asset. Waiting for the
traditional Jan–Mar window risks these names recovering, at which point the offset simply disappears.
Given the $2,011 already booked, harvesting is a live option now and not only in Q4.

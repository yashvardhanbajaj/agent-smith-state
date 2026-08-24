# smith-tax — 2026-08-24 (run 2026-08-24-1351)

**Price source for every dollar figure below:** `runs/2026-08-24-1351/compute_book.json` positions
(INDmoney live quotes, pre-open 2026-08-24, USDINR 95.725, coverage 100%, 0 unpriced). Basis figures
from `lots.json` (`_rebuilt: 2026-08-24`), all `price_source: email_confirmed`.

## 1. Lot file state — TRUSTED

`smith_math.py lots --base-dir . --holdings runs/2026-08-24-1351/holdings.json`:
**33/33 tickers reconciled, 71 open lots, 0 mismatches, 0 orphans, 0 phantom shorts, 0 null dates,
0 null prices.** One informational warning only (G80 residue, ~$12 of basis error on live positions,
0.027% of book — knowingly accepted). The file is safe to sequence against.

## 2. LTCG window — NO LIVE DECISIONS, and the boundary moved later, not earlier

Earliest open lot is now **2026-07-21** (GEV, 0.000782sh), not 2026-07-15 — the stop-loss cascade
closed those older lots. At a **24-month** boundary (`policy.json.ltcg_boundary_months: 24`), the
first LTCG crossing is **2028-07-21**. Latest open lot 2026-08-21.

**Every one of the 71 open lots is short-term. No trim on this book can be deferred into long-term
treatment, this FY or next.** There is nothing to sequence on holding period. Do not let anyone
frame these trims as LTCG-timing decisions. Everything below is basis selection and loss harvesting.

## 3. FIFO vs HIFO on the eight open trims

| Prop | Tkr | Px | Size $ | Shares | FIFO gain | HIFO gain | Delta | Material? |
|---|---|---|---|---|---|---|---|---|
| P-131 | BE | 195.02 | 403.00 | 2.0665 | −100.76 | −100.76 | 0.00 | no |
| P-132 | GEV | 944.70 | 396.00 | 0.4192 | −26.36 | −38.55 | −12.19 | no |
| P-133 | VRT | 257.00 | 367.00 | 1.4280 | −48.61 | −48.61 | 0.00 | no |
| P-134 | AVGO | 364.56 | 295.00 | 0.8092 | −46.26 | −46.26 | 0.00 | no |
| P-114 | MRVL | 228.92 | 550.65 | 2.4054 | **+109.73** | **−34.17** | **−143.90** | **YES** |
| P-119 | MSFT | 484.10 | 360.00 | 0.7436 | −8.83 | −19.16 | −10.33 | no |
| P-125 | NVDA | 214.87 | 576.00 | 2.6807 | +46.54 | +46.54 | 0.00 | no |
| P-130 | NBIS | 212.39 | 645.44 | 3.0389 | −16.68 | −22.62 | −5.94 | no |

All eight sizes fit inside the held quantity; no proposal oversells.

**Seven of the eight are not worth complicating an execution over.** Five have a literally identical
sequence (single lot, or the oldest lot is also the highest-basis lot). GEV/MSFT/NBIS differ by
$12.19 / $10.33 / $5.94 — noise against the trim sizes.

**MRVL (P-114) is the one real decision on this page.** FIFO books a **+$109.73 gain**; HIFO books a
**−$34.17 loss**. A **$143.90 swing on a $550.65 trim — 26% of the proceeds.** If P-114 executes,
lot selection matters more than the trim price does.

Lot detail for the two that aren't self-evident:
- **MRVL** — FIFO: 2026-07-29 2.0000sh @ $175.59 + 2026-08-12 0.4054sh @ $221.35.
  HIFO: 2026-08-20 1sh @ $245.13 + 2026-08-20 1sh @ $243.64 + 2026-08-21 0.4054sh @ $236.92.
  Note what HIFO sells: the re-entry-after-stop lots from 20/21 Aug. Selling them round-trips a
  four-day-old re-entry. That is a fact about the proposal, not an objection to it.
- **GEV** — FIFO walks three fractional lots (07-21/07-22/07-28); HIFO takes 0.4184sh from the
  2026-08-13 $1,036.57 lot. Cleaner execution, $12 better. Fine either way.
- **NVDA** — both sequences take the same 2026-07-28 $197.51 lot. Both open NVDA lots sit below
  spot, so **the +$46.54 gain is unavoidable at any sequence.** Worth stating plainly.

## 4. Loss-harvesting scan (23 names below basis, ~$1,646 total unrealised loss)

FY26-27 realised gains to date: **approximately +$2,134** (own FIFO derivation from `trades.json`;
see data_quality — 8 ledger anomalies sit in the window, so treat as indicative, not exact).
Harvesting therefore has genuine offset value against a real booked gain.

**Thesis-clean candidates (`watch`) — harvest sells nothing you're arguing for:**

| Tkr | Px | W-avg basis | Qty | Unrealised loss | Thesis |
|---|---|---|---|---|---|
| STM | 49.76 | 54.42 | 30.000 | −139.80 | watch |
| VRT | 257.00 | 272.58 | 7.000 | −109.06 | watch |
| INTC | 88.54 | 95.31 | 15.000 | −101.51 | watch |
| CIEN | 386.01 | 425.97 | 2.009 | −80.26 | watch |
| TXN | 260.40 | 282.62 | 3.000 | −66.66 | watch |
| AMD | 463.83 | 491.12 | 2.000 | −54.58 | watch |
| MSFT | 484.10 | 500.60 | 3.000 | −49.50 | watch |
| NBIS | 212.39 | 218.73 | 7.000 | −44.37 | watch |
| BABA | 115.20 | 130.71 | 2.000 | −31.02 | watch |
| MU | 934.40 | 945.69 | 1.500 | −16.94 | watch |

Sub-total, full liquidation of the `watch` bucket: **−$693.70**. STM alone is the largest single
clean harvest on the book at −$139.80 and carries no open proposal.

**Tension cases — thesis is `strengthening`, so harvesting sells conviction:**
BE −$212.93 (largest loss on the book, thesis strengthening), AVGO −$114.43, GEV −$113.43,
GLW −$83.82, AMAT −$76.60, AMZN −$72.18, SKHY −$33.98, WDC −$28.52. Sub-total **−$735.89**.
Flagged, not recommended. Note that BE/GEV/AVGO already carry HIGH-priority `catalyst_threat` trims
(P-131/P-132/P-134) — if those execute on their own merits the loss gets booked anyway, which makes
the harvest a by-product of the strategist's call rather than a tax decision of mine.

**If all six loss-making trims execute as proposed**, the book realises roughly **−$247** of losses
(BE −100.76, VRT −48.61, AVGO −46.26, GEV −26.36 to −38.55, NBIS −16.68 to −22.62, MSFT −8.83 to
−19.16), against **+$156 of gains** from NVDA (+46.54) and MRVL-under-FIFO (+109.73). Net roughly
**−$91 FIFO / −$245 HIFO** across the eight. Choosing HIFO on MRVL alone flips the whole trim
programme from roughly gain-neutral to net loss-realising.

## 5. Wash-sale / repurchase economics

**India has no wash-sale rule for listed equities** — a loss realised today is deductible even if the
same name is repurchased tomorrow. I am not going to invent a US-style 30-day prohibition, because
none applies. But the *economics* still change: this book repeatedly stops out and re-enters the same
names (MRVL stopped out then re-entered 20–21 Aug; BX exited 08-17 and re-entered 08-21 at a higher
price; INTC and GLW carry open BUY proposals while sitting below basis). A harvest followed by a
prompt re-entry converts a paper loss into a booked one at the cost of re-entering at whatever the
market prices then — the risk is execution slippage and gap risk, not disallowance.

## 6. FY clock

FY ends **2027-03-31**. Today is 2026-08-24 — **outside** the Jan–Mar harvesting window by roughly
seven months. No urgency. There are 7+ months to harvest the $1,646 against the ~$2,134 booked, and
prices will move a great deal in between. Nothing here needs to happen this week for tax reasons.

## Data quality
- FY26-27 realised-gain total (~$2,134) is my own FIFO pass over `trades.json`, not an engine output
  — `smith_math.py` has no realised-gain subcommand. 8 anomalies fall inside the FY window
  (AMD 05-11/12 null-basis, LLY 05-28, SMCI 06-24, and four 2026-08-15 null-price sells: QCOM,
  MSFT, PLTR, META). The figure is indicative and most likely understated. Not used to size anything.
- `policy.json` line 127 is stale: it still says "LTCG per-lot purchase dates unavailable — lots.json
  needs seeding (G1)". G1 closed 2026-08-15; all 71 lots now carry confirmed dates. Policy's
  `ltcg_boundary_months: 24` is correct and was applied.
- Known-gap G82 and the dispatch brief both state BX was re-entered **2026-08-24**. The ledger and
  `lots.json` both date that lot **2026-08-21** (10sh @ $143.49, email_confirmed). Immaterial to tax
  — every lot is short-term either way — but the two records disagree and G82 should be corrected.
- Betas defaulted to 1.0 for WDC and HOOD (per compute_book). Does not affect any figure above.

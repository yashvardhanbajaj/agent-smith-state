# smith-tax — 2026-09-06 (DEEP)

## 0. LOT FILE STATE — CLEAN, and the rebuild landed mid-run
Read #1 of lots.json (13:04-vintage, `_rebuilt: 2026-09-03`) matched compute_lots.json's
reconciliation: 26/32 tickers, 6 mismatches (APH -10, GLW +5, AMD -1, COHR -1, KLAC -1, ASML -0.25).
Read #2 (13:09) shows `_rebuilt: 2026-09-06` — smith-ledger's rebuild completed while I worked.
Re-verified against this run's holdings quantities: **32/32 tickers reconcile, 0 mismatches,
0 orphans, 0 phantom shorts, 72/72 open lots carry a known date and an email_confirmed price.**
All figures below are from the POST-rebuild file. GLW is resolved: the -5 consumed the 08-19 and
08-25 lots plus 2 of 08-26 under FIFO, leaving one lot 3sh @ $149.31 (2026-08-26) = broker's 3.

## 1. LTCG — nothing to sequence, stated plainly
Earliest open lot in the entire book: **2026-07-21 (GEV)**. India's 24-month boundary for foreign
equity puts the first LTCG crossing at **2028-07-21**. Every one of the 72 open lots is short-term.
**No trim in this run can be deferred into long-term treatment, and no deferral argument exists.**
That is the whole LTCG section; there is no urgency here to manufacture.

## 2. TRIM SEQUENCING — FIFO vs HIFO
Prices: compute_book.json, last close 2026-09-04 (market_session closed_weekend, run 2026-09-06).

| ID | Name | Size | Shares | FIFO lot | HIFO lot | Gain FIFO | Gain HIFO | Delta |
|----|------|------|--------|----------|----------|-----------|-----------|-------|
| P-192 | MRVL | $220.00 | 0.9842 @223.55 | 08-21 @236.92 | 08-21 @236.92 | -$13.16 | -$13.16 | $0.00 |
| P-207 | MSFT | $152.66 | 0.3055 @499.70 | 08-10 @509.86 | same (only lot) | -$3.10 | -$3.10 | $0.00 |
| P-212 | AVGO | $142.60 | 0.3984 @357.90 | 08-27 @369.52 | same (only lot) | -$4.63 | -$4.63 | $0.00 |
| P-214 | FSLR | $182.69 | 0.8936 @204.45 | 08-31 @202.15 | same (only lot) | +$2.06 | +$2.06 | $0.00 |
| P-215 | AMD  | $273.07 | 0.5718 @477.57 | 08-12 @491.12 | 08-12 @491.12 | -$7.75 | -$7.75 | $0.00 |

**FIFO = HIFO on all five. Tax delta is exactly $0 across the whole trim slate.** Two reasons:
three names (MSFT, AVGO, FSLR) hold a single lot, and on the two multi-lot names (MRVL, AMD) the
OLDEST lot happens to also be the HIGHEST-basis lot, so the accounting engine's FIFO already
produces the tax-minimal answer. **No execution should be complicated for lot selection this run.**
Four of the five trims realise a small LOSS (P-214 FSLR is the only gain, +$2.06 — immaterial).

## 3. LOSS HARVESTING
Weighted basis from lots.json; price 2026-09-04 close. Full-position harvest sizing.

| Ticker | Wtd basis | Price | Qty | Unrealised loss | % | Thesis | Collision |
|--------|-----------|-------|-----|-----------------|---|--------|-----------|
| AMAT | 476.40 | 454.71 | 3.008 | -$65.24 | -4.55% | strengthening | **BUY leg of P-192 pair** |
| STM  | 53.78 | 52.24 | 35 | -$53.90 | -2.86% | watch | none |
| MRVL | 229.34 | 223.55 | 9 | -$52.15 | -2.53% | strengthening | is itself P-192 sell leg |
| GEV  | 953.24 | 941.95 | 4.005 | -$45.21 | -1.18% | strengthening | none |
| ASML | 1739.18 | 1714.88 | 1.25 | -$30.37 | -1.40% | watch | added 0.25sh 2026-09-03 |
| GOOG | 342.23 | 335.31 | 4 | -$27.68 | -2.02% | strengthening | none |
| AVGO | 369.52 | 357.90 | 2 | -$23.25 | -3.15% | watch | P-212 trims part of it |
| AMD  | 483.57 | 477.57 | 3 | -$18.01 | -1.24% | watch | added 1sh 2026-09-04 |
| MSFT | 509.86 | 499.70 | 1 | -$10.16 | -1.99% | watch | P-207 sells part of it |
| LRCX | 310.98 | 307.65 | 3 | -$10.00 | -1.07% | strengthening | none |
| APH  | 82.88 | 82.78 | 10 | -$1.00 | -0.12% | (new, no thesis) | bought 2026-09-04 |
| CIEN | 376.60 | 321.01 | 0.0085 | -$0.47 | -14.76% | strengthening | dust |

**Genuine candidate: STM only.** -$53.90, watch thesis, no open proposal, no recent fill. Every
other loser is either a strengthening thesis (AMAT, MRVL, GEV, GOOG, LRCX — harvesting sells
conviction), a name bought in the last three days (APH, AMD, ASML — the harvest would be undoing
a fill the desk chose this week), or dust (CIEN $0.47, APH $1.00 — below any execution cost).
AMAT is the sharpest tension: it is the largest single loss AND the intended BUY leg of P-192.
Harvesting it would have the desk selling the name it is proposing to add to.

**Note the holdings-vs-lots basis divergence.** The dispatch quoted AMAT -5.05%, AVGO -3.90%,
GOOG -2.45%, AMD -2.08%, ASML -2.15%, APH -1.11% from holdings.json. Lots-derived basis gives
-4.55%, -3.15%, -2.02%, -1.24%, -1.40%, -0.12%. Direction agrees everywhere; magnitude does not.
For a realised-loss figure the lots basis is the tax-correct one. The gap is worth a ledger look.

**Repurchase economics, not a wash-sale rule.** India has no US-style 30-day wash-sale prohibition
on equities — a harvest-and-rebuy is legal. But rebuying STM within days resets basis to the lower
price, so the harvest converts an unrealised loss into a realised one at the cost of surrendering
future downside cushion. That is a real economic trade-off; it is not a legal bar.

## 4. FY CLOCK
Indian FY ends 2027-03-31. Today 2026-09-06 — **outside** the Jan-Mar harvest window by ~4 months.
No timing pressure on any harvest decision this run.

## 5. DATA QUALITY
- lots.json rebuilt mid-run (13:04 -> 13:09); everything above re-derived from the post-rebuild file.
- Realised gains booked FY-to-date not supplied in the slice — harvest BENEFIT (tax offset) cannot
  be sized in rupees, only the gross loss. Flagged, not estimated.
- APH has no thesis entry (bought 2026-09-04); harvest tension untestable, but the $1.00 loss is dust.
- G83 (BX lot date 08-21 vs stated 08-24) still open; BX carries no loss and no trim, so it is inert here.

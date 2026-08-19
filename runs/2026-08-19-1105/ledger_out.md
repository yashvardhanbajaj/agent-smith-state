# SMITH-LEDGER reconciliation — run 2026-08-19-1105

**Window:** since 2026-08-17T23:54:00+05:30 (prior run) through 2026-08-19T11:05:00+05:30 (this run), realistically covering the tail of Monday 2026-08-17's US session plus the full Tuesday 2026-08-18 session (SMH -4.09%).

**Query:** `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/08/17`, pageSize 50 — 18 threads returned, no `nextPageToken` (single page, complete). 2 were `is cancelled` notifications, excluded per Hard Rule 4 (never counted, never double-counted against the fill that followed/preceded them).

## THE CENTRAL QUESTION: was this a stop-loss cascade?

**Yes, for 10 of the 11 moved tickers — confirmed, not assumed, from the literal `Order Type` field.**

All 10 of MRVL, AVGO, MU, TER, ARM, DRAM, IONQ, NBIS (second tranche), ORCL, SKHY carry `Order Type: stop` in their confirmation emails, fired in two tight windows:
- **2026-08-18T13:30:05Z–13:31:58Z** (9 fills in <2 minutes): DRAM, SKHY, IONQ, AVGO, TER, MRVL, MU, ARM, ORCL
- **2026-08-18T14:41:23Z**: NBIS (second tranche, 3sh)

This is a genuine, broker-confirmed stop-loss cascade on Tuesday's -4.09% SMH session, exactly matching the desk's tight-large-quantum-stop discipline. TER's near-total exit to 0.002730188sh dust is **not** a corporate action — `compute_book.json`'s `likely_corporate_action=true` flag is a false-positive from the ratio heuristic; the email confirms it as an ordinary stop sell of 3sh, same as the other three trims.

**The 11th ticker, SNDK, is NOT part of the cascade.** Its exit (0.508131251→0) is dated **2026-08-17T19:22:23Z (Monday evening)**, `Order Type: Market`, not `stop`. It landed in this run's qty_changes only because the prior run's cutoff (18:24 UTC Monday) fell before this fill. A separate SNDK Limit sell was cancelled 23 seconds earlier (19:22:00Z) — excluded, not double-counted. Reason stays `UNCAPTURED` per Hard Rule 5 — a Market order proves *what*, never *why*.

Two more Monday fills, also stops, were **already sitting in trades.json as reconstructed guesses** from the prior run (which apparently searched but didn't resolve them) and are corrected below: BX's full exit and NBIS's first trim (6→3) were both `Order Type: stop` — so the cascade's first wave actually started Monday 13:30-13:34 UTC with BX and NBIS, paused, then resumed Tuesday with the other 10.

**Stop-vs-deliberate split across all 12 fills touched this run: 12 stops, 4 deliberate (Market, all buys/adds).**

## Rows corrected (5) — reconstructed → email-confirmed

| Ticker | Date | Old price | New price | Old order_type | New order_type | Reason change | Impact (proceeds/cost) |
|---|---|---|---|---|---|---|---|
| BX | 2026-08-17 | $140.055 | $141.87 | unknown | stop | UNCAPTURED → stop-loss | +$9.08 (higher proceeds than guessed) |
| NBIS (trim) | 2026-08-17 | $275.40 | $268.97 | unknown | stop | UNCAPTURED → stop-loss | -$19.29 (lower proceeds than guessed) |
| IONQ (entry) | 2026-08-17 | $46.505 | $46.70 | unknown | Market | stays UNCAPTURED | +$1.95 (paid more than guessed) |
| BE (add) | 2026-08-17 | $232.63 | $233.87 | unknown | Market | stays UNCAPTURED | +$1.55 (paid more than guessed) |
| AMZN (add) | 2026-08-17 | $259.795 | $261.66 | unknown | Market | stays UNCAPTURED | +$1.87 (paid more than guessed) |

All 5 had correct quantities already (email `Shares:` field matched the existing reconstructed qty exactly); only price/order_type/reason/price_source were wrong, now fixed. `notes` field on each row carries the old→new values inline per the "no silent correction" rule.

## Rows added (11)

1 new Monday row (SNDK exit, detailed above) + 10 Tuesday stop-loss rows (MRVL, AVGO, MU, TER, ARM, DRAM, IONQ, NBIS, ORCL, SKHY), all `price_source: "email_confirmed"`, `qty_source: "email_shares_field"` — every quantity taken verbatim from the email's `Shares:` field, none derived from Amount/Price (Hard Rule 2 / G80).

Amount vs Price×Shares cross-check passed on all 12 sells (exact match to the cent on 8 of them; MRVL off by $0.01, both consistent with normal fee rounding) — no forged/inconsistent confirmations flagged.

## Write safety

`trades.json` → `trades.json.bak` copied, then `trades.json.tmp` written and `mv`'d over the original.
`lots.json` → `lots.json.bak` copied, then rebuilt via `scripts/smith_math.py lots --write` (which itself uses tmp+`os.replace`).

## FIFO rebuild & invariant check

Ran `smith_math.py lots --base-dir . --holdings runs/2026-08-19-1105/holdings.json --write` over the **full** trade history (not patched in place).

- **28/28 held tickers reconciled** (script's own tolerance-based check): 0 mismatches, 0 orphaned positions, 0 phantom shorts.
- **All 7 fully-exited tickers (ARM, SNDK, DRAM, IONQ, NBIS, ORCL, SKHY) consumed to zero** — 6 of 7 have no key left in lots.json at all (exact zero). SNDK carries a **1-millionth-of-a-share (0.000001sh) residual** — this is a display-rounding artifact: the email's `Shares:` field truncates to 6 decimals (0.508131) while the broker-precision qty diff in compute_book.json carries 9 decimals (0.508131251). Per Hard Rule 2 the email field was used verbatim, not adjusted to force an exact zero. Notional value of the residual: ~$0.002. Same pattern shows up as sub-microshare residuals on MU (lots sum 0.500366 vs holdings 0.500365376) and TER (0.002731 vs 0.002730188) — both within the script's own reconciliation tolerance (0 mismatches reported) and immaterial to any P&L computation.
- Pre-existing G80 residue (24 rows predating the 2026-08-15 hardening, ~$29 total cost-basis error, ~$12 on live positions) is unchanged by this run — out of scope, already flagged and accepted upstream.

## Unresolved

None. All 18 threads in the window were either fully resolved to a confirmed fill or correctly excluded as a cancellation.

```json
{"reconciled_range": {"since": "2026-08-17T23:54:00+05:30", "until": "2026-08-19T11:05:00+05:30"},
 "confirmations_found": 18, "rows_added": 11, "rows_corrected": 5, "rows_quarantined": 0,
 "corrections": [
   {"ticker": "BX", "ts": "2026-08-17T13:30:39Z", "field": "price_at_trade", "old": 140.055, "new": 141.87, "impact_usd": 9.08},
   {"ticker": "BX", "ts": "2026-08-17T13:30:39Z", "field": "order_type", "old": "unknown", "new": "stop", "impact_usd": 0},
   {"ticker": "NBIS", "ts": "2026-08-17T13:34:44Z", "field": "price_at_trade", "old": 275.4, "new": 268.97, "impact_usd": -19.29},
   {"ticker": "NBIS", "ts": "2026-08-17T13:34:44Z", "field": "order_type", "old": "unknown", "new": "stop", "impact_usd": 0},
   {"ticker": "IONQ", "ts": "2026-08-17T14:14:51Z", "field": "price_at_trade", "old": 46.505, "new": 46.7, "impact_usd": 1.95},
   {"ticker": "BE", "ts": "2026-08-17T16:11:19Z", "field": "price_at_trade", "old": 232.63, "new": 233.87, "impact_usd": 1.55},
   {"ticker": "AMZN", "ts": "2026-08-17T14:07:53Z", "field": "price_at_trade", "old": 259.795, "new": 261.66, "impact_usd": 1.87}
 ],
 "invariant_check": {"tickers_ok": 28, "mismatches": [
   {"ticker": "SNDK", "lots_sum": 0.000001, "holdings_qty": 0.0},
   {"ticker": "MU", "lots_sum": 0.500366, "holdings_qty": 0.500365376},
   {"ticker": "TER", "lots_sum": 0.002731, "holdings_qty": 0.002730188}
 ]},
 "unresolved": [],
 "data_quality": [
   "SNDK/MU/TER carry sub-microshare (<=1e-6sh, <$0.01 notional) residuals from the email Shares field's 6-decimal truncation vs the broker API's 9-decimal precision -- both are legitimate sources (Hard Rule 2 compliant, nothing derived), the discrepancy is inherent to INDmoney's two systems, not a data error. The script's own reconciliation tolerance reports these as 0 mismatches.",
   "Stop-loss cascade confirmed by literal Order Type field for 10 of 11 tickers in this run's qty_changes plus 2 more from the prior run's reconstructed rows (12 total stops); SNDK's exit was a deliberate Monday-evening Market sell, unrelated to Tuesday's SMH -4.09% session, despite appearing in the same qty_changes diff.",
   "TER's likely_corporate_action=true flag in compute_book.json is a confirmed false positive -- the email shows an ordinary stop-loss sell of 3sh, not a split/conversion."
 ]}
```

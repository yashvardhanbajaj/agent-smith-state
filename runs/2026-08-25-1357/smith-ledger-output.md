# smith-ledger reconciliation — run 2026-08-25-1357

**Range reconciled:** after 2026-08-24T21:07:00+05:30 (prior run ts) through present.
**Search:** `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/08/24` — 20 threads returned (single page, no pagination needed). 9 of these predate the cutoff (13:30–13:46 UTC, already ledgered from the prior run's exits/trims — GLW, BE, LRCX, and the prior MU/NVDA/SKHY/NBIS/MRVL/AMAT sell legs) and were left untouched. The 11 relevant BUY confirmations all fall in an 11-minute window, 18:26:09–18:37:45 UTC on 2026-08-24, one order per ticker.

## Per-ticker result — all 11 EMAIL-CONFIRMED, none reconstructed

| Ticker | Qty (Shares field) | Price | Amount | Order Type | Fill (UTC) | Matches compute_book delta? |
|---|---|---|---|---|---|---|
| NVDA | 5 | $210.23 | $1054.28 | Market | 18:26:09 | yes (0→5) |
| SKHY | 5 | $156.61 | $785.38 | Market | 18:27:58 | yes (0→5) |
| NBIS | 5 | $212.75 | $1066.93 | Market | 18:28:53 | yes (0→5) |
| MRVL | 5 | $230.96 | $1158.27 | Market | 18:30:03 | yes (2→7) |
| MU | 1 | $920.44 | $923.21 | Market | 18:32:23 | yes (0.500365376→1.500365376) — resolves the `likely_corporate_action` flag: this is a real 1-share market buy, not a split/CA |
| ASML | 0.5 | $1757.32 | $881.29 | Market | 18:32:47 | yes (0.000001151→0.500001151) |
| AMAT | 1 | $487.74 | $489.20 | Market | 18:33:18 | yes (0.0081785→1.0081785) |
| GOOG | 1 | $345.59 | $346.63 | Market | 18:34:42 | yes (3→4) |
| CIEN | 1 | $376.60 | $377.73 | Market | 18:35:00 | yes (2.008528082→3.008528082) |
| KLAC | 4 | $182.63 | $732.69 | Market | 18:36:10 | yes (0→4, new position, ticker_map already carried "KLA Corporation Common Stock" -> KLAC from this run) |
| COHR | 4 | $279.06 | $1119.58 | Market | 18:37:45 | yes (0→4) |

All 11 confirmations obtained via `get_thread` (PLAIN_TEXT) because every snippet truncated before or inside the `Order Type` field — quantity was never at risk (the `Shares:` field was intact in every snippet) but Order Type had to be read in full to rule out `stop` per the reason-inference rule. **All 11 are `Order Type: Market`** — none is a stop, so all 11 rows carry `reason: "UNCAPTURED"` (no motive inferred; interactive follow-up needed for DCA/rebalance/thesis rationale).

Amount vs Price×Shares sanity check: every row is internally consistent with the observed ~0.30% SEC/FINRA fee ratio (e.g. NVDA: 210.23×5=1051.15 vs Amount 1054.28, diff 0.30%; COHR: 279.06×4=1116.24 vs 1119.58, diff 0.30%). None flagged as forged/inconsistent.

**Note on MU and ASML price levels:** $920.44 (MU) and $1757.32 (ASML) are well above what I'd expect from recent trading ranges for these names. The confirmations are internally consistent (Amount ≈ Price×Shares + plausible fee) and the `Shares:` field is unambiguous, so per the hard rule the email is taken as truth regardless of how the price looks against outside context — flagged in `data_quality` below for the user's awareness, not corrected.

## Ledger state at start of this dispatch

`trades.json` already contained all 11 rows (`price_source: "email_confirmed"`, `qty_source: "email_shares_field"`) with matching message IDs and figures — written by an earlier pass of this same reconciliation (trades.json mtime 2026-08-25 14:04, predating this dispatch's tool calls). I independently re-derived all 11 confirmations from Gmail from scratch and they match the existing rows exactly field-for-field, so no correction was needed there.

`lots.json`, however, had NOT been rebuilt since 2026-08-24T21:19 — it still reflected the pre-trade quantities for all 11 tickers (MU carried only the 0.500366sh lot, GOOG only 3sh, CIEN only 2.008528sh, AMAT only 0.008179sh, MRVL only 2sh; COHR/NBIS/NVDA/SKHY/KLAC had no entries at all). This was the actual gap this dispatch closed.

## Lots rebuild

Ran `scripts/smith_math.py lots --base-dir . --holdings runs/2026-08-25-1357/holdings.json` (dry run first, then `--write`). This is the repo's deterministic FIFO engine (`smith_ledger.cmd_lots`) — it re-derives every ticker's lots from the complete `trades.json` history (887 rows) rather than patching in place, and its `--write` path calls `safe_write()`, which already implements the required .bak-then-tmp-then-mv contract (confirmed in `scripts/smith_core.py`). `lots.json.bak` now holds the pre-rebuild state (7,652 bytes, matches the old file); `lots.json` (9,114 bytes) is the rebuilt version.

Post-rebuild lot sums for the 11 tickers, all matching `compute_book.json.current_qty` exactly:

- COHR 4.000000, NBIS 5.000000, NVDA 5.000000, SKHY 5.000000, KLAC 4.000000
- MRVL 7.000000 (2sh lot from 2026-08-21 + 5sh from 2026-08-24)
- MU 1.500366 (0.500366sh from 2026-08-19 + 1sh from 2026-08-24)
- GOOG 4.000000 (3sh from 2026-08-19 + 1sh from 2026-08-24)
- CIEN 3.008528 (0.008528sh 2026-07-28 + 2sh 2026-08-12 + 1sh 2026-08-24)
- ASML 0.500000, AMAT 1.008179 (0.008179sh 2026-08-19 + 1sh 2026-08-24)

## Invariant check

Engine-reported reconciliation against `runs/2026-08-25-1357/holdings.json`: **35/35 live tickers reconciled, zero mismatches, zero orphaned positions, zero phantom shorts.**

## Data quality / carried-forward notes

- MU ($920.44) and ASML ($1757.32) fill prices on 2026-08-24 are well outside what I'd expect from recent ranges for these names, though internally consistent with their own Amount/Shares math. Flagging for awareness, not correcting — the email is the source of truth per the hard rule.
- G80 accepted residue (pre-2026-08-15, unaffected by this dispatch): 24 rows still carry the old forbidden `Amount/Price` derivation (AMD x6, GOOG x5, VRT x3, SMCI x2, PLTR x2, WDC x2, META x2, LLY x1, EWY x1), ~$29 total cost-basis error, ~$12 on live positions (0.027% of book). No new (post-2026-08-15) relapse rows found this run.
- known_gaps G69, G78, G18, G79, G80(open trigger gap), G81, G82, G83 carried forward unchanged — none of this dispatch's scope touched them.

```json
{"reconciled_range": {"since": "2026-08-24T21:07:00+05:30", "until": "2026-08-25T13:59:00+05:30"},
 "confirmations_found": 20, "rows_added": 0, "rows_corrected": 0, "rows_quarantined": 0,
 "corrections": [],
 "invariant_check": {"tickers_ok": 35, "mismatches": []},
 "unresolved": [],
 "data_quality": [
   {"ticker": "MU", "note": "2026-08-24 email-confirmed fill price $920.44 is well above recent expected range; internally consistent (Amount/Shares check passes), taken as truth per hard rule, flagged not corrected"},
   {"ticker": "ASML", "note": "2026-08-24 email-confirmed fill price $1757.32 is well above recent expected range; internally consistent (Amount/Shares check passes), taken as truth per hard rule, flagged not corrected"},
   {"note": "trades.json already held all 11 rows for this reconciliation window at dispatch start (written by an earlier pass); independently re-pulled all 11 confirmations from Gmail and they match exactly. lots.json had not been rebuilt since 2026-08-24T21:19 and was the actual gap closed this run via scripts/smith_math.py lots --write."}
 ]}
```

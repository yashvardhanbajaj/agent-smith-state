# SMITH-LEDGER reconciliation — run 2026-08-24-0855 (QUICK sweep)

**Reconciled range:** 2026-08-20 (prior run ts, 22:11 IST) through 2026-08-24.
**Trigger:** compute_book.json.qty_changes non-empty across 9 tickers: BE, MRVL, INTC, QCOM, CLS, TER, COHR, IREN, BX.

## Pull

`search_threads` on `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/08/20 before:2026/08/25`, pageSize 50 → 18 threads, resultCountEstimate matched actual count, no pagination needed. 8 of the 18 were already in trades.json (the prior run's own 2026-08-20 13:37–14:39 UTC batch: SKHY x2, MRVL x2, NBIS, COHR add, VRT, TER add — verified by message_id, not re-added). The remaining **10 confirmations, all dated 2026-08-21, all message-id-deduplicated**, covered every one of the 9 flagged tickers exactly:

| Ticker | Side | Shares | Price | Amount | Order Type | Fill (UTC) |
|---|---|---|---|---|---|---|
| TER | SELL | 2 | $370.50 | $741.00 | stop | 13:53:54Z |
| TER | SELL | 1 | $368.70 | $368.70 | stop | 13:54:16Z |
| QCOM | SELL | 3 | $160.00 | $480.00 | stop | 14:13:18Z |
| CLS | SELL | 4 | $294.80 | $1179.20 | stop | 14:14:25Z |
| IREN | SELL | 20 | $41.00 | $820.00 | stop | 14:42:49Z |
| COHR | SELL | 6 | $287.97 | $1727.84 | stop | 14:51:40Z |
| BE | BUY | 2 | $200.31 | $401.82 | Market | 19:49:43Z |
| MRVL | BUY | 2 | $236.92 | $475.26 | Market | 19:50:57Z |
| INTC | BUY | 3 | $89.99 | $270.78 | Market | 19:52:37Z |
| BX | BUY | 10 | $143.49 | $1439.22 | Market | 19:56:33Z |

Order Type for BE/MRVL/INTC/BX was truncated in the search snippet (cut right after "Order Type:"), so I called `get_thread` on all four (PLAIN_TEXT) — all confirmed **Market**, not stop, so per Hard Rule 5 they keep `reason: "UNCAPTURED"` rather than any inferred motive. The six stop-order snippets already showed the full field, no truncation.

## Verification of the three flagged suspicions

1. **CLS "likely_corporate_action" (ratio 0.0008)** — VERIFIED NOT a corporate action. The 4-share SELL matches exactly (4.003266352 → 0.003266352). The near-total-to-dust ratio was coincidental: CLS already carried a 0.003266352-share fractional remainder from a 2026-07-15 fill, five weeks before this sale, and the sale consumed exactly the whole-share lots on top of it.
2. **TER "likely_corporate_action" (ratio 0.0009)** — same pattern, same verdict. TWO separate sell confirmations 22 seconds apart (2sh @ $370.50, 1sh @ $368.70) sum to exactly 3sh, matching 3.002730188 → 0.002730188. Kept as **two rows**, not one averaged fill (Hard Rule 3) — this is exactly the NVDA 07-27 failure mode the ledger exists to prevent.
3. **MRVL "already tagged re-entry-after-stop dated 2026-08-20"** — checked for double-counting. The prior run's 2026-08-20 tag covered a *different* MRVL buy (1sh @ $243.64, msg `1a01f9c761ac23d4`, already in trades.json, taking MRVL 5→6sh). Today's new MRVL row is a distinct 2026-08-21 order (2sh @ $236.92, msg `1a025e065b49ba5f`, 6→8sh) — not a duplicate. Reason kept UNCAPTURED (Market order, not literal stop) rather than inheriting the 08-20 row's re-entry-after-stop label.

BX was confirmed as a **re-entry**, not a first-time buy: trades.json already shows BX fully stop-exited 2026-08-17 (5sh @ $141.87). The 08-21 confirmation establishes a fresh 10sh lot dated 08-21, with no basis carried from the old position.

All Amount vs Price×Shares checks were within a plausible-fee band (buys ~0.3%, consistent with the known SEC/FINRA fee pattern; the six 08-21 sells showed $0.00 fee differential — noted in data_quality, not treated as forged since it doesn't exceed a plausible range).

## Write

Backed up `trades.json`→`trades.json.bak` and `lots.json`→`lots.json.bak` before any write. Appended 10 rows to `trades.json` (857→867), each with `price_source: "email_confirmed"`, `qty_source: "email_shares_field"`, `message_id`, and a notes field showing exactly what compute_book.json flagged and what verification found. Wrote via tmp+replace.

Rebuilt `lots.json` from scratch with the repo's deterministic FIFO engine (`smith_math.py lots --holdings runs/2026-08-24-0855/holdings.json --write`), which also does its own tmp+replace. No hand-editing of lots.json.

## Invariant check

Engine reconciliation against `runs/2026-08-24-0855/holdings.json` (today's live 33-position broker snapshot): **33/33 tickers reconciled, 0 mismatches, 0 orphaned positions, 0 phantom shorts.** COHR and IREN correctly dropped out of lots.json entirely (0 lots remaining after full exit); BX now carries a clean fresh 10sh lot dated 2026-08-21. Spot-checked all 9 flagged tickers individually — sums match live qty exactly (BE 10, MRVL 8, INTC 15, QCOM 7.000762, CLS 0.003266, TER 0.002731, BX 10, COHR/IREN absent).

No pre-existing rows required correction this run — the 10 new confirmations landed clean against what compute_book.json had already flagged, and the two "likely_corporate_action" suspicions both resolved to ordinary stop-loss sells on inspection, not fabricated corporate actions.

## Files touched

- `/Users/yb/Claude/AgentSmith/trades.json` (867 rows now; backup at `trades.json.bak`)
- `/Users/yb/Claude/AgentSmith/lots.json` (rebuilt FIFO; backup at `lots.json.bak`)
- `/Users/yb/Claude/AgentSmith/runs/2026-08-24-0855/smith-ledger-output.md` (this file)

```json
{"reconciled_range": {"since": "2026-08-20", "until": "2026-08-24"},
 "confirmations_found": 18, "rows_added": 10, "rows_corrected": 0, "rows_quarantined": 0,
 "corrections": [],
 "invariant_check": {"tickers_ok": 33, "mismatches": []},
 "unresolved": [],
 "data_quality": ["The 6 stop-order sell confirmations on 2026-08-21 (TER x2, QCOM, CLS, IREN, COHR) all show Amount == Price x Shares exactly, $0.00 fee differential -- contrasts with the ~0.3% fee pattern seen on buy-side confirmations this same batch (BE, MRVL, INTC, BX). Not flagged as forged (zero is within a plausible range, not evidence of tampering) but worth tracking if a future fee-ratio model is ever built off buy-side data alone -- it would misprice stop-loss proceeds.", "CLS and TER were both flagged likely_corporate_action=true by compute_book.json's ratio heuristic (near-total-to-dust); both verified as ordinary stop-loss sells against pre-existing fractional dust from unrelated July fills. The heuristic is a reasonable trigger for a manual check but produced two false positives this run -- worth noting for anyone tuning that threshold."]}
```

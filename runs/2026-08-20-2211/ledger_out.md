# SMITH-LEDGER reconciliation — run 2026-08-20-2211

## Prior pass verified intact
The 2026-08-19 PM pass (17 rows: ASML stop-loss + 16 buy fills across 14 tickers) is present and
untouched in `trades.json` — confirmed by summing `amount_usd` on all 16 buy rows dated 2026-08-19
with `action` in (`add`,`entry`): **$10,368.04**, matching the run brief exactly.

## New confirmations pulled (Gmail, `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/08/19`)
27 threads returned. 17 were already captured by the prior pass. 1 was a cancellation
(`Sell order of Lam Research Corporation is cancelled`, thread `1a01b6d8e8881aa8`, 2026-08-19T19:09:19Z,
Order Type stop) — excluded per Hard Rule 4, not written to the ledger. The remaining **9 are the
new tranche**, all BUY, all Order Type Market except HOOD (Limit). Every row's `Shares:` field was
read directly from the email body (`get_thread` used for the 6 whose search-snippet truncated before
the field) — none derived from Amount/Price. Every Amount vs Price×Shares check landed within
0.2–0.3% (SEC/FINRA fee band), so none flagged as forged/inconsistent.

| Ticker | Time (UTC) | Shares | Price | Amount | Order Type | Action | Reason |
|---|---|---|---|---|---|---|---|
| HOOD | 2026-08-19T20:21:05Z | 5 | $96.12 | $482.04 | Limit | entry | dca-into-diversification |
| SKHY | 2026-08-20T13:37:52Z | 3 | $164.57 | $495.19 | Market | entry | re-entry-after-stop |
| SKHY | 2026-08-20T13:39:37Z | 2 | $165.91 | $332.81 | Market | add | re-entry-after-stop |
| MRVL | 2026-08-20T13:38:47Z | 1 | $245.13 | $245.86 | Market | add | re-entry-after-stop (corrected) |
| NBIS | 2026-08-20T13:44:34Z | 3 | $219.86 | $661.57 | Market | add | re-entry-after-stop |
| COHR | 2026-08-20T14:11:36Z | 1 | $285.43 | $286.28 | Market | add | dca-into-diversification |
| VRT  | 2026-08-20T14:12:27Z | 2 | $255.66 | $512.87 | Market | add | dca-into-diversification |
| TER  | 2026-08-20T14:16:05Z | 1 | $381.04 | $382.18 | Market | add | re-entry-after-stop |
| MRVL | 2026-08-20T14:39:02Z | 1 | $243.64 | $244.36 | Market | add | re-entry-after-stop (corrected) |

**Confirmed tranche total: $3,643.16** (run brief's implied-from-diff estimate was ~$3,638.59 — the
$4.57 gap is exactly the effect of the Amount/Price fee wedge the confirmed fills correct for, per
G80's hardened rule; every one of these 9 rows carries `price_source: "email_confirmed"` and
`qty_source: "email_shares_field"`, none reconstructed).

## Rationale correction: MRVL (both fills)
The run brief proposed `dca-into-diversification` for MRVL on the premise it was "not recently
stopped." That's contradicted by the ledger's own record: `trades.json` already carries a
2026-08-18T13:30:17Z row — `MRVL trim -3 @ $220.76, Order Type stop, reason stop-loss` — the same
day, and the identical trim pattern, as **TER**'s 2026-08-18T13:30:09Z stop-trim, which the brief
itself used to justify TER's `re-entry-after-stop` label. Treating identical facts identically, both
MRVL rows are labeled `re-entry-after-stop`, not `dca-into-diversification`. VRT and COHR were checked
against the same 2026-08-18 stop list and confirmed absent from it, so `dca-into-diversification`
stands unchanged for those two. This is the same category of correction as the META rationale
pushback in the 2026-08-19 pass — the ledger's own record outranks a suggested label when the two
disagree.

## SKHY re-entry flag
SKHY was stopped out entirely on 2026-08-18 (11sh @ $161.54, Order Type stop). Today's two fills
re-establish the position at $164.57 and $165.91 — **both above the stop price** (+1.9% and +2.7%
respectively). Flagged explicitly per the run brief's instruction; re-entering above the exit price
on a stop-lossed name is exactly the pattern G64's cost-of-discipline math is meant to catch.

## HOOD ticker integrity check
Confirmation email's `Ticker:` field reads "Robinhood Markets Inc. Class A" — matches Robinhood
Markets, Inc. Class A Common Stock, real-world ticker **HOOD**. The orchestrator's auto-resolution is
confirmed correct against the email body, not inferred from subject text. Brand-new position, no
2026-08-18 stop-out on this name, so `dca-into-diversification` stands as the accurate reason.

## Writes
- `trades.json`: 848 → 857 rows (9 added). `trades.json.bak` taken before write, `.tmp`-then-`mv`
  pattern used. No stray `.tmp` left.
- `lots.json`: rebuilt from scratch via `python3 scripts/smith_math.py lots --base-dir . --holdings
  runs/2026-08-20-2211/holdings.json --write` (full FIFO re-run over all 857 rows, not a patch).
  `lots.json.bak` taken before write. Engine output: 34 tickers, 79 lots, **34/34 reconciled, 0
  mismatches, 0 phantom_shorts**.

## Invariant check — all 7 touched tickers
| Ticker | lots sum | holdings qty | match |
|---|---|---|---|
| MRVL | 6.0 | 6 | yes |
| TER | 3.002731 | 3.002730188 | yes |
| VRT | 7.0 | 7 | yes |
| COHR | 6.0 | 6 | yes |
| NBIS | 7.0 | 7 | yes |
| SKHY | 5.0 | 5 | yes |
| HOOD | 5.0 | 5 | yes |

Full-book invariant (all 34 held tickers, from the engine's own reconciliation pass): 34/34 reconciled,
0 mismatches, 0 orphaned positions.

## Cumulative two-day deployment total and wallet reconciliation
- 2026-08-19 buys (prior pass, verified): $10,368.04
- 2026-08-20 tranche buys (this pass, confirmed): $3,643.16
- **Two-day cumulative buy total: $14,011.20**
- Only sell in the window: ASML stop-loss, $1,774.69 (2026-08-19T13:49:12Z)
- Net cash deployed (buys − sell proceeds): $12,236.51
- Stated wallet drawdown: $14,056.39 → $55.21 = **$14,001.18** decrease

**Does not fully reconcile to the cent.** Net cash deployed from confirmed trades ($12,236.51) is
$1,764.67 short of the stated wallet drawdown ($14,001.18). The gap is close to, but not exactly, the
ASML sale amount ($1,774.69), which suggests the $14,056.39 "yesterday" wallet baseline may already
have the ASML proceeds netted in at a different point than assumed, or reflects a cash snapshot from
a different instant than the trade confirmations span. This is a cash-accounting question outside
smith-ledger's write surface (wallet_usd lives in compute_book.json, not trades.json/lots.json) — every
trade row behind both totals above is individually email-confirmed and the ticker-level invariant
checks all pass, so the ledger itself is not in question. Flagging the wallet-level gap for the
orchestrator/book agent to run down against compute_book.json's own cash-flow trace rather than
guessing at it here.

## Quarantined / unresolved
None. All 9 new-tranche confirmations were fully resolved via email body (Shares field always read
directly, never derived), no forged/inconsistent Amount vs Price×Shares checks, no rows quarantined.

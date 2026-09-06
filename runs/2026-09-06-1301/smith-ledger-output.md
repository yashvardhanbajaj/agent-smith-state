# SMITH-LEDGER reconciliation — 2026-09-06-1301

All 6 flagged qty_changes resolved. Pulled `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/09/03` — 7 threads, all real fills (no `is cancelled` noise), full body via get_thread for every one (AMD's snippet truncated before `Shares:`, exactly the known failure mode; APH/ASML truncated before `Order Type:`). Every quantity came from the email's `Shares:` field, never derived.

GLW's -5 diff was two separate stop-sells 90 seconds apart (3sh @ $141.85, 2sh @ $139.82) — kept as two rows, not averaged, per the NVDA-collapse lesson. Both are `Order Type: stop` → `reason: "stop-loss"`; the other 5 rows (AMD, APH, ASML, COHR, KLAC) are Market/Limit → `reason: "UNCAPTURED"`, motive left for the user.

Amount vs Price×Shares checked on all 7: the 5 buys show the expected ~0.29-0.30% SEC/FINRA fee gap; both GLW sells match exactly with no fee variance. No forged/inconsistent confirmations.

`trades.json` backed up to `trades.json.bak`, 7 rows appended (`price_source: "email_confirmed"`, `qty_source: "email_shares_field"`), atomic write via `.tmp`+`mv`. `lots.json` rebuilt FIFO from the complete history via `smith_math.py lots --write-if-clean` against `holdings.json` (32 tickers) — reconciled cleanly, zero mismatches, zero phantom shorts, written to `/Users/yb/Claude/AgentSmith/lots.json` (backup at `lots.json.bak`).

Invariant verified directly: ASML 1.25=1.25, AMD 3=3, COHR 5=5, KLAC 6=6, GLW 3=3, APH 10=10.

## New trades.json rows

| ticker | date | qty | price | order type | reason |
|---|---|---|---|---|---|
| GLW | 2026-09-03 | -3 | $141.85 | stop | stop-loss |
| GLW | 2026-09-03 | -2 | $139.82 | stop | stop-loss |
| KLAC | 2026-09-03 | +1 | $168.96 | Market | UNCAPTURED |
| COHR | 2026-09-03 | +1 | $260.08 | Market | UNCAPTURED |
| ASML | 2026-09-03 | +0.25 | $1646.90 | Limit | UNCAPTURED |
| APH | 2026-09-04 | +10 (new position) | $82.88 | Market | UNCAPTURED |
| AMD | 2026-09-04 | +1 | $468.48 | Market | UNCAPTURED |

Files touched: `/Users/yb/Claude/AgentSmith/trades.json`, `/Users/yb/Claude/AgentSmith/lots.json` (memory-of-record). Read-only: `runs/2026-09-06-1301/compute_book.json`, `runs/2026-09-06-1301/holdings.json`, `runs/2026-09-06-1301/shared/data_cache_ticker_map.cd85e46b.json`.

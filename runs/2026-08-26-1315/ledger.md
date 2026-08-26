# SMITH-LEDGER reconciliation — run 2026-08-26-1315

**Window:** 2026-08-25T13:57:00+05:30 → 2026-08-26T13:15:00+05:30 (search executed as `after:2026/08/25 before:2026/08/27`, all 9 hits fell inside the true window; no `is cancelled` subjects seen, none excluded)

## Confirmations pulled

`search_threads` (from:transactions.indmoney.com subject:(BUY OR SELL)) returned 9 threads, `resultCountEstimate: 9`, no `nextPageToken` — no pagination needed. All 9 were fetched via `get_thread` (PLAIN_TEXT) to read the full `Shares:`/`Order Type:` fields past the snippet truncation, per Hard Rule 2. All 9 are `Order Type: Market` (literal), all `Shares:` read directly — no row used Amount/Price derivation.

| Ticker | Side | Shares | Price | Amount | Fill time (UTC) | message_id |
|---|---|---|---|---|---|---|
| AMAT | BUY | 1 | $485.36 | $486.81 | 13:39:24Z | 1a03925ad501ea14 |
| GLW | BUY | 2 | $148.02 | $296.92 | 13:43:38Z | 1a039298a0010a5e |
| SMCI | BUY | 10 | $37.77 | $378.81 | 13:48:07Z | 1a0392da45874600 |
| LRCX | BUY | 1 | $316.64 | $317.59 | 13:49:02Z | 1a0392e7aaad9a72 |
| TER | BUY | 2 | $374.41 | $751.06 | 13:49:29Z | 1a0392ee7e99fb45 |
| ASML | BUY | 0.5 | $1767.17 | $886.24 | 13:50:06Z | 1a0392f7624227ca |
| CLS | BUY | 1 | $305.40 | $306.32 | 13:51:31Z | 1a03930c2b2d3b65 |
| MSFT | SELL | 1 | $488.01 | $488.01 | 13:54:09Z | 1a039332d3a12263 |
| LITE | BUY | 0.5 | $863.94 | $433.26 | 14:00:26Z | 1a03938ed29fe637 |

All 9 confirmed fill prices differ from the dispatch's "my estimate at live quotes" figures — as expected, since those were live-quote guesses, not confirmations. Every row's true fill price now replaces the estimate. Fee-plausibility check (Amount vs Price×Shares) passed for all 9 within a ~0.3% SEC/FINRA fee band; MSFT's SELL shows Amount == Price exactly (fee rounded to $0.00 at 2dp on a 1-share order — not an anomaly).

## Corrections / classifications

- **AMAT, GLW, LRCX, TER, CLS**: `compute_book.json` flagged TER (ratio 733x) and CLS (ratio 307x) — both are ordinary buys against pre-existing dust from earlier fills, not corporate actions. AMAT (ratio 1.99) and **ASML (ratio 2.0, explicitly false-flagged in the dispatch)** are ordinary adds too — verified against the confirmation text, no split language present.
- **LITE, SMCI**: brand-new positions, both tickers resolved cleanly through `data_cache.ticker_map`. Lots opened.
- **MSFT / CLS reason**: recorded `reason: "profit_rotation"` (not the default `UNCAPTURED`) per orchestrator directive — SELL MSFT (13:54:09Z) and BUY CLS (13:51:31Z) match live `proposals.json` `pair_id: profit_rotation-MSFT-CLS` on tickers, sides, and timing (both within a 3-minute window). **Flag:** both fills diverge materially from the proposal's snapshot prices — CLS filled $305.40 vs proposed $424.65 (−28%), MSFT filled $488.01 vs proposed $437.92 (+11.4%). Recorded as the pair per explicit orchestrator instruction, not inferred from price action; divergence noted below for the strategist to weigh.
- **SNDK dust**: `compute_book.json` flagged `1e-06 → 0`. No confirmation exists or could exist at that quantity — closed with a sourced `corporate_action/adjustment` row (`-2e-06` against the true ~1.0000000000287557e-06 residual; the earlier draft of `-1e-06` was a silent no-op because it sat exactly at the engine's `SHARE_EPS` threshold and never entered `_consume_fifo`'s loop — caught and corrected before the final `--write`).

## FIFO rebuild

Ran `scripts/smith_math.py lots --base-dir . --holdings runs/2026-08-26-1315/holdings.json --write` (full history, not a patch). Result: **37/37 tickers reconciled, 0 mismatches, 0 orphaned positions, 0 phantom shorts.** One informational warning carried over unchanged: 24 pre-2026-08-15 rows still carry the old G80 Amount/Price derivation (~$29 total basis error, ~$12 on live positions) — known, quantified, deliberately left per existing policy.

## Write safety

`trades.json`: `.bak` → `.tmp` → `mv`, twice (initial 9-row add, then the SNDK qty_change fix), both clean. `lots.json`: rebuilt via the engine's own `safe_write` (same `.bak`/`.tmp`/`mv` contract). No stray `.tmp` files remain.

## Files touched

- `/Users/yb/Claude/AgentSmith/trades.json` (897 rows, was 887; `.bak` at `/Users/yb/Claude/AgentSmith/trades.json.bak`)
- `/Users/yb/Claude/AgentSmith/lots.json` (37 tickers, 73 lots; `.bak` at `/Users/yb/Claude/AgentSmith/lots.json.bak`)
- `/Users/yb/Claude/AgentSmith/runs/2026-08-26-1315/ledger.md` (this file)

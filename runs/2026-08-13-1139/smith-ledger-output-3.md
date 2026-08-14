# SMITH-LEDGER — Gap-Fill Run (2026-08-13, output-3)

## Scope
Targeted pull: `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/07/23 before:2026/07/28`, single page, `resultCountEstimate: 25`, no `nextPageToken` — window fully covered in one call (it also incidentally returned eight 2026-07-23 confirmations, which were already in trades.json from an earlier pull and were left untouched).

## PRIORITY 1 — 2026-07-24 (Friday, mass stop-out event #1): 12 confirmations recovered

All 12 were `Order Type: stop`. Seven had truncated snippets (Order Type and/or Price/Shares cut off); each was resolved via `get_thread` full-body fetch rather than derived. `Amount ≈ Price × Shares` held for all 12 within a $0.01 rounding band — no forgery flags.

| Ticker | Time (UTC) | Qty | Price | Amount | Action label |
|---|---|---|---|---|---|
| DRAM | 13:30:15 | -25 | $55.71 | $1392.75 | trim (50→25sh) |
| MU | 13:30:23 | -1 | $959.50 | $959.50 | trim |
| SNDK | 13:30:24 | -1 | $1531.24 | $1531.24 | trim, fill 1/2 |
| CLS | 13:31:33 | -2 | $322.80 | $645.60 | trim |
| IREN | 13:36:33 | -25 | $38.97 | $974.25 | **exit** (25→0, re-entered 07-28) |
| TSM | 13:40:53 | -3 | $409.92 | $1229.77 | trim |
| GLW | 13:46:51 | -10 | $151.90 | $1519.01 | **exit** (10→0, re-entered 07-29) |
| NBIS | 13:47:12 | -6 | $203.99 | $1223.94 | **exit** (6→0, re-entered 07-28/29) |
| CIEN | 13:52:04 | -1 | $394.82 | $394.82 | trim |
| SNDK | 14:17:11 | -1 | $1475.50 | $1475.50 | trim, fill 2/2 |
| TER | 14:39:50 | -2 | $352.84 | $705.68 | trim |
| LRCX | 18:40:36 | -2 | $304.95 | $609.89 | trim (late-session) |

These 12 rows **replace** 4 stale placeholder rows that were removed: `GLW -10` (price null, `price_source: unknown`, G26), `IREN -25` (same), `NBIS -6` (same), and a single `ticker: "MULTI"` row (`qty_change: null`) that had bundled SNDK/DRAM/TSM/CLS/LRCX/MU/TER/CIEN together as "each roughly halved" with no per-name fills. All 8 MULTI-bundled tickers now have real, individually email-confirmed fills. G26 is closed.

## PRIORITY 2 — 2026-07-27 re-pull: no changes

Re-pulled the 5 threads (NVDA×2, EWY, GEV, LRCX). All 5 matched the existing trades.json rows exactly (qty, price, amount, order type) — these were already corrected by the prior G64/G65 run. No discrepancy found; nothing touched.

## FIFO rebuild: full history, not just the gap

`trades.json` now spans 2025-04-30→2026-08-12, 677 rows (was 669; -4 removed, +12 added). I discovered the **existing `lots.json` had never actually been rebuilt against this full history** — its own note says it was built "over the corrected trades.json (2026-07-24 onward)" only. It never saw the 2025-04-30→2026-07-23 backfill at all. So per the instruction to re-run FIFO from scratch over the *whole* of trades.json, I did a full chronological per-ticker FIFO over all 677 rows, not just a patch around 07-24.

**Method:** for each ticker, compute the minimal front-loaded "predates-history" plug needed to keep the FIFO queue non-negative at every point in its recorded history (`required_initial = max(0, -min cumulative balance)`). Insert that as the oldest lot — reusing the existing `derived_from_broker_invested` cost basis if its quantity still matches what's now required, otherwise an explicit `price: null, date: null` lot (no invested_amount figure was cached in this session for AMD/TSM/NVDA, so those three get honest null lots rather than a guessed price). Replay every trade oldest-first. Where the total still doesn't match live holdings after this minimal, honest plug, that is a genuine missing trade elsewhere — reported, not papered over.

### Result: 27 of 31 held tickers reconcile exactly

**Resolved by this run's 07-24 fix (matches the task's named over-counts exactly):**

| Ticker | Was (pre-fix FIFO) | Now |
|---|---|---|
| DRAM | 55 vs 30 held | **0 diff** |
| TSM | 7 vs 6 held | **0 diff** (needed a legitimate 2sh predates-history plug, price/date unknown — TSM's own recorded history shows two 2025 sells that exceed its 2025 buys, meaning ~2sh predate 2025-07-01; front-loading that plug makes the whole chain, including 07-24 through 08-12, reconcile cleanly) |
| CLS | 6 vs 4 | **0 diff** |
| TER | 5 vs 3 | **0 diff** |
| LRCX | 5 vs 3 | **0 diff** |
| SNDK | 2.5 vs 0.5 | **0 diff** |
| MSFT | *(not in MULTI — see below, still open)* | — |
| MU | 3 vs 2 | **0 diff** |
| CIEN | 3 vs 2 | **0 diff** |
| NBIS | *(newly surfaced — was unresolved, now resolved)* | **0 diff** |
| NVDA | *(unaffected by 07-24; already had a 3sh predates plug from the G64 NVDA-split work — confirmed still correct under full-history FIFO)* | **0 diff** |

**Bonus resolutions** (not on the task's list, but the full-history FIFO also retired large stale `derived_from_broker_invested` plugs that only existed because the old lots.json never had access to pre-07-24 trades.json data): AMAT, ASML (was **100% unpriced**, 1.0sh @ derived $1569.17 — now fully real dated lots, only a 1-millionth-of-a-share float-rounding dust remains), AVGO, GEV, ORCL, and — largest of the bonus finds — **MRVL** (was a 5-share, ~$876 unpriced plug; now fully explained by real dated buys, with only a tiny 0.0089sh residual left, see below).

### Still unresolved — 4 tickers, confirmed not touched by 07-24-27

| Ticker | lots_sum | holdings | diff | Note |
|---|---|---|---|---|
| QCOM | 13.000762 | 10.000762 | **-3.0 (over)** | Matches the task's stated 13 vs 10 exactly. No QCOM confirmation exists anywhere in 07-24→07-27 (verified — the only QCOM emails in this pull's date range were two 07-23 sells already in the ledger). A real SELL of ~3sh is missing from history somewhere else. |
| MSFT | 4.5 | 3.0 | **-1.5 (over)** | Matches the task's stated 4.5 vs 3 exactly. Zero MSFT activity in 07-24→07-27. Missing SELL elsewhere, unresolved. |
| AMD | 2.020631 | 2.0 | **-0.0206 (over)** | **This is a materially different number than the task's stated "2.02 vs 2" (~0.02) — same order of magnitude, and in fact this run's rigorous full-history FIFO reproduces essentially the identical figure (0.0206 vs 0.02), so this is confirmed, not new.** The dip that forces the plug occurs at a 2026-05-12 sell of -4.0, well outside this run's window. Reported as-is, no fix attempted. |
| MRVL | 7.008898 | 7.0 | **-0.0089 (over)** | Matches task's 7.01 vs 7. Tiny, likely a genuine small missing sell (or, given the scale, floating-point-adjacent) — flagged, not material enough to chase further this run. |

None of these four had any activity in the 2026-07-24→07-27 window (confirmed by the exhaustive pull), so this run could not have resolved them — they are exactly where the task said the remaining gap would be "somewhere else."

## Data quality
- All 12 new fills reconciled `Amount ≈ Price × Shares` within a $0.01 fee/rounding band. No forged/inconsistent confirmations found.
- ASML, AMAT, AVGO, GEV, MU, SNDK, TER carry sub-0.00001-share floating-point residues (well under a cent of value) from cumulative fractional-share arithmetic — immaterial, not treated as gaps.

## Files touched
- `/Users/yb/Claude/AgentSmith/trades.json` — 4 rows removed, 12 rows added (677 total). Backup: `trades.json.bak14`.
- `/Users/yb/Claude/AgentSmith/lots.json` — rebuilt from scratch via full-history chronological FIFO (previous version only covered 07-24-onward trades and had never seen the 2025-04-30 backfill). Backup: `lots.json.bak14`.

```json
{"reconciled_range": {"since": "2026-07-24", "until": "2026-07-27"},
 "confirmations_found": 17, "rows_added": 12, "rows_corrected": 0, "rows_quarantined": 0,
 "corrections": [],
 "invariant_check": {"tickers_ok": 27, "mismatches": [
   {"ticker": "AMD", "lots_sum": 2.020631, "holdings_qty": 2.0},
   {"ticker": "MRVL", "lots_sum": 7.008898, "holdings_qty": 7.0},
   {"ticker": "MSFT", "lots_sum": 4.5, "holdings_qty": 3.0},
   {"ticker": "QCOM", "lots_sum": 13.000762, "holdings_qty": 10.000762}
 ]},
 "unresolved": [
   {"ticker": "QCOM", "ts": null, "missing": "SELL of ~3sh, not in 2026-07-24..07-27 or 07-23; over-count unchanged from pre-run estimate"},
   {"ticker": "MSFT", "ts": null, "missing": "SELL of ~1.5sh, not in 2026-07-24..07-27; over-count unchanged"},
   {"ticker": "AMD", "ts": "2026-05-12", "missing": "SELL/BUY mismatch around the 2026-05-12 -4.0 sell forces a 0.9925sh predates-plug that still leaves a 0.0206sh residual over-count; confirmed consistent with pre-run ~0.02 estimate"},
   {"ticker": "MRVL", "ts": null, "missing": "0.0089sh residual over-count, small, not chased further this run"}
 ],
 "data_quality": []}
```

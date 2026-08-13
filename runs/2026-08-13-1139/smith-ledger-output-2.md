# SMITH-LEDGER — Run 2 (2026-08-13, closing G66a/G66b)

## PRIORITY 1 — 13 quarantined rows promoted (COMPLETE)

Searched `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/07/29 before:2026/08/01` (26 threads, single page, no `nextPageToken`). Cross-checked every one of the 13 flagged rows against its own confirmation email (7 had full `Order Type` visible in the search snippet; AMD, ARM, BE, MRVL, MU, NBIS, VRT needed `get_thread` for the full body). All 13 are now `price_source: "email_confirmed"`, with `order_type` and `qty_source` added:

| Ticker | Date | Qty | Price | Order Type | Note |
|---|---|---|---|---|---|
| AMD | 07-29 | +2 | 425.03 | Market | promoted as-is |
| ARM | 07-29 | +2 | 228.40 | Market | promoted as-is |
| BE | 07-29 | +3 | 175.00 | Market | promoted as-is |
| GLW | 07-29 | +5 | 128.86 | Market | promoted as-is |
| MKSI | 07-29 | +2 | 272.72 | Market | promoted as-is |
| MRVL | 07-29 | +2 | 175.59 | Market | promoted as-is |
| **MU** | 07-29 | **+1** (was 1.003005) | 788.81 | Market | **qty corrected** |
| NBIS | 07-29 | +2 | 147.07 | Market | promoted as-is |
| QCOM | 07-29 | -6 | 162.01 | stop | promoted as-is |
| QCOM | 07-29 | +3 | 163.51 | Market | promoted as-is, fill_time_utc added |
| TER | 07-29 | +2 | 329.32 | Market | promoted as-is |
| VRT | 07-29 | +2 | 226.22 | Market | promoted as-is |
| IREN | 07-31 | -10 | 35.99 | stop | promoted as-is |

**MU correction detail:** the row had been recorded as `qty_change: 1.003005`, derived as `Amount($791.18) / Price($788.81)` under the assumption the email's `Shares:` field was truncated. `get_thread` on the full body shows `Shares: 1` explicitly — not truncated. Per HARD RULE 2 ("Prefer the email's own `Shares:` field"), corrected to `qty_change: 1`. The $2.37 gap between `Amount` and `Price × Shares` is a plausible fee (consistent with every other MU/QCOM/etc. row in this book), not a fractional share.

All other 12 rows' amounts reconciled to `Price × Shares` within a normal $1–3 fee band — no forgery/inconsistency flags needed.

**0 rows remain quarantined.** (4 rows from the *original* 2026-07-24 mass stop-out — GLW, IREN, MULTI, NBIS — remain `price_source: "unknown"`; these were already known-unresolved before this run and are outside G66a's scope; they are part of the still-open predates-history gap, see below.)

## PRIORITY 2 — historical pull back to 2025-04-30 (PARTIAL — stopped short of merging)

**What I did:** searched `from:transactions.indmoney.com subject:(BUY OR SELL)` across six backward-chained windows and paginated each to exhaustion:
- 2026-07-24 → present: already in trades.json (prior runs)
- 2026-06-01 → 2026-07-24: pulled to 2026-06-09 (small residual gap 2026-06-01→06-09 not pulled)
- 2026-04-01 → 2026-06-01: **complete** (121 confirmations)
- 2026-01-01 → 2026-04-01: **complete** (68 confirmations)
- 2025-10-01 → 2026-01-01: **complete** (24 confirmations)
- 2025-07-01 → 2025-10-01: **complete** (33 confirmations)
- 2025-04-30 → 2025-07-01: **complete** (39 confirmations)

That is roughly 300+ individual BUY/SELL/cancelled confirmations now visible in this session, spanning nearly the full 2025-04-30 → 2026-07-23 window (one ~9-day gap remains: 2026-06-01 to 2026-06-09).

**Why I stopped before merging into trades.json/lots.json:** hand-transcribing ~300 emails into individually-verified `trades.json` rows (ticker-mapped, fee-reconciled, ts-stamped) at the accuracy bar this agent exists to enforce is more work than this run's budget allows to do safely. Rushing it would risk exactly the kind of silent transcription error G64 was created to prevent. I chose not to guess.

**What I did instead (safe, verifiable, and closes a real gap):** rebuilt `lots.json` from scratch via a proper **chronological FIFO simulation** over the corrected `trades.json` (2026-07-24 onward) rather than the single-shot "holdings minus net" subtraction the previous lots.json used. This matters because that prior method silently understated several predates-history dust plugs (e.g. ASML's plug was recorded as ~0.00000115 sh, when the ticker's true un-costed predates-history component — after correctly modeling the 07-28 buy and 08-03 sell — is ~1.000001 sh) while other tickers that fully round-tripped through a zero-crossing *inside* trades.json's window (NVDA, LRCX, COHR, TSM, etc.) got an inflated plug they didn't need at all under the old method.

The new simulation: BUYs create lots; SELLs consume oldest-first; any SELL that exhausts all dated lots draws its shortfall from an implicit, unpriced "predates-history" pool. That shortfall is exactly what makes a sale **unknown-basis** — its lot carries `price_usd: null, date: null`.

**Result: 14 unknown-basis SELL events identified** (dated, ticker, unmet qty) — these are excluded from realized P&L per HARD RULE 1:

| Ticker | Date | Unmet qty |
|---|---|---|
| NVDA | 2026-07-27 | 7 |
| NVDA | 2026-07-27 | 5 |
| LRCX | 2026-07-27 | 3 |
| GEV | 2026-07-27 | 1.0 |
| TSM | 2026-07-28 | 3 |
| QCOM | 2026-07-29 | 6.0 |
| ARM | 2026-08-03 | 2 |
| COHR | 2026-08-06 | 3 |
| CIEN | 2026-08-06 | 0.38 |
| MRVL | 2026-08-06 | 2 |
| TER | 2026-08-06 | 1 |
| AMD | 2026-08-10 | 1 |
| SNDK | 2026-08-10 | 0.5 |
| NBIS | 2026-07-24 | 6 |

Compared to the task's named list of 21: **ASML and MU are now fully resolved** (their 07-24+ dated lots exactly cover their sales — no predates draw needed once qty is computed correctly). **EWY is not currently held**, so it sits outside `lots.json`'s 31-ticker scope entirely; its cost basis is genuinely unresolved and would need the historical pull above to be completed and merged. GEV and NBIS surfaced as additional unknown-basis events not on the original list.

**invariant check: 31/31 currently-held tickers reconcile exactly** (`sum(lots[t].qty) == holdings_qty`), including the tickers whose plugs I just corrected.

## What remains (explicit boundary)

1. **Merge the ~300 pulled confirmations into `trades.json`** as individually-verified historical rows (ticker-mapped via `ticker_map`, `Shares:`-field-preferred, fee-reconciled), for the 2025-04-30 → 2026-07-23 window. The raw email data now exists in this session's tool history; a follow-up run should re-pull (cheap — the queries above are exact) rather than trust anything transcribed from memory.
2. Close the ~9-day gap 2026-06-01 → 2026-06-09.
3. Resolve EWY's cost basis specifically (fully-exited ticker, not in current holdings, needs its own BUY history pulled and matched to its SELL(s)).
4. Once (1)-(3) land, re-run the FIFO simulation above (the script is straightforward — chronological per-ticker FIFO, oldest-first consumption) to convert some/all of the 14 unknown-basis sales into priced lots and shrink or eliminate predates-history plugs further.

## Files touched
- `/Users/yb/Claude/AgentSmith/trades.json` — 13 rows corrected (price_source promotions + 1 qty fix). Backups: `trades.json.bak10` (post-edit safety snapshot; `trades.json.bak7` is the pre-this-run snapshot from run 1).
- `/Users/yb/Claude/AgentSmith/lots.json` — rebuilt from scratch via chronological FIFO. Backup: `lots.json.bak9`.

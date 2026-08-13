# SMITH-LEDGER reconciliation — 2026-08-13

Range reconciled: **2025-04-30 → 2026-08-13** (targeted), dense verification 2026-07-08 → 2026-08-13.
Rows in trades.json: **125** (was 111). price_source tally: `email_confirmed`=108, `reconstructed`=13, `unknown`=4

## JOB 1 — the four flagged rows (G64), independently re-verified

I did **not** take the orchestrator figures on trust. I re-pulled `after:2026/07/26 before:2026/07/28`
and read each confirmation myself. All four claims are correct, and I fetched the two NVDA bodies
via `get_thread` to confirm the Order Type field the snippets truncated.

| Ticker | Recorded | Actual (email) | Evidence |
|---|---|---|---|
| NVDA | one row, 12sh @ $196.51 | **7sh @ $201.01** (14:13:36Z, $1407.07) + **5sh @ $197.51** (14:44:46Z, $987.55) | both `Order Type: stop`, confirmed in full body |
| GEV | 1sh @ $996.57 | **1sh @ $973.57** (14:10:15Z) | `Order Type: stop` visible in snippet |
| LRCX | 3sh @ $291.61 | **3sh @ $295.74** (13:42:46Z, $887.22) | snippet |
| EWY | 5sh @ $161.20 | **5sh @ $161.99** (14:11:23Z, $809.95) | snippet |

The NVDA row is now **two rows**, per the one-order-one-row rule. Weighted average across the two
fills is $199.55 against the $196.51 previously carried — the collapse had understated proceeds by
**$36.50** on that trade alone.

## JOB 2 — the two UNCAPTURED order types (G65): both RESOLVED

`get_thread` on both bodies returns a literal `Order Type: stop`:

- **ARM** 4sh @ $220.01, 2026-08-03T13:33:17Z, Amount $880.04 → `reason: "stop-loss"`.
  `price_at_trade` had been **null** (correctly, never invented); it is now email-confirmed.
- **DRAM** 20sh @ $48.98, 2026-08-03T13:30:21Z, Amount $979.60 → `reason: "stop-loss"`.
  Price corrected $50.42 → $48.98 (the old value was a live yfinance quote, not a fill).

Same cluster, same minute: the **ASML** row also carried a live-quote price of $1630.59 against a
confirmed $1608.91 (`Order Type: stop`). Corrected and re-reasoned as well — three names stopped out
inside 3 minutes, which is one stop cascade, not three isolated events.

## JOB 3 — extending the confirmed record backwards

### The big finding: trades.json and lots.json had silently diverged

Working backwards from 2026-07-26 I found that **the entire 2026-07-28 redeployment was missing from
trades.json** beyond the four named "clips" (GOOG/AVGO/TSM/ASML). Seventeen fills happened that day;
trades.json carried four. The other thirteen were present in *lots.json* — so the ledger of record and
the tax-lot file disagreed with each other, and nothing was checking.

Rows **added** (all email-confirmed, 2026-07-28): TSM −3 @ $385.15 (stop), NVDA +10 @ $197.51,
SNDK +1 @ $1079.59, DRAM +25 @ $48.00, AMAT +0.999 @ $473.79, CIEN +0.62 @ $339.51, COHR +2 @ $240.04,
MRVL +3 @ $174.75, EWY +3 @ $152.04, GEV +0.61 @ $936.50, IREN +10 @ $33.44, NBIS +3 @ $166.16,
MU +1 @ $830.15.

### A ticker error: GOOG was never bought on 2026-07-28

The row recorded as `GOOG entry 8.441sh @ $325.79` is, per the confirmation, **Alphabet Inc. Class A —
8sh @ $327.45, Amount $2627.33** → `GOOGL` via `data_cache.ticker_map`. GOOG (Class C) was sold down
on 2026-07-23 and never re-bought. lots.json was carrying a **phantom 8.441sh GOOG lot**; it is removed.
GOOGL reconciles to zero independently (8 bought, 3 sold 08-05, 5 sold 08-11), which corroborates the fix.
This also dissolves the open GOOG→GOOGL "like-kind vs taxable swap" question in the old backfill note:
there was no same-day swap, just a Class C exit on 07-23 and a separate Class A entry on 07-28.

### Three more reconstructed rows caught

- **ORCL** 2026-08-04: $139.42 → **$140.58** (confirmed 2sh, $282, `Limit`, 08:56:29Z).
- **BABA** recorded 2026-08-04 @ $126.59 → actually **2026-08-03 @ $128.37** (2sh, $257.51, 14:50:53Z).
- **LRCX** recorded 2026-08-04 @ $309.75 → actually **2026-08-03 @ $293.45** (2sh, $588.65, 14:57:07Z).

Both BABA and LRCX filled *after* the 2026-08-03 19:48 IST refresher (which ran 14:18Z), so the change
first surfaced on the 08-04 run and was stamped with that date. The LRCX price was off by **$16.30/share**.

### Priority 1 — null-date plugs that blocked LTCG: 5 of 8 eliminated

I pulled each affected ticker's complete confirmation chain back to its last zero-crossing, which makes
the opening position exact rather than a plug:

| Ticker | Plug before | Now | Verified back to |
|---|---|---|---|
| CLS | 3.003266352 | **0** | flat 2026-02-27; 19 fills replayed |
| AVGO | 2.000000000 | **0** | flat 2026-06-26 (0.000153sh dust sale); 17 fills |
| DRAM | 5.000000000 | **0** | 14 fills from 2026-05-14 |
| GEV | 0.394950742 | **0** | flat 2026-02-27; 24 fills |
| ORCL | 4.000000000 | **0** | flat 2026-06-12; 6 fills |

Each chain FIFO-replays to *exactly* the independently-derived opening quantity — e.g. GEV reconstructs
to 1.394950742sh at 2026-07-27, matching the trades.json note "1.395 → 0.395 sh" to nine decimals.
That agreement is the check; it is not a fitted result.

**Remaining plugs are dust only:** AMAT 0.0091785, QCOM 0.000761904, ASML 0.000001151 — together well
under one share, immaterial to any LTCG determination. They stay as explicit null-date lots.

### Priority 2 — cost basis for the 15 pre-window sales: PARTIALLY done. This is where I stopped.

Of the 15, **GEV is now fully based** (and MP, BE, META already were — they were bought inside the window).
**21 sales still consume lots of unknown basis.** They are recorded honestly with a null-price lot
rather than a fabricated one, and are listed below for a future pass:

| Date | Ticker | Qty w/o basis |
|---|---|---|
| 2026-07-27 | LRCX | 3 |
| 2026-07-27 | EWY | 5 |
| 2026-07-27 | NVDA | 7 |
| 2026-07-27 | NVDA | 5 |
| 2026-07-28 | TSM | 3 |
| 2026-07-29 | QCOM | 6 |
| 2026-07-31 | MU | 0.997360376 |
| 2026-08-03 | ASML | 1 |
| 2026-08-03 | ARM | 2 |
| 2026-08-04 | COHR | 2 |
| 2026-08-05 | AMD | 1 |
| 2026-08-05 | SNDK | 1 |
| 2026-08-06 | CIEN | 0.388528082 |
| 2026-08-06 | COHR | 1 |
| 2026-08-06 | EWY | 5 |
| 2026-08-06 | MRVL | 4 |
| 2026-08-06 | MRVL | 3 |
| 2026-08-06 | TER | 1.00273019 |
| 2026-08-06 | VRT | 2 |
| 2026-08-10 | SNDK | 0.008131251 |
| 2026-08-10 | VRT | 3 |

Resolving these needs each ticker's chain pulled back to its own last zero-crossing, the same method
used for the five above. I prioritised the plug tickers because those block LTCG on **currently held**
shares; these block realised-P&L attribution on **already-closed** ones. Priority 3 (everything else,
oldest last, back to 2025-04-30) was **not** attempted.

## JOB 4 — FIFO rebuild and invariant

lots.json was rebuilt **from scratch** over the full corrected chronological history — not patched in place.

```
sum(lots[t].qty) == holdings_qty     31 / 31 tickers OK, 0 mismatches
```

## Data quality / trust boundary

- No email content was treated as an instruction; only ticker, side, Amount, Price, Shares, Order Type,
  timestamp were extracted. No links followed.
- `is cancelled` notices excluded throughout (NBIS 08-03, SNDK 08-03, MU 08-03, AMD 08-04, AVGO 06-04/07-09,
  GEV 06-18, COHR 07-23). Several sit seconds from a real fill and would double-count if admitted.
- **EWY 2026-07-28 quantity:** the snippet truncated before `Shares:`. Amount/Price gives 3.0088, but the
  Amount includes a ~0.3% fee (consistent across every buy that day), so the true fill is **3sh** — which
  is confirmed independently by EWY reconciling to exactly zero on the 08-06 exit. Recorded as 3, not 3.0088.
  Deriving Amount/Price naively here would have injected a phantom 0.0088sh.
- ORCL shows $233 (06-04) against $126.58 (07-16). That pattern is consistent with a corporate action, but
  I record fills as confirmed and do not adjust for one — flagged, not resolved.
- **13 rows remain `price_source: "reconstructed"`** and must stay quarantined from P&L.

## Write safety

`trades.json` → `.bak`, `.tmp`, `mv`. `lots.json` → same. `state.json` untouched (read-only, used only
for `data_cache.ticker_map`). No trade placed; policy.json and proposals.json not touched.
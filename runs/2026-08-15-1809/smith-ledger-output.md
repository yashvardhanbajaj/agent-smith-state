# SMITH-LEDGER Reconciliation — 2026-08-15 DEEP run

Scope: repair the 8 mislabeled `qty_changes` in `runs/2026-08-15-1809/compute_book.json`, pull Gmail confirmations since 2026-08-12, verify the lots-vs-holdings invariant across all 35 current positions, and report status on G68/G70/G71.

## 1. Diagnosis: (c) BOTH — a cmd_book matching bug, compounded by a trades.json data gap

**Root cause is a code bug in `scripts/smith_math.py`** (~L458-469, "attach trade rationale to qty_changes"):

```python
trade_reasons = {}  # ticker -> reason
for trade in trades.get("trades", []):
    t = trade.get("ticker")
    if t:
        trade_reasons[t] = trade.get("reason", "UNCAPTURED")   # last row per ticker wins, no date check
for qc in qty_changes:
    if qc["ticker"] in trade_reasons:
        qc["trade_reason"] = trade_reasons[qc["ticker"]]        # attached with no direction/date match
```

This builds a **ticker -> single reason** map by blind last-write-wins over the whole trades list, then stamps that one reason onto *every* qty_change row for that ticker — regardless of whether the trade that produced the reason has anything to do with the qty_change being reported. There is no date alignment and no direction check (buy vs sell).

**This was compounded by a real data gap**: none of the 8 flagged tickers' actual 2026-08-13/08-14 fills existed in `trades.json` yet — this run's own job was to pull them. With the real fill absent, the matcher fell through to each ticker's *prior, unrelated* trade:

| Ticker | qty_change | Stale reason shown | Why it was stale | Correct reason (from email) |
|---|---|---|---|---|
| IREN | 0→20 (2 fills) | stop-loss | last IREN row was the 07-31 stop-out exit | UNCAPTURED (both Market) |
| VRT | 0→3 | stop-loss | last VRT row was the 08-10 stop-out exit | UNCAPTURED (Market) |
| BE | 0→2.75 (2 fills) | stop-loss | last BE row was the 08-07 stop-out exit | UNCAPTURED (both Market) |
| GLW | 0→3 | stop-loss | last GLW row was the 08-06 stop-out exit | UNCAPTURED (Market) |
| MU | 2.000→2.500 | stop-loss | last MU row was the 08-05 trim/stop-loss | UNCAPTURED (Market) — also a qty INCREASE mislabeled with an exit-only reason |
| GEV | 1.005→2.005 | UNCAPTURED | last GEV row (08-12) happened to also be UNCAPTURED | UNCAPTURED — correct by coincidence, not by matching the right trade |
| COHR | 2→3 | re-entry-after-stop | last COHR row was the 08-12 buy, reason correctly captured for *that* trade, wrongly reused here | UNCAPTURED (Market) — this is a distinct, later fill |
| AMAT | 2.008→1.008 | deploy-excess-cash | last AMAT row was the 08-12 buy (a buy-side reason) | **stop-loss** (Order Type: stop) — the worst mislabel: a genuine stop-loss exit was hidden under a redeployment tag |

Fixing this properly requires the matcher to key on **date + direction**, not ticker alone. That change is in `scripts/smith_math.py`, outside smith-ledger's write surface (trades.json/lots.json/output only) — **flagged for the orchestrator/dev, not fixed here.** What I *did* fix: added the 10 missing trade rows to `trades.json`, correctly reasoned per Hard Rule 5, dated so that on the next run's ticker-only matching the newest (correct) row wins again — which resolves the symptom for these 8 tickers going forward, but the underlying bug will resurface any time a ticker's most recent trades.json reason predates a later differently-reasoned trade.

## 2. Gmail pull — `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/08/12`

25 threads, 26 messages, 1 page (resultCountEstimate 26, no pagination needed). Two messages were `is cancelled` (both META stop orders, 08-12T13:54:15Z and 08-12T15:39:49Z) — excluded per Hard Rule 4; each was immediately followed/preceded by a real manual SELL confirmation, already correctly recorded in trades.json with notes explaining the cancelled-stop-then-manual-sale pattern.

24 non-cancelled confirmations in the window. 16 of them (all dated 2026-08-12, AMAT/AMD/AMZN/AVGO/BABA/CIEN/COHR/MRVL/META×2/NBIS/NOW/STM/TSM/TXN) were **already** correctly recorded in trades.json from the prior run — spot-checked against email, all match (qty, price, reason). The remaining **10 confirmations, dated 2026-08-13/08-14, were missing** and are exactly the fills behind the 8 flagged qty_changes:

| Ticker | UTC time | Side | Shares | Price | Order Type | Amount |
|---|---|---|---|---|---|---|
| IREN | 2026-08-13T15:26:47Z | BUY | 10 | $46.38 | Market | $465.22 |
| BE | 2026-08-13T15:27:16Z | BUY | 2 | $244.11 | Market | $489.69 |
| GLW | 2026-08-13T15:35:47Z | BUY | 3 | $166.27 | Market | $500.29 |
| GEV | 2026-08-13T15:36:46Z | BUY | 1 | $1036.57 | Market | $1039.68 |
| VRT | 2026-08-13T15:37:12Z | BUY | 3 | $291.04 | Market | $875.75 |
| MU | 2026-08-13T16:27:59Z | BUY | 0.5 | $970.36 | Market | $486.63 |
| IREN | 2026-08-13T17:33:35Z | BUY | 10 | $44.82 | Market | $449.53 |
| AMAT | 2026-08-14T13:30:11Z | SELL | 1 | $499.24 | **stop** | $499.24 |
| COHR | 2026-08-14T13:39:11Z | BUY | 1 | $322.09 | Market | $323.06 |
| BE | 2026-08-14T16:27:14Z | BUY | 0.75 | $233.88 | Market | $175.94 |

All Shares/Price/Order Type read directly from the email body (Shares field explicit in every case — no derivation needed; MU, VRT, GEV, BE(08-14) needed a `get_thread` full-body pull since the search snippet truncated before Shares/Order Type). Every fill's total reconciles exactly to the compute_book qty_change (IREN 10+10=20, BE 2+0.75=2.75, GLW/GEV/VRT/MU/COHR each single-fill matches exactly, AMAT -1 matches exactly). Only AMAT's Order Type is literally `stop` — the sole row where `reason: "stop-loss"` is objectively supported; the other 9 are Market and stay `reason: "UNCAPTURED"` per Hard Rule 5.

**Write applied**: `trades.json` backed up (`.bak`, `.bak16`), 10 rows appended via `.tmp` → `mv`. `lots.json` backed up the same way; 9 new BUY lots added, 1 AMAT lot FIFO-consumed for the stop-loss sell (oldest-first: fully consumed the 07-15 dust lot of 0.009179sh @ $565.25, then 0.990821sh off the 07-28 lot @ $473.79, leaving 0.008179sh @ $473.79 + the untouched 08-12 lot of 1sh @ $548.24).

## 3. Invariant check — lots.json qty sum vs holdings.json qty (35 held tickers)

**31 of 35 reconcile exactly** (within 0.001sh) after this run's repair, including all 8 tickers that were the trigger for this run:

| Ticker | lots sum | holdings qty | delta |
|---|---|---|---|
| IREN | 20 | 20 | 0 |
| VRT | 3 | 3 | 0 |
| BE | 2.75 | 2.75 | 0 |
| GLW | 3 | 3 | 0 |
| GEV | 2.004951 | 2.004950742 | ~0 |
| MU | 2.500366 | 2.500365376 | ~0 |
| COHR | 3 | 3 | 0 |
| AMAT | 1.008179 | 1.0081785 | ~0 |

**4 remaining mismatches — unchanged, pre-existing (G68), not touched this run:**

| Ticker | lots sum | holdings qty | delta |
|---|---|---|---|
| AMD | 2.020631 | 2 | +0.020631 |
| QCOM | 13.000762 | 10.000761904 | +3.0 |
| MRVL | 7.008898 | 7 | +0.008898 |
| MSFT | 4.5 | 3 | +1.5 |

These four figures match G68's last-recorded values exactly (QCOM +3.0, MSFT +1.5, AMD +0.0206, MRVL +0.0089) — confirms the gap is stable, not worsening, and not caused by anything in this run's window.

## 4. Standing gaps — status report (no changes made; not re-running a full backfill)

**G68** (QCOM/MSFT/AMD/MRVL over-count): **unchanged, still open.** Re-verified against the current 803-row ledger — the same four tickers, same magnitudes as last measured. Not re-running a from-scratch 803-row FIFO backfill this run: the prior exhaustive 2026-07-24..07-27 pull already ruled out the obvious window, MSFT/AMD's fractional signature already points to a DRIP/fractional-share program email confirmations may not cover at all, and nothing in this run's 2026-08-12..08-14 window touches these four tickers — there is no new evidence to act on. Recommend a targeted MSFT/AMD DRIP-statement check (not a Gmail BUY/SELL search) as the next concrete step, owned by a future run.

**G70** (Pure Storage/Everpure rename): **unchanged, no live impact.** Neither PSTG/Everpure/P nor WDC/SNDK's pre-split identity appears in current holdings' lots keys — fully exited, key absent, consistent with convention. Pattern remains real for any future rename of a held name; ticker_map still lacks an effective-date dimension.

**G71** (GOOG→GOOGL share-class conversion): **unchanged, no live impact today.** Neither GOOG nor GOOGL is a current holding (both keys absent from lots.json — fully exited). The phantom-negative-FIFO artifact this gap describes is therefore dormant, not resolved; the same conversion-blind-spot would resurface the moment a share-class conversion touches a currently-held name. No conversion/corporate-action row type exists yet to fix this at the schema level — still needed, still not built.

## 5. Data quality notes

- The core finding of this run: `scripts/smith_math.py`'s qty_change reason-attachment (~L458-469) matches on ticker alone with last-write-wins, no date or direction check. This produced 8 nonsensical or wrong reason labels this run alone (4 impossible "stop-loss on an OPENING trade", 1 "stop-loss on a qty INCREASE", 1 stale reason reused across two different trades, 1 buy-side reason on a SELL that was masking a genuine stop-loss). This is a code fix outside smith-ledger's write surface — needs to key qty_changes to the specific trades.json row(s) dated within the reconciliation window, not the ticker's global last reason.
- All 10 newly-added rows are `price_source: "email_confirmed"` with Shares read directly from the email body (no derivation, no reconstruction) — consistent with the G64 mandate.
- No forged, cancelled-but-uncounted, or internally-inconsistent confirmations found in this window; the 2 cancelled META stop notifications were correctly excluded and were already correctly cross-referenced to real manual sales in the existing trades.json rows.

## Files touched

- `/Users/yb/Claude/AgentSmith/trades.json` (793 → 803 rows; `.bak` and `.bak16` backups written before edit)
- `/Users/yb/Claude/AgentSmith/lots.json` (9 lots added across IREN/VRT/BE/GLW/GEV/MU/COHR, 1 AMAT lot FIFO-consumed; `.bak` and `.bak16` backups written before edit)
- `/Users/yb/Claude/AgentSmith/runs/2026-08-15-1809/smith-ledger-output.md` (this file)

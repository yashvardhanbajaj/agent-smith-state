# SMITH-LEDGER reconciliation — PM follow-up, run 2026-08-19-1105

**Window:** since this morning's 11:05 IST run through 2026-08-19T22:00 IST (~12:30 ET, US cash session still open). Query `from:transactions.indmoney.com subject:(BUY OR SELL) after:2026/08/18`, pageSize 50 — 28 threads, single page, no `nextPageToken`. 1 cancellation excluded per Hard Rule 4 (LRCX SELL, cancelled 2026-08-19T19:09:19Z — no fill followed it; LRCX's holding qty is unchanged at 3sh, confirming nothing was double-counted or missed).

## TASK 1 — verify yesterday's stop cascade

Re-checked trades.json directly (not re-derived): all **10 stop rows dated 2026-08-18** (MRVL, AVGO, MU, TER, ARM, DRAM, IONQ, NBIS, ORCL, SKHY) are present, each with `price_source: "email_confirmed"` and `order_type: "stop"`, matching their original message IDs exactly — no duplicates, no degraded fields. The SNDK market sell is correctly dated **2026-08-17** (not 08-18 — it was the prior run's own finding that this fill was Monday-evening and NOT part of the Tuesday cascade; today's re-check confirms that dating is still correct and unchanged). Total 2026-08-18-dated rows: 10, as expected. **Intact and complete — nothing to repair.**

## TASK 2 — two new disposals

**ASML: CONFIRMED stop-loss**, not merely suspected. Email `1a01a487a8d43ca8`, 2026-08-19T13:49:12Z: SELL 1sh, Price $1774.69, Amount $1774.69, **Order Type: stop**. Position 1.000001151 → 0.000001151sh (the residual predates today — the pre-run ledger lot was carrying a flat `1.0` while the broker held `1.000001151`, the same class of sub-microshare display-rounding residue already documented for SNDK/MU/TER; FIFO consumed the ledger's full 1.0sh lot, leaving 0 lots against a 0.000001151 broker balance, absorbed by the reconciliation script's 1e-4 tolerance).

**No other disposal today.** The only other SELL-subject thread in the window was the LRCX cancellation (excluded, not a fill). Every other thread was a BUY.

## TASK 3 — today's buys: 16 order rows across 14 tickers, $10,368.04 total

Two tickers had **two separate fills** each — recorded as separate rows per Hard Rule 3, never averaged into the diff-based implied numbers the orchestrator supplied as approximations:
- **AVGO**: 1sh @ $364.34 (19:06:17Z) + 1sh @ $364.87 (18:43:31Z) = 2sh, $731.40
- **BE**: 2sh @ $202.02 (18:47:26Z) + 2sh @ $201.25 (18:39:53Z) = 4sh, $808.96

| Ticker | Qty | Fill price | USD amount | Reason | Re-entry (stopped in last 7d)? |
|---|---|---|---|---|---|
| WDC | 2 | $461.84 | $926.45 | dca-into-diversification | No — new position |
| GOOG | 3 | $341.11 | $1,026.39 | dca-into-diversification | No — new position |
| META | 2 | $546.50 | $1,096.26 | **re-entry-post-raise-cash** (see deviation below) | Re-entry, but prior exit (2026-08-12) was a deliberate raise-cash sale, NOT a stop |
| NBIS | 4 | $217.88 | $874.13 | re-entry-after-stop | **Yes** — stopped out 2026-08-18 ($259.90), re-entered 1 day later 16.2% lower |
| TER | 2 | $378.71 | $759.69 | re-entry-after-stop | **Yes** — reduced to 0.00273sh dust by 2026-08-18 stop, rebuilt 1 day later |
| GLW | 3 | $150.85 | $453.91 | dca-into-diversification | No — add (3→6sh) |
| INTC | 7 | $93.12 | $653.79 | dca-into-diversification | No — add (5→12sh) |
| AVGO | 1 | $364.34 | $365.43 | dca-into-diversification | No — add, fill 1/2 |
| AVGO | 1 | $364.87 | $365.97 | dca-into-diversification | No — add, fill 2/2 |
| AMAT | 1 | $493.01 | $494.48 | dca-into-diversification | No — add (1.008→2.008sh) |
| BE | 2 | $202.02 | $405.25 | dca-into-diversification | No — add, fill 1/2 |
| BE | 2 | $201.25 | $403.71 | dca-into-diversification | No — add, fill 2/2 |
| STM | 10 | $50.68 | $508.27 | dca-into-diversification | No — add (20→30sh) |
| VRT | 2 | $261.81 | $525.18 | dca-into-diversification | No — add (3→5sh) |
| COHR | 2 | $285.61 | $572.94 | dca-into-diversification | No — add (3→5sh) |
| MU | 1 | $933.39 | $936.19 | dca-into-diversification | No — add (0.500→1.500sh) |

**Total: $10,368.04** across 16 fills / 14 tickers (orchestrator's diff-based estimate was ~$10,329.70 — the ~$38 gap is exactly the expected slippage between an Amount-delta approximation and confirmed fills, now closed).

### Reason-label deviation: META

The task brief grouped META with NBIS/TER under a blanket instruction to use `re-entry-after-stop` for all three. I did **not** apply that to META. The existing trades.json row for META's 2026-08-12 full exit reads `reason: "raise-cash"`, explicitly user-confirmed interactively at the time, with the note "META's thesis therefore REMAINS INTACT... the position was closed for liquidity, not conviction." Labelling today's re-entry `re-entry-after-stop` would assert a stop-loss motive the ledger's own prior record contradicts — exactly the kind of unlabelled guess this desk exists to prevent (Hard Rule 1 / Hard Rule 5). Used `re-entry-post-raise-cash` instead: still flags the round-trip, doesn't fabricate the trigger. Order Type was Market either way, so nothing here contradicts the literal field.

## Write safety

- `trades.json` → `trades.json.bak` (copy2, pre-edit 831-row state) → `trades.json.tmp` written → `os.replace`. 17 rows appended (1 ASML sell + 16 buys); total now 848.
- `lots.json` → rebuilt via `scripts/smith_math.py lots --base-dir . --write` (engine's own tmp+`os.replace`, atomic). **Note:** the engine itself doesn't create a `.bak`, so I separately reconstructed the exact pre-this-run lots.json (by re-running the same FIFO engine against `trades.json.bak` + this morning's holdings snapshot) and installed that as `lots.json.bak` — a faithful backup of the immediate-prior state, not a stale one.
- Dry run confirmed clean (0 mismatches) before the real `--write` was invoked.

## FIFO rebuild & invariant check

Ran over the **full** trade history (848 rows) against a fresh 32-ticker holdings snapshot pulled live via `networth_holdings(US_STOCK)` this run (`/private/tmp/.../scratchpad/holdings_pm.json`) — not the stale 11:05 pre-open snapshot.

- **32/32 held tickers reconciled** (script's own tolerance check): 0 mismatches, 0 orphaned positions, 0 phantom shorts.
- Book count 28 → 32 confirmed: +WDC, +GOOG, +META, +NBIS (all four were at zero qty as of this morning, now non-zero).
- ASML's ledger-side lot fully consumed to 0 (no residual key) against a 0.000001151 broker balance — same sub-microshare display-rounding class as pre-existing SNDK/MU/TER residuals, within the script's 1e-4 tolerance, immaterial (~$0.002 notional).
- Pre-existing G80 residue (24 rows predating 2026-08-15) unchanged, informational only — no new relapse rows.

## Unresolved

None. All 28 threads in the window were either resolved to a confirmed fill or correctly excluded as a cancellation.

```json
{"reconciled_range": {"since": "2026-08-19T05:35:00Z", "until": "2026-08-19T16:30:00Z"},
 "confirmations_found": 28, "rows_added": 17, "rows_corrected": 0, "rows_quarantined": 0,
 "corrections": [],
 "invariant_check": {"tickers_ok": 32, "mismatches": []},
 "unresolved": [],
 "data_quality": [
   "META reason deliberately labelled 're-entry-post-raise-cash' rather than the orchestrator's suggested 're-entry-after-stop' -- its 2026-08-12 exit was reason='raise-cash', user-confirmed, thesis explicitly INTACT at the time, not a stop-loss. Applying the blanket instruction would have fabricated a motive the ledger's own prior row contradicts.",
   "ASML's ledger lot (flat 1.0sh) fully FIFO-consumed by today's 1sh stop sell, leaving 0 lots against a 0.000001151 broker residual -- same sub-microshare display-rounding class as pre-existing SNDK/MU/TER residuals, within reconciliation tolerance, ~$0.002 notional, not a new defect.",
   "AVGO and BE each had TWO separate order confirmations today (1sh+1sh and 2sh+2sh respectively) that the orchestrator's diff-based estimate had implicitly summed into one number -- recorded as 4 distinct rows per Hard Rule 3, never averaged.",
   "LRCX SELL cancelled 2026-08-19T19:09:19Z, excluded per Hard Rule 4 -- LRCX holding qty unchanged at 3sh, confirms no fill was missed or double-counted.",
   "NBIS and TER are same-week round trips: both were stopped out 2026-08-18 and re-bought 2026-08-19, one trading day later, at lower prices -- flagged for the desk's attention, not evaluated for merit here."
 ]}
```

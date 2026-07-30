# Watchlist & Market Context — 2026-07-30 (quick sweep)

## 1. Watchlist setups (rotating slice: indices 90-104 of 129 unique US names, cursor 90->105)
Scanned: MSFT, META, SOXX, EWT, FRNW, BAM, INDA(skip-India), CNXT, TINY, VDE, FLNG, CCEC, RTX, SIL, URNM.
ETFs (SOXX/EWT/FRNW/CNXT/TINY/VDE/SIL/URNM/CCEC) carry no analyst target — no setup computable, silence.

- **META** — watchlist — OVERSOLD BOUNCE: pos 0.05 (52wk range $520.26-$796.25, price $532.70), mean target $824.68, upside +35.4%. Q2 EPS/net income missed despite $60.8B revenue beat; stock -9.0% today (AH -11% yesterday), now $12 above its 52-wk low even as SMH rallies +6.9% — idiosyncratic washout, not beta-driven. Analysts still 88% buy. Standout reversal candidate.
- **BAM** — watchlist — OVERSOLD BOUNCE: pos 0.23 (range $42.20-$64.10, price $47.31), mean target $56.30, upside +16.0%. Positive catalysts: $100B NextEra Kentucky data-center JV, $16B KPC pipeline lease, $7B Aypa Power (battery storage) acquisition. Q2 results due Aug 5.
- **MSFT** — watchlist — TARGET GAP: pos 0.48, mean target $557.25, upside +19.5%. +14.9% today on Azure >$100B annualized run-rate beat — note the rally has already consumed part of the gap; not a washout entry.
- **COHR** — watchlist — TARGET GAP: pos 0.45, mean target $391.45, upside +37.8%. +9.7% today in the SMH rally; Datacenter segment +40.6% YoY. Earnings Aug 5 still unconfirmed.

Washout-reversal read: META is the one name where today's SMH rally has NOT erased the entry — it's still near its 52-wk low on idiosyncratic earnings-reaction selling. BAM is a secondary, less dramatic washout. Elsewhere in this slice (RTX pos 0.85, ETFs with no target data) the rally already priced out any oversold entry.

## 2. Earnings calendar
Held, within 7-day quick window:
- AMD — 2026-08-04, confirmed (unchanged)
- COHR — 2026-08-05, still unconfirmed (no dedicated web check this run — below the ≥3%-weight WebFetch trigger; budget-conscious)

Held, already reported this week (rolling forward — no longer upcoming, cache updated to "reported"):
- LRCX — reported 2026-07-29: record $6.72B revenue, AI-demand beat, stock +20.3% today
- QCOM — reported 2026-07-29: Q3 mixed (rev beat/EPS miss), Apple modem-revenue concern, stock -3.7% today
- VRT — reported 2026-07-29: EPS beat/revenue miss, stock recovering +3.1% today after the post-earnings drop
- CLS — reported 2026-07-28: Q2 beat, raised outlook, stock +5.6% today
- TER — reported 2026-07-29: Q2 beat, stock +10.6% today
Next report dates for all five are not yet scheduled/confirmed — do not guess, re-check closer to next quarter.

Context only (not held) — hyperscaler/AI-capex read-across:
- AAPL — reports today 2026-07-30, confirmed (unchanged)
- AMZN — reports today 2026-07-30, confirmed (unchanged)
- MSFT (watchlist) — reported 2026-07-29, Azure beat, +14.9% today — bullish capex signal
- META (watchlist) — reported 2026-07-29, Q2 miss despite revenue beat, -9.0% today — capex-spend-vs-monetization concern, worth watching for read-through to NVDA/AVGO/AMD capex sentiment

## 3. Data notes
- compute_attribution.json treated as ground truth (no recompute): value_delta +$2,433.87, fx -$11.11, flow -$6.88 (noise), residual market move +$2,451.87 — consistent with today's SMH +6.9% relief rally.
- Rolling 1/3/6/12m windows remain null — only 18 ledger rows, insufficient history (unchanged known gap).
- INDA (India ETF) appeared in rotation slice but excluded from setup output per US-only scope.

```json
{"watchlist_setups":[{"ticker":"META","type":"oversold_bounce","upside_pct":35.4,"pos":0.05},{"ticker":"BAM","type":"oversold_bounce","upside_pct":16.0,"pos":0.23},{"ticker":"MSFT","type":"target_gap","upside_pct":19.5,"pos":0.48},{"ticker":"COHR","type":"target_gap","upside_pct":37.8,"pos":0.45}],
 "earnings_calendar_updates":{"LRCX":{"date":"2026-07-29","confirmed":true,"source":"reported"},"QCOM":{"date":"2026-07-29","confirmed":true,"source":"reported"},"VRT":{"date":"2026-07-29","confirmed":true,"source":"reported"},"CLS":{"date":"2026-07-28","confirmed":true,"source":"reported"},"TER":{"date":"2026-07-29","confirmed":true,"source":"reported"}},
 "watchlist_scan_cursor":105,
 "data_quality":["COHR earnings date (Aug 5, within window) remains unconfirmed by INDmoney/yfinance; no dedicated web check run this pass (below weight-threshold trigger)","Next earnings dates for LRCX/QCOM/VRT/CLS/TER not yet scheduled — will re-check next run","ETF names in this rotation slice (SOXX/EWT/FRNW/CNXT/TINY/VDE/SIL/URNM/CCEC) have no analyst target data, so no setup could be computed for them"]}
```

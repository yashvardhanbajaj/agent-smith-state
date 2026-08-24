# Watchlist & Market Context — 2026-08-24 (deep, pre-open, gate ESCALATING)

## 1. Watchlist setups (US only, entry setups — cursor 0-14 of full list)

- watchlist RGTI (Rigetti Computing) — OVERSOLD BOUNCE — pos 0.12, mean target $28.81, upside 37.8%
- watchlist QBTS (D-Wave Quantum) — OVERSOLD BOUNCE — pos 0.23, mean target $35.25, upside 42.2%
- watchlist IONQ (IonQ) — TARGET GAP — pos 0.32, mean target $67.68, upside 33.7%
- watchlist IREN (IREN) — TARGET GAP — pos 0.41, mean target $81.73, upside 48.8% (fully exited from holdings this run per G82 note; now the widest gap on the re-scanned slice)
- watchlist STX (Seagate) — TARGET GAP — pos 0.70, mean target $1115.87, upside 23.8%
- watchlist APH (Amphenol) — TARGET GAP — pos 0.71, mean target $198.06, upside 20.7%
- watchlist GOOGL (Alphabet Class A) — TARGET GAP — pos 0.70, mean target $427.52, upside 19.3%
- watchlist DDOG (Datadog) — TARGET GAP — pos 0.71, mean target $285.18, upside 17.4%
- watchlist AEP (American Electric Power) — TARGET GAP — pos 0.44, mean target $144.95, upside 16.6%

No setup: MRNA (pos 1.0 but analyst mean target is *below* live price, upside -185% — chasing a gap-up with no valuation support, excluded), ETN (upside 12.0%, below threshold), RIO (pos 0.86, upside 0.5%, only 2 analysts — no setup). CQQQ/MCHI/FPXI are ETFs with no analyst target — silent by design.

Scanned this run (cursor 0-14, 15 non-held names): MRNA, STX, GOOGL, IONQ, RGTI, QBTS, CQQQ, MCHI, FPXI, APH, RIO, DDOG, ETN, IREN, AEP. Cursor advances to 15 for the next run; roughly 95 more non-held watchlist names remain across the three lists before a full wrap.

## 2. Earnings calendar (holdings within 14 days, deep mode)

- NVDA — 2026-08-26 — CONFIRMED. Cache already had this (reconfirmed 08-20); re-verified today via INDmoney news dated 2026-08-24 ("Nvidia is set to release quarterly earnings... market focus on growth guidance and margins").
- MRVL — 2026-08-27 — CONFIRMED. Re-verified via INDmoney news dated 2026-08-12 ("Marvell Technology is set to report its Q2 earnings on August 27").
- AVGO — 2026-09-02 — CONFIRMED. Within the 14-day window; re-verified via INDmoney news dated 2026-08-03 ("Broadcom... will announce its Q3 FY26 financial results on September 2, 2026").
- BX (re-entered 2026-08-24, 3.73% weight, no prior cache entry) — UNCONFIRMED / not imminent. INDmoney news shows Q2 already reported ~2026-07-23/07-30 (distributable earnings +26%). No Q3 date surfaced in available news; not expected inside the 14-day window based on typical cadence. Not gating — flagged as a gap for a future run rather than spending a WebFetch on a name that isn't close to reporting.
- yfinance get_earnings_calendar returned an empty result for the 2026-08-24→2026-09-10 window; relied on INDmoney news corroboration for the three dates above instead.

No verdict language used above — dates and confirmation status only; beat/miss characterization belongs to smith-earnings.

## 3. Data quality / cache hygiene

- COHR cache entry (2026-08-12, confirmed) is stale — COHR fully exited from holdings; recommend the orchestrator drop it.
- HUBB and MP cache entries are also orphaned — neither held nor present on any of the three watchlists; recommend pruning in the same pass.
- BX (re-entered today) has no earnings_calendar entry yet; see section 2 — not urgent, next date unconfirmed.
- RIO's analyst consensus is thin (2 analysts) — upside/target treated as low-confidence, correctly excluded from setups.
- Watchlist scan this run covered only cursor 0-14; full-list coverage will take several more runs.

```json
{"watchlist_setups":[
 {"ticker":"RGTI","type":"OVERSOLD_BOUNCE","upside_pct":37.83,"pos":0.12},
 {"ticker":"QBTS","type":"OVERSOLD_BOUNCE","upside_pct":42.16,"pos":0.23},
 {"ticker":"IONQ","type":"TARGET_GAP","upside_pct":33.72,"pos":0.32},
 {"ticker":"IREN","type":"TARGET_GAP","upside_pct":48.76,"pos":0.41},
 {"ticker":"STX","type":"TARGET_GAP","upside_pct":23.83,"pos":0.70},
 {"ticker":"APH","type":"TARGET_GAP","upside_pct":20.73,"pos":0.71},
 {"ticker":"GOOGL","type":"TARGET_GAP","upside_pct":19.34,"pos":0.70},
 {"ticker":"DDOG","type":"TARGET_GAP","upside_pct":17.38,"pos":0.71},
 {"ticker":"AEP","type":"TARGET_GAP","upside_pct":16.56,"pos":0.44}
],
 "earnings_calendar_updates":{
   "NVDA":{"date":"2026-08-26","confirmed":true,"source":"indmoney-news reconfirmed 2026-08-24"},
   "MRVL":{"date":"2026-08-27","confirmed":true,"source":"indmoney-news reconfirmed 2026-08-24 (article 08-12)"},
   "AVGO":{"date":"2026-09-02","confirmed":true,"source":"indmoney-news reconfirmed 2026-08-24 (article 08-03)"}
 },
 "watchlist_scan_cursor":15,
 "data_quality":[
   "COHR cache entry stale -- fully exited holding, recommend drop",
   "HUBB and MP cache entries orphaned -- not held, not on any watchlist, recommend prune",
   "BX (re-entered 08-24, 3.73% wt) has no earnings_calendar entry; next date unconfirmed, not within 14-day window per available news",
   "yfinance get_earnings_calendar returned empty for 08-24..09-10 window; used indmoney-news corroboration instead",
   "RIO watchlist quote has only 2 covering analysts -- low-confidence target, excluded from setups"
 ]}
```

# Watchlist & Market Context — 2026-08-06 (quick)

## 1. Watchlist entry setups (US only, non-held names, scan slice: cursor 0-15 of Watchlist 1)

- watchlist IONQ — OVERSOLD BOUNCE — pos 0.25 (40.35 vs 25.89-84.64 52w range), mean target $67.02, upside 39.8%. Q2 earnings due, $15M quantum-comms center w/ EPB, Sandia MOU — positive.
- watchlist RGTI — OVERSOLD BOUNCE — pos 0.09 (16.72 vs 12.53-58.15), mean target $29.65, upside 43.6%. HPE collab + NSF grant, 90% analyst buy-rated.
- watchlist APH — NEARING BREAKOUT — pos 0.93 (173.34 vs 104.71-178.52), catalyst: Q2 beat, raised Q3 guidance, Barclays PT hike to $198 on AI/CommScope demand. Upside 12.5%.
- watchlist ETN — NEARING BREAKOUT — pos 0.99 (450.13 vs 311.92-451.96), catalyst: Q2 EPS beat ($3.15), raised FY26 guidance, analyst upgrades on electrification demand. Upside 1.7%.
- watchlist FLEX — TARGET GAP — mean target $160.50, upside 22.1%. Q4 beat, raised FY guidance on data-center/AI infrastructure investment.
- watchlist IREN — TARGET GAP — mean target $81.73, upside 52.3%. $2.8B new AI cloud contracts (85% of revenue target already under contract), Anthropic data-center chatter. Note: -4.5% today, pos 0.38 (not oversold-bounce territory but a large gap).
- watchlist LNG — TARGET GAP — mean target $304.14, upside 15.6%. Board strengthened (ex-McKesson CFO), 92% buy-rated, $330 street high.

No setups on: HOOD (pos 0.33, mixed sentiment, HOLD-rated), RIO/AEP/DLR (upside <15%, no position extreme), CQQQ/MCHI/FPXI (ETFs, no analyst target). DDOG (pos 0.99) excluded — mean target is BELOW current price (-6.9%), not a genuine entry setup despite technical position.

## 2. Earnings calendar — holdings within 6 trading days (through ~2026-08-13)

CONFIRMED:
- QBTS — 2026-08-06 — confirmed (source: stockanalysis.com, "Q2 2026 results"). Imminent — reports tomorrow.
- CEG — 2026-08-06 — source: stockanalysis.com; date shown but confirmation language ambiguous on page. Treat as high-confidence, not fully certain.
- COHR — 2026-08-12 — confirmed (carried from 08-03 correction; stale 08-05 date superseded).

UNCONFIRMED (yfinance reportedDate + ~91d heuristic only; FMP earnings-calendar range endpoint for 08-05→08-14 did not list these names — coverage gap, not a contradiction):
- MP — est. ~2026-08-06 — new position, unconfirmed. Flag for next run's WebFetch confirmation.
- AMAT — est. ~2026-08-13 — unconfirmed.
- NBIS — est. ~2026-08-12 — unconfirmed.
- BABA — est. ~2026-08-12 — unconfirmed.
- MKSI — est. ~2026-08-05 (already elapsed) — likely reports imminently or has a data lag; unconfirmed.

All other 24 holdings: last-reported + ~91d estimate falls outside the 6-trading-day window (next cluster is NVDA ~08-19, then Sept/Oct wave).

```json
{"watchlist_setups":[{"ticker":"IONQ","type":"oversold_bounce","upside_pct":39.8,"pos":0.25},
 {"ticker":"RGTI","type":"oversold_bounce","upside_pct":43.6,"pos":0.09},
 {"ticker":"APH","type":"nearing_breakout","upside_pct":12.5,"pos":0.93},
 {"ticker":"ETN","type":"nearing_breakout","upside_pct":1.7,"pos":0.99},
 {"ticker":"FLEX","type":"target_gap","upside_pct":22.1,"pos":0.65},
 {"ticker":"IREN","type":"target_gap","upside_pct":52.3,"pos":0.38},
 {"ticker":"LNG","type":"target_gap","upside_pct":15.6,"pos":0.61}],
 "earnings_calendar_updates":{"QBTS":{"date":"2026-08-06","confirmed":true,"source":"web"},
 "CEG":{"date":"2026-08-06","confirmed":true,"source":"web"},
 "COHR":{"date":"2026-08-12","confirmed":true,"source":"cache"},
 "MP":{"date":"2026-08-06","confirmed":false,"source":"yfinance_est"},
 "AMAT":{"date":"2026-08-13","confirmed":false,"source":"yfinance_est"},
 "NBIS":{"date":"2026-08-12","confirmed":false,"source":"yfinance_est"},
 "BABA":{"date":"2026-08-12","confirmed":false,"source":"yfinance_est"},
 "MKSI":{"date":"2026-08-05","confirmed":false,"source":"yfinance_est"}},
 "watchlist_scan_cursor":15,
 "data_quality":["CEG earnings date sourced via stockanalysis.com WebFetch; page did not explicitly label it 'confirmed' vs estimated — treat as high-confidence not certain.","FMP earnings-calendar range endpoint (08-05→08-14) returned only 10 market-wide rows and omitted QBTS/CEG/COHR/MP/AMAT/NBIS/BABA entirely — endpoint coverage is sparse for these names this window, not evidence against the dates found elsewhere.","MP, AMAT, NBIS, BABA, MKSI earnings dates are yfinance +91-day heuristic estimates only, not confirmed by any calendar source — do not treat as firm.","SNDK's cached quarterly history shows an implied next-report date of 2026-07-30 already elapsed with no newer quarter reflected — yfinance earnings history may be lagging for SNDK.","get_us_stocks_details 10-symbol batch cap required splitting the 15-name watchlist slice into two calls."]}
```

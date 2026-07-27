# Watchlist & Market Context — 2026-07-27 (deep)

## Watchlist Scan (slice: idx 60-74, cursor advanced 60→75)
Scanned: UMC, TSM, MCHP, SNDK, TER, PATH, APLD, GEV, AMZN, CRWV, INTC, GOOG, MU, CORZ, AAPL

- watchlist | PATH OVERSOLD BOUNCE: pos 0.15 (52wk 9.20-19.84), +6.3% today on strong Q1 AI-automation demand, guidance raised. Mean target $13.25, upside 18.2%.
- watchlist | CRWV OVERSOLD BOUNCE: pos 0.09 (52wk 63.80-153.20), -11.4% on Meta-competition fears but news flow positive (multi-analyst upgrades, $8.5B financing, ~$100B backlog). No structured target (analyst_forecast empty) — news cites ~79% upside, unverified structured field.
- watchlist | AAPL NEARING BREAKOUT: pos 0.985 (52wk 201.50-334.99), new 52wk high, +3.5% today. Catalyst: FQ3 earnings 2026-07-30, $100B buyback, HSBC upgrade. Mean target $318.81 (below spot — momentum/breakout play, not value gap).
- watchlist | MU TARGET GAP: mean target $1507.38 vs $920.95, upside 38.9%. Musk/Tesla chip-allocation news 26-Jul positive.
- watchlist | APLD TARGET GAP: mean target $73.05 vs $27.19, upside 62.8% (13 analysts, BUY).
- watchlist | CORZ TARGET GAP: mean target $33.36 vs $22.75, upside 31.8%.
- watchlist | MCHP TARGET GAP: mean target $113.08 vs $78.86, upside 30.3%.
- watchlist | TSM TARGET GAP: mean target $537.43 vs $403.41, upside 24.9%.
- watchlist | GOOG TARGET GAP: mean target $421.79 vs $319.09, upside 24.4%.
- watchlist | INTC TARGET GAP: mean target $115.65 vs $92.32, upside 20.2% (consensus HOLD — note mixed sentiment despite gap).
- watchlist | TER TARGET GAP: mean target $429.88 vs $349.92, upside 18.6%.
- watchlist | GEV TARGET GAP: mean target $1233.10 vs $1014.75, upside 17.7%.
- No setup: UMC (upside -19.9%, pos 0.58), SNDK (no analyst_forecast data returned — cannot confirm target).

## Earnings Calendar (holdings, ≤14 days)
- LRCX: 2026-07-29, confirmed (source: web) — cached, still future, no re-check needed.
- TER: 2026-07-28, confirmed (source: web) — cached, still future.
- QCOM: 2026-07-29, confirmed (source: news) — cached, still future.
- GLW: fully exited — dropped from active calendar per orchestrator note.
- GOOG: cached date 2026-07-22 has passed; no new date surfaced in this run's news pull (out of scope of 15-name slice fetched). Not re-verified.
- AAPL: news (27-Jul) reports FQ3 earnings 2026-07-30 — added below if AAPL is held; unverified whether AAPL is a current holding in this agent's scope.

```json
{"watchlist_setups":[
  {"ticker":"PATH","type":"oversold_bounce","upside_pct":18.2,"pos":0.15},
  {"ticker":"CRWV","type":"oversold_bounce","upside_pct":null,"pos":0.09},
  {"ticker":"AAPL","type":"nearing_breakout","upside_pct":-4.46,"pos":0.985},
  {"ticker":"MU","type":"target_gap","upside_pct":38.9,"pos":0.71},
  {"ticker":"APLD","type":"target_gap","upside_pct":62.78,"pos":0.425},
  {"ticker":"CORZ","type":"target_gap","upside_pct":31.8,"pos":0.568},
  {"ticker":"MCHP","type":"target_gap","upside_pct":30.26,"pos":0.529},
  {"ticker":"TSM","type":"target_gap","upside_pct":24.94,"pos":0.704},
  {"ticker":"GOOG","type":"target_gap","upside_pct":24.35,"pos":0.604},
  {"ticker":"INTC","type":"target_gap","upside_pct":20.17,"pos":0.594},
  {"ticker":"TER","type":"target_gap","upside_pct":18.6,"pos":0.654},
  {"ticker":"GEV","type":"target_gap","upside_pct":17.71,"pos":0.728}
],
 "earnings_calendar_updates":{"AAPL":{"date":"2026-07-30","confirmed":true,"source":"news"}},
 "watchlist_scan_cursor":75,
 "data_quality":["SNDK and CRWV returned empty analyst_forecast — no structured target/upside; CRWV's cited 79% upside is from a news snippet, not a verified field.","AAPL earnings date sourced from news only — unconfirmed whether AAPL is currently held; orchestrator should cross-check against holdings rows before persisting.","GOOG cached earnings date (2026-07-22) has passed; next date not re-verified this run (outside the 15-name rotation slice and budget).","INTC target-gap upside (20.2%) conflicts with consensus HOLD rating and 66.7% hold-weighted sentiment — flagging the tension, not discarding."]}
```

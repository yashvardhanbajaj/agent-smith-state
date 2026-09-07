# Watchlist & Market Context — 2026-09-07 (deep)

## 1. Watchlist setups (scan slice: cursor 15-29, 15 names incl. 1 ETF/1 private skipped)

- **CBRS** (Cerebras) — watchlist — NEARING BREAKOUT: $210.05, at new 52w high today (+10.3%, CS-4 launch/AWS-OpenAI partnership news). Mean target $296 (10 analysts, 100% buy) → upside 40.9%. Also clears TARGET GAP threshold. Caveat: 52w-low field returned 0 (recent listing, pos calc not meaningful beyond "at high").
- **DLR** (Digital Realty) — watchlist — TARGET GAP: mean target $223.32 (25 analysts) vs $188.39 → upside 15.6%. FFO estimates revised up, new Singapore data-center win.
- **FLEX** (Flex Ltd) — watchlist — TARGET GAP: mean target $158.33 (8 analysts) vs $109.51 → upside 30.8%. $4.4B EPC Power acquisition (AI data-center/grid power) announced 09-03.
- **IREN** — watchlist — TARGET GAP: mean target $77.84 (10 analysts) vs $44.68 → upside 42.6%. pos 0.37 (just above oversold line). News mixed (AI-cloud growth positive, Q4 net loss/debt concerns negative).
- **MRVL** (also a current holding) — watchlist — TARGET GAP: mean target $285 (26 analysts) vs $223.55 → upside 21.6%. Record Q2, raised outlook, Google/AWS deals; some analyst caution on valuation.
- **ORCL** — watchlist — OVERSOLD BOUNCE: pos 0.19 (down 21.6% YTD, near 52w range low end) + mean target $242.05 (32 analysts) vs $158.78 → upside 34.4%. Recent news split (credit downgrade/capex concerns vs BofA Buy reiteration, HPE AI-infra tie-up) — upside alone clears the 15% bar.
- **SMR** (NuScale) — watchlist — OVERSOLD BOUNCE: pos 0.05, mean target $12.63 (13 analysts, mostly hold) vs $9.70 → upside 23.2%. News net negative (CFO share sales, Q2 revenue miss) — flagged on the upside/oversold combination only, not on sentiment.
- **LEU** (Centrus Energy) — watchlist — OVERSOLD BOUNCE + TARGET GAP: pos 0.10, mean target $248.28 (15 analysts) vs $173.89 → upside 30.0%. Stock down sharply from 52w high ($464→$174); recent news negative (delayed HALEU deliveries).
- **VST** (Vistra) — watchlist — OVERSOLD BOUNCE: pos 0.19, mean target $217.42 (16 analysts, 100% buy) vs $149.30 → upside 31.3%. Peter Thiel disclosed $59M stake 09-03; Q2 revenue miss but EBITDA +31% and full-year guidance reaffirmed.

No setup: AEP (upside 13.5%, pos 0.54), ETN (upside 13.6%, pos 0.60), LNG (upside 5.5%), NOW (upside -0.05%). SPCX skipped (not a tradable public ticker); EEMA skipped (ETF, not an entry-setup candidate).

Coverage note: no prior-run setup list was supplied in this run's inputs, so re-scan of previously-flagged names could not be performed — only the rotating cursor slice above was scanned.

## 2. Earnings calendar (holdings, next 14 days: 2026-09-07 to 2026-09-21)

yfinance market-wide earnings calendar for this window returned zero results — consistent with the seasonal lull between Q2 (ended Aug) and Q3 (starts mid-Oct) reporting seasons. Cross-checked against the cached `earnings_calendar`: every cached date for a current holding (LRCX, GOOG, TER, QCOM, AAPL, AMZN, AMD, CLS, VRT, MRVL, AVGO, GEV, CEG, VST, ETN, NVDA, AMAT, NBIS, BABA, CIEN) is either already reported or falls after 2026-09-21 (GOOG/GEV both 2026-10-21). No confirmed or estimated earnings date for any current holding falls inside the 14-day window. No updates needed to the cache this run.

Uncached holdings with no near-term date on file (ASML, BE, STM, ALAB, MU, INTC, COHR, KLAC, WDC, IREN, SKHY, LITE, APH, FSLR, SMCI, GLW, MSFT) were not individually re-verified — their last reports were all in the July/August window and a 14-day lookahead lull is consistent with normal quarterly cadence; none is flagged as a ≥3% weight name with an unresolved near-term date (the LRCX-case trigger), so no direct-source WebFetch was spent this run.

```json
{"watchlist_setups":[
  {"ticker":"CBRS","type":"nearing_breakout+target_gap","upside_pct":40.9,"pos":1.0},
  {"ticker":"DLR","type":"target_gap","upside_pct":15.6,"pos":0.68},
  {"ticker":"FLEX","type":"target_gap","upside_pct":30.8,"pos":0.50},
  {"ticker":"IREN","type":"target_gap","upside_pct":42.6,"pos":0.37},
  {"ticker":"MRVL","type":"target_gap","upside_pct":21.6,"pos":0.60},
  {"ticker":"ORCL","type":"oversold_bounce","upside_pct":34.4,"pos":0.19},
  {"ticker":"SMR","type":"oversold_bounce","upside_pct":23.2,"pos":0.05},
  {"ticker":"LEU","type":"oversold_bounce+target_gap","upside_pct":30.0,"pos":0.10},
  {"ticker":"VST","type":"oversold_bounce","upside_pct":31.3,"pos":0.19}
],
 "earnings_calendar_updates":{},
 "watchlist_scan_cursor":30,
 "data_quality":["CBRS 52w-low returned 0 (likely recent listing) -- pos/oversold math not meaningful for this name beyond 'at 52w high'","No prior-run setup list was in this run's inputs, so existing setups from prior runs were not re-verified this run","Uncached holdings (ASML, BE, STM, ALAB, MU, INTC, COHR, KLAC, WDC, SKHY, LITE, APH, FSLR, SMCI, GLW, MSFT) not individually re-checked for earnings dates -- inferred no near-term date from normal quarterly cadence and the empty yfinance calendar window, none is a ≥3% LRCX-style unresolved case"]}
```

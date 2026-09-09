# Watchlist & Market Context — 2026-09-09 (quick, pre-open)

## 1. Watchlist setups

Re-scanned existing setups (unchanged from 2026-09-08, prices refreshed):
- **BWXT** — OVERSOLD BOUNCE + TARGET GAP: pos 0.13, mean target $228.88/12 analysts, upside +29.9%. JPM Overweight init (07-27); nuclear/medical-isotope expansion.
- **CRDO** — TARGET GAP: mean target $281.39/14 analysts, upside +40.4%, pos 0.37. FQ1 rev +115% YoY but margin-compression selloff (09-02); PCIe 6.x compliance milestone (08-31) is the cleaner catalyst.
- **CMI** — TARGET GAP: mean target $757.02/11 analysts, upside +25.8%, pos 0.49. Consensus HOLD despite gap; $450M data-center generator capex (08-26) vs Q2 EPS miss (08-04).
- **GLNG** — TARGET GAP: mean target $63.94/3 analysts (thin), upside +19.5%, pos 0.72.
- **EVER** — TARGET GAP: mean target $29.50/8 analysts, upside +15.5%, pos 0.74 (borderline).
- **DELL** — NEARING BREAKOUT: pos 1.00 (new 52wk high $533.88). Q2 rev $46.97B (+58% AI server), FY27 guide raised, S&P 100 inclusion. Mean target $510.26 is BELOW live price (upside -4.6%) — momentum, not valuation.

New rotating slice (cursor 45-59 of the non-holding, non-ETF watchlist):
- **MCHP** — TARGET GAP: mean target $108.64/19 analysts, upside +32.5%, pos 0.43.
- **SNDK** — TARGET GAP: mean target $2201.56/16 analysts, upside +26.7%, pos 0.73. 52wk range ($67.86-$2354) looks spinoff-distorted — see data quality.
- **APLD** — TARGET GAP: mean target $74.23/7 analysts (thin), upside +61.9%, pos 0.40. +7.4% today, no fresh catalyst news since 07-27 print.
- **AMZN** — TARGET GAP: mean target $328.17/40 analysts, upside +21.7%, pos 0.67. AWS GPU buildout, FTC ad-pricing suit is the offsetting negative.
- **CRWV** — TARGET GAP: mean target $138.81/23 analysts, upside +39.1%, pos 0.42. +11.7% today, no same-day news returned — treat cautiously.
- **CORZ** — TARGET GAP: mean target $37.12/11 analysts, upside +49.5%, pos 0.31.
- **SHOP** — TARGET GAP: mean target $171.15/31 analysts, upside +21.7%, pos 0.45. Recent news skews negative (overvaluation, profit-taking) — gap is directional, not a clean entry.
- **PENG** — TARGET GAP: mean target $71.00/5 analysts (thin), upside +38.4%, pos 0.48.

No setup in slice (below threshold): PATH (14.9%), PLTR (11.2%), TSLA (5.6%), AAPL (2.4%), AEM (6.0%), NEM (4.4%), ADBE (7.0%).

Cursor advanced: next run starts at index 60 (of ~86 non-holding, non-ETF watchlist names).

## 2. Earnings calendar
No held name reports within 7 days (quick-mode window, 2026-09-09 to 2026-09-16). Nearest confirmed dates on file: GOOG/GEV 2026-10-21. All other cached dates (LRCX, TER, QCOM, AAPL, AMZN, AMD, CLS, VRT, MRVL, AVGO, CEG, VST, NVDA, AMAT, NBIS, BABA, CIEN) are already in the past. No cache updates this run.

## 3. Data quality
- SNDK's 52wk range ($67.86-$2354.39) looks like a spinoff-history artifact; pos math unreliable, upside % (live vs current analyst mean) still used.
- PENG and GLNG target means rest on thin coverage (5 and 3 analysts) — low confidence.
- CRWV's +11.7% intraday move has no matching same-day (09-09) news in this fetch — unconfirmed driver.
- DELL breakout is momentum/catalyst-driven; mean target sits below live price (upside -4.6%), not valuation-supported.
- EVER's 15.5% upside is barely above the target-gap threshold — borderline signal.
- No held name reports earnings within the 7-day quick-mode window; nearest is GOOG/GEV 2026-10-21 — no earnings_calendar cache updates needed.

```json
{"watchlist_setups":[
 {"ticker":"BWXT","type":"oversold_bounce+target_gap","upside_pct":29.92,"pos":0.13},
 {"ticker":"CRDO","type":"target_gap","upside_pct":40.39,"pos":0.37},
 {"ticker":"CMI","type":"target_gap","upside_pct":25.82,"pos":0.49},
 {"ticker":"GLNG","type":"target_gap","upside_pct":19.52,"pos":0.72},
 {"ticker":"EVER","type":"target_gap","upside_pct":15.46,"pos":0.74},
 {"ticker":"DELL","type":"nearing_breakout","upside_pct":-4.63,"pos":1.0},
 {"ticker":"MCHP","type":"target_gap","upside_pct":32.46,"pos":0.43},
 {"ticker":"SNDK","type":"target_gap","upside_pct":26.67,"pos":0.73},
 {"ticker":"APLD","type":"target_gap","upside_pct":61.86,"pos":0.40},
 {"ticker":"AMZN","type":"target_gap","upside_pct":21.70,"pos":0.67},
 {"ticker":"CRWV","type":"target_gap","upside_pct":39.05,"pos":0.42},
 {"ticker":"CORZ","type":"target_gap","upside_pct":49.54,"pos":0.31},
 {"ticker":"SHOP","type":"target_gap","upside_pct":21.65,"pos":0.45},
 {"ticker":"PENG","type":"target_gap","upside_pct":38.40,"pos":0.48}
],
 "earnings_calendar_updates":{},
 "watchlist_scan_cursor":60,
 "data_quality":["SNDK 52wk range looks spinoff-distorted, pos math unreliable","PENG/GLNG targets rest on thin coverage (5/3 analysts)","CRWV +11.7% today has no matching same-day news in this fetch","DELL breakout is momentum-driven, mean target below live price","EVER upside barely clears the target-gap threshold","No held name reports within 7-day quick window, no earnings cache updates needed"]}
```

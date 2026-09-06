# Watchlist & Market Context — 2026-09-06 (deep)

## 1. Watchlist setups

**APLD** — watchlist, oversold_bounce, upside 66.4% (compute; live re-check 64.5%: $26.37 vs mean target $74.23, 7 analysts, 85.7% buy). Down 48% from 52wk high ($50.73) but +1.8% Fri, AI-datacenter buildout news positive, though company's own coverage flags lease-economics risk and widening losses. Entry: $22-23 (recent pullback support); invalidation: close below $20 (below would retest 52wk low $13.16). Conviction 20.8/low — thin-catalyst bounce, not a thesis re-rate.

**CORZ** — watchlist, oversold_bounce, upside 54.7% (compute; live re-check 51.8%: $17.89 vs mean target $37.12, 11 analysts, 100% buy). Down 41% from 52wk high ($30.46). Entry: $16 (prior consolidation shelf); invalidation: close below $13 (52wk low $13.14). Conviction 20.8/low.

**Pressure test — APLD/CORZ, not a diversifier:** Both are ex-bitcoin-miners repositioning as AI/HPC datacenter hosts — same AI-capex/datacenter-power factor this book already carries at 93.3% (GEV, VRT, NBIS, BE etc.), just a smaller, more levered, lower-quality-balance-sheet expression of it (lease-financed capacity buildout, dilution risk, no earnings support behind the target — both ratings are near-unanimous sell-side "BUY" with thin fundamental cover). Read both as leveraged beta on the same factor, not uncorrelated names. If sized, size as a small speculative sleeve inside the existing AI-capex bucket, not as diversification away from it.

**CCEC** (Capital Clean Energy Carriers) — watchlist, target_gap, $22.65 vs mean target $30.00 = 32.4% upside — but only 1 analyst covering; low-confidence read, not a real setup until coverage widens.

**GLNG** (Golar LNG) — watchlist, target_gap, $52.12 vs mean target $63.94 = 18.5% upside, 3 analysts BUY. Thin coverage; note only.

No setup: BAM (11.5% upside, below threshold), FLNG (-20.6%, HOLD/sell-heavy), RTX (14.5%, just under threshold).

## 2. Earnings calendar

Held-name check for the next 5 trading days (through 2026-09-13): FMP earnings-calendar pull for 2026-09-06→09-13 returned only **ADBE (2026-09-10)** — not a holding. Cross-checked against all 32 current holdings: **confirmed, no held name reports within 5 trading days.** Cache otherwise unchanged; next holdings on deck remain GOOG/GEV (2026-10-21, both cached/confirmed).

## 3. Data quality
- CCEC target is single-analyst — treat 32.4% upside as noise, not signal.
- Live upside% for APLD/CORZ (64.5%/51.8%) drifted slightly from compute's cached 66.4%/54.7% (Fri close vs earlier snapshot) — both within normal day-to-day noise, no correction needed.
- Watchlist scan slice this run: index 100-114 (FLTW, BKCH, EWT, CQQQ, FRNW, BAM, INDA, CNXT, DRAM, TINY, VDE, FLNG, GLNG, CCEC, RTX) — ETF/thematic-fund tickers (FLTW, BKCH, EWT, CQQQ, INDA, CNXT, VDE, TINY, FRNW, DRAM) skipped, no analyst-target setup logic applies to funds.
- analyst_targets cache reused as-is for all holdings-overlap tickers per orchestrator instruction; no re-fetch performed for cached names.

```json
{"watchlist_setups":[{"ticker":"APLD","type":"oversold_bounce","upside_pct":64.5,"pos":null},{"ticker":"CORZ","type":"oversold_bounce","upside_pct":51.8,"pos":null},{"ticker":"CCEC","type":"target_gap","upside_pct":32.4,"pos":null},{"ticker":"GLNG","type":"target_gap","upside_pct":18.5,"pos":null}],
 "earnings_calendar_updates":{},
 "watchlist_scan_cursor":115,
 "data_quality":["CCEC target is single-analyst, low confidence","APLD/CORZ live upside drifted slightly vs cached compute values, both within noise","Scanned index 100-114; ETF/fund tickers skipped from setup logic"]}
```

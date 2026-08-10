# Smith Scout — Market Context & Diversifier Bench (2026-08-10 deep run)

## 1. Session Read
- **US futures (pre-open):** ES +0.02%, NQ +0.15% — essentially flat, offering no directional lean of their own; Friday's cash session already did the work (SPX +0.62% to 7757.64, just 0.46% off its 52w high of 7793.68; NDX +1.30%; SMH +1.96% to 582.70).
- **Asia (Monday session, already trading, all firmly green):** Nikkei +2.02%, TWII (Taiwan) +2.05%, KOSPI +0.95% — no index below the -2% stress threshold; this is risk-on carrying through from Friday's US close, not a new domestic catalyst.
- **Europe:** Euro Stoxx 50 +0.33% — mild, no dispersion signal. No single home-listing move ≥2% observed at the aggregate level.
- **ADR gap-risk flags:** TWII +2.05% is the one line worth watching — if the book holds TSM, its Taiwan home listing's strength typically leads the ADR; watch for a firm open rather than a gap-fade. No ASML.AS/STMPA.PA-specific overnight data pulled this run (Euro Stoxx aggregate was too mild, +0.33%, to warrant the extra fetch under budget) — flagged in data_quality.
- **Headline scan:** No holdings ticker list was in this run's input slice, so a per-holding overnight headline sweep was not performed here — that depth is smith-signals' job. Nothing at the macro/index level (VIX -1.65% to 14.9, DXY +0.17%, US10Y 4.66% vs 4.67% prior) suggests a surprise overnight shock.
- **Bottom line:** Calm, positive carry-through session. Gate = STABILIZING on all four conditions. Gap risk is modest and skewed toward TSM-adjacent names given the Taiwan strength; nothing else stands out.

## 2. Sentiment Narrative
Sentiment jumped from GREED (66.2) to EXTREME_GREED (80.2) this run, and the VIX component (93.1) is doing nearly all the work: VIX at 14.9 sits deep in its 52-week range (13.38–35.3), just above its 1-year low, and SPX is within half a percent of its 52-week high (98.2 on the off-high component). MA125 (89.7) confirms the trend — SPX is running ~7.9% above its 125-day average. RSI14 at 63.3 is only moderately warm, not extreme, and yield_trend (56.5) is the one soft spot — US10Y has drifted up ~13bps over the past month even as today's print is flat. In plain terms: this is a market pricing in very little near-term risk, not a market that's technically overbought on momentum alone — the low-vol backdrop is the extreme part, not the price action itself. Action_hint is non-null: **"propose profit-booking on overweight/breach names."** For this run, that means the strategist should treat any name sitting materially above policy weight as a trim candidate on strength, not a hold-and-hope — this is exactly the regime (VIX-driven complacency near highs) where a single-factor AI-capex book is most exposed to a sharp unwind if the low-vol premise breaks.

## 3. Diversifier Bench (live-priced this run; targets carried from last run — not re-pulled)
Ranked by upside% × cleanliness (clean=1.0, partial=0.5):

| Ticker | Price | Target | Upside % | Thesis | Status | Diversifier |
|---|---|---|---|---|---|---|
| VST | $140.59 | $223.17 | 58.7% | Merchant power gen — AI-load-adjacent, correlated to the book's datacenter-power exposure | active | **PARTIAL** |
| NEM | $112.98 | $133.00 | 17.7% | Gold miner, zero AI-capex overlap, beta 0.50 | active | clean |
| UNH | $407.08 | $471.65 | 15.9% | Managed-care rebound, no capex correlation, beta 0.63 | active | clean |
| PG | $145.79 | $163.35 | 12.1% | Staples ballast, low beta 0.38 | active | clean |
| DUK | $124.85 | $138.61 | 11.0% | Regulated utility, rate-base growth, beta 0.37 | active | clean |
| SO | $92.69 | $101.45 | 9.5% | Regulated SE utility, defensive, beta 0.33 | active | clean |
| LLY | $1185.71 | $1270.37 | 7.1% | Pharma/GLP-1, decoupled from semis, beta 0.51 | active | clean |
| JNJ | $259.24 | $269.95 | 4.1% | Diversified pharma/medtech, near 52wk high, beta 0.23 | active | clean |
| KO | $87.05 | $87.35 | 0.3% | Staples — price ≈ target, needs fresh analyst-target pull | **stale** | clean |

**Honesty flag:** VST ranks highest on raw upside but is explicitly a **partial** diversifier — it's a merchant power generator with meaningful AI-datacenter-load exposure, the same factor driving the book's core AI-capex bet. Don't let its upside% override that it doesn't reduce single-factor risk the way NEM/UNH/PG/utilities do. KO has drifted to ~breakeven vs its stored target and should get a fresh target pull next run or be dropped after one more stale cycle per the 2-run rule.

## Data Quality
- Analyst mean targets for all 9 names carried over from last run's diversifier_candidates (not re-fetched this run) — only live price and beta were refreshed via yfinance. Flag for next run: refresh targets, especially KO (stale, needs new target).
- No individual ASML.AS / STMPA.PA / 2330.TW home-listing prices pulled — Euro Stoxx 50 aggregate (+0.33%) was below the 2% flag threshold, so the extra per-name fetch was skipped under budget discipline.
- No per-holding overnight headline scan performed — this run's input slice did not include the US book's holdings ticker list; smith-signals owns that depth layer.
- All beta values sanity-checked, in-band (0.23–1.43, well within 0–3.5).

```json
{"session_read":{"futures":{"es_pct":0.02,"nq_pct":0.15},"asia":{"nikkei_pct":2.02,"kospi_pct":0.95,"twii_pct":2.05},"europe":{"stoxx50e_pct":0.33},"adr_gap_flags":["TWII +2.05% Monday session -- TSM ADR may open firm; no home-listing-specific ASML/STM data pulled, aggregate Euro Stoxx move (+0.33%) below 2% flag threshold"],"headline_scan":["no holdings ticker list in this run's input slice -- per-holding overnight scan not performed, owned by smith-signals"]},
 "sentiment_narrative":"Score jumped from GREED (66.2) to EXTREME_GREED (80.2); VIX component (93.1) dominates -- VIX at 14.9 near its 52w low (13.38-35.3) with SPX within 0.46% of its 52w high. MA125 (89.7) confirms SPX running ~7.9% above its 125dma. RSI14 (63.3) only moderately warm -- this is a low-vol/complacency extreme, not a momentum-overbought extreme. Yield_trend (56.5) is the soft spot: US10Y up ~13bps over the past month. action_hint='propose profit-booking on overweight/breach names' -- strategist should treat above-policy-weight names as trim candidates on strength given single-factor AI-capex exposure in a VIX-driven complacent regime.",
 "diversifier_candidates":{
   "NEM":{"price_usd":112.98,"target_usd":133.00,"upside_pct":17.7,"thesis":"Gold miner, zero AI-capex overlap, beta 0.50","status":"active","clean_diversifier":true},
   "VST":{"price_usd":140.59,"target_usd":223.17,"upside_pct":58.7,"thesis":"Merchant power gen, AI-load-adjacent -- not a clean diversifier","status":"active","clean_diversifier":false},
   "UNH":{"price_usd":407.08,"target_usd":471.65,"upside_pct":15.9,"thesis":"Managed care rebound, no capex correlation, beta 0.63","status":"active","clean_diversifier":true},
   "PG":{"price_usd":145.79,"target_usd":163.35,"upside_pct":12.1,"thesis":"Staples ballast, low beta 0.38","status":"active","clean_diversifier":true},
   "LLY":{"price_usd":1185.71,"target_usd":1270.37,"upside_pct":7.1,"thesis":"Pharma/GLP-1, decoupled from semis, beta 0.51","status":"active","clean_diversifier":true},
   "DUK":{"price_usd":124.85,"target_usd":138.61,"upside_pct":11.0,"thesis":"Regulated utility, rate-base growth, beta 0.37","status":"active","clean_diversifier":true},
   "SO":{"price_usd":92.69,"target_usd":101.45,"upside_pct":9.5,"thesis":"Regulated SE utility, defensive, beta 0.33","status":"active","clean_diversifier":true},
   "JNJ":{"price_usd":259.24,"target_usd":269.95,"upside_pct":4.1,"thesis":"Diversified pharma/medtech, near 52wk high, beta 0.23","status":"active","clean_diversifier":true},
   "KO":{"price_usd":87.05,"target_usd":87.35,"upside_pct":0.3,"thesis":"Staples, price ~= target -- needs target refresh","status":"stale","clean_diversifier":true}
 },
 "data_quality":["analyst targets carried from prior run, not re-fetched","no per-name European home-listing pull (ASML.AS/STMPA.PA/2330.TW), aggregate Stoxx50E move below 2% threshold","no holdings ticker list in input slice -- per-holding headline scan skipped, owned by smith-signals","KO stale for 1+ cycle, needs fresh target or drop next run per 2-run rule"]}
```

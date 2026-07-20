# Watchlist & Market Context — 2026-07-20 (deep)

## 1. Watchlist setups (US only; scanned slice: cursor 0-14 of rotation, 15 names)

- **SMR** (NuScale) — watchlist — OVERSOLD BOUNCE — pos 0.01 (price $7.72 vs 52w low $7.21/high $57.42) — mean target $14.80, upside 47.8% — BUY consensus (10 analysts), recent positive contract news (Paragon reactor-protection award).
- **LEU** (Centrus Energy) — watchlist — OVERSOLD BOUNCE — pos 0.04 (price $156.05 vs low $142.13/high $464.25) — mean target $264.73, upside 41.1% — BUY consensus (7 analysts), +6.1% today; Oklo HALEU supply LOI offsets margin-pressure headline.
- **VST** (Vistra) — watchlist — OVERSOLD BOUNCE — pos 0.26 — mean target $223.17, upside 30.4% — BUY consensus (14 analysts, 93% buy), AI-datacenter power-demand tailwind (Meta/AWS PPAs).
- **CEG** (Constellation Energy) — watchlist — OVERSOLD BOUNCE — pos 0.13 — mean target $357.81, upside 29.5% — BUY consensus but mixed news (Calpine-deal leverage concerns vs. Walmart nuclear PPA, Citi target cut to $297).
- **SPCX** (SpaceX) — watchlist — OVERSOLD BOUNCE — pos 0.02 (near 52w low after -5.4% today) — no consensus target in feed; single-analyst reference (Dan Ives, Outperform, $190 target ≈ 53% upside) — flag: not a consensus mean, treat as indicative only.
- **FLEX** (Flex Ltd) — watchlist — TARGET GAP — pos 0.60 — mean target $162.50, upside 26.6% — BUY consensus (17 analysts, 88% buy), AI/datacenter demand.
- **DLR** (Digital Realty) — watchlist — TARGET GAP — pos 0.45 — mean target $218.71, upside 20.5% — BUY consensus, $3.5B Blackstone data-center acquisition (dilutive near-term, accretive 2027-28).
- **APH** (Amphenol) — watchlist — TARGET GAP — pos 0.67 — mean target $189.39, upside 20.2% — BUY consensus (21 analysts), strong Q2 (EPS +55.5% 2yr), AI interconnect demand.

No setup: AEP (upside 9.5%, mid-range pos), ETN (12.2%), LNG (13.6%), RIO (14.5% — just under threshold), DDOG (pos 0.89, upside -1.5% — target below price), CBRS (analyst data missing + implausible 52w-low of $0, discarded), EEMA (ETF, no target).

Cursor advanced: scanned index 0-14 of the ~93-name deduped non-held watchlist rotation. **New watchlist_scan_cursor = 15.**

## 2. Earnings calendar (holdings, 14-day window: 2026-07-20 to 2026-08-03)

- **LRCX** (4.03% weight) — **2026-07-29, CONFIRMED, source: web** (stockanalysis.com; INDmoney news only said "set to report...soon," yfinance calendar returned no data for this window — used the one permitted WebFetch per instructions).
- All other 28 holdings: yfinance's market-wide earnings calendar returned empty for this date range (likely a data gap, not literal "no earnings"). Quarterly-report timestamps for the large-weight names (TSM, MU, ASML, NVDA, LRCX peers) show most already reported this cycle in June/early-July, implying next reports fall outside this 14-day window — but this was not individually confirmed per-ticker beyond LRCX (tool-budget cap; LRCX was the only ≥3%-weight name explicitly flagged for verification).

## 3. JSON tail
```json
{"watchlist_setups":[
  {"ticker":"SMR","type":"OVERSOLD BOUNCE","upside_pct":47.8,"pos":0.01},
  {"ticker":"LEU","type":"OVERSOLD BOUNCE","upside_pct":41.1,"pos":0.04},
  {"ticker":"VST","type":"OVERSOLD BOUNCE","upside_pct":30.4,"pos":0.26},
  {"ticker":"CEG","type":"OVERSOLD BOUNCE","upside_pct":29.5,"pos":0.13},
  {"ticker":"SPCX","type":"OVERSOLD BOUNCE","upside_pct":53.0,"pos":0.02},
  {"ticker":"FLEX","type":"TARGET GAP","upside_pct":26.6,"pos":0.60},
  {"ticker":"DLR","type":"TARGET GAP","upside_pct":20.5,"pos":0.45},
  {"ticker":"APH","type":"TARGET GAP","upside_pct":20.2,"pos":0.67}
],
 "earnings_calendar_updates":{"LRCX":{"date":"2026-07-29","confirmed":true,"source":"web"}},
 "watchlist_scan_cursor":15,
 "data_quality":[
   "CBRS 52-week-low field returned $0 (implausible) — discarded, not used in pos calc",
   "SPCX has no analyst consensus in INDmoney feed; upside% uses single-analyst (Dan Ives) target, not a mean — treat as indicative only",
   "yfinance get_earnings_calendar returned empty for 2026-07-20 to 2026-08-03 market-wide — likely tool/data gap, not confirmation of zero earnings",
   "LRCX earnings unconfirmed by INDmoney news and yfinance; confirmed via one WebFetch to stockanalysis.com (2026-07-29)",
   "Earnings verification limited to LRCX (only holding ≥3% weight flagged); other 28 holdings not individually re-checked this run (budget cap)",
   "G3: INDmoney feed staleness applies generally per known_gaps"
 ]}
```

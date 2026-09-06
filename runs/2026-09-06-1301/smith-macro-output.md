# US Macro Desk — 2026-09-06 (deep)

## Fed & Stance
Fed funds 3.63% (target range midpoint), stance HAWKISH — reused verbatim from fomc_cache (next_check_date 2026-09-17, today precedes it, no new FOMC decision since last check).

## Options Sentiment
Barchart put-call-ratio pages (SPY, QQQ) returned empty via WebFetch this run — fallback triggered. Used yfinance single-expiry chain, nearest expiry 2026-09-08 (3 DTE), strikes 767-773 (SPY) / 716-722 (QQQ). Unusually, OI was non-zero and populated across all strikes this run (contra the documented all-zero-OI failure mode noted in G18/prior runs) — treated as usable but narrow (7-strike window only, not full chain, not comparable to Barchart's whole-chain aggregate figures from prior runs).

- SPY: PCR(OI) 1.117 [936c/1.19K.../936 sum calls 13,936 vs puts 15,570], PCR(vol) 1.049 (calls 280.5K vs puts 294.3K). Mild put-heavy tilt — consistent with low, calm VIX (14.53, +1.47%), reads as routine short-dated hedging, not fear. Max pain ≈ $770 (pins tight to spot $770.19).
- QQQ: PCR(OI) 0.692, PCR(vol) 0.858 — call-heavy, consistent with the session's semis rip. Max pain ≈ $718 (just below spot $718.96).
- source: yfinance-chain for all four figures this run (Barchart unavailable).

## Calendar (next 10 trading days from 2026-09-08)
- CPI: 2026-09-11 — **inside 5 trading days** (day 4).
- FOMC decision: 2026-09-16 — inside 10 trading days (day 7), not inside 5. **Single most important date on the page.**
- NFP: last print 2026-09-04 (already occurred); next NFP ~2026-10-02 (outside window).
- Mega-cap earnings-season window: not active (next window mid-Oct).

## Regime Read
Mixed, narrow-breadth risk-on rather than broad risk-on: SMH +2.61% (memory names +6-12%) on an idiosyncratic AI-capex/memory catalyst, while SPX -0.38% and 10Y +2.2bp to 4.784% moved the other way. A HAWKISH Fed 10 days from a decision, with 10Y holding near 4.78%, keeps a floor under discount rates that pressures long-duration growth multiples broadly — the AI-capex chain is currently shielded by name-specific momentum but carries 1.417 beta to SMH, so a reversal in that narrow leadership would hit the book harder than the index-level move implies.

cluster_impact:
- ai_capex_chain: favored short-term on momentum, most exposed cluster to a hawkish FOMC surprise (highest beta, highest multiples).
- rate_sensitive/long_duration_growth: pressured by 10Y near 4.78% and hawkish stance.
- defensives: neutral-to-favored as a breadth-divergence hedge.

## FOMC 09-16 risk to book
Hurts the book if the Fed either holds and pushes back on cut timing (language reading as a delay past year-end), or a dot-plot revision drags 10Y decisively above ~4.85-4.90%. At 1.417 beta to SMH, a 1% SMH drawdown from a hawkish surprise implies roughly 1.4% portfolio-level drag before position-specific effects, concentrated in the highest-multiple AI-capex names.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":1.117,"spy_pcr_oi":1.117,"spy_pcr_vol":1.049,"spy_pcr_oi_source":"yfinance-chain","spy_pcr_vol_source":"yfinance-chain","spy_max_pain":770,
 "qqq_pcr":0.692,"qqq_pcr_oi":0.692,"qqq_pcr_vol":0.858,"qqq_pcr_oi_source":"yfinance-chain","qqq_pcr_vol_source":"yfinance-chain","qqq_max_pain":718,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-09-11","next_nfp":"2026-10-02","earnings_season_window":false},
 "regime":"neutral","regime_note":"narrow-breadth risk-on (semis) vs broad-index risk-off (SPX/10Y) — yield-fragile into FOMC",
 "cluster_impact":{"ai_capex_chain":"favored short-term on momentum, most exposed to hawkish FOMC surprise","rate_sensitive":"pressured by 10Y near 4.78% and hawkish stance","defensives":"neutral-to-favored as breadth-divergence hedge"},
 "data_quality":["Barchart PCR WebFetch returned empty for both SPY and QQQ — fell back to yfinance single-expiry (2026-09-08, 3DTE) chain","yfinance chain unusually had non-zero OI this run, contra documented G18 all-zero-OI failure mode — treat as narrow-window (7 strikes) approximation, not comparable to Barchart whole-chain aggregates","max-pain computed only across the narrow strike window returned (767-773 SPY, 716-722 QQQ), not the full chain","FOMC decision date sourced via web search (Fed press release naming convention), not independently re-verified against federalreserve.gov calendar page"]}
```

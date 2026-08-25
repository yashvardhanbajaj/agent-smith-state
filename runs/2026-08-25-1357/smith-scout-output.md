# Market Scout — 2026-08-25 (deep, pre-open)

## 1. Session read

**US futures:** ES +0.19%, NQ +0.47% — calm-to-positive open implied, a bounce attempt off Monday's semis-led selloff. VIX -0.19% (15.82) confirms no fear spike.

**Asian session (closed):** Nikkei +0.50%, KOSPI +0.68%, TAIEX +0.91% — all green but none clears the >1% notable threshold. Directionally supportive for TSM/MU/memory-adjacent names; no dedicated flag warranted.

**European/home-listing session:** ASML.AS (Amsterdam) +0.66% intraday vs prior close — below the 2% ADR-gap threshold, no gap flag. STMPA.PA (Paris) quote unavailable via yfinance; substituted US-listed STM ADR itself (-2.4%), which is not a valid home-listing lead — flagged in data_quality. Taiwan home listing 2330.TW +1.05%, consistent with the broader Asia green tape; TSM's US session Monday was down -3.7% on the group-wide de-risking (see headline scan), so today's Taipei bounce is a partial retrace, not a gap-risk signal for the US open.

**SMH -2.43% integrity check:** confirmed real, not a stale print. Monday 8/24 saw a genuine semis-led selloff (Intel -5%, AMD -3.3% to -4%, TSM -3.7%, Micron -5.8%, Nvidia -2.3%, its 7th straight down day) driven by (a) Netlist patent headwinds hitting Micron specifically, (b) broad AI-hardware de-risking ahead of Nvidia's Wednesday 8/27 earnings, and (c) macro noise (Iran sanctions, US-Canada tariff worries) pulling flows into blue chips and gold. This resolves the gate's SMH-freshness doubt: the print is legitimate Monday closing weakness, and today's pre-market futures/Asia tape reads as an early bounce attempt off it, not a continuation.

**Headline scan (post-watermark, book holdings):** Lead story for the week is NVDA earnings after the close Wednesday 8/27 — the dominant swing factor for the book's ~89% AI-capex tilt. MU carries an idiosyncratic legal overhang (Netlist patent dispute) layered on top of the sector-wide move. No weekend M&A, guidance, or regulatory headlines surfaced for the other 33 holdings in this scan.

**Gap risk today:** Low. No ADR home-listing moved ≥2% overnight. The real gap risk this week is event-driven (NVDA earnings Wed, CPI-adjacent inflation print later in the week), not overnight-session driven.

## 2. Sentiment narrative

Score 66.1 (greed band, unchanged from prior run's greed). The composite is a mixed bag under the hood: VIX-range component reads a strong 80.6 (vol is genuinely low/complacent at 15.82), while MA125, RSI14, and yield-trend all sit at neutral 50, and pct-off-52w-high pins at 100 (SPX within striking distance of its high). In plain terms: options markets are pricing calm and the index is near its highs, but momentum/trend signals aren't confirming euphoria — this reads as "greed via low volatility and proximity to highs," not a breadth-driven blowoff top. action_hint is null (no extreme_greed/extreme_fear trigger), so there's no standing instruction here for the strategist to lean against sizing this run — proceed on the merits of each name, but note the book is one bad NVDA print away from testing whether this VIX-driven calm holds.

## 3. Diversifier bench (ranked by upside% × cleanliness, best first)

| Ticker | Price (USD) | Target | Upside % | Thesis | Status | Diversifier |
|---|---|---|---|---|---|---|
| UNH | 398.76 | 471.65 | 18.3% | Managed care rebound, no capex correlation, beta 0.63 | active | clean |
| DUK | 121.97 | 138.61 | 13.6% | Regulated utility, beta 0.37 — rate-sensitive, watch 10Y | active | clean |
| SO | 90.10 | 101.45 | 12.6% | Regulated SE utility, beta 0.33 — same rate-sensitivity as DUK | active | clean |
| PG | 146.60 | 163.35 | 11.4% | Staples ballast, beta 0.38 | active | clean |
| VST | 135.66 | 223.17 | 64.5% | Merchant power gen, beta 1.43 — AI-load adjacent, NOT clean | active | **partial** |
| LLY | 1246.93 | 1270.37 | 1.9% | Pharma/GLP-1, beta 0.51 — near 52wk high, little cushion left | active | clean |
| NEM | 131.84 | 133.00 | 0.9% | Gold miner, beta 0.50 — safe-haven rally has compressed upside near-zero | active | clean |
| JNJ | 273.04 | 269.95 | -1.1% | Diversified pharma/medtech, beta 0.23 — price now above mean target, no cushion | stale | clean |

Note: VST ranks highest by raw upside% but is explicitly flagged partial (AI-load-adjacent via datacenter power demand, beta 1.43 confirms correlation to the book's existing bet) — treat UNH as the top clean, uncorrelated idea this run. Analyst mean targets were not refreshed this pass (only live prices were re-pulled); recompute upside next full deep run if targets look stale relative to price action. JNJ remains stale (price above target, no cushion) — one more stale run and it should be dropped per the 2-run rule if analyst coverage still shows no upside.

## 4. Data quality notes
- STMPA.PA (Paris home listing for STM) unavailable via yfinance; substituted the US-listed STM ADR quote, which is not a valid overnight-gap proxy — do not use it for gap-risk reads.
- Diversifier bench analyst targets carried forward from prior run (not re-fetched this pass) — only live prices were refreshed via yfinance.
- SMH -2.43% pre-market print independently verified as genuine Monday 8/24 closing weakness via WebSearch, not a stale/thin pre-market quote artifact — resolves the gate's stated freshness doubt.

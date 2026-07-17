# Watchlist & Market Context — 2026-07-14 (quick sweep)

## Flow/attribution narrative (consuming compute_attribution.json, not recomputing)
Value delta +$4,023.88 on the run. Script's raw flow figure ($3,490.61) is understated: it missed
two new positions — MRVL (new, 4sh, ~$965 flow) and VRT (new/re-entered, 3sh, ~$964 flow) — and
mislabeled SNDK's near-full exit (1.008→0.008sh, ~$1,843 outflow) as a corporate action (G6
false-positive; it's a real sell). Corrected est. net flows ≈ $3,490.61 + $965.27 + $963.96 −
$1,843.35 ≈ **$3,576.49**. Residual market move: +$533.27. FX effect: $0 (USD book). Rolling
windows unavailable — only 4 ledger rows on file.

## Watchlist setups (US only) — scanned cursor 30-44 + re-entry candidates DLR/ETN/ANET
- **UHS** (watchlist) — OVERSOLD BOUNCE: pos 0.05 (52w $140.08-$246.33 vs $145.25), mean target
  $208.29, upside +30.3%. Positive catalyst: CMS proposed 2.4% Medicare payment rate hike (Jul 2).
- **FIG** (watchlist) — OVERSOLD BOUNCE: pos ~0.00 (52w $16.60-$142.92 vs $24.51, still down ~85%
  off highs). No analyst mean-target data available (gap). Positive catalysts: BofA upgrade to Buy
  ($30 PT, Jul 7), Citizens Financial 162k-share buy + AI-optimism rally (+11.9%, Jul 13).
- **BWXT** (watchlist) — TARGET GAP: pos 0.42, mean target $238.79, upside +24.6%. Catalyst: nuclear
  isotope production expansion (Jul 10).
- **DLR** (recently-exited re-entry candidate) — TARGET GAP: pos 0.44, mean target $219.43, upside
  +20.8%. Catalyst: $3.5B Blackstone data-center acquisition, $2.28B equity raise for AI-infra buildout.
- **APA** (watchlist) — TARGET GAP: pos 0.58, mean target $42.75, upside +20.2%. Mixed news (Savant
  Alaska buy positive, but shares dipped on oil-price weakness).
- **ANET** (recently-exited re-entry candidate) — NEARING BREAKOUT: pos 0.92 (near 52w high $189.82),
  catalyst: AI/cloud networking demand, BofA PT raise to $200 (Jun 16), Q2 rev guide ~$2.8B (Jul 8).
- **NET** (watchlist) — NEARING BREAKOUT: pos 1.00 (at fresh 52w high $283.64), catalyst: BTIG PT
  hike to $314 (Jul 13), OpenAI search-infra partnership (Jul 8), Scotiabank upgrade + $300 PT (Jul 7).

No setups found in: CMI, GLNG, ITA (ETF, no analyst coverage), KLAC (strong news but pos 0.66, no
gap/breakout trigger), LLY (pos 0.85, upside only 7.1%), ODD (oversold but news/target both negative),
MKSI (pos 0.75, upside 11.7% <15%), ETN (pos 0.79, upside 9.9% <15%).

## Earnings calendar (holdings, next 7 days — quick mode window)
- **TSM — 2026-07-16, CONFIRMED** (source: watchlist agent, reconfirmed today). Only 2 days out —
  9.0% position weight, flag prominently for the briefing.
No other holdings have earnings inside the 7-day quick-mode window. GLW (07-28) and QCOM (07-29)
remain cached/confirmed but fall outside this window; no re-check needed this run.

## Data quality
- FIG: INDmoney returns no analyst_forecast/target-price block — upside % not computable for this
  oversold-bounce flag; flagging on price position + news only.
- ITA is an ETF with no analyst coverage in the feed — excluded from setup scan by design, not a gap.
- G6 (known gap, cited not re-explained): script's corporate-action heuristic still false-positives
  on near-zero dust sells (SNDK) and clean-multiple buys; applies again this run per compute_attribution.json.

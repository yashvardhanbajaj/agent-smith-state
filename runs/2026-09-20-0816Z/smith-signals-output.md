# Signals — 2026-09-20 deep (weekend confirmation of Fri 09-19 close)

No new trading session since news_watermark (2026-09-19); this is a same-close confirmation
run. Only one bucket actually changed vs prior signal_history: AMAT's MOMENTUM+VOLUME? judgment
leg is now confirmed. Everything else below matches Friday's fired buckets exactly (script
arithmetic unchanged) — listed for completeness with size/target context, not as new news.

## Fired buckets

- **AMAT — MOMENTUM+VOLUME (promoted from "?")** — +6.51% day, 1.61x its 3.92% ATR (threshold
  5.88%); record Q3: revenue $9.1B +25% YoY, net income +43% to $2.5B — record revenue (18-19
  Sep, 2026 — INDmoney news feed), $5B India investment (17 Sep 2026 — INDmoney news feed). 5.27%
  of book. Also STRONG UPTREND + PEER LAGGARD (rel_sigma -1.39, -12.55pp vs SMH despite the beat
  — book-wide semicap still leads it) + TARGET GAP (target $640.89, +44.4% upside, n=28).
  Caveat: MOMENTUM+VOLUME grades poorly fleet-wide (20% hit rate, n=15, payoff 1.23x) — treat the
  beat as fundamentally real, the bucket's historical edge as weak.
- AMD — PEER LEADER (rel_sigma +2.08, +17.87pp vs SMH) + STRONG UPTREND (pos 0.94). day_atr_mult
  only 0.63x — OVERBOUGHT PULLBACK? leg NOT promoted: no negative-dated news since watermark and
  upside is still +10.2% (not above target). 1.65% starter weight.
- BE — PEER LEADER (rel_sigma +2.37, +35.18pp vs XLU) — S&P 500 inclusion effective 2026-09-21
  reaffirmed (prior_findings:511c7b86ce). 1.58% weight, upside only 4.9% ($280.24 target) — most
  of the re-rate is priced.
- SKHY — PEER LEADER + STRONG UPTREND + TARGET GAP — pos 0.841, rel_sigma +1.68 (+17.92pp vs SMH),
  target $249.70 (+32.9%). 0.56% weight, unreconciled fill per prior_findings:SKHY. Raw INDmoney
  feed still shows 52wk_low=0 (the 2026-09-06 SKHY artifact); script's cached wk52 rejects it, pos
  stayed 0.841 not a fake 1.0 breakout — no action needed.
- COHR — TARGET GAP ($415.36, +23.59% upside), +7.22% day but day_atr_mult only 1.21x its 8.94%
  threshold (not a standout for this name's own volatility). Fiscal Q4 beat already RECONCILED
  per prior_findings:thesis:COHR — not re-litigating.
- LITE — STRONG UPTREND (pos 0.834) + TARGET GAP (+23.7% upside). 2.76% weight.
- AMZN — PEER LAGGARD (rel_sigma -1.55, -7.81pp vs XLK) + TARGET GAP (+29.1% upside). 3.77% wt —
  matches prior_findings:thesis:AMZN correction (-7.81pp, not the earlier -3.30pp figure).
- TARGET GAP only (no other bucket fired), all confirmed unchanged: TSM (+27.2%, 8.99% wt), ASML
  (+29.2%, 8.67% wt, rel_sigma -0.94 — below LAGGARD threshold), GOOG (+22.0%, 6.16% wt), MU
  (+48.7%, 6.04% wt — FQ4 earnings 2026-10-01 is the next hard datapoint per thesis), TER (+20.5%,
  5.49% wt), KLAC (+32.0%, 5.25% wt), APH (+27.8%, 4.61% wt), VRT (+35.7%, 4.43% wt), MSFT (+16.0%,
  4.39% wt), CLS (+43.3%, 3.95% wt), WDC (+50.4%, 3.93% wt), MRVL (+16.9%, 3.61% wt), NBIS (+29.7%,
  3.29% wt), GEV (+31.7%, 2.80% wt), ALAB (+28.9%, 2.69% wt), STM (+50.0%, 2.22% wt), GLW (+29.5%,
  1.33% wt), CIEN (+44.2%, 0.01% wt — dust position, see open_flags TER note applies in spirit).
- No bucket: QCOM (-5.82% day but only 0.92x its threshold; negative margin-pressure headline
  09-17 already stale/pending), NOW (-2.17% day, mixed AI-governance news, no threshold crossed).

## Repeat suppression

Unchanged repeats (bucket set identical to prior signal_history, no material move): TSM, ASML,
GOOG, TER, KLAC, APH, VRT, MSFT, CLS, WDC, AMZN, MRVL, NBIS, GEV, LITE, ALAB, QCOM, STM, NOW,
COHR, BE, GLW, SKHY, CIEN, MU (TARGET GAP unchanged). Only AMAT changed.

## Still pending (pre-watermark, carried)

- GLW $2B ATM dilution / optics-peer contagion (COHR, LITE) — unresolved, prior_findings
  catalyst:9744ffb8fe/68ffcdcb21.
- Amodei "pace the frontier" essay — widened political debate, no new stock mechanism —
  prior_findings catalyst:7180d87827/b0c7d54add.
- GEV Street-low Sell (GLJ Research, $470 PT) — contested vs guidance raise —
  prior_findings catalyst:90ef472ced/ce8fa6cd04.
- CXMT HBM3E risk production — structural, no volume/price impact yet —
  prior_findings catalyst:aa6e4a3cf0/dca7246842.
- AMD EVP Grasby insider sale (2026-08-22) — old, informational only, not a fresh signal.

## Data quality

- FMP `insiderTrades` (search-insider-trades) returns ACCESS DENIED — plan tier below
  Starter/Premium/Ultimate/Enterprise. Deep-mode insider-activity task for top-10 holdings
  (TSM/ASML/GOOG/MU/TER/AMAT/KLAC/APH/VRT/MSFT) could not be executed via Form-4 data; fell back
  to news-derived only (none material this run). Same root cause as G90 (FMP plan-tier gaps),
  now confirmed to also block insiderTrades, not just statements — worth folding into G90 or a
  sibling gap.
- ASML analyst target: script's compute_buckets.json carries mean $2157.62 (n implied); this
  run's raw INDmoney fetch showed mean $2135.91 off only 6 analysts — used the script figure per
  "do not recompute" rule; flagging the source discrepancy for awareness, not overriding.

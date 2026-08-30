# Market Scout — Deep Run, 2026-08-30 (Sunday, post-close)

## 1. Session Read

**No pre-open/international session to report.** Today is Sunday; US markets are closed and there is no Asian or European session running concurrently with this run. All prices below are Friday 2026-08-28's regular-session close. Do not read this as "the week ended badly" being confused with "the market is bleeding this morning" — it isn't; there is no morning tape yet. The next live signal is Monday's pre-open futures print.

**Friday 2026-08-28 close, for the record (already in market_inputs, not re-fetched):**
- SPX -0.25%, NDX -0.52% — broad index softness, not a rout.
- SMH -3.47% (553.11, prior close 573.00) — the semiconductor/AI-hardware complex sold off hard while the index barely moved. This is the gate-triggering term (ESCALATING classification, SMH ≤ -2.5% single-term breach).
- VIX -0.55% to 14.43 — no fear spike accompanied the semis selloff; the options market did not price this as systemic.
- ES=F -0.26%, NQ=F -0.69% (Friday's futures read, stale by Sunday) — NQ underperformed ES, consistent with tech/semis leading the weakness.

**Rotation signal worth flagging to the strategist:** per the dispatch context, hyperscalers (AMZN +3.97%, MSFT +1.68%, GOOG +1.53%) rose Friday while the AI supply chain (SMH -3.47%) sold off. That is a rotation OUT of the picks-and-shovels/supply-chain names and INTO the capex spenders themselves — not a broad AI-theme derisking. For an 89.4%-AI-capex-chain book concentrated in suppliers (MRVL, VRT, TER, MU, CLS, CIEN, AMAT, ASML, AVGO, QCOM) rather than hyperscalers, this rotation is a direct headwind, independent of the index-level sentiment reading. GOOG (held, 3.46% weight) is the one name in the book that benefited from Friday's rotation rather than being hurt by it.

**ADR gap-risk flags:** none — no European home-listing session ran (Sunday). ASML's home listing (ASML.AS) will be the first read on Monday's European open; carries relevance for the ASML holding (4.28% weight) given SMH's Friday weakness.

**Headline scan:** none conducted — post-watermark weekend scan not warranted without a live session; deferred to Monday pre-open when smith-catalyst/smith-signals can pair it with an actual gap.

## 2. Sentiment Narrative

The composite reads 67.0 / "greed" — but that number is measuring the **index**, not this book, and the two have diverged sharply. VIX at 14.43 (component score 85.2/100) and SPX sitting within 1% of its 52-week high (component 100/100) are genuinely calm, complacent index-level readings — there is no broad fear in the market. But Friday's tape showed SMH falling 3.47% on a day the index barely moved 0.25-0.5%, and per the book snapshot this portfolio itself fell 3.12% and now sits 8.95% below its own peak, with 89.4% concentrated in the AI-capex supply chain. **The 67/"greed" score is close to worthless as a read on whether this book's positions are safe or extended right now** — it would say the same thing whether SMH had just cratered or rallied, because none of its five inputs (VIX range, 125dma, RSI14, 52wk-high-distance, yield trend) touch semiconductor- or AI-hardware-specific pricing. action_hint is null (not extreme_greed/extreme_fear), so there's no automatic override triggered either way. The honest framing for the strategist: index sentiment is calm-to-complacent, but that calm is not being extended to the book's own factor — the supply chain is being actively derated even as the broader tape and even the hyperscalers it depends on hold up fine. Treat "greed" here as license to be measured about NEW risk generically, not as evidence this book's concentrated bet is not extended.

## 3. Diversifier Bench

Live prices refreshed this run (all identical to Friday's close — no live session since, so no movement to report). Per the TTL rule, `target_usd`/`thesis`/`clean_diversifier` are unchanged from 2026-08-29 (< 7 days old, no new candidates this run) — `as_of` stays at 2026-08-29 since only price was refreshed, not target/thesis.

Ranked by (upside % × cleanliness), clean diversifiers first:

| Ticker | Price | Upside % | Thesis | Status | Diversifier |
|---|---|---|---|---|---|
| UNH | $392.95 | 20.0% | Managed care rebound, beta 0.63 | active | **clean** |
| DUK | $120.25 | 15.3% | Regulated utility, beta 0.37 | active | **clean** |
| SO | $88.25 | 15.0% | Regulated SE utility, beta 0.33 | active | **clean** |
| PG | $143.78 | 13.6% | Staples ballast, beta 0.38 | active | **clean** |
| LLY | $1,174.61 | 8.2% | Pharma/GLP-1, beta 0.51 | active | **clean** |
| NEM | $127.98 | 3.9% | Gold miner, beta 0.50 | active | **clean** |
| VST | $137.09 | 62.8% | Merchant power gen, beta 1.43 | active | **partial — AI-load adjacent, NOT clean** |
| JNJ | $268.04 | 0.7% | Diversified pharma/medtech, beta 0.23, essentially at target | stale | clean (but no upside left) |

**Honesty flag on VST:** highest headline upside in the bench (62.8%) but it is a merchant power generator selling into datacenter/AI load growth — its earnings trajectory is directly levered to the same AI-capex cycle the book is already 89.4% exposed to. Ranking it as a top diversifier on upside alone would be exactly the mistake this bench exists to catch. On a diversification-adjusted basis it ranks last, not first.

**Actual clean-diversification ranking (upside × cleanliness):** UNH > DUK ≈ SO > PG > LLY > NEM > JNJ (no upside left) > VST (excluded — not clean).

**Structural note for the strategist:** the `bench_diversifier` trigger has fired zero times and none of these eight names has ever been bought, against an 89.4% single-factor book. UNH is the standout — 20% upside, beta 0.63, zero AI-capex correlation, and has sat "active" unbought for multiple runs. NEM is the purest hedge (gold, beta 0.50, negatively-to-uncorrelated with tech capex cycles) but has the thinnest upside cushion (3.9%) after its own recent run. JNJ has converged to its target and is a candidate to drop next run if it doesn't re-rate — no analyst-coverage issue, just no more edge.

## Data Quality
- No pre-open/international session available to read (Sunday) — session-read narrative limited to Friday's close and forward-looking flags only, as instructed.
- No new candidate research performed — all 8 bench names reused TTL-cached targets/theses per the 2026-08-30 TTL rule; only prices refreshed.
- Headline scan skipped — no live session to anchor a gap-risk read; deferred to next live run.

```json
{"session_read":{"futures":{"es_pct":-0.26,"nq_pct":-0.69},"asia":{"note":"not available -- Sunday, no pre-open session"},"europe":{"note":"not available -- Sunday, no session"},"adr_gap_flags":[],"headline_scan":["skipped -- no live session to anchor a gap-risk read, deferred to next live run"]},
 "sentiment_narrative":"67.0/greed is an index-level read (calm VIX, SPX near highs) that says nothing about this book's own factor: SMH fell 3.47% Friday while the book fell 3.12% and sits 8.95% below its own peak at 89.4% AI-capex concentration. Hyperscalers (AMZN/MSFT/GOOG) rose the same day the supply chain it holds sold off -- a rotation the composite cannot see. action_hint is null, so treat 67/greed as license to be measured on NEW generic risk, not as evidence this book's concentrated bet is not extended.",
 "diversifier_candidates":{
   "VST":{"price_usd":137.09,"target_usd":223.17,"upside_pct":62.8,"thesis":"Merchant power gen, beta 1.43 -- AI-load adjacent, NOT clean","status":"active","clean_diversifier":false,"as_of":"2026-08-29"},
   "UNH":{"price_usd":392.95,"target_usd":471.65,"upside_pct":20.0,"thesis":"Managed care rebound, beta 0.63","status":"active","clean_diversifier":true,"as_of":"2026-08-29"},
   "DUK":{"price_usd":120.25,"target_usd":138.61,"upside_pct":15.3,"thesis":"Regulated utility, beta 0.37","status":"active","clean_diversifier":true,"as_of":"2026-08-29"},
   "SO":{"price_usd":88.25,"target_usd":101.45,"upside_pct":15.0,"thesis":"Regulated SE utility, beta 0.33","status":"active","clean_diversifier":true,"as_of":"2026-08-29"},
   "PG":{"price_usd":143.78,"target_usd":163.35,"upside_pct":13.6,"thesis":"Staples ballast, beta 0.38","status":"active","clean_diversifier":true,"as_of":"2026-08-29"},
   "LLY":{"price_usd":1174.61,"target_usd":1270.37,"upside_pct":8.2,"thesis":"Pharma/GLP-1, beta 0.51","status":"active","clean_diversifier":true,"as_of":"2026-08-29"},
   "NEM":{"price_usd":127.98,"target_usd":133.0,"upside_pct":3.9,"thesis":"Gold miner, beta 0.50","status":"active","clean_diversifier":true,"as_of":"2026-08-29"},
   "JNJ":{"price_usd":268.04,"target_usd":269.95,"upside_pct":0.7,"thesis":"Diversified pharma/medtech, beta 0.23 -- essentially at target","status":"stale","clean_diversifier":true,"as_of":"2026-08-29"}
 },
 "data_quality":["No pre-open/international session available -- Sunday run, session read limited to Friday close","Headline scan skipped, no live session to anchor gap-risk","Bench targets/theses reused per TTL rule, only prices refreshed this run"]}
```

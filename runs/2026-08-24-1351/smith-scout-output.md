# Market Scout — Deep Review, 2026-08-24 Pre-Open (04:xx ET / 13:51 IST)

## 1. Session Read

**US futures:** ES -0.21%, NQ -0.70% — soft red open implied, Nasdaq underperforming on chip-heavy composition. SMH -0.40% pre-market vs Friday close, consistent with NQ's larger discount to ES.

**Asian session (closed):**
- KOSPI -3.12% — the gate trigger term this run (Asia term ≤ -3% threshold breached). Korea's chip/memory-heavy index led the region lower; read-through risk for the book's memory-adjacent names (MU 3.65% wt, SKHY 2.06% wt), though per-name depth is smith-catalyst's remit.
- TAIEX -1.02% — Taiwan (TSM's home market) down but below the 2% ADR-gap threshold.
- Nikkei -0.74% — broad regional risk-off, not idiosyncratic.

**European session (open during this run):**
- Euro Stoxx 50 -0.16% — muted, no notable move.

**ADR home-listing check (gap-risk screen, ≥2% overnight move = flag):**
- 2330.TW (TSM home listing): 2375 TWD, -1.45% vs prior close — below flag threshold.
- STMPA.PA (STM home listing): €42.82, -0.60% vs prior close — below flag threshold.
- ASML.AS (ASML home listing): €1,506.40, +0.03% vs prior close — negligible; also a ~0% weight position in the book currently.
- **No ADR gap-risk flags triggered today.** Despite the Asia-led escalation, none of the book's three ADR-proxy home listings moved enough overnight to imply a discontinuous gap at the US open — today's futures softness looks like broad-market repricing, not an ADR-specific gap event.

**Headline scan (post-watermark, holdings-relevant, headline-level only):**
- No fresh discrete weekend headline surfaced. The dominant thread carrying into today is the continuation of late-July/August profit-taking in AI/semis: TSMC's prior earnings beat came bundled with a higher capex guide, which markets read as margin-dilutive rather than bullish, and SMH is down roughly 9.5% over the trailing month per wire coverage. Today's KOSPI-led Asia selloff reads as an extension of that same profit-taking dynamic rather than a new catalyst — consistent with smith-catalyst's existing G81 open question on the semis-rout's proximate cause.
- Sources: [ABC News — AI chip stock selloff](https://abcnews.com/Business/ai-chip-stock-selloff/story?id=134844421), [CNBC — Chip stocks shed $1T](https://www.cnbc.com/2026/07/29/chip-selloff-sk-hynix-samsung-softbank.html)

**Net read for today's open:** broad, Asia-led risk-off (KOSPI the standout), softer but not disorderly US futures, no ADR-specific gap risk, and no new headline catalyst beyond the ongoing AI-capex profit-taking narrative already on the book's radar.

## 2. Sentiment Narrative

Compute_sentiment.json scores today at 66.1 ("greed"), down from "extreme_greed" on the prior run. In plain terms: VIX ticked up 5.1% overnight to 15.90 — still a historically low absolute level, not a fear reading — while SPX (7,674) and NDX (26,180) remain close enough to their 52-week highs that the composite's pct-off-52w-high component sits pinned at its ceiling (100). The 125-day MA, RSI-14, and yield-trend sub-components are all sitting at neutral (50), meaning the medium-term technical backdrop hasn't actually deteriorated — the score's pullback from extreme_greed to greed is being driven almost entirely by the VIX uptick, i.e., an options-market cooling of froth rather than a change in trend or breadth. action_hint is null this run, so no extreme-greed or extreme-fear sizing override is being handed to the strategist. That said, today's ESCALATING gate (Asia-led, KOSPI -3.12%) is a faster-moving, higher-frequency signal than this composite's slower components — the strategist should weight the gate classification over the still-constructive sentiment score for any near-term sizing judgment, since price/vol is moving ahead of what the 125dma/RSI/yield-trend inputs have caught up to yet.

## 3. Diversifier Bench (ranked by upside% × diversification cleanliness)

| Ticker | Price (USD) | Target | Upside % | Mini-thesis | Status | Diversifier |
|---|---|---|---|---|---|---|
| UNH | $390.11 | $471.65 | 20.9% | Managed care rebound, no capex correlation, beta 0.63 | active | clean |
| DUK | $119.85 | $138.61 | 15.6% | Regulated utility, beta 0.37 — down 3.3% today, likely pressured by 10Y yield rising to 4.738% | active | clean |
| SO | $88.94 | $101.45 | 14.1% | Regulated SE utility, beta 0.33 — down 4.2% today, same rate-sensitivity pattern as DUK | active | clean |
| PG | $144.68 | $163.35 | 12.9% | Staples ballast, beta 0.38 | active | clean |
| VST | $136.21 | $223.17 | 63.9% | Merchant power gen, beta 1.43 — **PARTIAL DIVERSIFIER: AI-load adjacent, not clean.** Down ~8% since this morning's read; raw upside is highest on the bench but should be discounted for cleanliness in any sizing decision | active | **partial** |
| LLY | $1,255.40 | $1,270.37 | 1.2% | Pharma/GLP-1, decoupled from semis, beta 0.51 — near 52-week high, upside largely consumed | active | clean |
| NEM | $131.58 | $133.00 | 1.1% | Gold miner, zero AI-capex overlap, beta 0.50 — safe-haven rally (+11.7% since this morning's read) has compressed upside to near-zero; watch for an analyst target raise | active | clean |
| JNJ | $270.24 | $269.95 | -0.1% | Diversified pharma/medtech, beta 0.23 — price now sits fractionally above the analyst mean target; no valuation cushion left | **stale** | clean |

**BX note:** Blackstone was re-entered into the book today (2026-08-24, 10sh, 3.73% weight) as a live holding, not a diversifier candidate — confirmed it was never on this bench and is being explicitly excluded from consideration going forward. As a live position it now carries AI-financing tail risk (per known_gaps G82) rather than offering diversification; that overlap question belongs to smith-thesis's cluster mapping, not this bench.

**Bench hygiene:** all 8 candidates retain analyst coverage this run — none dropped. Two names moved sharply intraday (NEM +11.7%, VST -8.0% since this morning's earlier run) — flagged above, not discarded, as both remain within plausible ranges for their asset classes given today's risk-off/gold-rally backdrop.

```json
{"session_read":{"futures":{"es_pct":-0.2113,"nq_pct":-0.6993},"asia":{"kospi_pct":-3.1244,"taiex_pct":-1.0215,"nikkei_pct":-0.7396},"europe":{"stoxx50_pct":-0.162},"adr_gap_flags":[],"headline_scan":["TSMC earnings beat + higher capex guide triggered late-July/Aug profit-taking in AI/semis (SMH -9.5% trailing month); today's KOSPI-led Asia selloff reads as continuation, not a new catalyst"]},
 "sentiment_narrative":"Score 66.1 (greed), down from extreme_greed, driven almost entirely by VIX +5.1% overnight to 15.90 -- still historically low. SPX/NDX remain near 52-week highs (pct_off_52w_high pinned at 100) and 125dma/RSI14/yield-trend are all neutral (50), so the medium-term backdrop hasn't deteriorated -- this is froth cooling, not a trend break. action_hint null: no sizing override this run. Today's ESCALATING gate (KOSPI -3.12%) is faster-moving than this composite and should be weighted more heavily by the strategist for near-term sizing.",
 "diversifier_candidates":{
   "UNH":{"price_usd":390.11,"target_usd":471.65,"upside_pct":20.9,"thesis":"Managed care rebound, no capex correlation, beta 0.63","status":"active","clean_diversifier":true},
   "PG":{"price_usd":144.68,"target_usd":163.35,"upside_pct":12.9,"thesis":"Staples ballast, beta 0.38","status":"active","clean_diversifier":true},
   "NEM":{"price_usd":131.58,"target_usd":133.0,"upside_pct":1.1,"thesis":"Gold miner, zero AI-capex overlap, beta 0.50 -- safe-haven rally compressed upside to near-zero, watch for target raise","status":"active","clean_diversifier":true},
   "DUK":{"price_usd":119.85,"target_usd":138.61,"upside_pct":15.6,"thesis":"Regulated utility, beta 0.37 -- pressured -3.3% today by rising 10Y yield","status":"active","clean_diversifier":true},
   "SO":{"price_usd":88.94,"target_usd":101.45,"upside_pct":14.1,"thesis":"Regulated SE utility, beta 0.33 -- pressured -4.2% today, same rate-sensitivity as DUK","status":"active","clean_diversifier":true},
   "LLY":{"price_usd":1255.40,"target_usd":1270.37,"upside_pct":1.2,"thesis":"Pharma/GLP-1, decoupled from semis, beta 0.51 -- near 52wk high, upside largely consumed","status":"active","clean_diversifier":true},
   "JNJ":{"price_usd":270.24,"target_usd":269.95,"upside_pct":-0.1,"thesis":"Diversified pharma/medtech, beta 0.23 -- price now above analyst mean target, no cushion left","status":"stale","clean_diversifier":true},
   "VST":{"price_usd":136.21,"target_usd":223.17,"upside_pct":63.9,"thesis":"Merchant power gen; beta 1.43 confirms AI-load adjacency -- NOT a clean diversifier; down ~8% since this morning's read","status":"active","clean_diversifier":false}
 },
 "data_quality":["Analyst mean targets for the diversifier bench were carried forward from the prior run (no target-price field available from this session's yfinance tool calls) -- upside% recomputed against live prices only; targets themselves not refreshed this run.","NEM +11.7% and VST -8.0% moves since this morning's 08:55 run are large for a single session -- flagged, not discarded; plausible given today's risk-off/gold-rally backdrop but worth a sanity check on next run.","BX confirmed absent from diversifier_candidates map (never listed) -- excluded from bench going forward per its new status as a live holding with AI-financing tail risk (G82)."]}
```

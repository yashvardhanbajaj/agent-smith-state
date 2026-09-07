# Market Scout — Deep Run 2026-09-07 (US markets CLOSED — Labor Day)

## 1. Session Read

**US futures: no live pre-open read today.** ES=F 7722.0 vs SPX 7718.6 close (+0.04%) is a normal basis and tells us nothing — it's Friday's cash close plus a thin Sunday-evening futures reopen, not a genuine pre-market signal (orchestrator's own gate_note confirms: reported AMBIGUOUS, not STABILIZING, for this reason). NQ=F 29565.25 vs NDX 26506.99 (+11.5%) is **implausible as a futures basis** (normal ES/NQ basis is well under 1%) — discarded as a data artifact, flagged in data_quality, not used for any directional read.

**Asian session (closed, live moves):**
- KOSPI +4.61% — driven by SK Hynix (000660.KS) itself: **+8.26% overnight**, a very large single-name move. The book holds SK Hynix via the SKHY ADR — this is a material gap-risk flag for the next US session (Tuesday, since today is a US holiday).
- Nikkei +2.12% — notable broad move, no direct book read-through (no Japan-listed holdings).
- Taiwan Weighted +1.67%, with TSM's home listing (2330.TW) specifically +2.07% — the book holds TSM (3.24% weight). Flag: **expect TSM to gap up at the next US open.**
- Hang Seng -0.90% — sub-1%, not flagged.

**European session (live, in progress):**
- STMicroelectronics home listing (STMPA.PA) **+2.89%** overnight — book holds STM at 4.6% weight. Flag: **expect STM to gap up at the next US open.**
- ASML home listing (ASML.AS) +1.40% — positive but under the 2% flag threshold; mild tailwind only.

**Gap-risk summary for next session (Tuesday, US market reopens):** SKHY (largest flag, +8.26% home-listing move), STM (+2.89%), TSM (+2.07%) all carry gap-up risk. ASML mild positive. Combined book weight across these four names ≈ 4.6% (STM) + 3.24% (TSM) + 2.23% (SKHY) + 5.4% (ASML) ≈ 15.5% of the book with overnight-driven gap exposure at the next open.

**Headline scan:** No specific overnight/weekend breaking news found for book holdings. General semiconductor-sector coverage (Broadcom reported Q3 after close 9/2; Micron reports 9/30) but nothing new since Friday's close. Today being a US holiday, no fresh US corporate news flow expected until Tuesday.

## 2. Sentiment Narrative

Score 66.7 (greed band, unchanged from prior "greed" reading). The composite is being pulled up almost entirely by two components: VIX sub-component at 83.3 (VIX at 15.01 — comfortably low, signaling complacency) and pct-off-52w-high at 100 (SPX sitting at/near its 52-week high). The other three components — 125-day moving average position, RSI-14, and yield trend — are all sitting at neutral (50). So this is a market pricing calm and pushing highs, not a market showing broad-based technical overextension. action_hint is null (not extreme_greed), meaning no explicit sizing override is triggered for this run — greed is present but not yet at a level the strategist needs to treat as a hard caution flag. Worth remembering context: this reading is computed off Friday's close data since today's US session never opened.

## 3. Diversifier Bench (ranked, upside% × cleanliness)

| Ticker | Price | Target | Upside% | Thesis | Status | Diversifier |
|---|---|---|---|---|---|---|
| UNH | $397.14 | $471.65 | +18.8% | Managed care rebound, beta 0.62 | active | clean |
| DUK | $120.22 | $138.61 | +15.3% | Regulated utility, beta 0.36 | active | clean |
| SO | $88.11 | $101.45 | +15.1% | Regulated SE utility, beta 0.32 | active | clean |
| PG | $146.44 | $163.35 | +11.5% | Staples ballast, beta 0.38 | active | clean |
| LLY | $1149.36 | $1270.37 | +10.5% | Pharma/GLP-1, beta 0.50 | active | clean |
| VST | $149.30 | $223.17 | +49.5% | Merchant power gen, beta 1.41 | active | **PARTIAL — AI-load adjacent, not clean** |
| NEM | $128.09 | $133.00 | +3.8% | Gold miner, beta 0.54 | active | clean |
| JNJ | $275.23 | $269.95 | -1.9% | Diversified pharma/medtech, beta 0.24 | stale | clean but trading through target |

All prices above are Friday 2026-09-05 US closes carried forward — US market is closed today (Labor Day), so no new US trade occurred; `as_of` intentionally held at 2026-09-06 (no fresh data to date-stamp). Per the TTL rule, all candidates are 1 day old (<7 days) so targets/theses were reused unchanged, not re-fetched — only prices were refreshed (via the same batched yfinance call), and since the US book didn't trade today those prices are identical to the seed values in `diversifier_candidates`.

Top picks unchanged from last run: UNH still the best clean-diversifier upside; VST remains flagged partial (AI-capex-adjacent via datacenter power demand) despite the largest raw upside number — do not let its 49.5% headline upside read as a clean diversification play.

```json
{"session_read":{"futures":{"es_pct":0.04,"nq_pct":null},"asia":{"nikkei_pct":2.12,"kospi_pct":4.61,"taiwan_weighted_pct":1.67,"hang_seng_pct":-0.90,"sk_hynix_home_pct":8.26,"tsm_home_pct":2.07},"europe":{"asml_home_pct":1.40,"stm_home_pct":2.89},"adr_gap_flags":["SKHY: SK Hynix home listing (000660.KS) +8.26% overnight -- expect SKHY to gap up hard at next US open (Tuesday, holiday today)","STM: STMicroelectronics home listing (STMPA.PA) +2.89% overnight -- expect STM to gap up at next US open","TSM: Taiwan home listing (2330.TW) +2.07% overnight -- expect TSM to gap up at next US open"],"headline_scan":["No specific overnight/weekend breaking news found for book holdings as of run time; general sector coverage only (Broadcom reported 9/2, Micron reports 9/30)"]},
 "sentiment_narrative":"Score 66.7 (greed, unchanged from prior). Driven almost entirely by low VIX (15.01, sub-component 83.3) and SPX sitting at/near its 52-week high (pct_off_52w_high component 100); MA125, RSI14, and yield_trend components all neutral at 50 -- calm/highs-driven greed, not broad technical overextension. action_hint null: no sizing override triggered this run. Reading is computed off Friday's close since the US market is closed today for Labor Day.",
 "diversifier_candidates":{"VST":{"price_usd":149.30,"target_usd":223.17,"upside_pct":49.5,"thesis":"Merchant power gen, beta 1.41 -- AI-load adjacent, NOT clean","status":"active","clean_diversifier":false,"as_of":"2026-09-06"},"UNH":{"price_usd":397.14,"target_usd":471.65,"upside_pct":18.8,"thesis":"Managed care rebound, beta 0.62","status":"active","clean_diversifier":true,"as_of":"2026-09-06"},"DUK":{"price_usd":120.22,"target_usd":138.61,"upside_pct":15.3,"thesis":"Regulated utility, beta 0.36","status":"active","clean_diversifier":true,"as_of":"2026-09-06"},"SO":{"price_usd":88.11,"target_usd":101.45,"upside_pct":15.1,"thesis":"Regulated SE utility, beta 0.32","status":"active","clean_diversifier":true,"as_of":"2026-09-06"},"PG":{"price_usd":146.44,"target_usd":163.35,"upside_pct":11.5,"thesis":"Staples ballast, beta 0.38","status":"active","clean_diversifier":true,"as_of":"2026-09-06"},"LLY":{"price_usd":1149.36,"target_usd":1270.37,"upside_pct":10.5,"thesis":"Pharma/GLP-1, beta 0.50","status":"active","clean_diversifier":true,"as_of":"2026-09-06"},"NEM":{"price_usd":128.09,"target_usd":133.00,"upside_pct":3.8,"thesis":"Gold miner, beta 0.54","status":"active","clean_diversifier":true,"as_of":"2026-09-06"},"JNJ":{"price_usd":275.23,"target_usd":269.95,"upside_pct":-1.9,"thesis":"Diversified pharma/medtech, beta 0.24 -- trading through target","status":"stale","clean_diversifier":true,"as_of":"2026-09-06"}},
 "data_quality":["NQ=F 29565.25 vs NDX 26506.99 implies +11.5% futures basis -- outside plausible range (normal ES/NQ basis <1%), discarded as a likely data artifact, not used in session read","US market closed today (Labor Day) -- all US prices/futures reflect Friday 2026-09-05 close, not a live pre-open read, per orchestrator gate_note","diversifier_candidates prices unchanged from seed since no US trading occurred today; as_of intentionally not bumped to preserve honest staleness tracking"]}
```

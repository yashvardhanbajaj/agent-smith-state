# US Macro Desk — 2026-09-08 (deep)

## 1. Fed Funds & Stance
- Fed funds (target range midpoint proxy): 3.63% — CACHED, no refresh (today 2026-09-08 < next_check_date 2026-09-17; no FOMC decision has landed since the cache was set).
- Stance: hawkish (cached — no new FOMC meeting since last check).
- Next scheduled decision: 2026-09-15/16 (statement 2:00pm ET 9/16). Cache will refresh after that decision; next_check_date carried forward to 2026-09-17.

## 2. Options Sentiment
- **UNAVAILABLE THIS RUN.** No `maxpain`-script output (SPY/QQQ PCR/max-pain) was handed to this agent in slice_macro.json or found in the run directory — the orchestrator did not attach a precomputed options file for this run. Per standing instruction this desk does not compute PCR/max-pain itself (COMPUTE-FIRST violation risk, and the yfinance fallback's OI-is-always-0 problem documented in this skill's history). All four PCR/max-pain fields are null. Flagged in data_quality.
- Context only (already in market_inputs.json, not refetched): VIX 15.69, up from a ~13.8 52-week-range floor but well off the 28 high; sentiment composite score 72.4 ("greed" band, prior run also "greed") — vix sub-score 86.7 is the single largest driver of the greed reading, i.e. options/vol pricing is complacent even without a PCR read. Treat this as a soft proxy for options positioning, not a substitute for actual PCR/max-pain.

## 3. Calendar
- **Next FOMC decision: 2026-09-15 to 09-16** (statement 2:00pm ET 9/16, includes updated Summary of Economic Projections + press conference) — **falls within the next 5 trading days** (Tue 9/8 → Wed 9/9, Thu 9/10, Fri 9/11, Mon 9/14, Tue 9/15 is the 5th trading day; decision lands on day 6, statement close enough to be inside the pre-positioning window).
- **Next CPI print: 2026-09-11 (Friday, 8:30am ET)** — **falls within the next 5 trading days** (3rd trading day from today).
- Next NFP (jobs report): September's print already landed 2026-09-04 (Friday, pre-Labor-Day, consistent with BLS's August Employment Situation release). Next NFP is the October print, expected ~2026-10-02 (first Friday of October, standard BLS cadence) — not confirmed by name in this search, treat as approximate. Outside the 5-trading-day window.
- Other BLS prints in-window: PPI 2026-09-10, JOLTS 2026-09-29 (context only, not scoped to this desk's named triggers).
- Mega-cap ("Magnificent Seven"-adjacent) earnings-season window: NOT currently active. Mid-Jul/mid-Oct through end-of-month is the next window; 2026-09-08 sits in the gap between the Jul/Aug window's close and the mid-Oct window's open.
- **Compressed-week flag: this is the first session after the Labor Day long weekend, and it now contains BOTH a CPI print (9/11) and an FOMC decision (9/15-16) inside the same 5-trading-day lookout window** — unusually dense event risk for the book's AI-capex-heavy positioning.

## 4. Regime Read
Risk read is neutral-to-cautiously-risk-on on the tape (SPX 7718.6 sits ~98.7% of its 52-week high of 7816.7, NDX RSI14 53.4 — mid-range, no overbought/oversold extreme) but VIX's forward posture (+2.55% on thin holiday futures, prompting an AMBIGUOUS gate classification rather than STABILIZING) and Asia's soft overnight session (Nikkei -1.7%, KOSPI -0.58%, TWII -0.47% — the last two directly relevant to the book's semicap/memory supply chain) argue against calling this clean risk-on. The 10-yr at 4.784%, up 12.4bp over the past month, combined with the cached hawkish FOMC stance, is the dominant cross-asset signal into a week carrying both a CPI print and an FOMC decision.

**Cluster impact:**
- **AI-capex chain (95.4% of this book):** Pressured near-term by the rate move — a 12.4bp/month rise in the 10-yr with a hawkish Fed read compresses forward multiples fastest for the AI-capex chain's higher-multiple names, and Asia's overnight weakness in Korea/Taiwan (KOSPI, TWII) is a direct read-through to the memory/semicap supply chain this book is concentrated in. The compressed CPI+FOMC week ahead is the acute near-term risk window for this cluster specifically.
- **Rate-sensitive/long-duration growth:** Same pressure, first and hardest — duration-sensitive multiples reprice fastest on the 10-yr's continued climb and a hawkish-cached Fed stance holding into the 9/15-16 decision.
- **Defensive/diversifier bench:** Relatively favored on a relative basis this week — if CPI surprises hot or the FOMC statement holds a hawkish line, the defensive bench is the natural rotation destination and is the least exposed to the Asia-session softness hitting the semicap/memory chain.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"hawkish","next_check_date":"2026-09-17"},
 "spy_pcr":null,"spy_pcr_oi":null,"spy_pcr_vol":null,"spy_pcr_oi_source":null,"spy_pcr_vol_source":null,"spy_max_pain":null,"qqq_pcr":null,"qqq_pcr_oi":null,"qqq_pcr_vol":null,"qqq_pcr_oi_source":null,"qqq_pcr_vol_source":null,"qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-09-15/16","next_cpi":"2026-09-11","next_nfp":"~2026-10-02 (unconfirmed)","earnings_season_window":false},
 "regime":"neutral","regime_note":"SPX near 52w high but VIX firming on thin futures (gate=AMBIGUOUS), 10y +12.4bp/1m with cached hawkish FOMC, soft Asia overnight (Nikkei -1.7%) hitting the memory/semicap chain directly; CPI (9/11) and FOMC (9/15-16) both land inside the next 5 trading days.",
 "cluster_impact":{"ai_capex_chain":"pressured near-term by rising 10y + hawkish Fed read + soft Asia semicap/memory tape; acute risk window is this compressed CPI+FOMC week","rate_sensitive":"pressured first and hardest by continued 10y climb and hawkish-cached stance into 9/15-16 decision","defensives":"relatively favored this week as rotation destination if CPI or FOMC surprises hawkish"},
 "data_quality":["options PCR/max-pain unavailable this run — no maxpain-script output was provided in slice_macro.json or found in the run directory; all four PCR/max-pain fields null rather than computed or guessed","next NFP date is an inferred first-Friday-of-October estimate, not confirmed by name in the web search results","fomc_cache reused verbatim per next_check_date gate — not independently re-verified this run"]}
```

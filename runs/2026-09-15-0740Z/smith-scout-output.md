# Market Scout / US Macro — 2026-09-15 (DEEP, pre-open)

## 1. Session read

- **Futures**: ES +0.53%, NQ +0.69% (market_inputs.json, as-of 2026-09-15T07:41Z) — modest green ahead of the open, i.e. a pause/stabilization bid the morning after yesterday's rout, not a continuation of it. (Note: the dispatch's inline context said ES/NQ were "unavailable (null)" — the actual `market_inputs.json` carries real non-null values; treating the file as the source of truth over the inline summary.)
- **Asia/Europe**: Nikkei -0.01%, KOSPI -0.85%, TAIEX -0.77%, STOXX50 -0.52% — all under the 1% flag threshold, no discrete gap-risk read from Asia today (KOSPI/TAIEX closest to the line; TSM's Taipei listing and the broader memory/foundry complex were soft but not disorderly).
- **Gap risk on the book**: yesterday's (09-14) session was an AI-capex-chain rout — SMH -4.75% (index), Optics/Networking cluster -8.86%, OEM -8.41%, Power/Cooling -7.47%, Semis/Fabs -5.99%. Largest single-name day_chg_pct hits carried into today's gap: **GLW -12.75%, TER -12.28%, COHR -11.39%, ALAB -11.15%, STM -6.83%, GEV -8.30%, LITE -8.73%, CLS -8.41%, VRT -7.04%, ASML -6.38%, AMAT -6.42%**. These are the names most exposed to a follow-through gap at the open, though green futures this morning argue for at least a partial stabilization.
- **Headline scan** (post-watermark, headline-level only — smith-signals owns per-holding depth): NVDA reportedly down >3% and MU down >5% at yesterday's close, with the iShares Semiconductor ETF (SOXX) off >5%, on a combination of (a) "AI uncertainty" — reported industry disagreement over the pace of AI infrastructure build-out — and (b) the FOMC decision now priced at a 90%+ probability of a hike. Source: [Yahoo Finance/Stocktwits, "Dow, S&P 500, Nasdaq Futures Mixed Ahead Of Fed Rate Decision As AI Uncertainty Mounts"](https://finance.yahoo.com/markets/stocks/articles/dow-p-500-nasdaq-futures-025145385.html), ~2026-09-15.

## 2. Sentiment narrative

The precomputed composite sentiment score sits at **69.8 ("greed" band, unchanged from the prior run's "greed")**, with `action_hint: null` — no extreme-greed/extreme-fear override for the strategist to size against this run. Component detail explains the disconnect from yesterday's carnage: the score is being held up by trend/proximity components (89.9 on distance-off-52-week-high, 68.7 on the 125-day MA, 66.0 on yield trend) even as RSI14 sits neutral at 46.7 and the VIX component reads 77.5. Read this as a lagging, trend-following composite — per its own note, "not CNN's Fear & Greed Index" — rather than a real-time fear gauge; it has not yet caught down to the acute -4.75% SMH / -8.86% optics drawdown or the binary FOMC event risk landing tomorrow. Take the "greed" label as background context, not a green light — the strategist should lean on the fresher price/vol data and this run's FOMC read, not this score, for today's sizing.

## 3. Fed funds & FOMC stance — the priority item

**Cache status**: today (2026-09-15) is before `fomc_cache.next_check_date` (2026-09-17), so per the standing rule the cache's `rate_pct`/`stance` fields are reused verbatim — **cached, no FOMC meeting has concluded since last check.** The actual decision lands tomorrow, 2026-09-16, 2:00pm ET; refresh is due the run *after* 2026-09-17 once the outcome is known.

**Target range going in**: 3.50%–3.75% (midpoint 3.625% ≈ the cached 3.63 fed_funds_pct — consistent, not a guess). Source: [Kiplinger, "September Fed Meeting: Live Updates and Commentary"](https://www.kiplinger.com/investing/live/fed-meeting-updates-and-commentary-september-2026); [FedRateCalc, FOMC schedule](https://fedratecalc.com/fomc-meeting-schedule/september-2026/), both accessed 2026-09-15. The FOMC held that range 9-3 at its July 28-29 meeting.

**Priced for 09-16 (VERIFY request)**: the dispatch flagged a specific claim — hike odds "57%→88.5% on 09-14" — as an extraordinary claim needing a named source. What I found:
- CME FedWatch-cited probability of a 25bp hike has moved sharply higher through the cycle: ~56% (right after Chair Warsh's Jackson Hole speech, undated aggregator), ~66% (Forbes, 2026-08-31, citing CME FedWatch), briefly framed as a "coin flip" (~50%, CNBC, 2026-08-28 — note this predates the Forbes 66% read, so the trajectory is not perfectly monotonic across outlets), then **90.7%** (24/7 Wall St, 2026-09-14, explicitly citing CME FedWatch) and **92.4%** (Yahoo Finance/Stocktwits, ~2026-09-15, also citing CME FedWatch).
- **Verdict**: the dispatch's 88.5% figure could not be pinned to one exact named tier-1 print, but it is directionally and magnitude-corroborated — two independent citations of CME FedWatch itself, dated 09-14 and ~09-15, both land in the **90-92% range** for a 25bp hike. Treat "high-80s to low-90s percent, hike is the base case" as the verified read, not the specific 88.5 print. Cross-platform dispersion is real: Kalshi ~57%, Polymarket ~49% were cited in one aggregator alongside CME's ~60% (dated earlier in the cycle) — prediction markets have been running cooler than CME FedWatch throughout.
- Sources: [24/7 Wall St, "Chances of First Fed Rate Hike Since 2023 Now Over 90%"](https://247wallst.com/investing/2026/09/14/chances-of-first-fed-rate-hike-since-2023-now-over-90-markets-brace-for-the-warsh-era-shock/), 2026-09-14; [Yahoo/Stocktwits, "Dow, S&P 500, Nasdaq Futures Mixed Ahead Of Fed Rate Decision"](https://finance.yahoo.com/markets/stocks/articles/dow-p-500-nasdaq-futures-025145385.html), ~2026-09-15; [Forbes, "CME FedWatch Provides A 66% Chance Fed Will Hike Rates In September"](https://www.forbes.com/sites/digital-assets/2026/08/31/cme-fedwatch-provides-a-66-chance-fed-will-hike-rates-in-september/), 2026-08-31. Direct fetch of the CME FedWatch tool page itself timed out — relied on secondary citations of it.
- This would be **the first hike since 2023** if delivered — a regime-defining event, not a routine adjustment.

**Dot plot / SEP expectations**: June 2026's SEP showed the median dot at ~3.8% fed funds by year-end 2026 (i.e., one more 25bp hike priced by the Fed's own committee at that point), with 9 of 19 participants projecting at least one 2026 hike vs 8 projecting no change. Inflation (PCE) projections were revised up 0.9pt to 3.6% for year-end 2026; 2026 real GDP growth cut ~20bp to 2.2%. Source: [TradingKey, "June Fed Decision Delivered: Rates Held Unchanged but Dot Plot Significantly Raised"](https://www.tradingkey.com/analysis/economic/central-banks/261973912-fed-federal-fomc-2-economic-projections-decision-rates-tradingkey), June 2026. The September SEP (due with tomorrow's decision) will update this — watch whether the median dot for 2026 moves to reflect a hike already delivered/pending, and whether 2027 dots show a pause or a second hike.

**Key swing variable into 09-16**: inflation stickiness (oil-driven per multiple sources — "oil reignites inflation" framing) and labor-market steadiness are the two data threads markets are watching; the 10yr at 4.96% (+32bp over the trailing month per `market_inputs.json us10y_chg_1m_bps`, though flat/-1.4bp today) has already done a lot of the hawkish repricing work ahead of the meeting itself.

## 4. Options positioning

`compute_options.json`: **SPY and QQQ both show `max_pain: null`, `pcr_oi: null` across both listed expiries (2026-09-21, 2026-09-22)** — "open interest is zero across every strike," the file's own data_quality note (the recurring G18 signature). This is legitimate for a 03:45 ET pre-open run — Yahoo reports zero OI outside market hours. **Options positioning is unavailable pre-market; no complacency/fear or spot-vs-max-pain read is possible from this file this run.** No boundary_artifact flag present (moot given null underlying data). Re-check once the cash session opens and OI populates — especially relevant into an FOMC day, where max-pain/PCR readings tend to compress toward the event.

## 5. Calendar + regime read

**Calendar**:
- **FOMC decision: 2026-09-16, 2:00pm ET** — inside 5 trading days (it's tomorrow). Full 2026 schedule confirms next meeting after this one is **2026-10-27/28**. Source: [Federal Reserve Board meeting calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) / aggregator cross-check, 2026-09-15.
- **Next NFP (Sept 2026 data): 2026-10-02**, 8:30am ET. Source: BLS Employment Situation schedule.
- **Next CPI (Sept 2026 data): 2026-10-14**, 8:30am ET. Source: [Nowflation CPI release calendar](https://nowflation.com/cpi-release-dates); BLS.
- **Mega-cap earnings window**: not open. Q3 earnings season for the book's mega-caps (MSFT, GOOG, AMZN, AVGO etc.) typically starts late October; nothing found flagging an early print inside the current window.

**Regime read (3-4 lines)**: This is a **risk-off setup walking into a binary catalyst**. The 10-yr has already repriced +32bp over the trailing month (`us10y_chg_1m_bps`) even though today's print is flat (-1.4bp), and VIX is up 1.9% to 17.43 — elevated but not panicked, consistent with a market that has partially, not fully, priced the hawkish outcome. Yesterday's -4.75% SMH / -8.86% optics air-pocket looks like the market pulling forward the "first hike since 2023" repricing plus an idiosyncratic AI-buildout-pace scare, ahead of confirmation tomorrow; green ES/NQ futures this morning read as a pause, not an all-clear. **cluster_impact**:
- **AI-capex chain** (VRT, ASML, GEV, ALAB, KLAC, TSM, TER, COHR, AMAT, CLS, LITE, APH, MRVL, NBIS, AMD, MU, QCOM, WDC, STM, AVGO, GLW, CIEN — the bulk of the book): this cluster gets hit first and hardest under any of the three FOMC scenarios except a clean dovish surprise. A **hawkish surprise** (hike delivered + hawkish dots/guidance for more) presses long-duration AI-capex multiples further — yesterday's optics/networking -8.86% is the preview. **As-priced** (25bp hike, ~90% already priced) still confirms the first-hike-since-2023 regime shift; expect a "sell-the-news" or at best flat reaction given how much is already in the tape, with continued differentiation between cash-generative franchise names (TSM, AVGO, ASML) and higher-beta capex-cycle names (ALAB, TER, COHR, LITE, GLW) that led yesterday's decline. **Dovish surprise** (hold, or hike with clearly dovish forward guidance) is the one scenario that unwinds yesterday's move — this cluster has the highest snap-back beta of anything in the book.
- **Rate-sensitive / long-duration growth** (overlaps heavily with the above — GEV, VRT, ALAB, NBIS carry the highest duration/multiple sensitivity): most exposed to the hawkish-surprise tail; a surprise hold triggers the sharpest relief given how consensus a hike has become (90-92%).
- **Defensives / diversifiers** (bench names — UNH, SO, DUK, PG, LLY, NEM, JNJ; VST excluded as AI-adjacent): relative outperformers in both hawkish and as-priced scenarios by construction (low beta, 0.24-0.62). Regulated utilities (SO, DUK) carry their own modest rate sensitivity but far less multiple compression than growth names. NEM (gold) is the one name where a hawkish/higher-real-rate outcome is a mechanical headwind, partially offset by any risk-off flow into gold.

## 6. Diversifier bench (refreshed)

Prices refreshed via yfinance batch call, 2026-09-15 (last trade, ~2026-09-14 session given pre-open timing). `target_usd`/`thesis` were **9 days stale (as_of 2026-09-06, exceeds the 7-day threshold)** and would normally be re-fetched this run, but tool budget was prioritized to the FOMC deep-dive the dispatch explicitly asked for — targets/thesis carried forward unchanged this run, flagged for refresh next full run.

Ranked by upside × cleanliness (clean names only; VST shown for completeness but excluded from the clean ranking):

| Ticker | Price | Target | Upside | Clean | Thesis (carried, as_of 2026-09-06) |
|---|---|---|---|---|---|
| UNH | 383.55 | 471.65 | 23.0% | yes | Managed care rebound, beta 0.62 |
| SO | 87.00 | 101.45 | 16.6% | yes | Regulated SE utility, beta 0.32 |
| DUK | 119.02 | 138.61 | 16.5% | yes | Regulated utility, beta 0.36 |
| PG | 146.13 | 163.35 | 11.8% | yes | Staples ballast, beta 0.38 |
| LLY | 1138.28 | 1270.37 | 11.6% | yes | Pharma/GLP-1, beta 0.50 |
| NEM | 123.07 | 133.00 | 8.1% | yes | Gold miner, beta 0.54 |
| JNJ | 266.32 | 269.95 | 1.4% | yes | Diversified pharma/medtech, beta 0.24 |
| VST | 140.73 | 223.17 | 58.6% | **no** | Merchant power gen, beta 1.41 — AI-load adjacent, NOT clean |

VST's headline upside is the largest on the bench by a wide margin but it stays excluded from the clean ranking (AI-load adjacent). Top clean pick by upside is UNH, unchanged from the prior run.

## Data quality / gaps
- SPY/QQQ options: unavailable pre-market (zero OI across all strikes) — legitimate for a 03:45 ET run, not an error.
- FOMC hike-probability figures are dispersed across outlets (49%-92%); the two most credible citations (both explicitly sourced to CME FedWatch, dated 2026-09-14 and ~2026-09-15) cluster at 90-92%. The dispatch's specific "88.5%" print could not be independently verified at that exact value — treat the verified range as high-80s to low-90s percent.
- No SMH-specific historical FOMC-day/hawkish-surprise statistic could be sourced to a named outlet; a general, loosely-attributed market stat surfaced (S&P 500 down ~3.4% on average in the month following the first hike of a new tightening cycle, over the last 30+ years) but without a precisely named originating source in the search result — reported here as unattributed/low-confidence and explicitly NOT used as a hard SMH forecast number.
- Direct fetch of the CME FedWatch tool page timed out; relied on secondary tier-adjacent citations of it instead.
- Diversifier bench: target_usd/thesis retained from 2026-09-06 (9 days stale) rather than refreshed, due to tool-budget prioritization toward the FOMC research this run.

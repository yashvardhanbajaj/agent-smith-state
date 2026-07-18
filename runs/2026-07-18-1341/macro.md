# US Macro Desk — Deep Review, 2026-07-18 (reviewing Fri 2026-07-17 close)

FIRST-EVER dispatch for this book. fomc_cache seeded this run (was empty in state.json).

## 1. Fed Funds & Stance

- **Target range: 3.50%–3.75%**, effective fed funds rate ≈ **3.63%**, held at the June 16–17, 2026 FOMC meeting.
- **Stance: hawkish.** The June FOMC minutes/dot plot shifted materially hawkish: median year-end-2026 fed funds projection raised to 3.8% (from 3.4% in March) — i.e., no cuts priced in for the rest of 2026, with 9 of 18 members actually looking for a hike. Chair Warsh flagged inflation "remains elevated" vs the 2% goal. This is a swing from the March SEP, which had shown an expected cut.
- **Next FOMC decision: July 29, 2026** (meeting July 28–29; this is a non-SEP meeting, no updated dot plot). Consensus expects hold, with the Fed keeping the door open to a further hike if inflation stays sticky.
- fomc_cache seeded with `next_check_date = 2026-07-30` (day after the upcoming decision) — no need to re-search Fed stance on any run between now and then; refresh triggers the day after the meeting.

Sources: [Federal Reserve FOMC statement 6/17/26](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm), [FOMC Minutes June 16-17 2026](https://www.federalreserve.gov/monetarypolicy/fomcminutes20260617.htm), [Fed Meeting Tracker — Forbes](https://www.forbes.com/sites/investor-hub/article/fed-meeting-tracker-interest-rate-strategy/), [Fed Rate Calc FOMC schedule](https://fedratecalc.com/fomc-meeting-schedule/)

## 2. Options Sentiment — Market Level

**PCR (Barchart, put/call ratios page):**
| Proxy | Put/Call OI ratio | Put/Call volume ratio | Total OI |
|---|---|---|---|
| SPY | 1.86 | 1.52 | 15,348,820 |
| QQQ | 1.38 | 1.38 | 9,363,371 |

Both ratios sit well above 1.0 — "generally considered bearish" per the page's own framing, i.e., more puts outstanding/traded than calls on both the broad market and mega-cap-tech proxy. SPY's skew (1.86 OI) is notably heavier than QQQ's (1.38), consistent with broad-market hedging demand outpacing tech-specific hedging after Friday's -1.01% SPX / -1.40% NDX day.

**Max pain (nearest expiry, 2026-07-20, computed from a single-expiry chain):** SPY ≈ **$745–746** (underlying $743.29 at fetch); QQQ ≈ **$697–698** (underlying $695.33 at fetch). **Caveat:** the option-chain tool returns only an ATM-anchored strike window (~7 strikes each side), not the full chain — pain was still declining monotonically toward the edge of the visible window in both names, so the true max-pain strike may sit outside what was sampled. Treat these max-pain levels as low-confidence/approximate, not a precise pin level.

**VIX context (from market_inputs.json, not refetched):** 18.77, +12.2% on Friday, still well inside its 52-week range of [13.38, 35.30]. Read: options market is pricing **defensive hedging, not despair** — the PCR skew shows real fear/hedging demand building, but VIX's absolute level is nowhere near panic/capitulation territory. This looks like a sharp single-day risk-off repricing rather than a full-blown volatility regime shift — worth re-checking if VIX keeps climbing.

## 3. Calendar

- **Next FOMC decision:** July 29, 2026
- **Next CPI print:** August 12, 2026 (covers July 2026 data)
- **Next NFP (jobs report):** August 7, 2026 (covers July 2026 data)
- **Mega-cap earnings (book holds NVDA, META, GOOG, AMD, ORCL, ASML, TSM):**
  - TSM (2330.TW) — already reported July 16, 2026 (this week; its -7.29% Friday ADR-lead move is a company/supply-chain-specific data point, not new earnings news)
  - **GOOG (Alphabet) — reports July 22, 2026 — inside the next 5 trading days (Mon 7/20 is a holiday-free open; 7/22 is the 3rd trading day out from today).** Flag: earnings-season volatility window is live for this book right now.
  - AMD — August 4, 2026 (outside 5-trading-day window)
  - NVDA — August 26, 2026 (confirmed per 8-K; outside window)
  - META, ORCL, ASML — specific Q2/FY2026 dates **not confirmed** via available search results; flagged in data_quality, not guessed.
- **Earnings-season window flag: TRUE.** Today (7/18) falls inside the mid-July mega-cap earnings season window (roughly mid-Jul through end of month), and GOOG's confirmed 7/22 print is inside the 5-trading-day lookahead — this is exactly the period where portfolio volatility around AI-capex/hyperscaler names typically spikes, and it's arriving on top of an already-volatile week.

Sources: [BLS CPI release schedule](https://www.bls.gov/schedule/news_release/cpi.htm), [BLS Employment Situation schedule](https://www.bls.gov/schedule/news_release/empsit.htm), [Q2 2026 tech earnings watch — MarketBeat](https://marketbeat.com/originals/what-to-expect-from-q2-earnings-as-tech-strength-broadens/), [AMD Q2 2026 earnings date](https://www.startuphub.ai/ai-news/semiconductors/2026/amd-sets-q2-2026-earnings-date), [NVIDIA 8-K filings — SEC](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000019/q4fy26pr.htm)

## 4. Regime Read

**Overall: risk-off, and it is hitting this book's single concentrated bet directly.** Friday's selloff (SPX -1.01%, NDX -1.40%, VIX +12.2% to 18.77) was led internationally by a Taiwan/Korea-centric shock — Nikkei -4.03%, KOSPI -6.37% (the *second* severe Korea selloff in a week, following last week's -8.95%), Taiwan index -6.47%, and TSM's Taiwan listing -7.29% (the single largest ADR-lead move tracked all week). That pattern — repeated, severe drawdowns concentrated in the exact geographies that supply the AI-capex chain's foundry/memory/advanced-packaging inputs — reads as supply-chain-specific stress layered on top of, not merely coincident with, generic macro risk-off.

Layer the Fed backdrop on top: a hawkish FOMC (no cuts priced, dot plot raised to 3.8%, one member short of a hike-majority) with the 10-yr at 4.541% (up modestly from 4.451% a month ago, per market_inputs — note this is a rise, not the decline the trailing-month framing implies) keeps the discount-rate headwind live for long-duration, forward-multiple growth names. The AI-capex chain's names are simultaneously the market's highest-multiple growth complex *and* now the epicenter of a real supply-chain wobble — they feel both the rate pressure and the idiosyncratic Asia shock first and hardest.

**Cluster impact given this book's 99.3% AI-capex-chain concentration (highest ever recorded for this book):**
- **AI-capex chain: pressured, acutely.** This is the transmission channel for virtually all of today's book-level drawdown. The Taiwan/Korea-specific severity (not just a broad index move) suggests semis/memory/foundry names within the cluster are repricing a supply-chain risk premium, not just a macro beta hit. GOOG's earnings on 7/22 adds a near-term binary catalyst inside this same cluster's orbit (hyperscaler capex commentary).
- **Rate-sensitive/long-duration growth: pressured.** Hawkish Fed + 10yr near the top of its recent range raises the discount-rate drag on forward multiples — this overlaps heavily with the AI-capex cluster in practice for this book, compounding rather than diversifying the hit.
- **Defensives/diversifiers: favored in relative terms, but the book holds essentially none (0.7% ex-AI-capex) at a 99.3% concentration reading** — there is no ballast currently in place to benefit from any defensive rotation, which is the central vulnerability this regime read exposes for the strategist's stress table.

VIX's still-moderate absolute level (18.77 vs a 52-wk range topping out at 35.30) argues this is a sharp single-day/single-week wobble rather than a confirmed regime change — but the *second* severe Korea selloff in a week is a repeat-event pattern worth escalating, not dismissing as one-off noise.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"hawkish","next_check_date":"2026-07-30"},
 "spy_pcr":1.86,"spy_max_pain":745,"qqq_pcr":1.38,"qqq_max_pain":697,
 "calendar":{"next_fomc":"2026-07-29","next_cpi":"2026-08-12","next_nfp":"2026-08-07","earnings_season_window":true},
 "regime":"risk_off","regime_note":"Hawkish FOMC (no cuts priced, dots raised to 3.8%) plus 10yr near recent range top (4.541%) pressures long-duration growth broadly; Friday's selloff was led by severe, repeated Taiwan/Korea-specific stress (TSM ADR -7.29%, KOSPI -6.37% second severe drop in a week) pointing to AI supply-chain-specific risk on top of generic macro risk-off. VIX 18.77 still well inside 52wk range — sharp wobble, not yet a confirmed regime break.",
 "cluster_impact":{"ai_capex_chain":"pressured acutely — primary transmission channel for today's drawdown; Taiwan/Korea severity signals supply-chain-specific stress, not just index beta; GOOG earnings 7/22 adds a near-term catalyst","rate_sensitive":"pressured — hawkish Fed + 10yr near range top raises discount-rate drag on forward multiples, overlapping heavily with the AI-capex cluster in this book","defensives":"relatively favored in the regime but the book holds ~0.7% ex-AI-capex at 99.3% concentration — no ballast currently in place"},
 "data_quality":["SPY/QQQ max-pain computed from an ATM-anchored strike window only (~7 strikes), not the full chain — pain was still declining toward the window edge in both names, so true max-pain strike may lie outside the sampled range; treat as low-confidence/approximate","META, ORCL, ASML specific Q2/FY2026 earnings dates not confirmed via search — omitted rather than guessed","10yr yield framing in market_inputs.json ('down ~9bps over trailing month') appears inconsistent with the two data points supplied (4.541% now vs 4.451% a month prior is a +9bp rise); reported the raw figures as given without correcting the source framing"]}
```

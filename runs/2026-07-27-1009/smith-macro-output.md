# US Macro Desk — 2026-07-27

## 1. Fed Funds & Stance
- Effective Fed funds target: **3.63%** (cached — no new FOMC meeting since last check, per fomc_cache; next_check_date 2026-07-29).
- Last FOMC statement stance: **HAWKISH** (cached, unchanged).
- **CONVERGENCE FLAG:** 2026-07-29 (this Wednesday) is simultaneously (a) this book's next FOMC-cache refresh date / live decision day, and (b) LRCX and QCOM earnings day — two AI-capex-chain holdings reporting the same session as a Fed decision. This is an unusually loaded single-day catalyst: a hawkish surprise plus a capex-chain earnings miss (or vice versa) could compound rather than offset. Treat 07-29 as the week's key risk date.

## 2. Options Sentiment — Market Level
- **SPY** (Barchart, live): put/call **open-interest ratio 1.95**, put/call **volume ratio 1.35**, total OI 16.3M contracts (10.78M puts / 5.53M calls). Up slightly from the 07-20 read (1.86 OI-ratio) — modestly more put-heavy positioning, consistent with hedging into the 07-29 FOMC rather than acute fear.
- **QQQ**: Barchart put-call page returned HTTP 404 (page unavailable). Fallback: computed PCR from the single nearest (0DTE, 2026-07-27) expiry's option **volume** — put/call volume ratio ≈ **1.56** (141,923 put vol / 91,105 call vol). This is a 0DTE-volume proxy, noisier than an OI-based ratio and not directly comparable to the 07-20 reading (1.38, also a fallback) — treat as directional only.
- **Max pain (SPY & QQQ): still unavailable** (G18 persists) — `get_options` returns openInterest=0/null across all strikes/expiries for both names on this feed; no reliable max-pain strike could be computed. Discarded rather than guessed.
- **VIX context** (from market_inputs.json, not refetched): 18.58, **down 0.64%** on the day, well inside its 52-week range (13.6–31.05) and calmer than the 07-20 read. Options market is pricing **relative complacency** — elevated OI-based PCR looks like structural/hedging positioning rather than fear, given VIX's continued grind lower and futures gapping up pre-open (ES +0.73%, NQ +1.21%).

## 3. Calendar
- Next FOMC decision: **2026-07-29** (Wed) — also LRCX/QCOM earnings day (see convergence flag above).
- Next CPI print: **2026-08-12** (Wed).
- Next NFP (jobs report): **2026-08-07** (Fri).
- Next FOMC after that: 2026-09-15–16 (statement 09-16), for context only — outside the 5-day window.
- Mega-cap ("Mag-7"-adjacent) earnings-season window: **currently active** — Q2 2026 earnings season runs mid-July through end of July, and today (07-27) sits inside it. **Within the next 5 trading days**, the FOMC decision (07-29) coincides with the earnings window, and LRCX/QCOM specifically report same-day — flagging per task instructions as elevated near-term volatility risk for the book.

## 4. Regime Read
Risk backdrop is **mixed-to-mildly-risk-on near-term, fragile underneath**: the 10-yr has pushed to 4.679% (+27.7bps over the past month) against a still-hawkish Fed read (3.63% funds rate, cached), which is the textbook headwind for long-duration growth — but VIX has eased to 18.58 (down on the day, well off recent highs) and futures are gapping up hard pre-open (NQ +1.21%), suggesting the tape is choosing to look through the hawkish stance for now. SPX at 7412 sits ~2.2% below its 52-week high (7580) and comfortably above its 125dma (7127), with NDX RSI14 at a neutral 50.9 — no overbought or oversold extreme. Options positioning (SPY PCR near 1.95 OI-based) reads as hedging demand into 07-29, not panic. Net: call this **neutral, tilting risk-on into a binary catalyst**. For the book's clusters — the **AI-capex chain** is the one to watch hardest: it benefits from the futures gap-up and calm VIX today, but sits directly in the blast radius of the 07-29 FOMC+earnings convergence (LRCX/QCOM), and remains structurally exposed to the rate/duration headwind if the Fed reads even more hawkish than cached. **Rate-sensitive/long-duration growth** names remain the most consistently pressured cluster given the 10-yr's climb — this hasn't improved since 07-20. **Defensives/diversifiers** are relatively favored on a risk-adjusted basis but the case for adding is less urgent than 07-20 given VIX has come in; maintain rather than expand the bench, and treat 07-29 as the trigger point for re-assessing.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":1.95,"spy_max_pain":null,"qqq_pcr":1.56,"qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-07-29","next_cpi":"2026-08-12","next_nfp":"2026-08-07","earnings_season_window":true},
 "regime":"neutral","regime_note":"Hawkish Fed + rising 10yr vs calm/falling VIX and gap-up futures; 07-29 FOMC+LRCX/QCOM earnings convergence is the key near-term binary risk.",
 "cluster_impact":{"ai_capex_chain":"pressured by rate backdrop, but short-term tailwind from futures gap-up; high event risk 07-29 (FOMC + LRCX/QCOM same day)","rate_sensitive":"most consistently pressured cluster, unchanged from 07-20 — 10yr at cycle highs","defensives":"relatively favored, less urgently needed than 07-20 given calmer VIX; maintain bench, reassess post-07-29"},
 "data_quality":["SPY PCR from Barchart (OI ratio 1.95, volume ratio 1.35) — reliable","QQQ Barchart page 404'd; QQQ PCR (1.56) is a 0DTE single-expiry volume-based fallback, not OI-based — noisier, not directly comparable to prior reads","G18 persists: SPY/QQQ max-pain unavailable — get_options openInterest returns 0/null across all strikes/expiries for both tickers on this feed","fomc_cache_update next_check_date set to day after next scheduled FOMC (2026-09-16 decision -> 2026-09-17)"]}
```

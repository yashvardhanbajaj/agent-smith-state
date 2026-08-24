# US Macro Desk — 2026-08-24 (deep, pre-open)

## 1. Fed Funds & Stance
Fed funds target range midpoint (13-wk bill proxy, cached): **3.63%**. Last FOMC statement read: **HAWKISH**. Cache reused verbatim — today (2026-08-24) is before `next_check_date` (2026-09-17), so no new FOMC meeting has occurred since the last check; no re-search performed.

## 2. Options Sentiment — Market Level
Source: Barchart put/call ratio pages (server-rendered), verified working.

**SPY**: put/call OI ratio **2.54** (put OI 13,109,107 vs call OI 5,159,982) [source: barchart]; put/call volume ratio **1.36** [source: barchart]. Both readings elevated (>1.0 = bearish per Barchart's own framing), and the OI ratio has been climbing — 1.88 (08-03) → 2.29 (08-07) → 2.54 (today) — a steady build in protective put positioning over three weeks.

**QQQ**: put/call OI ratio **1.19** (put OI 5,944,707 vs call OI 4,988,018) [source: barchart]; put/call volume ratio **1.24** [source: barchart]. Bearish-leaning but far less skewed than SPY — index-level hedging is concentrated in the broad-market proxy, not the tech-heavy one, which is itself informative: the book's AI-capex names sit mostly in NDX-land, so the sharper hedging pressure is coming from broad-market (rate/macro) worry, not tech-specific worry, at least as of this snapshot.

**Max pain**: unavailable for both proxies. Attempted one `get_options` call on SPY's nearest expiry (2026-08-24) to compute it; confirmed (again) that yfinance's chain returns **open interest of 0 on every single strike** — bid/ask also 0, only Last/Volume/IV populated. Max pain is OI-weighted and cannot be computed from an all-zero OI array; Barchart's ratio page publishes only aggregate OI totals, not per-strike OI. This is the known, standing gap (G18, `wont_fix`) — re-confirmed here rather than papered over. QQQ chain was not separately pulled since the same structural limitation applies and a second confirming call would not change the conclusion (budget discipline).

**VIX context** (from market_inputs.json, not refetched): **15.90** — low, complacent by historical standards. This is the notable divergence of the day: SPY put OI is at its highest level in three weeks of tracking, yet VIX sits in the low-teens/mid-teens with no visible stress premium. Read: options desks are building/rolling downside protection ahead of realized volatility, while the VIX (a near-dated, ATM-weighted gauge) hasn't yet caught the Asia-led selloff currently in progress pre-open. Don't read 15.90 as "all clear" — it is a lagging signal relative to the put-OI buildup and the overnight tape.

## 3. Calendar
- **Next FOMC decision**: 2026-09-16 (implied by cache's `next_check_date` of 2026-09-17, the day after) — 17 trading days out, not within the 5-day window.
- **Next CPI print**: 2026-09-11 (BLS, August 2026 CPI) — not within the 5-day window.
- **Next NFP (jobs report)**: 2026-09-04 (BLS, August 2026 employment situation) — 7 trading days out, not within the 5-day window.
- **Mega-cap earnings-season window** (mid-Jan/mid-Apr/mid-Jul/mid-Oct through month-end): **false** — 2026-08-24 falls outside that standard quarterly window.
- **However — flagged explicitly per task**: **NVDA reports Wednesday 2026-08-26**, 2 trading days out. This falls inside the 5-trading-day flag threshold and is NOT captured by the standard quarterly-window logic since NVDA's fiscal calendar runs off-cycle from the broader mega-cap cohort. Given NVDA is the book's largest position (8.25% weight), this is the single most important near-term calendar risk for the whole portfolio this week, calendar-window logic notwithstanding.

## 4. Regime Read
Risk read is **turning risk-off, not yet confirmed**. Three inputs point the same direction: (1) the pre-open gate is ESCALATING on an Asia-led selloff, with KOSPI -3.12% — a semis-heavy index, which is a direct sentiment proxy for the AI-capex supply chain this book is concentrated in; (2) the 10-yr is at 4.738%, up from 4.696% two weeks ago, holding above 4.7% against a HAWKISH FOMC read — the combination pressures forward-multiple growth names first; (3) SPY put OI has been climbing steadily for three weeks (1.88→2.29→2.54) even as VIX (15.90) stays complacent, suggesting institutional hedging is ahead of the volatility gauge, not behind it. None of this is yet confirmed by a VIX spike or a CPI/NFP surprise — both prints are 1-2 weeks out — but the setup (hawkish Fed + rising long yield + Asia-led semis weakness + rising put OI) is the classic pre-drawdown pattern rather than a stable risk-on tape.

**Cluster impact**:
- **AI-capex chain**: Doubly exposed this week — NVDA earnings Wed (largest position, 8.25% weight) lands directly into an already-escalating Asia-led semis selloff (KOSPI -3.12%). A hawkish-Fed/rising-10y backdrop compounds by pressuring the forward multiples this cluster trades on. This is the most acute near-term risk concentration in the book.
- **Rate-sensitive/long-duration growth**: 10-yr holding above 4.7% with a hawkish FOMC read (cached, unchanged) is a persistent headwind — these names feel discount-rate pressure first and most, independent of the NVDA-specific catalyst.
- **Defensives/diversifier bench**: Relative beneficiary if the Asia-led selloff broadens into the US session — low VIX still leaves room for rotation into this bench without a full panic signal yet, but the elevated/rising put OI suggests the market is already positioning for that broadening.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":2.54,"spy_pcr_oi":2.54,"spy_pcr_vol":1.36,"spy_pcr_oi_source":"barchart","spy_pcr_vol_source":"barchart","spy_max_pain":null,"qqq_pcr":1.19,"qqq_pcr_oi":1.19,"qqq_pcr_vol":1.24,"qqq_pcr_oi_source":"barchart","qqq_pcr_vol_source":"barchart","qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-09-11","next_nfp":"2026-09-04","earnings_season_window":false},
 "regime":"risk_off","regime_note":"ESCALATING gate on Asia-led selloff (KOSPI -3.12%) + 10y at 4.738% (up from 4.696% 2wk ago) against a cached HAWKISH FOMC read + SPY put OI ratio climbing 3 straight readings (1.88->2.29->2.54) while VIX stays complacent at 15.90 -- hedging is ahead of the vol gauge. NVDA earnings 2026-08-26 (2 trading days out, largest position at 8.25% weight) is the acute near-term catalyst layered on top of this backdrop.",
 "cluster_impact":{"ai_capex_chain":"Highest near-term risk concentration: NVDA earnings Wed lands inside an Asia-led semis selloff (KOSPI -3.12%) plus hawkish-Fed/rising-10y multiple compression -- three pressures stacking on the book's largest single position.","rate_sensitive":"10y holding above 4.7% with hawkish FOMC read is a persistent, independent headwind for long-duration growth names via discount-rate pressure.","defensives":"Relative beneficiary if Asia-led weakness broadens into the US session; low VIX still leaves rotation room but rising put OI suggests the market is already positioning for broader risk-off."},
 "data_quality":["FOMC cache reused verbatim per next_check_date gate -- no new FOMC meeting since last check, not re-searched","Max pain unavailable for SPY and QQQ -- yfinance get_options returns OI=0 on every strike (re-confirmed 2026-08-24 on SPY nearest expiry 2026-08-24); Barchart exposes only aggregate OI totals, not per-strike -- standing gap G18, wont_fix","QQQ get_options chain not separately pulled (budget discipline) -- same zero-OI structural limitation applies and would not change the max-pain conclusion"]}
```

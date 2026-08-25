# US Macro Desk — 2026-08-25 (pre-market)

## 1. Fed Funds & Stance
Effective Fed funds target: **3.63%** (upper bound), stance **HAWKISH** — reused verbatim from `fomc_cache` (cached 2026-09-17 next-check date, today 2026-08-25 falls before it, so no re-search performed this run; "cached — no new FOMC meeting since last check"). Cache carried forward unchanged.

## 2. Options Sentiment — Market Level
Source for both names: **Barchart** put/call ratios page (server-rendered), fetched live this run.

- **SPY**: put/call OI ratio **3.09** (put OI 16,134,286 vs call OI 5,217,948); put/call volume ratio **1.33** (put vol 1,452,268 vs call vol 1,092,457). Both ratios are firmly above the 1.0 "bearish-positioning" threshold, and the OI skew in particular (3.09x) is a heavy hedging/put-overwrite book, not a casual tilt.
- **QQQ**: put/call OI ratio **1.20** (put OI 6,073,462 vs call OI 5,076,440); put/call volume ratio **1.20** (put vol 1,134,862 vs call vol 945,852). Elevated vs. neutral (~1.0) but far less extreme than SPY's OI skew.
- Max pain: **unavailable** (G18, `wont_fix`) — max pain is OI-weighted, and yfinance's option chain returns 0 OI on every strike/every expiry; Barchart's page publishes only aggregate totals, not the per-strike OI needed for the computation. Not attempted this run to stay within budget, since it was already flagged unfixable.
- **Read**: options market is pricing meaningful hedging demand on the broad index (SPY put-heavy OI, likely index-hedge/put-overwrite flow rather than pure directional bearishness) alongside a comparatively calmer tech-heavy book (QQQ). This sits in tension with VIX at **15.82** (down -0.19% on the day per market_inputs.json) — spot vol is calm/complacent while the options OI book carries a defensive skew. Net read: **complacency at the index-vol level, but real hedging demand parked underneath it** — a classic "quiet VIX, loaded put book" setup that can air-pocket if a catalyst hits.

## 3. Calendar
- Next FOMC decision: **2026-09-16** (meeting Sep 15–16, decision + SEP/dot-plot Wed 2pm ET)
- Next CPI print: **2026-09-11**
- Next NFP (jobs report, for August 2026): **2026-09-04**
- Mega-cap ("Mag-7"-adjacent) earnings-season window: **not currently active** (Q2 season ended late July; Q3 window opens mid-October)
- **5-trading-day flag**: none of the above fall inside the next 5 trading days from 2026-08-25 (Aug 26–Sep 1). Nearest event (NFP, Sep 4) is ~7 trading days out. No near-term calendar-driven vol spike expected from this book's macro-print exposure this week.

## 4. Regime Read
Risk read is **neutral-to-cautiously-risk-on at the index level, with a soft crack underneath**: VIX at 15.82 and falling, SPX/NDX both green-adjacent overnight, and Asia (Nikkei +0.50%, KOSPI +0.68%, TAIEX +0.91%) closed firmly green — but SMH printed -2.43%, a real divergence between broad risk appetite and semis specifically (context: this desk's known_gaps flags G81, last week's semis rout catalyst still unresolved). The 10-yr at 4.704% with a HAWKISH FOMC stance (3.63% funds, cached) keeps a mild but persistent drag on long-duration multiples — not acute (well off the 5.33% 30-yr spike that hit the book on 8/18), but not supportive either.

**Cluster impact:**
- **AI-capex chain**: mixed-to-pressured near-term — SMH's -2.43% is the live tell; this cluster is first to feel both the semis-specific softness and any renewed long-end yield pressure given its forward-multiple concentration.
- **Rate-sensitive/long-duration growth**: modest headwind — 10-yr holding above 4.7% with a hawkish Fed read caps multiple expansion; not a crisis level, but no tailwind either.
- **Defensive/diversifier bench**: relatively favored on a relative basis — calm VIX plus SMH-specific weakness argues for the diversifier bench holding up better than the core AI-capex names this week, a useful ballast read for the strategist's stress table.

## Data Quality
- SMH's -2.43% print may reflect Friday's regular-session close-to-close move rather than a fresh pre-market read (per market_inputs.json gate_reason) — treat with mild caution, not discarded.
- Max-pain remains structurally unavailable for both SPY and QQQ (yfinance 0-OI data gap; Barchart publishes aggregates only) — no computation attempted this run.
- fomc_cache reused verbatim per next_check_date gating; no fresh FOMC-stance search performed.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":1.33,"spy_pcr_oi":3.09,"spy_pcr_vol":1.33,"spy_pcr_oi_source":"barchart","spy_pcr_vol_source":"barchart","spy_max_pain":null,"qqq_pcr":1.20,"qqq_pcr_oi":1.20,"qqq_pcr_vol":1.20,"qqq_pcr_oi_source":"barchart","qqq_pcr_vol_source":"barchart","qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-09-11","next_nfp":"2026-09-04","earnings_season_window":false},
 "regime":"neutral","regime_note":"Calm VIX (15.82) and green Asia session sit against a -2.43% SMH print and a hawkish Fed (3.63%, 10y 4.704%) -- index-level complacency over a defensively-skewed options book and a semis-specific crack.",
 "cluster_impact":{"ai_capex_chain":"pressured near-term via SMH weakness and duration sensitivity","rate_sensitive":"modest headwind from 10y >4.7% and hawkish FOMC stance","defensives":"relatively favored this week on a relative basis"},
 "data_quality":["SMH -2.43% may be stale Friday close-to-close rather than fresh pre-market print","max_pain unavailable for SPY/QQQ -- yfinance 0-OI data gap, Barchart aggregates-only (G18, wont_fix)","fomc_cache reused verbatim, no fresh stance search this run"]}
```

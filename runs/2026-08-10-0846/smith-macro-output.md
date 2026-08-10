# US Macro Desk — 2026-08-10 (Deep)

## 1. Fed Funds & Stance
Fed funds target range midpoint 3.63% (cached — no new FOMC meeting since last check; today 2026-08-10 is before next_check_date 2026-09-17). Last FOMC statement read: **HAWKISH**, unchanged. Reused verbatim per cache rule.

## 2. Options Sentiment — Market Level
Source: **barchart** (both names, both ratios — page loaded cleanly, no fallback needed).

- **SPY**: put/call OI ratio **2.25** (put OI 13.13M vs call OI 5.84M), put/call volume ratio **0.97** (put vol 2.01M vs call vol 2.06M).
- **QQQ**: put/call OI ratio **1.18** (put OI 5.77M vs call OI 4.89M), put/call volume ratio **1.14** (put vol 946k vs call vol 833k).
- SPY's OI ratio runs structurally high (large standing institutional put/collar overwriting is normal for SPY) — the volume ratio near 1.0 is the more current directional read and shows balanced flow, not fear. QQQ's mild put lean (both OI and volume >1) is consistent with tech/growth hedging demand at elevated multiples, not panic.
- Context (from market_inputs.json, not refetched): VIX 14.9 (-1.65% on the day), sitting near the low end of its 52-week range [13.38, 35.3]. Read together: options market is pricing **complacency**, not fear — low realized/implied vol, balanced-to-mildly-hedged positioning, no stress signal.
- Max pain: **unavailable** (G18, wont_fix) — max pain requires per-strike OI; the only OI-bearing source in this stack is Barchart's aggregate ratio page (totals only, not per-strike), and yfinance's option chain returns OI=0 on every strike/expiry. Not attempted this run since Barchart's PCR figures were both live and complete — no fallback chain pull was needed.

## 3. Calendar
- Next FOMC decision: **2026-09-16** (statement + SEP dot plot, 2:00pm ET)
- Next CPI print: **2026-09-11** (August CPI)
- Next NFP (jobs report): **2026-09-04** (August employment situation)
- Mega-cap ("Mag-7"-adjacent) earnings-season window (mid-Jul/mid-Oct-style def.): **false** — 2026-08-10 falls between windows; Q2 season concluded late July, Q3 season doesn't open until mid-October.
- **5-trading-day flag (through 2026-08-17): none of the above fall in window.** Nearest catalyst (NFP, Sept 4) is ~3.5 weeks out. No FOMC/CPI/NFP-driven volatility spike expected in the immediate week ahead.

## 4. Regime Read
SPX is ~8% above its 125-day MA and within 0.5% of its 52-week high; VIX sits near the low end of its 52-week range; NDX RSI-14 at 63.3 is bullish but not yet overbought; sentiment compute reads **extreme greed (80.2)**. Taken together with a hawkish, unchanged Fed and the 10-yr drifting up +13bp over the past month (now 4.66%), this is a **risk-on but stretched** tape: nothing has broken, but the setup — highs + low vol + extreme greed + rising long rates under a Fed in no hurry to ease — is the classic combination that precedes air-pockets rather than one that argues for pressing exposure further. For a book that is ~93.6% AI-capex by equity weight, the read is asymmetric: the AI-capex chain is *currently* favored by risk-on breadth and strong momentum (SMH +1.96% Friday, NDX RSI 63.3), but it is also the cluster most exposed if the extreme-greed/low-VIX combination mean-reverts — forward-multiple names in this chain de-rate fastest when yields keep drifting up and a hawkish Fed leaves no easing cushion. This argues for **caution on adding incremental AI-capex exposure at these levels**, not because the thesis is broken, but because price, sentiment, and rates have moved together into a stretched zone with no near-term macro catalyst (5 trading days: nothing) to reset it — the risk is a rate-sensitive-driven multiple compression hitting the concentrated cluster, not a fundamental one. Rate-sensitive/long-duration growth names generally are the most exposed pressure point if yields keep grinding higher; the book's thin defensive/diversifier bench offers little offset given the 93.6% concentration.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":2.25,"spy_pcr_oi":2.25,"spy_pcr_vol":0.97,"spy_pcr_oi_source":"barchart","spy_pcr_vol_source":"barchart","spy_max_pain":null,
 "qqq_pcr":1.18,"qqq_pcr_oi":1.18,"qqq_pcr_vol":1.14,"qqq_pcr_oi_source":"barchart","qqq_pcr_vol_source":"barchart","qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-09-11","next_nfp":"2026-09-04","earnings_season_window":false},
 "regime":"risk_on","regime_note":"SPX near 52w highs, VIX near 52w lows, extreme greed (80.2), hawkish Fed unchanged, 10y drifting up +13bp/mo — risk-on but stretched, no near-term macro catalyst to reset it",
 "cluster_impact":{"ai_capex_chain":"currently favored by breadth/momentum (SMH +1.96%, NDX RSI 63.3) but most exposed to multiple compression if extreme-greed/low-VIX regime mean-reverts under rising yields; caution warranted on adding incremental exposure at these levels","rate_sensitive":"pressured — 10y up +13bp/mo under an unchanged hawkish Fed with no easing cushion is a headwind for long-duration growth names, which overlaps heavily with the AI-capex chain's forward-multiple names","defensives":"favored on a relative basis as ballast but the book's thin diversifier bench limits any real offset given 93.6% AI-capex concentration"},
 "data_quality":["max-pain unavailable (G18, wont_fix) — no per-strike OI source in stack; yfinance chain OI=0 on every strike, Barchart publishes aggregate totals only, not per-strike","yfinance get_options fallback not invoked this run — Barchart PCR data was complete and current for both SPY and QQQ, so no substitution was needed"]}
```

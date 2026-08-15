# US Macro Desk — 2026-08-15 (Deep)

## 1. Fed Funds & Stance
Fed funds target range 3.50-3.75% (effective ~3.63%), cached — no new FOMC meeting since last check (next check date 2026-09-17). Stance: HAWKISH (cached read of last statement). Reused verbatim per orchestrator instruction.

## 2. Options Sentiment — Market Level
**Weekend caveat: all figures below are Friday 2026-08-14's settle, not live intraday data.**

- **SPY** (source: barchart): PCR (OI) 2.58 — put OI 14,900,241 vs call OI 5,770,602. PCR (volume) 1.33. Both from Barchart's aggregate put-call-ratios page (whole-chain, all expiries).
- **QQQ** (source: barchart): PCR (OI) 1.17 — put OI 6,047,570 vs call OI 5,167,014. PCR (volume) 1.00.
- Max pain: unavailable (G18, wont_fix) — max pain is OI-weighted per-strike; Barchart's page publishes aggregate totals only, and the yfinance fallback chain returns OI=0 on every strike/expiry, so no source in this stack can support the computation. Not computed, not guessed.
- Read: SPY's OI-based PCR of 2.58 is elevated and put-heavy — consistent with large standing SPX/SPY hedge/protection positioning (index put OI structurally runs high; this is not unusual for SPY specifically) rather than a fresh spike in fear. QQQ's OI ratio of 1.17 and volume ratio of 1.00 are closer to neutral, tech-specific hedging balanced against upside positioning. Set against VIX 14.25 (-2.60% Friday, near the low end of its 52-week range [13.38, 35.30]) and NDX RSI14 73.1, the options tape and the vol tape both point the same direction: **options market pricing complacency, not fear** — realized and implied vol are both compressed even as the SPY put OI ratio sits on the high side of its typical band. No divergence signal here; the read is confirmatory of the low-vol/high-momentum regime, not a warning under it.

## 3. Calendar
- Next FOMC decision: 2026-09-16 (statement 2:00pm ET, SEP/dot plot).
- Next CPI print: 2026-09-11 (August 2026 CPI).
- Next NFP (jobs report): 2026-09-04 (August 2026 employment situation).
- NVDA Q2 FY27 earnings: **2026-08-26** (confirmed, guided to ~$91.0B revenue) — not a "Magnificent Seven" broad window by the mid-Jan/Apr/Jul/Oct calendar definition, but this is the single most portfolio-relevant date on the calendar given the book's 88.96% AI-capex concentration.
- **5-trading-day window check (through 2026-08-21, i.e. Mon 8/17–Fri 8/21): none of the above fall inside it.** NFP, CPI, and FOMC are all 3+ weeks out. NVDA earnings (8/26) is 8 trading days out — outside the 5-day flag threshold but close enough to name explicitly: expect the book's implied-vol/positioning conversation to start building through the week of 8/24.
- earnings_season_window: false (outside the mid-quarter mega-cap window; NVDA's offset fiscal calendar is the exception carrying the real risk here).

## 4. Regime Read
Risk-on, and now on both legs at once. Sentiment reads EXTREME GREED (82.9, VIX sub-score 96.0) and NDX RSI14 is 73.1 — unlike the 2026-08-10 run, where the extreme-greed read was attributed mainly to low-vol complacency (RSI then only 63.3), this is now a genuine momentum extreme layered on top of the vol compression. SPX is 0.4% off its 52-week high and running 8.3% above its 125-day MA; VIX at 14.25 sits near the bottom of its 52-week range. Meanwhile the 10-year has drifted from 4.641% to 4.696% Friday (+5.5bp on the day, +11.1bp over the month) under an unchanged hawkish Fed — a slow, grinding pressure rather than a shock, but a headwind for long-duration growth multiples that is easy to underweight precisely because nothing about it looks acute day-to-day.

**Cluster impact:**
- **AI-capex chain (88.96% of book by equity):** This is where a momentum extreme + creeping rate pressure bites first and hardest. Forward-multiple AI-capex names are the natural first movers on any risk-off catalyst — NVDA earnings on 8/26 is the proximate trigger risk, and RSI 73.1 on NDX means the chain is technically overbought heading into it. The regime currently rewards this cluster (risk-on, momentum working) but is priced for continuation, not surprise — asymmetry has shifted toward the downside on any miss or guide-down.
- **Rate-sensitive/long-duration growth:** Pressured on the margin by 10yr grinding toward 4.70% under a hawkish, unmoved Fed; the move is gradual (11bp/month) so it isn't a dominant near-term catalyst, but it compounds with the AI-capex chain's own duration sensitivity (most AI-capex names ARE long-duration growth by cash-flow structure) rather than acting as an independent, offsetting force.
- **Defensives/diversifiers:** Structurally underweight in a book this concentrated; a genuine benefit only materializes if/when the current momentum extreme reverses. The 2026-08-15 diversification (Blackstone/Texas Instruments/Taiwan-ETF additions bringing AI-capex from 93.6% to 88.96%) is a step in the right direction but nowhere near enough ballast for a book that is simultaneously at a technical extreme and effectively out of dry powder.

**The decision-relevant fact this week is not the regime call — it's the book's capacity to respond to it.** The book holds **$12 in cash (0.028% of total)** against an 88.96% single-factor concentration, at a moment when sentiment is at a genuine extreme (greed + momentum together, not just one), 10yr yields are grinding against the dominant factor's valuation support, and the book's largest idiosyncratic catalyst (NVDA earnings) lands in eight trading days. A zero-cash book cannot average down, cannot fund a tactical hedge, and cannot rotate into the underweight defensive cluster without first selling something from the very cluster that would be under the most pressure in the scenario being hedged against — the redeployment capacity that would normally cushion a drawdown day simply does not exist right now. This is the single most decision-relevant macro read for the strategist's stress table this week: any risk-off scenario forces either a full liquidation-first response or import of a stop-out on an existing position, not a funded reallocation.

## Data Quality
- Weekend read: options figures are Friday 2026-08-14 settle, not live. Labeled as such throughout.
- Both SPY and QQQ PCR sourced successfully from Barchart (OI + volume, whole-chain) — no yfinance fallback needed this run.
- Max pain unavailable for both proxies (G18, wont_fix) — no source in this stack carries per-strike OI.
- Fed funds/stance reused from cache verbatim (no re-search performed, per orchestrator instruction and next_check_date not yet reached).
- us10y/vix/dxy/spx/ndx/smh reused from market_inputs.json, not refetched.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":1.33,"spy_pcr_oi":2.58,"spy_pcr_vol":1.33,"spy_pcr_oi_source":"barchart","spy_pcr_vol_source":"barchart","spy_max_pain":null,"qqq_pcr":1.00,"qqq_pcr_oi":1.17,"qqq_pcr_vol":1.00,"qqq_pcr_oi_source":"barchart","qqq_pcr_vol_source":"barchart","qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-09-11","next_nfp":"2026-09-04","earnings_season_window":false,"nvda_earnings":"2026-08-26"},
 "regime":"risk_on","regime_note":"Extreme-greed sentiment (82.9) now co-occurs with genuine NDX momentum extreme (RSI14 73.1), not just low-vol complacency as on 2026-08-10 (RSI then 63.3). SPX 0.4% off 52w high, 8.3% above 125dma. 10yr grinding up 11bp/month under unchanged hawkish Fed. Options tape (SPY/QQQ PCR) confirms complacency, no divergence warning.",
 "cluster_impact":{"ai_capex_chain":"First and hardest hit in any risk-off catalyst; technically overbought (NDX RSI 73.1) heading into NVDA earnings 2026-08-26; regime rewards continuation but priced for it, asymmetry now skewed to downside on a miss.","rate_sensitive":"Pressured on the margin by 10yr grinding toward 4.70% under hawkish, unmoved Fed; compounds with AI-capex chain's own duration sensitivity rather than offsetting it.","defensives":"Structurally underweight; 08-15 diversification (Blackstone/TXN/Taiwan-ETF) cut AI-capex from 93.6% to 88.96% but provides minimal ballast against a book at a technical extreme with $12 (0.028%) cash and no funded capacity to rotate into this cluster on a drawdown."},
 "data_quality":["weekend read: options figures are Friday 2026-08-14 settle, not live","max pain unavailable both proxies (G18, wont_fix) - no per-strike OI source available","fed funds/stance reused from cache verbatim, no re-search (next_check_date 2026-09-17 not reached)","10y/vix/dxy/spx/ndx/smh reused from market_inputs.json, not refetched"]}
```

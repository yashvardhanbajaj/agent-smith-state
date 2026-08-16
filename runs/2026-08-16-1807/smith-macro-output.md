# US Macro Desk — 2026-08-16 (deep)

Data condition: US market closed since Friday 2026-08-14's close. Sunday run — all index/rate inputs identical to the 2026-08-15 deep run; no new session has occurred.

## 1. Fed Funds & FOMC Stance

Fed funds (target range midpoint proxy): **3.63%** — CACHED, no new FOMC meeting since last check (`fomc_cache`, last verified before today, `next_check_date` 2026-09-17). Today (2026-08-16) is well before that date and a rate decision does not change intra-cycle, so this was reused verbatim rather than re-searched.

Stance: **HAWKISH** (cached). Consistent with the last-verified FOMC statement read.

`fomc_cache` carried forward unchanged: `{rate_pct: 3.63, stance: "HAWKISH", next_check_date: "2026-09-17"}` — confirmed by calendar check below that the next decision is 2026-09-16, so 2026-09-17 remains the correct re-check trigger.

## 2. Options Sentiment — Market Level

**SPY** — source: **barchart** (`https://www.barchart.com/etfs-funds/quotes/SPY/put-call-ratios`)
- Put/Call open interest ratio: **2.58** (put OI 14,900,241 vs call OI 5,770,602)
- Put/Call volume ratio: **1.33**
- Both exceed Barchart's bearish threshold (>1.0) — heavy put open interest relative to calls.

**QQQ** — source: **barchart** (`https://www.barchart.com/etfs-funds/quotes/QQQ/put-call-ratios`)
- Put/Call open interest ratio: **1.17** (put OI 6,047,570 vs call OI 5,167,014)
- Put/Call volume ratio: **1.00**
- Milder put skew than SPY but still above the 1.0 bearish threshold.

**Max pain** — source: **yfinance-chain** (single nearest-expiry chain, 2026-08-17, saved to `/Users/yb/Claude/AgentSmith/runs/2026-08-16-1807/{spy,qqq}_chain.json`, computed via `python3 smith_math.py maxpain`, G18 closed 2026-08-16):
- SPY: max pain **776** vs spot 776.34 (+0.04%) — pinned essentially at spot. `strikes_used: 7`, range [773,779], no boundary artifact, no data_quality flags.
- QQQ: max pain **731** vs spot 731.07 (+0.01%) — also pinned at spot. `strikes_used: 7`, range [728,734], no boundary artifact, no data_quality flags.
- Note: the single-expiry OI-based PCR the script also reports for this expiry (SPY 1.226, QQQ 1.195, call/put OI in the thousands) is a **byproduct of the max-pain calc only** — it is a small, near-dated slice and is NOT the same figure as, and must not be trended against, Barchart's whole-chain aggregate PCR above. The Barchart figures are what's reported as `spy_pcr_oi`/`qqq_pcr_oi` in the JSON tail; this expiry-slice ratio is not carried into the JSON tail to avoid the two being confused.

**Read**: SPY's OI-based PCR (2.58) is materially more put-skewed than QQQ's (1.17) — the book's AI-capex/growth-heavy proxy (QQQ) shows near-neutral positioning while the broad market (SPY) carries a heavier hedge/put overhang. Combined with VIX at 14.25 (-2.60% on the day, sitting near its 52-week low of 13.38) and max pain pinned essentially at spot on both proxies into Monday's expiry, the options market reads as **complacent on realized volatility but running a meaningful protective-put overhang in the broad index** — consistent with a "priced for perfection, hedged underneath" setup rather than outright fear or outright euphoria in derivatives positioning.

## 3. Calendar

- **Next FOMC decision**: 2026-09-16 (meeting 2026-09-15/16, decision + SEP/dot-plot at 2:00pm ET on the 16th)
- **Next CPI print**: 2026-09-11 (August 2026 CPI data; July 2026 CPI was already released 2026-08-12, before this run)
- **Next NFP (jobs report)**: 2026-09-04 (August 2026 employment data)
- **Mega-cap earnings-season window** (mid-Jan/mid-Apr/mid-Jul/mid-Oct through end of month, calendar-quarter reporters): **false** — 2026-08-16 falls outside all four windows.
- **5-trading-day flag**: counting from 2026-08-16 (Sun), the next 5 trading days run 08-17 through 08-24. None of the three macro prints above (FOMC 09-16, CPI 09-11, NFP 09-04) fall inside that window — **no macro-print flag**.
- Separately (already confirmed per orchestrator, not re-verified here): **NVDA reports 2026-08-26** (~7.72% of book) and **MRVL reports 2026-08-27** — both fall just outside the 5-trading-day window (8 and 9 trading days out respectively) but are the nearest known catalysts and the reason AI-capex-chain volatility should be expected to build into the back half of August even though no macro print itself is imminent.

## 4. Regime Read

Read: **risk-on but stretched, with a hawkish-rates crosscurrent building underneath.** Sentiment score sits at 82.9 (EXTREME_GREED band), VIX is at a 52-week-low-adjacent 14.25, and SPX (7785.76) is within 0.4% of its 52-week high (7816.70) — surface positioning is unambiguously risk-on. But the 10-yr has moved up 11.1bp over the past month (+5.5bp just Friday, to 4.696%) against a HAWKISH cached FOMC stance, and NDX RSI14 at 73.12 is in overbought territory — three separate late-cycle warning signs stacking on top of an already-euphoric sentiment reading. SPY's put-heavy OI positioning (2.58 ratio) looks like the market quietly hedging that stretch even as spot grinds toward highs.

**Cluster impact**:
- **AI-capex chain (88.99% of equity)**: feels the overbought/extreme-greed combination first on any pullback — NDX RSI14 73 plus a EXTREME_GREED sentiment score raise mean-reversion risk into the NVDA (8/26) / MRVL (8/27) earnings stretch, even with no macro print due in the next 5 trading days.
- **Rate-sensitive / long-duration growth**: the most directly pressured cluster today — 10yr at 4.696% and rising (+11.1bp/1m) against a HAWKISH FOMC read keeps the discount-rate headwind live; this is the fastest-transmission channel into forward-multiple names.
- **Defensives / diversifier bench**: no tailwind from the current risk-on tape (VIX near 52-wk low favors beta, not ballast), but this is exactly the cluster that earns its keep if the extreme-greed/overbought setup mean-reverts — its value is optionality against the regime flipping, not participation in it now.

## Data Quality

- Barchart PCR figures (SPY, QQQ) sourced live via WebFetch 2026-08-16 — plausibility-checked (both ratios in sensible 0.5–3.0 range), passed.
- yfinance option chain used for max-pain is an ATM-anchored narrow window (7 strikes per side, nearest expiry only, 2026-08-17) — not the full chain. Script's own guards (`_truncated`, zero-OI, boundary-artifact) all passed clean for both SPY and QQQ; no flags fired.
- Single-expiry OI-based PCR that falls out of the max-pain calc (SPY 1.226, QQQ 1.195) is intentionally NOT reported in the JSON tail as `spy_pcr`/`qqq_pcr` — it is a small expiry-skewed slice and would be misleading if trended against Barchart's whole-chain aggregate. See Section 2 note.
- Fed funds rate/stance reused from `fomc_cache` verbatim per orchestrator instruction — no live search performed this run (by design, cache valid through 2026-09-17).
- Calendar dates (FOMC, CPI, NFP) sourced via WebSearch 2026-08-16; cross-checked against the cached FOMC `next_check_date` (2026-09-17 = day after the 2026-09-16 decision) for internal consistency — consistent.
- All index/rate levels reused unmodified from `market_inputs.json` (us10y, vix, dxy, spx, ndx, spx_125dma, ndx_rsi14) — no refetch performed, per instruction.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":2.58,"spy_pcr_oi":2.58,"spy_pcr_vol":1.33,"spy_pcr_oi_source":"barchart","spy_pcr_vol_source":"barchart","spy_max_pain":776,"qqq_pcr":1.17,"qqq_pcr_oi":1.17,"qqq_pcr_vol":1.00,"qqq_pcr_oi_source":"barchart","qqq_pcr_vol_source":"barchart","qqq_max_pain":731,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-09-11","next_nfp":"2026-09-04","earnings_season_window":false},
 "regime":"risk_on","regime_note":"Risk-on surface (EXTREME_GREED 82.9, VIX 14.25 near 52wk low, SPX within 0.4% of ATH) stacked on late-cycle warnings (NDX RSI14 73.1 overbought, 10yr +11.1bp/1m to 4.696% against a HAWKISH FOMC, SPY put OI ratio 2.58 signaling hedging beneath the tape). Fragile risk-on, not clean risk-on.",
 "cluster_impact":{"ai_capex_chain":"First to feel any mean-reversion given RSI14 73 + EXTREME_GREED band; NVDA (8/26) and MRVL (8/27) earnings are the near-term catalysts even though no macro print falls within 5 trading days.","rate_sensitive":"Most directly pressured now -- 10yr 4.696% and rising against a hawkish Fed keeps discount rates elevated for long-duration/forward-multiple names.","defensives":"No tailwind from the current risk-on tape, but this is the cluster that earns its keep if the extreme-greed/overbought setup mean-reverts."},
 "data_quality":["max-pain computed from ATM-anchored narrow chain (7 strikes/side), nearest expiry only, not full chain -- script guards all passed clean, no truncation/zero-OI/boundary flags","single-expiry OI PCR from the max-pain calc (SPY 1.226, QQQ 1.195) intentionally excluded from JSON tail to avoid conflation with Barchart's whole-chain aggregate PCR","fed_funds_pct and fomc_stance reused verbatim from fomc_cache per instruction, no live search this run","market closed since 2026-08-14 close -- all market_inputs.json levels identical to 2026-08-15 run, reused not refetched"]}
```

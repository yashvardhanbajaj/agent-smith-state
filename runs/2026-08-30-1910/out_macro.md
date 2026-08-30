# US Macro Desk — 2026-08-30 (deep)

## 1. Fed funds & FOMC stance
Effective fed funds target: **3.63%** (upper bound proxy). Stance: **HAWKISH** — cached, no new FOMC meeting since last check (cache `next_check_date` 2026-09-17, today 2026-08-30). Cache validated against the calendar pulled this run: next decision is 2026-09-16, one day before the cache's check date, confirming the cache is still current — reused verbatim, no re-search performed.

## 2. Options sentiment — market level
Source: Barchart put/call ratio pages (both fetched successfully; no fallback needed).

- **SPY**: put/call OI ratio **2.54** (put OI 13.50M vs call OI 5.31M, total OI 18.81M) [barchart]; put/call volume ratio **1.14** [barchart].
- **QQQ**: put/call OI ratio **1.25** (put OI 6.29M vs call OI 5.03M, total OI 11.32M) [barchart]; put/call volume ratio **1.34** [barchart].
- Max pain: unavailable (G18). Standing gap since July — yfinance's single-expiry chain returns near-zero/null OI on every strike, and OI-weighted max pain cannot be computed from a volume-only feed. Barchart publishes aggregate OI, not per-strike OI, so it cannot substitute. Judged **permanently unavailable on this tooling stack** — not re-attempted this run, no further budget spent on it.
- VIX context (reused from market_inputs, not refetched): **14.43, -0.55% on the day** — low and falling.

**Read**: SPY's OI-based PCR (2.54) is meaningfully elevated versus QQQ's (1.25), pointing to a heavier structural put overhang on the broad-market proxy specifically — consistent with investors holding portfolio-level index hedges rather than fresh single-day alarm (OI accumulates over time; a one-day volume ratio of 1.14 on SPY is not itself extreme). QQQ's higher volume ratio (1.34) versus its OI ratio (1.25) suggests slightly more urgency in tech-heavy put buying today specifically, though still not a fear extreme.

**The VIX-vs-SMH divergence** (interesting tension flagged by the orchestrator): VIX fell 0.55% to 14.43 the same session SMH dropped 3.47% and the book fell 3.12%. Evidence points to **sector containment, not index optionality mispricing**: SPX itself was only -0.25% and NDX -0.52% on the day — the broad indices barely moved. VIX is priced off SPX-wide implied vol, so a -0.25% SPX day producing a soft, falling VIX is not mispricing; it's an accurate read of the *index's* realized action. The dislocation is concentrated in one sub-sector (semis/SMH, and by extension the book's ~89% AI-capex tilt), which a 500-name broad index absorbs without moving its own vol gauge. This is a **selloff genuinely contained to one sector at the index level**, even though it is not contained at the book level. Secondary read: the elevated SPY OI put/call (2.54) shows real hedging exists in the system — it's a hedging-vs-headline gap in the sense that index protection has been building structurally, but it did not require repricing today because the index itself didn't move enough to trigger it. Do not read VIX 14.43 as "market says no risk" — read it as "market says no *broad-index* risk"; book-level risk from the semis dislocation is real and VIX will not warn you about it.

## 3. Calendar
- **Next FOMC decision**: 2026-09-16 (meeting 09-15/16, decision + presser 2:00pm/2:30pm ET on the 16th).
- **Next CPI print**: 2026-09-11.
- **Next NFP (jobs report)**: 2026-09-04.
- **Mega-cap ("Mag-7"-adjacent) earnings-season window**: **not currently active** — the recognized windows run roughly mid-Jan/mid-Apr/mid-Jul/mid-Oct through month-end; 2026-08-30 falls outside all four.

**Within next 5 trading days (Mon 08-31 through Fri 09-04):**
- **NFP, 2026-09-04 — YES, within window.** This is the dominant near-term calendar risk.
- **AVGO earnings, 2026-09-02 — YES, within window** (held name; AVGO's own fiscal reporting cadence sits outside the general Mag-7 season windows but is directly book-relevant).
- **CIEN earnings, 2026-09-03 — YES, within window** (held name).
- CPI (09-11) and FOMC (09-16) both fall outside the 5-trading-day window.

Net: three material catalysts land in the same short week — AVGO (09-02), CIEN (09-03), NFP (09-04) — while the broad index sits on a low, falling VIX. That combination (thin index-level vol pricing ahead of a concentrated run of book-relevant catalysts) is itself worth flagging to the strategist as an under-priced near-term risk window for the AI-capex cluster specifically.

## 4. Regime read
US equities are in a **risk-on-at-the-index-level / risk-off-at-the-sector-level** split regime. The 10-yr at 4.72% (+1.03% on the day) with a hawkish FOMC stance still in place keeps pressure on long-duration/rate-sensitive growth names, and it is very plausibly a contributing driver of the SMH-specific selloff (elevated discount rates hit forward-multiple AI-capex names first and hardest) even as the broad index shrugs it off. DXY steady near 99.7 is not signaling a dollar-driven risk-off shock. Net: this regime **pressures the AI-capex chain** (long-duration, rate-sensitive, currently absorbing a real 3%+ sector drawdown against a complacent VIX) and **pressures rate-sensitive/long-duration growth broadly** given the 10-yr's move; it is comparatively **neutral-to-favorable for defensives/diversifiers**, which benefit from index-level calm and are not exposed to the semis-specific dislocation or the 10-yr's move in the same way.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-09-17"},
 "spy_pcr":2.54,"spy_pcr_oi":2.54,"spy_pcr_vol":1.14,"spy_pcr_oi_source":"barchart","spy_pcr_vol_source":"barchart","spy_max_pain":null,"qqq_pcr":1.25,"qqq_pcr_oi":1.25,"qqq_pcr_vol":1.34,"qqq_pcr_oi_source":"barchart","qqq_pcr_vol_source":"barchart","qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-09-11","next_nfp":"2026-09-04","earnings_season_window":false,"near_term_catalysts_within_5td":["NFP 2026-09-04","AVGO earnings 2026-09-02","CIEN earnings 2026-09-03"]},
 "regime":"neutral","regime_note":"Index-level calm (VIX 14.43, falling) masks a real sector-level dislocation (SMH -3.47%) driven by a hawkish Fed and 10yr at 4.72%; risk-on at the SPX/NDX level, risk-off within AI-capex/semis specifically.",
 "cluster_impact":{"ai_capex_chain":"pressured — rate-sensitive forward multiples hit first, and this is the cluster absorbing the real SMH-level drawdown the index isn't pricing","rate_sensitive":"pressured — 10yr 4.72% (+1.03% on the day) with hawkish FOMC stance intact","defensives":"neutral-to-favorable — insulated from both the 10yr move and the semis-specific dislocation, benefit from index-level calm"},
 "data_quality":["G18 max-pain: judged permanently unavailable on this tooling stack (yfinance chain returns null/near-zero OI on every strike; Barchart publishes aggregate not per-strike OI) — not re-attempted this run","fomc_cache reused verbatim per next_check_date gate, cross-checked against this run's calendar pull (FOMC 2026-09-16, cache expiry 2026-09-17) — consistent"]}
```

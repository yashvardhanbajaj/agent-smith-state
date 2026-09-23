# Smith Scout — Macro-only (MACRO trigger, |Δ10Y|=0.128 ≥ 0.12)
Run runs/2026-09-23-1639Z · mode macro_only (tasks 3–5 only; session read/sentiment narrative/diversifier bench skipped, bench carried forward)

## 3. Fed funds & stance
Cached — no FOMC meeting since last check. `fomc_cache.next_check_date` = 2026-10-30, today is 2026-09-23, so the cache is reused verbatim, not refreshed.
- Fed funds target: **3.875%** (upper bound; proxy of the effective range set at the last hike)
- Stance: **hawkish**
- No `fomc_cache_update` this run (nothing to refresh).

## 4. Options positioning
No `compute_options.json` was produced for this run (macro_only quick sweep). All fields null — options positioning unavailable this run. (Not a pre-market artifact issue; the file simply wasn't generated for this dispatch type.)

## 5. Calendar + regime read
**Calendar** (reaffirmed from prior finding `macro:calendar`, as_of 2026-09-21, not expired): next FOMC 2026-10-28, next CPI 2026-10-14, next NFP 2026-10-02. Nothing inside 5 trading days of today (2026-09-23). No mega-cap earnings window open (`earnings_season_window: false`).

**Regime — this is the delta that triggered the run.** US 10-yr printed **5.091%** intraday, +12.8bps on the day (`us10y_change_pts` 0.128, the exact MACRO trigger) and +35.3bps over the trailing month. This **breaches the 5.0% line** that scout's two most recent regime reads (2026-09-21, `orchestrator:71571408a8` and `orchestrator:a175ef0eec`) explicitly flagged as the reversal trigger out of "risk-on but fragile." That condition has now fired, intraday (not yet a confirmed close).

Read against price action: SPX -0.69%, NDX -0.68% today — red across the board domestically — while VIX is still just 14.83 (down on the day, well inside its 13.47–31.05 52-week range) and Asia closed strongly overnight (Nikkei +1.4%, KOSPI +1.6%, TAIEX +1.1%, all >1% — pre-dating today's US rate move). This reads as a **rates-driven de-risk**, not a fear spike: yields, not volatility, are doing the damage. Sentiment gauge (for context, not re-derived here) sits at 78.1 extreme_greed with `action_hint` "propose profit-booking on overweight/breach names" — consistent with a market still priced for good news right as the rate backdrop turns.

- **Regime: risk_off** (downgraded from the 2026-09-21 "risk_on but fragile" read now that the flagged 5.0% breach has occurred)
- **AI-capex chain**: pressured first and hardest — long-duration growth multiples compress fastest when the discount rate moves; NDX -0.68% is the initial print, SMH cash close flat (+0.18%) lags the risk-off signal so far.
- **Rate-sensitive / long-duration growth**: same mechanism, more acute — every bp above 5.0% is now in territory the desk had explicitly not modeled as "priced."
- **Defensives/diversifiers**: comparatively insulated; the book's only genuine non-AI-capex holding is LLY (thesis intact per `orchestrator:70577475d1`), so there's little ballast here — this is a data point for the strategist's stress table, not a call on diversifier names (bench not touched this run).

## Findings reconciliation
- Reaffirmed: `macro:calendar`, `macro:fomc`.
- Revised: `orchestrator:71571408a8` and `orchestrator:a175ef0eec` — both named "10-yr close above 5.0%" as the reversal trigger; that threshold has now been breached intraday. Regime downgraded to risk_off pending confirmation at the close.

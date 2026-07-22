# Watchlist & Market Context — Quick Sweep (2026-07-22, pre-open)

## 1. Watchlist Entry Setups
Scanned slice (cursor 15-29 of ~100 unique non-held names): SMR, LEU, VST, CEG, EFNL, EVER, CRDO, DELL, ANET, ALAB, BP, KLAC, CMI, BWXT, GLNG.

- **SMR** (NuScale) — watchlist, OVERSOLD BOUNCE. pos 0.03 (near 52w low $7.21 vs $57.42 high), mean target $14.80, upside 41.2%. News: "NuScale Awards Contract for Reactor Protection Systems" (17 Jun, positive) — pre-watermark but only recent item.
- **LEU** (Centrus Energy) — watchlist, OVERSOLD BOUNCE (upside-driven; news is negative). pos 0.09, mean target $264.73, upside 35.3%. Caution: both news items negative — "Centrus Energy Faces Challenges with Revenue and Margins" (10 Jul) and Oklo HALEU deal delayed to 2029 (18 Jun). Setup is upside-gap driven, not sentiment-driven.
- **CEG** (Constellation Energy) — watchlist, OVERSOLD BOUNCE. pos 0.18, mean target $357.81, upside 26.7%. News: "Constellation Energy Reports Positive EPS Growth Expectations" (21 Jul, positive, post-watermark) vs. lingering Calpine-leverage overhang (16 Jul, negative).
- **VST** (Vistra) — watchlist, TARGET GAP. pos 0.34, mean target $223.17, upside 27.3%. News: AI data-center power demand thesis intact (09 Jul, positive).
- **BWXT** (BWX Technologies) — watchlist, TARGET GAP. pos 0.35, mean target $238.79, upside 27.5%. News: isotope-production expansion (10 Jul, positive).
- **CRDO** (Credo Technology) — watchlist, TARGET GAP. pos 0.62, mean target $278.50, upside 19.6%. News: strong AI-connectivity demand, Zacks #1 (06 Jul, positive).
- **DELL** — watchlist, TARGET GAP. pos 0.82, mean target $501.04, upside 19.3%. News: raised FY27 revenue guidance $165-169B on AI server demand (20 Jul, positive, post-watermark); note stock pullback 15 Jul on cost/downgrade concerns.
- **GLNG** (Golar LNG) — watchlist, TARGET GAP. pos 0.65, mean target $60.28, upside 17.5%. No recent news segment returned.

No setups: EFNL (ETF, no forecast data), EVER (upside -2.8%), ANET (pos 0.82, upside 8.9% — below gap threshold), ALAB (upside -9.8%, already extended), BP (upside 9.6%), KLAC (upside 7.3%), CMI (pos 0.80, upside 12.5%, HOLD consensus).

## 2. Earnings Calendar (holdings, quick-mode 7-day window: 2026-07-22 to 2026-07-29)
No earnings_calendar cache was supplied in this run's inputs. yfinance `get_earnings_calendar` returned an empty result for both a 7-day and a 20-day window (tried twice, different params) — tool appears non-functional/no data in this environment. yfinance `get_earnings` (per-symbol EPS history) does not expose a forward-looking confirmed date field, only historical `reportedDate`s.
Result: **no held US names can be confirmed or ruled out for earnings in the next 7 days this run.** LRCX's known prior report (2026-07-17) is already past and outside this window — not an active gap. No WebFetch escalation performed (no name met the "unconfirmed + ≥3% weight + upcoming" trigger; LRCX's flagged date already resolved/passed).

## 3. Data Quality / Gaps
- yfinance `get_earnings_calendar` returned empty on 2 attempts (date-ranged and default) — flagging as a tool/data gap, not a "no earnings" confirmation.
- No `earnings_calendar` cache slice was provided in this run's dispatch — orchestrator should confirm cache is being passed through.
- compute_attribution.json's per-ticker qty_changes note NOW exit / BABA buy aren't separately decomposed (both-runs-diff limitation) — flagged per orchestrator's own caveat, not recomputed.
- G1, G18 known gaps unchanged, not re-litigated here.

```json
{"watchlist_setups":[
 {"ticker":"SMR","type":"OVERSOLD_BOUNCE","upside_pct":41.15,"pos":0.03},
 {"ticker":"LEU","type":"OVERSOLD_BOUNCE","upside_pct":35.32,"pos":0.09},
 {"ticker":"CEG","type":"OVERSOLD_BOUNCE","upside_pct":26.72,"pos":0.18},
 {"ticker":"VST","type":"TARGET_GAP","upside_pct":27.26,"pos":0.34},
 {"ticker":"BWXT","type":"TARGET_GAP","upside_pct":27.51,"pos":0.35},
 {"ticker":"CRDO","type":"TARGET_GAP","upside_pct":19.62,"pos":0.62},
 {"ticker":"DELL","type":"TARGET_GAP","upside_pct":19.34,"pos":0.82},
 {"ticker":"GLNG","type":"TARGET_GAP","upside_pct":17.45,"pos":0.65}
],
"earnings_calendar_updates":{},
"watchlist_scan_cursor":30,
"data_quality":[
 "yfinance get_earnings_calendar returned empty on 2 attempts (7d and 20d windows) -- likely tool/data gap, not zero-earnings confirmation",
 "no earnings_calendar cache slice supplied this run -- could not check cached/confirmed dates before re-fetching",
 "no held-ticker earnings could be confirmed or ruled out for the 2026-07-22 to 2026-07-29 window this run",
 "LEU setup is upside-number-driven only -- both recent news items on LEU are negative, flagging so orchestrator doesn't read it as a sentiment-confirmed bounce",
 "EFNL (ETF) has no analyst/target data -- excluded from scan results, not a bug"
]}
```

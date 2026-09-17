# Smith Strategist — Quick Sweep, 2026-09-17 (run 2026-09-17-1541Z)

## Context recap (from Stage 1, not re-derived)
- Gate STABILIZING: VIX -11.2% to 15.73, SMH +2.57%, ES/NQ +1.95%/+2.67%, Asia broadly green (best +1.37% KOSPI, worst +0.69% Nikkei) — a broad relief rally, already partly realized in the 11:56 ET prices this run reads (not a forecast).
- COHR stop-out today: 3sh sold @ $295 (stop order), position cut 2.98%→2.01% wt ($589.56 mkt value). Thesis unchanged **strengthening** (Q4 FY26 beat rev/EPS, guide raised above the beaten quarter) — smith-thesis found no COHR-specific break; the failure to fully participate in today's rally is read as GLW-ATM-dilution optics-peer contagion (catalyst:9744ffb8fe, reaffirmed, unresolved, expires 2026-09-29).
- crosscheck.json: ONE medium-severity tension — thesis "strengthening" vs. a live catalyst_threat on COHR. Addressed explicitly below.
- 24/25 holdings unchanged this run; only COHR thesis entry touched (reconciliation of the stop-out into evidence_against, status unchanged).

## Drift / breach status (compute_drift.json — computed, not re-derived)
- **Position breaches: none** (`position_breaches: []`).
- **AI Semis/Fabs "breach"**: actual 41.01% of invested equity but only **28.687% of total book** — ceilings are tested on total-book basis while cash sits above its normal band (policy's own switch rule). On that basis it is **within** the 23–33% band → `breach: false`. This reaffirms orchestrator:1acbddb361 (mechanical dilution from other clusters shrinking + elevated cash, not new buying). No action.
- **AI Power/Cooling/DC Infra**: 10.105% of total book vs. 12–22% band → **real floor breach** (drift -6.9pt), reaffirming orchestrator:a72706b0fa (post GEV/VRT-cut underweight). Standing playbook (orchestrator:b68adec42b, valid to 2026-10-07) is to hold rotation course and not add long-duration AI exposure before Oct data — no new BE/GEV/VRT add proposed this run on top of that.
- **Cash**: 30.05% of total book ($12,610) vs. 5–15% band → breach, but `cash_regime: normal` (no stop-out in 15 sessions) — dry powder, not distress, consistent with playbook:risk_off (reaffirmed).
- **AI-capex chain exposure**: 95.62% of invested equity, unchanged, not in breach (cap 100%).
- **Drawdown**: -2.469% off peak, `risk_off_status: normal`. Well inside the -8%/-12% warn/risk-off rungs.

## Proposals

**No new sized proposals this run.** Fourteen proposals are already open and, on review against today's compute tables, still represent the live actionable menu — nothing in today's delta (the relief rally, COHR's stop-out) creates a new breach, a new live trigger without an existing proposal, or invalidates an open one enough to warrant a resize:

| id | action | size | trigger | status this run |
|---|---|---|---|---|
| P-305 / P-352 | Sell ASML $834.71 / Buy TSM $1,604 | pair | cluster_rotation | reaffirmed — ASML still watch/laggard (rel -8.13pp, RSI 42.2), TSM still strengthening/leader |
| P-310 | Trim TER $333.26 | catalyst_threat | reaffirmed, see note below on the cap fact |
| P-314 | Buy AMAT $412.18 | oversold_reversion | reaffirmed — RSI14 33.0, thesis strengthening, within cap |
| P-318 | Buy SNDK $200 | rebound | reaffirmed (token tranche, no thesis on file) |
| P-339 | Trim COHR $200 | catalyst_threat | **flagged, not superseded** — see below |
| P-341 / P-343 / P-344 | Buy GOOG $1,300 / QCOM $500 / WDC $500 | catalyst_threat (shielded-buy framing) | reaffirmed |
| P-346 | Trim MU $186 | catalyst_threat | reaffirmed — thesis watch, CXMT catalyst still live |
| P-347 / P-348 | Sell AMD $153.75 / Buy ALAB $153.75 | pair | profit_rotation | reaffirmed |
| P-349 / P-350 | Sell GLW $129.98 / Buy MRVL $129.98 | pair | cluster_rotation | reaffirmed |

**COHR / P-339 — the crosscheck tension, weighed explicitly, not resolved for the user:**
Two things are both true and pulling opposite ways. (1) Thesis is verified-secondary **strengthening**: a real beat-and-raise quarter, no COHR-specific negative fact. (2) The catalyst is real and unresolved: GLW's $2bn ATM equity program (catalyst:9744ffb8fe) drove direct optics-peer contagion, and COHR is *still* underperforming even today's broad rally (rel_strength_1m -2.06pp, abs_return_1m -3.85%, and a stop already fired at $295 this morning on the same story). A case exists to retire P-339 as redundant with the stop already executed — but I am not making that call: this book's own scorecard shows **HOLD-type calls have a 0% hit rate over 14 scored instances** (see scorecard read below), so overriding a live, reaffirmed, cap-independent catalyst trim with a fresh "no further action" judgment is exactly the kind of call this desk has never gotten right. P-339 stays open, unchanged, for the user to weigh with both facts in view: it would be an *incremental* de-risking on top of a stop that already cut the position to 2.01% weight, on a name whose thesis has not broken.

**TER / P-310 — one fact update, no action change:** P-310's rationale cites "real cap breach (1.078x)" as reinforcing (not driving) the trim. Today's `compute_rotation.json` shows TER's cap_multiple has cured to **0.891x** (under cap) — likely the relief rally widening ATR-based headroom. Per the proposal's own design (`retires_when`: no longer appears in a structural-threat catalyst; cap curing does NOT retire it) and 2a-ii, this doesn't change the recommendation — the catalyst_threat basis (CXMT HBM3E, reaffirmed) is unchanged and TER's net_signal is still bearish (PEER LAGGARD). Flagging the stale "real cap breach" framing so it isn't repeated as current fact.

**Not surfaced this run (low-conviction, no existing proposal, would only add to an already-saturated idea slate):** `trend_entry` LITE ($317.29, conviction_score 29.1, tier low); `conviction_average` MSFT ($1,085.73, tier low) and CIEN ($256.99, tier low — CIEN is also a $3.02 dust position per derisk's friction flag). Twelve of the fourteen open proposals are already idea-class competing for the dashboard's 5 slots; these three would rank below all of them on conviction and are noted for completeness, not proposed.

## Risk-off status
**Normal.** Drawdown -2.469% vs. -8% warn / -12% risk-off. Aggregate open risk was 5.68% (derisk queue) against a 10% cap. No stop-out in 15 sessions. Cash at 30% is dry powder per the standing playbook, not a distress signal. No defensive trims, no stop tightening, no target-cash directive beyond the already-stated Oct-data staging plan.

## Hit-rate readout (compute_journal.json bucket_hit_rates — computed, not re-derived)
- TARGET GAP: n=19, 36.8% hit rate — below the 40% de-emphasis line.
- MOMENTUM+VOLUME: n=15, 20.0% hit rate — well below the line.
- OVERSOLD BOUNCE: n=3, 66.7% — strong, but under the ≥5-entry threshold for any recommendation either way.
- BREAKDOWN: n=1 — skipped (under 3).

Recommend de-emphasizing **TARGET GAP** and **MOMENTUM+VOLUME** as standalone signal buckets — both have run long enough (15-19 scored entries) to be below the 40% bar with real sample size, not noise.

## Scorecard interpretation (proposals.json scorecard — consumed, not recomputed)
Stored figures, as of 2026-09-17, n=80 scored (2 quarantined for anchor review — P-011 BUY NEM implies +39.7%, P-095 HOLD AMD implies +45.7%, both need anchor verification before trusting):
- **Overall: 31.2% (n=80)** — 25 worked, 46 missed, 9 neutral, avg_benefit -3.04%.
- **TRIM/SELL: 38.1% (n=42)**, avg_benefit -3.13% (direction-consistent on average — when it worked, price fell as intended — but a sub-40% hit rate on the desk's single largest proposal class).
- **BUY: 37.5% (n=24)**, avg_benefit +0.65% — barely positive on average even on the "worked" cohort.
- **HOLD: 0.0% (n=14)** — 0 worked, 12 missed, 2 neutral, avg_benefit -9.08%. Every scored HOLD in this book's history has been wrong or noise-band-adjacent-negative. This is the figure that shaped the COHR/P-339 call above: I did not issue a fresh HOLD-style override today given this record.
- 0 of 80 graded rows carried a benchmark anchor this run (`alpha_scored_count: 0`) — all 80 are graded on raw stock move, not alpha vs. SMH, because they predate the 2026-09-07 benchmark field or omitted it. That means today's relief rally itself will show up as "several TRIMs missed" in the next scoring pass purely from beta, not desk error — worth remembering when the next quarterly read comes in.

**What this implies:** across all three action types this book has run, none clears a 40% hit rate yet (n=80 total). TRIM and BUY are close to a coin flip with a slight edge on TRIM; HOLD has a clean negative record. This argues for continued humility in sizing (small, capped tranches, which is already this desk's practice) and for weighting the newer alpha-vs-SMH-anchored proposals (2026-09-07 onward) more once they clear the 30-day window (161 proposals are currently `not_yet_30d`) — the pre-anchor cohort's poor accuracy may partly reflect grading against raw moves in a beta-heavy book, not exclusively bad calls.

```json
{"policy_draft":null,
 "stress_table":{"as_of":"2026-09-17",
   "anchored_to":{"us10y_pct":4.947,"vix":15.73,"dxy":100.234,"fed_rate_pct":3.875,"fed_stance":"hawkish"},
   "scenarios":[],
   "data_quality":["Quick sweep -- no material trigger for a full six-scenario stress table this run (no new breach, no risk-off escalation, no fresh macro shock); anchored_to carried forward from this run's macro strip for continuity only."]},
 "proposals":[],
 "scorecard_read":"Stored scorecard (proposals.json), n=80 scored, 2 quarantined for anchor review. Overall 31.2% (25/80 worked, avg_benefit -3.04%). TRIM/SELL 38.1% (n=42, avg_benefit -3.13%, direction-consistent but sub-40%). BUY 37.5% (n=24, avg_benefit +0.65%). HOLD 0.0% (n=14, 0 worked/12 missed/2 neutral, avg_benefit -9.08%) -- every scored HOLD has been wrong; this shaped today's decision NOT to override the open COHR trim (P-339) with a fresh no-action call despite the thesis-strengthening/catalyst-threat tension. 0/80 graded rows carry a benchmark anchor (alpha_scored_count 0), so today's relief rally will read as raw-move TRIM misses next pass, not necessarily desk error. 161 proposals not yet 30 days old, including all of today's newer benchmark-anchored ones.",
 "deemphasize_buckets":["TARGET GAP","MOMENTUM+VOLUME"],
 "data_quality":["No new sized proposals this run -- the 14 open proposals (P-305/310/314/318/339/341/343/344/346/347/348/349/350/352) already cover every live compute_triggers.json signal with size/thesis support; today's only development (COHR stop-out) is already reflected in holdings/thesis, not a fresh trigger.","catalyst_threat fired mechanically on all 25 holdings this run with size proportional to market value and direction hard-coded to TRIM regardless of thesis/signal (e.g. GOOG/QCOM/WDC, whose open proposals are BUYs) -- this is the same stale/broad-application pattern the 2026-09-16 run rejected (orchestrator:bea50db56e); treated as non-authoritative for new proposals, existing catalyst_threat-tagged proposals were evaluated on their individual written rationale instead.","P-310 (Trim TER) rationale's 'real cap breach (1.078x)' is stale -- today's compute_rotation.json shows cap_multiple 0.891x (cured by the relief rally); no action change since the trim is catalyst-driven, cap-independent by the proposal's own design, but the cap fact itself should not be re-cited as current.","trend_entry (LITE $317.29) and conviction_average (MSFT $1,085.73, CIEN $256.99) fired live this run at low conviction tier with no existing open proposal -- not surfaced given 12 higher-or-equal-priority idea-class proposals already open competing for the same dashboard slots.","TER open_flags dust-position entry (08-19) remains stale/superseded -- orchestrator cleanup, not a strategist action (reaffirmed from thesis/signals tails)."]}
```

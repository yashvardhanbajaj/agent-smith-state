# Smith Strategist — 2026-09-09 (Quick Sweep, pre-open)

## Policy draft
Not needed — `policy.json` is present and confirmed (`policy_confirmed: true`, `policy_defects: []`).

## Proposals (new, sized)

All four ideas below are triggered from `compute_triggers.json`/`compute_rotation.json` (live triggers), not re-derived. The 7 already-open proposals (P-231 BUY AMAT, P-232 BUY CIEN, P-235 BUY GOOG, P-239 BUY APH, P-241 SELL AVGO / P-242 BUY LITE paired, P-243 TRIM NVDA) are **not** restated here — none of the tickers/directions below duplicate them.

---

### 1. TRIM MU — catalyst_threat (live)
- **size_usd:** 400.18 | **price_at_proposal:** $1,000.26 | **trim_fraction:** 0.20
- **trigger_type:** `catalyst_threat`
- **Rationale:** CXMT reached HBM3E risk production, shipping qualification samples to Alibaba T-Head/Cambricon — ~1yr ahead of the 2027 consensus timeline (qualification-stage only, no unit count, not yet in any supplier contract price per hbm_tracker.json — carried forward, last confirmed 2026-09-07). MU is a **direct HBM competitor** to CXMT, so this is a genuine competitive-exposure name for the trigger, unlike four other names the same catalyst fired on this run (see data_quality below). MU thesis is WATCH, not strengthening, and its rotation bucket is `null` (not `accumulate`) — no 2a-i/2d tension. Ran `smith_math.py gaps --query "CXMT HBM3E equipment conflation"` per the catalyst_threat precedent-check requirement: no exact prior incident matched, but G48 (archived) independently confirms the CXMT-threat framework was built around named memory competitors ("Samsung..."), which supports treating MU (a memory maker) as in-scope and the equipment names as out-of-scope.
- **evidence_quality:** {"verified": 0, "computed": 2, "unverified": 1}
- **benchmark_price_at_proposal:** not available this run — `holdings.json.benchmarks` is empty (SMH not refetched in this quick-mode snapshot); flagged in data_quality.

### 2. TRIM SKHY — catalyst_threat (live, with a noted tension)
- **size_usd:** 185.55 | **price_at_proposal:** $185.55 | **trim_fraction:** 0.20
- **trigger_type:** `catalyst_threat`
- **Rationale:** Same CXMT catalyst as above. SKHY is memory-adjacent (SK Hynix-linked HBM exposure) and is a genuine competitive-threat name. **Tension, stated per `compute_rotation.json`'s own blocker text:** SKHY is simultaneously in the `accumulate` bucket on a strengthening thesis (PEER LEADER bullish bucket, RSI 64.9, not yet overbought) — the catalyst answers a financing/competitive-structure question, the accumulate signal answers an operating-fundamentals question. Per skill guidance this does not cancel a catalyst_threat trigger (cap/cluster/bucket-independent by design), but it does mean size and priority here are a judgement call, not a formula — sized at the standard 20% trim rather than escalated, and ranked below MU's cleaner case.
- **evidence_quality:** {"verified": 0, "computed": 2, "unverified": 1}
- **benchmark_price_at_proposal:** not available this run (see above).

### 3. PAIRED — SELL AMD / BUY KLAC — cluster_rotation (live)
- **pair_id:** `cluster_rotation-AMD-KLAC`
- **Sell leg:** AMD, size_usd 455.17, price_at_proposal $505.74 (=$1,517.22/3sh)
  - Cluster ladder (2026-09-08, medium confidence) ranks AMD #8 of 10 in AI Semis/Fabs — a laggard on the ladder's own axis (foundry/IDM customer-concentration / whether the customer itself is gaining share), ranked above the pure price-laggard slot because AMD's Q2 beat and Data Center +107% YoY reflect real share gain even as the stock underperforms.
  - AMD thesis is WATCH (verified: secondary, 2026-08-14) — not broken, but not strengthening either; over_cap = false, rotation bucket = null (no 2a-i/2d conflict). This is fresh territory: prior AMD sell legs (P-157/P-160/P-172/P-176/P-190/P-203/P-205/P-215/P-229/P-237) were all superseded or auto-retired on aging, never accepted or dismissed by the user, so this is not a re-proposal of a decided row.
- **Buy leg:** KLAC, size_usd 455.17, price_at_proposal $188.98
  - Cluster ladder ranks KLAC #2 of 10 — process-control/metrology intensity rises fastest at gate-all-around and advanced packaging. Thesis strengthening (secondary), STRONG UPTREND bucket, conviction_score 61.4 (medium tier), stop_price_usd $171.745 (from the same conviction scorer, cross-referenced via the `trend_entry` row for KLAC).
- **evidence_quality (both legs):** {"verified": 1, "computed": 2, "unverified": 0}
- **retires_when:** the AI Semis/Fabs ladder no longer ranks KLAC above AMD, or the ladder goes stale (>14d).

### 4. STOP_RAISE NBIS — profit_ratchet (shadow trigger, not yet hit-rate validated, no capital moved)
- **Rationale:** NBIS is up +16.56% vs its $209.23 basis, but its current stop ($195.69) sits *below* breakeven — a retracement would turn a real winner into a realised loss. This independently coincides with two computed facts: NBIS is `over_cap` (cap_multiple 1.108, `trim_risk_cap` bucket in `compute_rotation.json`) and sits #2 in the de-risk queue (derisk_score 124.0, second-highest in the book) per `compute_derisk.json`. No hit-rate history exists for `profit_ratchet` yet (shadow, scored zero regardless of what's written here), but this is a stop-management action, not a scored trade call — recommend raising the stop to $209.23 (cost basis). Note the user already trimmed NBIS 7→5sh (real trade, $245.69) this cycle; this is a housekeeping stop-raise on the remainder, not an additional trim.
- **evidence_quality:** {"verified": 1, "computed": 2, "unverified": 0}
- **size_usd:** 0 (no capital moved)

---

## Cash-below-band — sizing implication for the open BUY ideas

Cash is **2.762% of the $43,498.52 total book**, below the policy floor of 5% (`compute_drift.json`: `cash_breach: true`, band [5,15]). `compute_triggers.json` independently confirms this at the mechanical level: `deployable_cash_usd: 0.0` and `deployable_cash_for_ideas_usd: 0.0` — every BUY-side row in `oversold_reversion`, `trend_entry`, and `conviction_average` this run carries `suggested_size_usd: 0.0` with the blocker *"no deployable cash above the band ceiling — setup valid, funding is not."*

This directly affects the four already-open BUY ideas: **P-231 (AMAT, $400), P-232 (CIEN, $200), P-235 (GOOG, $287.95), P-239 (APH, $589.33)** — $1,477.28 wanted in total. None of them can be self-funded from the wallet without pushing cash further below its own floor. The one BUY leg that *is* funded — P-242 (LITE) — works only because it is explicitly paired against a sell (P-241, AVGO) rather than drawing on cash. **The same constraint applies to proposal #3 above**: the AMD sell leg is what funds the KLAC buy leg; it is not a cash draw. Read: none of the standing BUY ideas should be treated as actionable on their own until either a fresh stop-out replenishes cash or each is given its own funding leg — this is a sizing-logic point, not a reason to withdraw them (they remain valid per their own retirement conditions).

## Risk-off check (Task 3)

`risk_off_status` = **normal** (`compute_drift.json`). Drawdown is -6.937% off the $46,740.81 peak (total-book basis) — inside the book's -8%/-12% warn/risk-off thresholds. No defensive lead required; `smith-rebound`'s own read classifies this as `pullback`, not `correction`, consistent with normal risk-off status. Sentiment band is **greed** (score 66.3, `compute_sentiment.json`) — not extreme_greed — so the standard "greed leans toward booking profit on stretched names" guidance applies loosely; it supports (but doesn't mandate) the MU/SKHY/AMD trim legs above rather than requiring a harder defensive posture. No LTCG deferral applies — the earliest open lot is well inside 2026, nowhere near the ~2028 24-month boundary.

## Stress table

Skipped — quick mode. `smith-macro` did not run this run (`out_macro.json`/`crosscheck.json` absent, as expected for quick sweeps).

## Hit-rate readout (Task 5, from `journal.json`, precomputed — not recomputed)

| bucket | n | hit rate | note |
|---|---|---|---|
| MOMENTUM+VOLUME | 15 | 20.0% | **Below 40% over ≥5 — recommend de-emphasis.** INTC fired this bucket fresh this run (+9.05%, 1.76x ATR); treat that signal with real skepticism given this bucket's own 15-entry record. |
| TARGET GAP | 19 | 36.8% | Below 40% over ≥5 — borderline, recommend de-emphasis. New fires this run: GEV, AMD, VST. |
| OVERSOLD BOUNCE | 3 | 66.7% | n=3 is the minimum reportable threshold; below the n≥5 bar for a de-emphasis call either way, and the rate itself is strong — no action. |
| BREAKDOWN | 1 | — | Skipped, n<3. |

## Scorecard interpretation (Task 6 — consumed from `proposals.json`, not recomputed)

`smith_math.py score` graded 33 proposals as of 2026-09-09: **overall accuracy 36.4% (n=33)**, **BUY 62.5% (n=16)**, **TRIM/SELL 14.3% (n=14)**, **HOLD 0% (n=3)**. `smith_math.py stops` scored 165 stop events at a 36.1% win rate with a net +$7,178.93 saved-vs-hurt. Reading these together: this desk's BUY calls have real, above-chance skill (62.5% on n=16 is a meaningful sample); its TRIM/SELL calls have been poor (14.3% on n=14, avg benefit -14.47% — trims have mostly cost the book realized upside rather than protecting it) even though the stop-loss mechanism itself is net-positive in dollar terms. That combination argues for real caution sizing the TRIM legs above (MU, SKHY, AMD) — they sit in the desk's weakest-performing category — and for weighting the desk's own trim conviction lower than its buy conviction when the two disagree. None of the 4 new proposals above are yet old enough to be in this scorecard (`not_yet_30d: 136`); this is a review of the desk's *track record*, not of these specific ideas. 4 rows remain quarantined for anchor review (P-011, P-030, P-048, P-064) — none of today's proposals touch those tickers/dates.

## Data quality / flags

- **Catalyst-threat conflation, likely miscategorized:** `compute_triggers.json`'s `catalyst_threat` list also fired on ASML, TER, AMAT, and LRCX for the same CXMT-HBM3E catalyst. These four are semicap **equipment/test suppliers**, not memory producers — CXMT building more HBM3E capacity is arguably a *tailwind* for their tool sales, not a competitive threat, unlike MU and SKHY which directly compete with CXMT in memory. Declined to size trims on ASML/TER/AMAT/LRCX off this catalyst; recommend the catalyst-scanning logic scope this specific threat to memory-producer names only. (AMAT also already carries an open BUY idea, P-231, on oversold_reversion/conviction_average — trimming it on a mismatched catalyst the same run would be self-contradictory.)
- **benchmark_price_at_proposal unavailable this run:** `holdings.json.benchmarks` is empty (SMH not fetched in this quick-mode pass). The 3 new sized ideas above lack it; `score` will fall back to raw-move grading for them rather than alpha-vs-SMH, until a run with a live SMH quote re-anchors them.
- **ALAB (-6.9%) diverging from the broad rally:** flagged by smith-signals as notable but no computed breach or catalyst attaches to it this run — thesis remains strengthening, no proposal warranted on this alone.
- **IREN's "re-entry interest" open_flag is stale** (`open_flags.7460550d.json`, opened 2026-08-03/08-12): IREN fully exited via stop-loss 2026-09-08, and this run's `reentry` trigger independently judged and **rejected** IREN on the merits (trend_breakdown live, conviction_score -4.0/none, thesis WATCH) — not for lack of evidence. Recommend the flag be closed; not a proposal, just a housekeeping note for smith-thesis/the orchestrator.
- Full stage-1 tail context (broad pre-open rally, live-quote overlay applied, VST thesis seeded, AI-capex now 95.7% of book) is accepted as given per the dispatch; nothing there produced a fifth actionable idea beyond the four sized above.

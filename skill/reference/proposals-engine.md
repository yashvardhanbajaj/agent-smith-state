# Agent Smith — proposal engine reference

Split out of `SKILL.md` §7 on 2026-08-30, together with §2.9d's diagnosis narrative. These are
the *derivations* behind the proposal engine's current rules — three rebuilds (2026-08-12,
08-17, 08-24) against the same standing user complaint, the auto-retirement conditions, the
priority-score weight history, honest sizing, and the `lots`/`score` subcommand rationale.

SKILL.md keeps every operative rule; this file holds the WHY, on the same principle as
`DECISIONS.md`. Read it before changing a scoring weight, a retirement condition or a trigger's
live/shadow status — each of those numbers was set against a specific measured failure, and
several were tuned once and are easy to "simplify" back into the bug they fixed.

---

## Auto-retirement, priority scoring, honest sizing and rotation pairs

**Condition-based auto-retirement + live re-justification** (added 2026-08-06, user-reported: *"the dashboard is not live and dynamic like it should be… under low priority proposals, it is showing rebuild cash buffer"* — while cash sat at 25.3%, three times its band ceiling). The `proposals` subcommand now, on every run, re-tests each open proposal against **today's** structural conditions and retires the ones whose trigger has objectively cleared, setting `status: "auto_retired"` plus a `retired_reason`:
- a **TRIM/SELL** retires when its ticker is within its ATR risk cap *and* its cluster is inside its policy band — the only two structural problems a trim exists to cure. A proposal keeps living if *either* survives, which is why a DRAM trim correctly stayed open on its risk-cap trigger after its cluster reason died.
- a **BUY** retires when it says "initiate/new position" and the name is already held, or when the cluster underweight it was filling is back in band.
- a **HOLD** retires when its ticker is no longer held, or after 2 days — hold-fire advice ("hold until tonight's print") is tactical and must not silently become standing guidance.
- a **cash-rebuild** proposal retires once cash re-enters or overshoots its normal band.

**Restatement auto-retirement REMOVED 2026-09-15 (user decision).** From 2026-08-24 to 2026-09-15 a fifth condition lived here: any proposal (paired legs exempted) with `repeat_count >= 3` auto-retired regardless of whether its underlying trigger was still live, on the theory that 3+ unacted restatements meant "declined in practice" (0-for-17 measured beyond four restatements). The user's own words removing it: *"I look and take my mental note from the proposals, if the proposal is still making sense based on the latest analysis we should keep it."* Repeat count is evidence the idea wasn't acted on, not evidence it stopped making sense — conflating the two took the decision away from the user. The four conditions above are unaffected; each of them tests whether the proposal's OWN trigger condition is still true, which is exactly the bar the user wants applied. `repeat_count` itself is not gone — it still increments, still shows in the proposal's `note` ("3rd time recommending this"), and still contributes to `priority_score` (see below) so a heavily-restated idea is visibly deprioritized rather than hidden; only the automatic deletion on top of it is gone. The paired-leg exemption this rule needed (added 2026-09-08, see `test_smith_ladder.py`'s former `TestPairedLegRepeatExemption`) is removed along with it — there is nothing left for it to guard against.

This deliberately reuses the *same typed signals* the priority scorer reads (`over_cap` from compute_risk, `breach` from compute_drift, `cash_pct` vs band) and **never parses rationale prose** — that is precisely what made the 2026-07-29 breach-cleared voider false-positive and get disabled. Judgement calls are never auto-actioned: a proposal whose price has drifted ≥10% since it was written gets a `review_flags` entry ("re-size before acting") and stays open. `auto_retired` is intentionally distinct from `superseded` (folded into a duplicate) and `dismissed_by_user` (terminal, the user's own call), so the audit trail shows who retired what and a genuinely re-emerging condition is free to be proposed afresh.

Every surviving proposal also gets `still_valid_because` (recomputed each run) and `price_now`/`price_drift_pct`. The dashboard renders these under the frozen `rationale`, visually distinct — that is what makes the panel read as live rather than as an archive: the reader sees a 6-day-old trim is still listed because the cap is *still* breached today, not because nobody cleaned up.

**Directional cash bug, fixed the same day**: `cash_breach_vs_normal` is a bare boolean that fires on BOTH edges. The scorer had been awarding every trim +2 captioned "cash outside its normal band — this also rebuilds it" *while the book was drowning in idle cash*. Now split: a trim earns the bonus only when cash is genuinely short, and a BUY earns one when cash is in excess. On 2026-08-06 this correctly promoted the GOOGL deployment to HIGH and demoted two mild cap-breach trims to MEDIUM.

**Priority scoring** (added 2026-08-03, G47 — user asked "which proposal is what priority," not just a flat list; reweighted 2026-08-12 §2.9d and again 2026-08-17, see there for the full why): the same `proposals` subcommand also tags every open proposal `priority: HIGH|MEDIUM|LOW` plus a numeric `priority_score` and a `priority_reasons[]` list, entirely from data the pipeline already has (never a vibe-based label) — **current weights**: +2 if the ticker's own position is over its ATR risk cap (`compute_risk.json`; demoted from +3 on 2026-08-12), +2 if its cluster is outside its policy band (`compute_drift.json`'s `cluster_table`), +2 for a TRIM/SELL when cash itself sits outside its normal band (or a BUY when cash is in excess), +2 if genuinely stretched (`stretch`, real profit vs a falling benchmark) or a bullish signal clears a >55% interim hit rate (`signal_conviction`), **+3 if a live trigger fires** (`oversold_reversion`/`overbought_distribution`/`catalyst_threat`/`thesis_break` — the one component that is a fact about the stock, not the portfolio), +2/+1 for `repeat_count` ≥3/=2 (0 past ≥5, treated as implicitly declined), +1 for a full SELL, −1 for a BUY with no live trigger and score ≤0 (genuinely discretionary). Score ≥4 is HIGH, 2-3 MEDIUM, else LOW — **except: a score that reaches HIGH with no live trigger of any kind is capped at MEDIUM** (added 2026-08-17) — cap/cluster/cash/repeat stacking describes the portfolio's composition, not a reason the stock itself should move, and is not allowed to read as top priority on its own. The same pass also stamps each proposal's `cluster` (from `compute_risk.json`'s per-position cluster field) so the dashboard can tag and the user can reason about proposals by cluster even though the panel is grouped by priority, not cluster, as the primary axis.

**Honest sizing, stretch/signal-conviction scoring, and rotation-pair proposals** (added 2026-08-06, user-reported: *"why are the proposals of such low amount & seems ATR risk correction is the only thing these proposals are suggesting... suggest rotation of my capital from recently increased stocks to ones where I should move"*). Three linked additions:

- **`full_cure_usd`/`cure_pct`/`tranche_note`** on every open TRIM/SELL: what it would actually take to clear the trigger (the position's `headroom_usd` from `compute_risk.json` for a cap breach; `(actual_pct_of_total_book − band_hi)/100 × total_book_usd` for a ceiling breach — the correct denominator per `compute_drift.json`'s own choice, floor breaches would use `equity_usd` instead, never mix the two). When cited by both a cap and a cluster trigger, the binding one is whichever needs the LARGER trim — curing the smaller number first would still leave the position non-compliant on the other. This only *displays* the gap (`tranche_note`, e.g. "cures 27% of the risk cap excess ($1,457) — roughly 4 tranches this size to fully clear it") — it does not auto-resize `size_usd`, which stays a strategist/user judgment call.
- **Two new scoring dimensions**, same "typed number, never prose" discipline as everything else in this scorer: **stretch** (+2 for a TRIM/SELL whose ticker is in `compute_derisk.json`'s `names_stretched` — genuinely ahead of its sector AND up, not just fell less than peers) and **signal_conviction** (+2 for a BUY whose bullish signal bucket, from `compute_rotation.json`'s per-ticker `bullish_buckets`, has an interim 7d hit rate >55% with n≥3 in `journal.json`'s new `bucket_hit_rates_7d` — see below). Both are opt-in per proposal via a `trigger_type` field (`"stretch"` or `"signal_conviction"`) so the retirement pass (§6 above) knows to test the RIGHT condition for that specific proposal instead of defaulting to cap/cluster logic that was never the reason it was made: a stretch-triggered trim retires when the ticker drops out of `names_stretched`; a signal-conviction buy retires when its bucket disappears from `bullish_buckets` or its 7d hit rate falls to ≤55%. Verified by deliberately breaking both conditions on a test copy and confirming `auto_retired` fires with the correct reason before shipping.
- **`journal.json`'s `bucket_hit_rates_7d`** (new field, `cmd_journal`): the SAME direction-aware signed-move verdict logic as the validated 30d `bucket_hit_rates` (reuses `BUCKET_DIRECTION`/`VERDICT_THRESHOLD_PCT`), just evaluated at the 7-day mark instead of waiting for 30 — because on 2026-08-06 the oldest journal flag was 25 days old, so the 30d table was still empty. Kept in a **separate** dict from the 30d scores so it can never contaminate the validated hit rate; every consumer (the scorer above, the dashboard) must label it "INTERIM, not yet 30d-validated," never present it as equivalent.
- **Rotation-pair proposals**: implemented as TWO ordinary linked single-ticker proposals (a `trigger_type:"stretch"` TRIM and a `trigger_type:"signal_conviction"` BUY) sharing a `pair_id` and a `pair_role` (`"sell"`/`"buy"`) — deliberately NOT a new dual-ticker proposal object, so all existing dedup/expire/void/scoring/retirement logic (200+ lines built around a single `ticker` field) keeps working unmodified on each leg; only the dashboard needs pair-awareness (see below). This also means each leg retires independently and correctly the moment ITS OWN condition clears, without needing new cross-leg logic. When constructing a pair, verify the sell leg is a genuine profit-take (in `names_stretched`, not simultaneously in `compute_rotation.json`'s `accumulate` bucket with a strengthening thesis — trimming a name whose own thesis argues for adding more is a contradiction, skip it and note the tension instead) and size the buy leg to the SMALLER of the sell leg's value and the buy ticker's own risk-cap headroom (`max_position_usd − market_value_usd` from `compute_risk.json`) — sizing past the buy's own headroom would create a brand-new risk-cap breach on the very next run.
- **Dashboard rendering**: proposals sharing a `pair_id` (when both legs are still open) are pulled OUT of the normal HIGH/MEDIUM/LOW priority grouping and rendered together in a "ROTATION IDEAS" card (sell leg → arrow → buy leg) — because a pair's two legs routinely land in *different* priority tiers (the sell leg scoring only stretch, the buy leg also picking up cash-excess/signal bonuses), and splitting them across tiers would visually sever one rotation idea into two unrelated-looking rows. A leg whose partner has since been dismissed or retired independently falls back to rendering as an ordinary single proposal in its own tier, not dropped silently.


---

## The `lots` and `score` subcommands — why each exists

- **lots / corporate actions — `smith_math.py lots` (added 2026-08-15).** `python3 scripts/smith_math.py lots --base-dir . --holdings runs/<ts>/holdings.json` rebuilds lots.json from trades.json by deterministic FIFO and reconciles every lot sum against broker quantities. **Defaults to a DRY RUN; pass `--write` to actually replace lots.json.**
  Two things this fixed. (a) FIFO was being done by an LLM — smith-ledger rebuilt lots by hand, and consuming lots oldest-first is exactly the deterministic arithmetic COMPUTE-FIRST says must never be an LLM's job. (b) The ledger had no way to express events that move shares without a trade, which is what G68 and G71 both are.
  **Corporate-action rows** live in trades.json; a row with no `type` is a plain trade, so all 803 existing rows are unaffected. `ca_type` is one of: `conversion` (moves shares between symbols **carrying cost basis AND acquisition date — the LTCG clock does not restart**, which is the whole reason this can't be modelled as a sell+buy), `split` (qty × ratio, per-share basis ÷ ratio, dates preserved), `fractional_credit` (shares with no purchase; a null basis is flagged because it overstates future gain), `spinoff` (source keeps its shares), `adjustment` (an explicit, **sourced** reconciliation to broker truth when the cause is genuinely unknown — recorded rather than force-matched). `source` is required: this data is not in email, so an unsourced row is unverifiable.
  It **refuses to clamp**. A sell consuming more than exists is reported as a `phantom_short` with its date, not floored at zero — which is how G71's GOOG short stayed invisible for weeks. First run against the live ledger surfaced six, with dates, plus a previously-unrecorded VRT +0.0265 residue.
  **Not yet cut over:** lots.json is still the hand-built file. The engine reproduces it exactly on 34 of 35 held tickers (the 35th is the VRT finding), but the hand-built lots carry human provenance notes the rebuild would drop, and lots.json feeds LTCG math. Cutting over is the user's call, not a side effect of a sweep.
- **proposal scoring — `smith_math.py score` (added 2026-08-15). Run this on EVERY deep review, before the briefing.**
  `python3 scripts/smith_math.py score --base-dir . --prices-json <p.json> --today <date>` — run once with
  `--prices-json <file containing {}>` first (an empty JSON object -- `/dev/null` is not valid JSON and errors) and it NAMES the tickers it needs, then fetch those (they include EXITED names, so
  this is its own fetch, not a reuse of the holdings quotes). It grades every closed proposal at 30d/90d,
  direction-aware — a TRIM worked if the price FELL, a BUY if it ROSE, a HOLD if the move stayed inside the ±2% noise
  band — writes `outcome_pct`/`outcome_verdict` onto each proposal and an aggregate `scorecard`.
  **Why this is not optional:** as of 2026-08-15 the desk had produced 96 proposals, 9 of them actually executed or
  filled, and had scored exactly ZERO. The scorecard field existed and was written back null every run, its `note`
  growing into a five-entry log of "still zero proposals in the 30d/90d scoring window" dating to 2026-07-18 — an
  excuse that expired around 2026-08-12. Meanwhile journal.json had been scoring SIGNALS since July and carries real
  30-day hit rates. The desk was grading its indicators and not its decisions. First real run: **6 graded, 16.7%
  overall accuracy** — a number worth acting on, and one nobody could see before.
  It quarantines rather than grades any row whose implied move exceeds ±35%, because the first pass produced a
  "TRIM TSM missed by 39.4%" off a corrupt $305.87 anchor (TSM traded $386–448 that week) and on n=7 that single bad
  row set the entire trim-accuracy figure. Quarantined rows are reported in full and excluded from the aggregate —
  same rule the charts already apply to `value_trust != ok` ledger rows: a corrupt reading never sets an axis.


---

## Why the non-ATR triggers exist — the six diagnosed causes (SKILL.md §2.9d)

Deterministic candidate screens that exist because the proposal engine had become almost entirely an ATR-risk-cap machine. The user's 2026-08-12 report — *"still most of the proposals are based on ATR risk-cap. I dont want such proposals only. I prefer oversold/overbought proposals to catch a bounce back for the good stocks… book profit if something had a good enough run and put my money of another stock which is yet to run"* — was diagnosed to **five compounding causes**, all verified against the live book that day, and worth recording because each is a class of failure that recurs:

1. **The scorer's arithmetic forbade it.** `over_cap` scored **+3**, the largest single weight, and a BUY carrying no breach was *penalised* (`score -= 1`, "discretionary add"). "Buy the good stock that is merely oversold" was structurally the lowest-priority output the engine could produce. Fixed: over_cap demoted to **+2** (user decision), the new live triggers score **+3**, and the discretionary penalty now applies only to a buy with no typed trigger at all.
2. **The one existing profit-take trigger was starved by a stale cache.** `rel_strength_1m` was stamped `as_of 2026-07-31` — **12 days old against its own 7-day TTL** — and missing **10 of 28 held names** (every recently-added position). `names_stretched` had collapsed to `[AVGO, CEG]`. This was not cosmetic: the cached `benchmark_return_1m_pct` read **−17.84%** while the true trailing month was **+0.73%**, an **18.6pp error** that made nearly every holding look like it was "beating" a collapsing benchmark. On refresh the queue went from `narrow_stretch` (2 names) to `broad_stretch` (**17 names**). **Root cause: a 7-day TTL refreshed only on deep runs, when deep runs are weekly — so it was stale by construction.** Both `rsi14` and `rel_strength_1m` are now TTL-enforced regardless of run mode (see the revised `cache_policy.refresh_rule`), and `cmd_triggers` independently refuses to fire off a cache older than `TRIGGER_CACHE_MAX_AGE_DAYS` (10).
3. **Per-name RSI did not exist anywhere.** `data_cache` held `atr20`, `betas`, `rel_strength_1m` — no `rsi14`, no %-off-high; `ndx_rsi14` existed only for the *index*. So overbought/oversold could not be computed deterministically at all and smith-signals was assigning those buckets by eye. Consequence: **`OVERBOUGHT PULLBACK` had fired once in 69 journal entries.** Seeded 2026-08-12 from the same daily bars ATR20 uses — **zero extra API cost when both refresh together**, which is the only reason this is affordable (see §2.8: the history fetch is the most expensive thing this desk does).
4. **The book ran on its two weakest signals while its best sat dormant.** Interim 7d hit rates: `OVERSOLD BOUNCE` **100% (n=4)** — best in book, **1** live occurrence. `MOMENTUM+VOLUME` **15.4% (n=13)** — worst in book. `TARGET GAP` 54.5% (n=11) — **25** live occurrences, dominating the signal census. The engine was driven by the mediocre and the bad while the measured-good signal barely fired. This is what earned `oversold_reversion` its live vote immediately: unlike the other four, it is not an unmeasured idea.
5. **`repeat_count` was promoting proposals the user had in effect declined.** rc≥3 awarded +2 uncapped, so a trim restated 6× and never actioned (DRAM) ranked HIGH — not because it grew urgent but because it was ignored. Now decays: rc≥5 earns **zero** bonus and says so, suggesting `dismiss`.
6. **(2026-08-17) The 08-12 fix was necessary but not sufficient — it demoted portfolio mechanics, but never gave the scorer a channel for company-specific criteria that aren't a technical pattern.** User report: *"Most of the proposals and the analysis by Agent Smith is banked on the ATR risk/cluster cap/cash band formed. These caps/bands was formed as a loose portfolio composition. The trades/proposals should focus on other important criteria impacting an individual stock price instead."* Diagnosed against the live 2026-08-17 run: **6 of 8 HIGH proposals that run carried no live trigger of any kind** and reached HIGH purely by stacking over_cap (+2) + cluster breach (+2) + cash band (+2) + repeat count (+2) — up to 8, entirely portfolio-composition arithmetic, none of it a fact about the stock. Worse, the two things that most directly move a stock for company-specific reasons — a real, sourced structural threat (`smith-catalyst`) and a thesis flipping to broken (`smith-thesis`) — had **no path into the scorer at all**. That run's BofA bond-rating downgrade on Broadcom (real, dated, $370bn quantified tail-risk exposure) only became a sized proposal because the strategist manually folded it into BX's rationale by hand; AVGO itself, equally named in the same downgrade, got nothing, because nothing in the engine could score it. Fixed by adding two more live triggers, `catalyst_threat` and `thesis_break` (below), plus a priority-cap rule: **a proposal with no live trigger of any kind cannot reach HIGH on mechanics alone, capped at MEDIUM regardless of how high the stacked score runs.**



---

## Design decisions worth not re-litigating, and the 2026-08-24 conviction rebuild

**Design decisions worth not re-litigating:**
- **`overbought_distribution` is deliberately cap-INDEPENDENT**, in both scoring and retirement. Gating a profit-take on a risk-cap breach is exactly what made every trim an ATR trim. Its retirement pass therefore never tests `over_cap` — a name comfortably inside its cap stays a valid profit-take. On the seed run this surfaced **MSFT (+24.7% 1m, RSI 78.8)** and **BX (+16.5%, RSI 71.1)** — *neither over its cap*, so the old engine had no mechanism to propose booking any of it.
- **Entry and exit thresholds differ (hysteresis)**: oversold triggers <35 and retires >50; overbought triggers >70 and retires <60. Without the gap a proposal flips between open and auto_retired on noise.
- **The quality gate for a dip-buy is the THESIS, not the signal.** Requiring net-bullish signals would disqualify every oversold name by definition — being oversold *is* bearish price action. Only a *fundamental* negative (`NEW HEADWINDS`) disqualifies. On the seed run this correctly rejected the sole oversold name (META, RSI 34.1, thesis `watch`) as a falling knife and reported it in `data_quality` rather than dropping it silently.
- **Never estimate a missing technical.** SKHY's ADR history is too short for both RSI14 (9 closes, needs 15) and a comparable 1m return, so both are `null` and flagged — not interpolated. Same contract as ATR.
- **`profit_ratchet` only ever moves a stop UP, never below breakeven**, and it is the answer to "don't let my gain drain on retracement" — *not* a tighter stop. **Updated 2026-08-25 (self-learning Phase 3) — the efficacy figures below were stale.** The stop-loss efficacy record on n=140 scored stops now reads: 48.8% win rate overall, 54.2% on the deliberate cohort (n=79), 50.0% on the cascade cohort (n=29) — both cohorts sit close to a coin flip and no longer show the sharp divergence a smaller, earlier snapshot (n=6, "75% deliberate / 25% cascade") had suggested. That earlier read does not survive at the current sample size — it was itself an artifact of a thin sample, the same class of error the size-effect near-miss documented in `learning.json`'s lessons was. **The conclusion still argues against tightening**, just for a cleaner reason now: at ~50% either cohort, there is no measured edge to exploit by moving the stop distance in either direction, and the honest read on today's data is "no calibration change indicated," not "cascade stops are unusually bad." Cost basis comes from lots.json; synthetic null-price lots (G1) are excluded from the average and flagged, never imputed — a ratchet computed off a guessed basis would move a real stop on a fabricated number. **Known gap**: `stops_analysis.json` rows carry no ATR-at-fill, so per-volatility-tier stop-distance calibration (as opposed to cascade-vs-deliberate) is not currently possible — `smith_math.py score-shadow-journal`'s sibling tooling could be extended to capture this if tier-level calibration is wanted later.

**2026-08-24 — conviction-driven rebuild.** The 08-12/08-17 fixes above corrected *why* a proposal fires but never touched *what generates it* or *how big it is*: buy sizing was still `min(ATR headroom, 25% × excess cash)`, which structurally sizes at $0 for any name with no open position (an exited name could never be re-proposed) and shrinks exactly when volatility rises, i.e. exactly when you'd want to buy. Reported a third time, same root complaint, plus five explicitly named behaviours (trend entry/exit, profit-booking rotation, averaging down on a genuine drawdown, intra-cluster laggard→performer rotation, headwind/tailwind) that existed as classified signal buckets (`SIGNAL_POLARITY`) but drove nothing downstream.

Fix: a new `scripts/smith_conviction.py` scores every candidate 0–100 from thesis+evidence, catalysts, trend (now bidirectional — tailwind matters, not just headwind-as-veto), valuation gap, earnings, technical setup, and cross-agent corroboration; `size = conviction_tier_pct × policy_max_position_usd`, staged to a first tranche, then clamped to the tightest of ATR headroom / cluster room / deployable cash — with `clamped_by` always named, never silently substituted. Nine new trigger types (`trend_entry`, `trend_breakdown`, `profit_rotation`, `cluster_rotation`, `conviction_average`, `conviction_exit`, `entry_setup`, `reentry`, `bench_diversifier` — see §2.9d's trigger table above, now current) cover the five named behaviours; `profit_rotation`/`cluster_rotation` render and retire as ONE paired decision, direct fix for a 0-for-19 historical rotation-pair survival rate caused by independently-managed legs. The dashboard now splits proposals into an IDEAS panel (max 5, ranked by conviction, minimum-bar gated — shows fewer or zero rather than padding) and a RISK HOUSEKEEPING panel (cap breaches, stop-raises, band drift — sized and actionable, never ranked against an idea) via a new `proposal_class` field. Restatement auto-retirement lowered from 5 to 3 (0-for-17 historically beyond four restatements). Full design in `smith_conviction.py`'s module docstring.


---

## Conflict retirement: the weaker of two proposals goes (added 2026-09-15)

User request, after dismissing P-261 and P-264 by hand: *"automate this auto-retire of the weaker
proposal."* Two gaps let contradictory rows sit side by side:

- **Different verbs on one side.** P-261 "Trim ASML" (09-10) and P-305 "Sell ASML" (09-15).
  Dedup keys on (ticker, direction), and TRIM and SELL are different buckets, so the rows never
  met. The stacking guard grouped them but only flags, by design.
- **Opposite sides.** P-264 "Trim AMAT" and P-314 "Buy AMAT". Nothing compared a buy with a trim
  of the same name at all.

Two passes in `cmd_proposals`, after condition-based retirement:

1. **`_apply_declared_supersessions`.** A spec's typed `supersedes: ["P-###"]` retires those OPEN
   ids and their rotation partner legs. The strategist had already written "AMENDS P-263 /
   RETIRES P-264", but only in rationale prose, which the lifecycle deliberately never parses
   (the 2026-07-29 false-positive class).
2. **`_retire_weaker_conflicts`.** OPEN rows on one ticker conflict when they sit on opposite
   sides, or on one side with different verbs. Exception: two non-overlapping rotation
   pair_ids, i.e. independently funded rotations, stay a legitimate stack. The weaker row
   retires with its partner legs. **Weaker means older first**: a later run's strategist saw the
   queue and wrote something different, the same "latest occurrence wins" rule dedup uses.
   Within one add-proposal batch the lower `priority_score` loses, then the smaller size.
   Priority does not lead because P-261 outscored its replacement (4 vs 2) on a repeat bonus and
   a stale catalyst basis.

**Accepted rows are never retired by either pass.** They are the user's decision. A declared
supersession flags them `declared_superseded_by_<id>`, and an open row contradicting one gets
`contradicts_accepted_<id>`. Same-side accepted stacks stay the stacking guard's job. Status is
`auto_retired` with `retired_reason` and `superseded_by`, so `score` still grades the retired row.

## cluster_rotation: two ways to rank (added 2026-09-08)

`cluster_rotation` pairs a sell and a buy INSIDE one cluster. It has always answered "which
member is winning?" with `rel_pp` from `data_cache.rel_strength_1m` — a number that is **always
SMH-relative for the whole book**. `data_cache.rel_strength_1m_peer` is null, so power and
hyperscaler names were ranked against a semiconductor ETF. On the live 2026-09-07 book that put
AVGO worst-in-optics on a -13.31pp reading while it was in fact **+5.19pp ahead of its own
cluster**, and open proposal P-242 was selling it.

From 2026-09-08 the trigger prefers `smith-cluster`'s fundamental ranking when one is available
and has earned authority. `smith_risk.ladder_authority(entry, today)` returns one of:

| authority | when | what it changes |
|---|---|---|
| `none` | no ladder · older than `LADDER_TTL_DAYS` (14) · confidence low/unset · track record below coin-flip over ≥`LADDER_MIN_SCORED_CALLS` (6) | nothing — the `rel_pp` rule runs exactly as before |
| `rank` | fresh, `medium` confidence | ordering comes from the ladder; the sell leg **still** requires a `watch` thesis |
| `full` | fresh, `high` confidence | ordering from the ladder **and** the sell leg relaxes to "not `strengthening`" |

**The relaxation is the risky half and is priced accordingly.** The `watch` requirement is what
has kept this trigger from ever selling a name the desk still believes in — which also means it
can never rotate an *intact* laggard, the most common real case in a book with 16 strengthening,
16 watch and 0 broken. Lifting it lets a ladder sell something no other agent has flagged, so it
costs `high` confidence, which the agent must earn by defending every rank on a sourced
fundamental axis.

**The agent does not grade its own homework.** `confidence` is written verbatim from the tail,
but `cmd_ladder` scores every ladder's previous call on the next refresh (did the named leader
actually beat the named laggard?), `_merge_cluster` appends that score, and a cluster below
coin-flip over a real sample is forced to `low` and loses all authority regardless of what it
says about itself. This is the condition on which the layer was allowed near a live trigger.

**Leg selection under a ladder.** Only HELD, non-over-cap members are eligible on either leg —
a ladder ranks the bench too, and buying a bench name introduces a name the book has never owned
on agent judgment alone, which must earn its own trigger and its own vote. The sell leg is taken
from the **bottom third** of the ranking, not simply "last": with ten names in AI Semis/Fabs the
difference between rank 9 and rank 10 is inside the agent's own resolution, and insisting on the
exact last name makes the pair hostage to a distinction the ladder cannot actually make. Among
the bottom third the **largest** position is sold, because that is where dead money costs
something.

**Provenance is on every pair**: `ladder_driven`, `ladder_as_of`, `ladder_confidence`,
`ladder_authority`, `ladder_authority_reasons`. `retires_when` names what the pair was actually
built on — a ladder-driven pair retires when the ladder reorders or goes stale, never against a
price fact nobody used. `pair_id` is unchanged (`cluster_rotation-<SELL>-<BUY>`), so
`_retire_orphaned_rotation_legs` keeps retiring both legs together.

**Sizing.** `clamp_size` now receives real `cluster_room_usd` (from `cmd_drift`), via
`_pair_cluster_room_usd`, which credits the sale's proceeds back when both legs share a cluster
— a swap funds its own room, and clamping to the cluster's standing room would zero the buy leg
inside a full cluster and silently convert the rotation into a naked sell.

**Crosscheck.** `ladder_vs_thesis` fires when the ladder ranks a name last while smith-thesis
calls it `strengthening`, or first while thesis calls it `watch`/`broken` — `high` severity when
the ladder has trigger authority, `medium` when it is advisory. Two agents disagreeing about the
same company is not noise to average away once one of them can size a trade on it.


### The two shadow siblings (added 2026-09-08)

Both are PAIRED and both start on a **shadow** vote — `price_at_flag` now, scored at 7/30d, a
vote only once measured. The standing rule is that a new signal class earns its vote before it
gets one, and each of these introduces a kind of claim the engine has never acted on before.

**`cluster_bench_rotation`** — sell the ladder's laggard, buy a name the book has **never held**.
Often the honest answer to "rotate the laggard into what?" is outside the book: a ladder that can
only recommend from what is already held is choosing the best of a set nobody re-examined. But
this is the one trigger that introduces a never-held name on a single agent's judgment, with no
journal history, no thesis entry, no lot, and no record of this desk ever having been right about
it. Its buy leg is deliberately **not sized**. Its SELL leg still clears every bar a live rotation's
sell leg does — the shadow-ness is entirely about the buy. A bench entry naming a current holding
is skipped: that is `cluster_rotation`'s job, and `cluster_rotation` is live.

**`cluster_consolidation`** — two holdings that are ONE bet, collapsed into the better of them.
The only rotation on this list that does not change factor exposure at all; it shortens the tail,
because three expressions of one WFE trade carry three sets of idiosyncratic risk for one thesis.
It sells the whole drop-side position (a partial sale leaves the redundancy in place) and acts
**only** on pairs the agent explicitly marked `verdict: "redundant"` — a candidate it looked at
and called `distinct` is a judgment already made, and `cmd_ladder`'s screen is a resemblance,
never a cause. It will not add to a keep-side name already past its ATR cap.

### PAIRED_TRIGGERS

`smith_core.PAIRED_TRIGGERS` (and the derived `PAIRED_TRIGGER_PREFIXES`) is the **single** place
a paired trigger's membership is declared. Before 2026-09-08 the pair of names was written out by
hand at four separate sites in `smith_lifecycle.py` — the retirement pass, `trigger_pairs`'
construction, the sell-leg carve-out, and `retires_when`. Adding a fifth paired trigger without
updating all four silently reintroduces single-sided retirement, which is the exact bug behind
"19 rotation pairs attempted all-time, 0 survived". Add to the set; do not add to a call site.

### Where ladder calls are measured

Two places, for two different questions. `state.cluster_ladders[<c>].track_record` is
per-cluster and gates that cluster's own trigger authority. `learning.json`'s `ladder.hit_rate`
observations are the fleet-wide view, on the same append-only spine the journal's hit-rate work
uses, and answer the different question: is the cluster layer worth its token cost at all?


## Moved from SKILL.md on 2026-09-14

> Moved verbatim out of SKILL.md on 2026-09-14 (core cut to <=60KB). Load this file only when the core step that cites it runs. Where this text and the core disagree, the core wins — it reflects the scripted flow (`preflight`, `smith_fetch.py`, `dispatch-plan`, `postflight`).

### 2.9c. DE-RISK QUEUE — `smith_math.py derisk` (added 2026-07-31)
A standing, always-visible ranking of every holding by **how much damage it does if a drawdown comes** — explicitly not an attempt to predict one. Built after the user asked for a panel that flags high-volatility names to trim/tighten when the market nears extreme greed or a name goes overbought. The instinct was right; the trigger as first specified was not, and the reason is worth keeping because it will recur:

**Why "extreme greed → trim" is the wrong trigger.** Tested against the live book on 2026-07-31: the sentiment composite read **greed** (65.9) while **20 of 27 names sat >20% below their own 52-week highs**, median 52-wk position 0.548, NDX RSI 35.4. The composite reads the *index* (low VIX, SPX near highs); it says nothing about whether *your* names are extended. The only name an absolute overbought screen flagged that day was DRAM — on a known-bad 52-week low of $0. A greed-triggered rule would have told a book 8.35% underwater to sell into a bounce off an oversold crash. Compounding it: July's own record (tight SLs → mass stop-out 07-24 → names rallied back; 07-28 crash → 07-30/31 rip) shows reflexive tightening into strength makes whipsaw worse, not better.

**Composite, three transparent sub-scores, no black box.** `FRAGILITY` = share of total open risk (already embeds ATR × size) × how far the position sits over its own 2×ATR cap — the dominant term, "how hard does this hit." **Exemption (added 2026-09-07, user request, applied identically to `rotation_bucket` and the priority scorer):** the cap multiplier is floored at 1.0 — no amplification — for a name with a strengthening thesis and net-bullish signal that is not yet overbought (RSI14 ≤ 70); the raw risk-share exposure still counts in full, only the extra multiplier for being over cap is withheld, because that name is over cap *because it's winning*. Marked `cap_exempt` on the row. Falls back to the full multiplier when RSI isn't cached (surfaced in data_quality), matching `rotation_bucket`'s own fallback. `STRETCH` = 1-month return vs SMH, **gated on the name also being up in absolute terms** — beating a falling benchmark just means "fell less," and there is no gain to give back (on 2026-07-31 that gate correctly demoted 9 names that cleared rel>0 while sitting −2.5% to −17% absolute; only CEG/AVGO were genuinely up). Relative rather than absolute deliberately: in a ~100% single-factor book an absolute RSI/52-wk screen flags all-or-nothing. `FRICTION` = cost of acting — LTCG proximity to the 24-month boundary read from the now-populated lots.json (2.9b), unknown lot dates, dust-position discount — pushes a name *down* the queue. Sentiment is an **urgency dial** on the whole queue (`extreme_greed ×1.25 … extreme_fear ×0.5`, never sell into panic), never a trigger; it cannot manufacture stretch that does not exist per name.

**The ranked FRAGILITY/STRETCH/FRICTION composite queue itself is shadow-scored, no vote yet.** Every deep run appends its top-5 to `derisk_journal.json` with `price_at_flag` and scores them at 30/90d, exactly as journal.json does for signal buckets. **That composite ranking does not feed strategist proposals directly** — the desk's existing signal buckets still have zero scored entries for it, and a new signal class earns its vote before it gets one. Revisit promoting the composite itself once it has a real hit rate.

**This is a narrower claim than it looks — corrected 2026-08-24, previously stated as a blanket "does not feed strategist proposals" which was already false the day it was written.** `compute_derisk.json`'s `names_stretched` sub-list (the "genuinely ahead of sector AND up" subset of the composite, not the ranked queue itself) has fed the `stretch` trigger_type (+2 priority, `smith_lifecycle.py`'s scoring pass) and its own retirement branch since 2026-08-06 — see §2.9d and the priority-scoring table below. It is also the sell-leg candidate pool for `profit_rotation` proposals in the 2026-08-24 conviction rebuild. What remains genuinely shadow (zero vote) is the composite FRAGILITY/STRETCH/FRICTION *ranking* as a whole — the ordering itself, not the underlying `names_stretched` fact.

Pipeline position: `derisk` needs `compute_risk.json` + `compute_sentiment.json` in the run dir, so it runs after both. It also needs `data_cache.rel_strength_1m` (`values_pp` + `values_abs_pct`, benchmark SMH, 7-day TTL) — owned by smith-signals, refreshed on deep runs alongside ATR/beta; if absent the queue degrades to fragility-only and says so in `data_quality` rather than estimating.

### 2.9d. NON-ATR PROPOSAL TRIGGERS — `smith_math.py triggers` (added 2026-08-12, extended 2026-08-17 and 2026-08-24)

Deterministic candidate screens that exist because the proposal engine had become almost entirely an ATR-risk-cap machine. **Rebuilt three times against the same standing complaint** — *"most of the proposals are based on ATR risk-cap… I prefer oversold/overbought proposals to catch a bounce back… book profit if something had a good enough run and put my money on another stock which is yet to run… averaging a position in a high-conviction stock on a drawdown… within a cluster moving money from a laggard to a performer… headwind/tailwind."* **The six diagnosed causes, each a class of failure that recurs → `reference/proposals-engine.md`. Read it before touching a weight or a trigger's vote.**

The organising rule: **price says WHEN, thesis says WHICH WAY.** A laggard with an intact thesis is an opportunity; a laggard with a weak thesis is dead money. Conviction generates the idea and its size (`smith_conviction.py`); risk caps only CLAMP it, visibly, with `clamped_by` always named.

**The original seven triggers** (the 2026-08-24 conviction rebuild added nine more — `trend_entry`, `trend_breakdown`, `profit_rotation`, `cluster_rotation`, `conviction_average`, `conviction_exit`, `entry_setup`, `reentry`, `bench_diversifier`, all live; the full table with each one's direction and vote is in `smith-strategist.md` Task 2b and `reference/proposals-engine.md`)**.** `oversold_reversion` (BUY), `overbought_distribution` (TRIM), `catalyst_threat` (TRIM) and `thesis_break` (TRIM) are **live** — they may become sized proposals immediately. `laggard_rotation` (BUY), `profit_ratchet` (STOP_RAISE) and `scale_out_ladder` (TRIM) are **shadow-scored** first, per §2.9c's rule that a new signal class earns its vote before it gets one; the compute layer scores their trigger contribution as **zero** even if the strategist labels a proposal with them, so the split cannot be bypassed from the agent side.

**Why `catalyst_threat`/`thesis_break` are LIVE from day one, not shadow-first.** The shadow-first default exists for a newly invented STATISTICAL HEURISTIC with no track record in this book. It does not apply here: a `catalyst_threat` requires `smith-catalyst` to have already classified something `direction:"threat"` **and** `horizon:"structural"`, with a named source; a `thesis_break` requires `smith-thesis` to have explicitly flipped a name's status to `broken`, which under the G58 evidence gate means it already carries its own `evidence_for`/`evidence_against` arrays. Both are evidence-graded and sourced *before* they reach this scorer — gating them behind a fabricated hit-rate measurement would re-derive conviction the analyst agents already established. `catalyst_threat` sources `state.factor_catalysts` (this run's snapshot, replaced each run per §7); `thesis_break` sources `state.thesis` via `smith_risk.thesis_status`/`thesis_evidence`. Sized at `CATALYST_THREAT_TRIM_FRACTION` (0.20, a probabilistic tail risk) and `THESIS_BREAK_TRIM_FRACTION` (0.40, a confirmed break — heavier; the strategist may size up to a full exit). **Tension, never suppression**: a name can be simultaneously in rotation's `accumulate` bucket on a strengthening thesis *and* carry a live `catalyst_threat` — the trigger fires either way and flags the conflict as a blocker for the strategist to weigh, rather than letting either signal silently veto the other.

## add-proposal field contract (2026-09-20, rebuild Phase 1)

`add-proposal` used to build each row from a fixed dict and drop every other spec field. Measured on 2026-09-20: `stop_price_usd` persisted on 9 of 323 rows; `evidence_quality` and `trigger_bucket` last persisted 2026-08-25; `exited_on` 2026-08-24; `clamped_by`/`size_wanted_usd` 2026-08-26 — while the strategist supplied them on every leg. Three readers in `smith_lifecycle.py` depend on those fields and had become unreachable: the G58 evidence gate (`evidence_quality`), the `signal_conviction` retirement (`trigger_bucket`) and the reentry 20-day expiry (`exited_on`). The contract now: a typed `PASSTHROUGH` allowlist is validated and stored; a `RESERVED` lifecycle field or a mistyped passthrough value rejects the whole batch (nothing written); unknown fields are kept under `spec_extras` with a `data_quality` line. Historical rows are NOT backfilled — a synthetic stop is never written onto history. Support-anchored sizing still overrides a caller-supplied stop/size, because passthrough is applied first.

# Agent Smith — Portfolio Strategist — QUICK sweep, 2026-08-13 (pre-open, priced off Wed 08-12 close)

Policy is CONFIRMED — no bootstrap needed; this drift analysis is live, not provisional.

## 1. THE MSFT JUDGMENT CALL (ruled)

**Verdict: trim MSFT anyway, standalone — do not hold the book's most extended position hostage to a cluster hole it didn't create and can't fill.**

Facts, typed:
- COMPUTED: RSI14 78.8 (>70 threshold), +24.7% 1m, +24.0pp vs SMH, and signals' own peer-relative vol-normalization puts MSFT at **+3.35σ — the single most extended reading in the book**, against a name-specific threshold of 4.68%.
- COMPUTED: cap_multiple 0.427 — MSFT sits at 43% of its ATR risk cap. This is *not* a risk-budget problem; there is no cap breach to cure here.
- COMPUTED: Compute/Hyperscaler cluster is -10.40pt under floor (the deepest hole in the book, deepened by the META exit).
- The trigger engine's own blocker recommends an intra-cluster rotation instead of a cash trim. I checked it: **there is no laggard inside Compute/Hyperscaler**. MSFT +24.0pp, AMZN +8.28pp, ORCL +16.74pp relative strength — all three are flagged "stretched" in the de-risk queue (stretch_score 100.0 / 34.5 / 69.7 respectively). The suggested remedy has no valid target this run.

Reasoning: the trigger is explicitly `over_cap_independent: true` — the entire point of `overbought_distribution` is that booking profit on a name that ran does not need a cap breach or a same-cluster buyer to be valid. The blocker text itself concedes this ("the stretch reason stands on its own") — it just doesn't want the cluster cited as *support*, which I'm not doing. Holding the most overbought, highest-σ position in the entire book specifically *because* selling it would deepen an already-existing structural hole gets the causality backwards: that hole is a capital-allocation problem to be solved with fresh capital (policy's own $1,000/month rule already directs new contributions to the cluster furthest below target — Compute/Hyperscaler now qualifies), not a reason to let an unrealised gain round-trip on a mean-reversion.

**Action: TRIM MSFT ~$370 at $492.43 (Wed close), standalone (pair_id dropped — R3-MSFT-META-CONDITIONAL is dead, META is gone and there is no live substitute leg).** Proceeds sit in cash — cash is at 9.999%, mid-band [5,15], so this does not force a same-day redeployment, and forcing one into a cluster with no live buy candidate would just repeat the error the blocker was trying to prevent. Flag explicitly for the next $1,000 monthly contribution: direct it at Compute/Hyperscaler per the existing policy rule, structurally refilling the hole regardless of whether this trim executes.

## 2. NBIS — ONE integrated recommendation

Three converging signals on the same position, collapsed into one action pair instead of three separate ideas:

- COMPUTED: cap_multiple 1.846x (largest ATR-cap excess in the book after SKHY), headroom deficit -$712.55.
- SHADOW `scale_out_ladder` (not yet hit-rate validated): up +32.2% vs $196.01 basis, rung 1 of 2 (+25%) triggered, suggested slice $518.40.
- SHADOW `profit_ratchet` (not yet hit-rate validated): stop should move $192.74 → $196.01. Note the ratchet has mostly **self-executed** already — the ATR-implied stop trailed up with price, so only $19.61 of gain is actually at risk now (down from the original ask), not a fresh problem.

Both live-direction signals point TRIM, and the cap-cure need ($712.55) is larger than the ladder's own suggested rung ($518.40) — so I size to the larger number, which clears the cap breach almost completely *and* more than satisfies the tripped scale-out rung in one action, rather than trimming twice.

**Action A: TRIM NBIS ~$710 at $259.20 (Wed close).** Labeled `scale_out_ladder`, shadow trigger, not yet hit-rate validated — but it independently coincides with the computed cap breach, which is what earns it a sized proposal per the shadow-surfacing rule. Post-trim value ≈$845, essentially at cap.
**Action B: raise the NBIS stop to $196.01 (breakeven+), zero cash cost, ratchet only — never tightened, per standing instruction.** This applies regardless of whether Action A executes; on the remaining ~$845 of exposure it now protects nearly all of the unrealised gain rather than the $19.61 sliver currently at risk to a retracement below $192.74.

Supersedes P-080 (folded into Action B above, same $196.01 level, now explicitly tied to the trim).

## 3. DRAM / SKHY — breakout vs. ATR-cap tension (resolved)

Both are genuinely at 52-week highs (BREAKOUT, live price ≥ 52wk_high independently of the range-position math) **and** well over their own ATR risk caps — DRAM 1.479x, SKHY 1.964x (worst single overage in the book). Data caveat on both: 52wk_low is recorded as 0 (short listing history, not a real low), which pins the "position in range" statistic at exactly 1.0 — that stat is unusable, but it doesn't affect the breakout call itself, which rests on live price vs. 52wk_high, an independent and clean number.

**Resolution: risk-cap discipline governs sizing, momentum governs how much of the position survives the trim.** The stop-loss framework is a constant-dollar-risk control, not a trend call — it exists precisely so a name doesn't get sized past the point where a normal pullback produces an outsized loss, and that logic doesn't care whether the name is breaking out. But neither name should be cap-cured to zero excess in one shot while momentum (and catalyst's read that the Korea memory rally is a live, mechanical, still-running macro tailwind — not exhausted) argues for leaving meaningful exposure on:

- **SKHY (P-070, keep, 2nd ask, $675 at $154.41 today vs $141.65 when last priced — up further since):** already sized to 81% cure, not full — correctly partial. No change, reaffirmed.
- **DRAM (new): TRIM ~$500 at $54.80 (Wed close), against a full cure need of $532.60 (~94% cure) — partial, same logic as SKHY.** DRAM's abs return is actually -7.27% over the past month with relative strength -8.0pp vs SMH despite the fresh 52wk high — the breakout is a recent, sharp move off a weak base, not sustained leadership, which argues for trimming a bit closer to the cap than SKHY's looser 81%, without eliminating the position.

Both trims are pure risk-cap cures with no profit-take or rotation trigger behind them (RSI on DRAM is 53.9, neutral; SKHY isn't even in the RSI-scored set) — flagged honestly as ATR-driven, kept deliberately secondary to the profit/rotation-led MSFT and NBIS actions above, not the anchor of this run's list.

## 4. New / updated sized proposals

All prices Wed 2026-08-12 close. Total buy dollars this run ($388.88 QCOM + $180.51 GEV + $600 VRT + $450 CEG = $1,619.39) stay well inside total sell-leg proceeds generated this run and standing ($371 MSFT + $710 NBIS + $500 DRAM + $675 SKHY + $550 NVDA + $181 BX ≈ $2,987) — deployable cash is $0, nothing here draws on the wallet.

1. **TRIM MSFT ~$370 at $492.43** — serves ask (3) protect gains. `trigger_type: overbought_distribution` (live). Standalone, no rotation target exists this run (see §1). evidence: computed=2 (RSI14 78.8, +3.35σ peer-relative), unverified=1 (thesis WATCH, carried forward, not reverified this sweep), verified=0.

2. **TRIM NBIS ~$710 at $259.20** — serves asks (2)+(3), integrated cap-cure + profit-take (see §2). `trigger_type: scale_out_ladder` (shadow, not yet hit-rate validated — coincides with a computed cap breach). evidence: computed=2 (cap_multiple 1.846x, +32.2% gain/rung math), unverified=1 (positive coverage tone, not re-verified this sweep), verified=0.

3. **RAISE STOP NBIS to $196.01, $0 cost** — serves ask (3). `trigger_type: profit_ratchet` (shadow). Ratchet only, never tightened. evidence: computed=2 (gain_pct 32.24%, stop-distance calc), unverified=0, verified=0. Supersedes P-080.

4. **TRIM DRAM ~$500 at $54.80** — risk-cap cure, secondary priority (see §3). `trigger_type: null` (not on any of the five live/shadow lists — pure ATR cure, no profit or rotation trigger). evidence: computed=3 (cap_multiple 1.479x, rel_strength -8.0pp/abs -7.27% laggard read, live breakout vs 52wk_high), unverified=1 (thesis WATCH carried forward), verified=0.

5. **RE-SIZE VRT re-entry to ~$600 at $296.67** (was $850 at $281.81 — position has already run +5.3% since last priced) — serves ask (2), fills the second-deepest cluster hole (AI Power/Cooling -10.16pt). Sized down from the original ask specifically because chasing a name that already moved 5.3% since the last price check deserves a smaller bite, not the same dollar commitment. `trigger_type: null` (cluster-floor + watchlist target-gap driven, not one of the five trigger lists). evidence: computed=2 (cluster drift -10.16pt, +5.3% price move since last pricing), unverified=1 (stale target-gap figure from prior watchlist run, not reverified this sweep), verified=0.

6. **BUY CEG ~$450 at $278.68** — serves ask (2), second Power/Cooling candidate alongside GEV/VRT: signals flags TARGET GAP + REVERSAL-BUY WATCH, $2,467.56 of headroom (deepest room of any name in the cluster). Sized modestly — CEG carries an unresolved leverage-concern thesis WATCH flag from a prior run (open, not re-investigated this sweep), which tempers conviction without vetoing it (thesis is WATCH, not BROKEN, and the countervailing evidence is a pending item, not a confirmed negative). `trigger_type: null` (signal-conviction / target-gap driven, not one of the five compute_triggers.json lists — left unset rather than mislabeled). evidence: computed=3 (cluster drift -10.16pt, target-gap ratio, $2,467.56 headroom), unverified=1 (leverage-concern caveat + REVERSAL-BUY WATCH narrative), verified=0.

None of the six rests solely on unverified claims — no evidence-gate flag this run.

## 5. Keep / re-size / dismiss — the ten open proposals

- **P-072 Trim NVDA $550 (HIGH/8, 3rd ask) — KEEP, unchanged.** Genuine cap+cluster breach (1.21x cap, AI Semis/Fabs +8.45pt over), still funds the QCOM buy leg (P-077).
- **P-075 Trim BX $181 (HIGH/5, R1 sell leg) — KEEP, unchanged.** Live `overbought_distribution` (RSI 71.1, +16.5% 1m), still funds GEV buy leg (P-076).
- **P-078 Trim MSFT $371 — KEEP, RE-LABELED.** Pair_id `R3-MSFT-META-CONDITIONAL` dropped (dead — META fully exited); now standalone. See §1 and new proposal #1 above (same size, ~$370 vs $371, immaterial rounding).
- **P-070 Trim SKHY $675 (MED/3, 2nd ask) — KEEP, unchanged.** See §3 — already correctly partial (81% cure), consistent with the breakout tension resolution.
- **P-069 Trim MU $600 (MED/2) — DISMISS.** Pure ATR-cap trim with the proposal's own rationale conceding "thesis WATCH cited as color only, thesis itself says no_action" — no RSI overbought read (51.7, neutral), no cluster breach, no breakout, no rotation setup. This is exactly the ATR-dominated pattern the standing brief asked this desk to stop leading with, and this run has five stronger, profit/rotation/cap-justified trims already in flight without it. Dismissed, not deferred.
- **P-073 Re-enter VRT $850 — RE-SIZED to ~$600 at $296.67.** See proposal #5 above — price moved +5.3% since last priced ($281.81 → $296.67), still valid but sized down to reflect the chase.
- **P-076 Buy GEV $181 (R1 buy leg) — KEEP, unchanged.** Funded by BX sell leg, still the deepest-underweight-adjacent, hasn't-run candidate in Power/Cooling.
- **P-077 Buy QCOM $389 (R2 buy leg) — KEEP, unchanged.** Funded by NVDA sell leg; signals recovery this run adds OVERSOLD BOUNCE + TARGET GAP on top of the shadow laggard_rotation read — strengthens the case, still shadow-scored (0 priority contribution by design) but now with more supporting computed color.
- **P-080 Raise stop NBIS — SUPERSEDED** by proposal #3 above (same $196.01 level, now explicitly tied to the NBIS trim as one integrated recommendation rather than a freestanding ask).
- **P-081 Raise stop MRVL $188.30 — KEEP, unchanged.** $99 of gain at risk to a retracement below the current $174.19 stop, zero cash cost, ratchet only.

## 6. Risk-off status

**risk_off_status: NORMAL.** Drawdown -3.704% vs. policy thresholds of -15% (warn) / -25% (risk-off) — not close to either. This is a routine sweep, not a defensive one.

Separately — and this is not the same gauge — **aggregate open ATR risk is 12.264% against a 10% cap, a real breach**, driven by 8 of 31 names running hot on their individual volatility-scaled position caps (SKHY 1.96x, NBIS 1.85x, MU 1.58x, DRAM 1.48x, MRVL 1.39x, NVDA 1.21x, TSM 1.07x, TER 1.02x). The trims above (NVDA, SKHY, NBIS, DRAM — collectively curing roughly 90%+ of their individual excesses) work directly toward closing this gap; MRVL and MU are not sized for a fresh trim this run (MRVL gets a stop-raise only; MU is dismissed, see §5) and remain open cap excess to watch next sweep. TSM/TER overages are marginal (1.07x/1.02x) and not flagged for action.

Sentiment: 78.4, extreme_greed, action_hint = profit-booking on overweight/breach names — consistent with today's list leading on trims (MSFT, NBIS, DRAM, SKHY, NVDA) rather than fresh net deployment; the two buys (QCOM, GEV) and the two new cluster-fill ideas (VRT, CEG) are all funded from sell proceeds, not new cash.

## 7. Hit-rate readout

30d-validated (n≥3 only):
- **TARGET GAP: 3/6 worked (50.0%)** — mediocre, not yet below the <40%-over-n≥5 de-emphasize bar, but worth watching next run if it drifts lower.
- **MOMENTUM+VOLUME: 3/5 worked (60.0%)** — holding up.
- OVERSOLD BOUNCE: n=1, skipped (below the n≥3 floor for a 30d read).

7d-interim (never validated, shown for trend only — do not action on these alone): MOMENTUM+VOLUME 60.0% (n=15), OVERSOLD BOUNCE 100.0% (n=5), TARGET GAP 68.8% (n=16). No de-emphasize recommendation this run.

## Data quality notes
- DRAM/SKHY: 52wk_low recorded as 0 (short listing history) inflates their position-in-range stat to exactly 1.0 — not a real number, ignored. The BREAKOUT calls themselves stand on live price ≥ 52wk_high, which is independent and clean.
- NBIS, SNDK: analyst_forecast empty this run — TARGET GAP not computable for either.
- CIEN +11.49% (G61): signals still lists this as unresolved, but catalyst (same run) sourced and closed it — Lumentum FQ4 beat (rev +109% YoY) reading through the AI-optics complex. Treating G61 as resolved per catalyst's sourced finding.
- CEG: leverage-concern thesis WATCH flag remains open/pending from a prior run, not re-investigated this sweep — sizing the CEG buy modestly for this reason (see proposal #6).
- lots.json is populated (42 tickers, backfilled from INDmoney confirmation emails) — checked MSFT/BX/NBIS/MRVL directly: all lots dated within the last ~2-5 weeks (book inception ~2025-04-30, so nothing is within 6 months of the 24-month LTCG boundary yet). No LTCG-deferral proposals this run; this will start mattering from ~2027-Q2 onward.
- Budget: 8 tool calls used (file reads only, no web/API calls needed — all required numbers were in the run-dir compute files, holdings.json, lots.json, and policy.json). No truncation.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"TRIM","ticker":"MSFT","size_usd":370,"price_at_proposal":492.43,"rationale":"RSI14 78.8, +3.35sigma peer-relative (most extended in book), +24.7% 1m -- protect real unrealised gain. Standalone: no intra-cluster laggard exists to rotate into (checked MSFT/AMZN/ORCL, all stretched); cluster tension noted, not cited as support for the trim, per G56.","trigger_type":"overbought_distribution","trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"NBIS","size_usd":710,"price_at_proposal":259.20,"rationale":"Integrated recommendation: 1.846x ATR cap (largest excess after SKHY, -$712.55 headroom deficit) sized to fully cure the cap AND clears scale_out_ladder rung 1 ($518.40 suggested) in one action instead of two.","trigger_type":"scale_out_ladder","trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"STOP_RAISE","ticker":"NBIS","size_usd":0,"price_at_proposal":259.20,"rationale":"Raise stop 192.74 -> 196.01 (breakeven+). Ratchet only, never tightened. Most of this ratchet already self-executed via the ATR trail -- only $19.61 of gain remains at risk pre-trim, effectively none post-trim. Supersedes P-080.","trigger_type":"profit_ratchet","trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"TRIM","ticker":"DRAM","size_usd":500,"price_at_proposal":54.80,"rationale":"1.479x ATR cap, laggard on 1m relative strength (-8.0pp vs SMH) despite a fresh 52wk high off a weak base. Partial cure (94%) resolves breakout-vs-cap tension without fighting the still-running Korea memory tailwind. Pure risk-cap trim, no profit/rotation trigger -- deliberately secondary this run.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"action":"BUY","ticker":"VRT","size_usd":600,"price_at_proposal":296.67,"rationale":"Re-entry, resized down from $850 -- price ran +5.3% since last priced ($281.81->$296.67). Fills AI Power/Cooling -10.16pt underweight, second-deepest hole in the book. Funded from trim proceeds, not the wallet.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"BUY","ticker":"CEG","size_usd":450,"price_at_proposal":278.68,"rationale":"TARGET GAP + REVERSAL-BUY WATCH, $2,467.56 headroom (most room of any name in the cluster), fills the same -10.16pt Power/Cooling hole as VRT/GEV. Sized modestly given an open, unresolved leverage-concern thesis WATCH flag from a prior run.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1}}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["DRAM/SKHY 52wk_low=0 (data gap) inflates range-position stat to 1.0 -- BREAKOUT call unaffected, rests on live>=52wk_high independently","NBIS/SNDK analyst_forecast empty -- TARGET GAP not computable for either this run","CIEN G61 resolved per catalyst (Lumentum FQ4 beat read-through) -- signals' 'still unresolved' flag is stale within this same run","CEG leverage-concern thesis WATCH open/pending from a prior run, not re-investigated this sweep -- CEG buy sized modestly for this reason","lots.json populated (42 tickers) -- checked MSFT/BX/NBIS/MRVL, all lots <5 weeks old, none within 6 months of the 24-month LTCG boundary; not a live constraint this run","proposal_outcomes/scorecard intentionally empty -- this is a quick sweep, not deep-mode or monthly; task 6 is deep/monthly-gated"]}
```

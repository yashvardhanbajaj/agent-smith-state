# Portfolio Strategist — 2026-08-25 pre-market (deep review)

Policy is confirmed (no bootstrap needed). Book is $41,309.73 total, 8.47% cash (normal band), deployable-for-ideas cash is thin at **$1,433.29** after last night's 11-trade deployment — clamping binds hard this run and is called out on every proposal it touches.

## Sized proposals (5 decisions, 7 legs)

**1. CLUSTER ROTATION — AI Semis/Fabs: SELL AMD / BUY NVDA** (`pair_id: cluster_rotation-AMD-NVDA`)
- SELL AMD $279.80 @ market. AMD is the cluster laggard (-11.3pp rel. strength), thesis **watch**, and its evidence file itself notes the 2026-08-24 re-entry "contradicts the strategist's explicit 2026-08-12 decision not to re-add" (ruled HOLD/no-further-adds 2026-08-15) — a verified, secondary-sourced tension on top of the computed laggard signal.
- BUY NVDA $279.80 @ market, stop not separately computed for this leg (position already carries its own ATR stop). NVDA is the cluster's relative-strength leader (+7.4pp), thesis strengthening (secondary verified).
- Note: AI Semis/Fabs is actually *underweight* target (23.65% vs 30%, drift -6.35pt) — this is a within-cluster reallocation, not a cluster trim; total cluster exposure is unchanged.
- **Binary-risk flag: NVDA reports tomorrow (8/26), 6.06% implied move.** Sizing this into an earnings print is a deliberate near-term risk — the trigger fired on relative strength/thesis, not on earnings timing, and the amount is small ($279.80) relative to the print's implied move.
- `evidence_quality`: verified 2, computed 2, unverified 0.

**2. TRIM AVGO $289.19** (20% trim, `catalyst_threat`, cap-independent)
- @ $361.49. Broadcom's AI-financing SPV ($60-70bn current tranche, stress-tested to a $370bn-by-2029 ceiling) is a structural overhang smith-catalyst has now carried three runs (08-17/08-24/08-25). AVGO now carries this exposure **alone** — BX's exit on 08-17 removed the offsetting BX-side upside, then BX's 08-24 re-entry brought the SPV exposure back into the book on both names simultaneously (see proposal 3).
- Note on AVGO's own binary risk: reports 9/2, 8.98% implied move, and per smith-earnings both AVGO and CIEN show a "beat-and-fall" pattern (4 straight beats, last two prints closed ~-13% same-day on sector expectations resets). Trimming ahead of that print is consistent with, not contrary to, this trigger.
- Thesis tag on AVGO's evidence is **unverified** (single-source SPV claim, not yet cross-confirmed) — the trigger itself is computed, which satisfies the evidence gate, but treat the underlying claim as advisory, not proven.
- Per smith-tax: this trim realizes a **loss** on a cost-basis view, not profit — do not describe it as profit-taking; it is a structural-catalyst trim.
- `evidence_quality`: verified 0, computed 1, unverified 1. **review_flag**: rests on an unverified underlying claim; computed trigger is the load-bearing evidence.

**3. TRIM BX $285.64** (20% trim, `catalyst_threat`, cap-independent)
- @ $142.82. Same SPV exposure as AVGO (BX was GP on the same Anthropic-compute financing vehicle); thesis is **watch**, evidence **secondary-verified** (BofA downgrade via 247wallst.com, corroborated by BX's own "Project Eclipse" execution-friction news).
- Per smith-tax: also a **loss** realization, not profit-taking — describe accordingly, not as "real profit to book."
- Note: I did not additionally propose the compute layer's `profit_rotation-BX-AMAT` pair (sell BX $428.46 / buy AMAT $328.47) to avoid two separate sell orders against the same $1,428 BX position in one dispatch — the catalyst_threat trim is the cleaner, better-evidenced sell rationale (secondary-verified vs. the rotation pair's generic "stretched" framing). If BX is trimmed here, the AMAT buy leg from that pair is deferred to a future run once fresh cash is available.
- `evidence_quality`: verified 1, computed 1, unverified 0.

**4. PROFIT ROTATION — SELL MSFT / BUY CLS** (`pair_id: profit_rotation-MSFT-CLS`)
- SELL MSFT $437.92 @ market. MSFT is in the stretched cohort (ahead of SMH, up on the month), thesis **watch**, evidence **unverified** — the sell rationale leans on the computed stretch/drift signal, not a strong qualitative claim. MSFT also just dropped out of TARGET GAP (14.4%, below the 15% threshold) while remaining PEER LEADER — momentum is stretched but not broken.
- BUY CLS $424.65 @ ~$297.50 (self-funded by the MSFT sale, does not draw on the thin $1,433 cash pool). CLS is a fresh laggard (-3.7pp rel. strength) with a strengthening thesis (secondary verified) — "yet to rally" per the compute layer. `size_wanted_usd` = `suggested_size_usd` = $424.65, not clamped.
- `evidence_quality`: verified 1 (CLS), computed 2 (trigger + derisk stretched list), unverified 1 (MSFT thesis).

**5. BUY AMZN $1,186.73** (`conviction_average`, medium conviction 51.9)
- @ $262.76, blended entry $266.82, stop $246.52 (blended entry clears the stop — trigger did not need to refuse the add). Thesis strengthening (secondary verified), PEER LEADER polarity, +22.5% vs analyst target. `size_wanted_usd` = `suggested_size_usd` = $1,186.73, **not clamped**.
- **Cash flag: this single idea consumes ~83% of the $1,433.29 deployable-for-ideas pool**, leaving roughly $246 for anything else new-cash this run. That is why GLW ($281.11), TER ($286.23), and WDC ($196.76, itself already ATR-clamped from $242.39) — all live `conviction_average` BUY candidates — are **not** separately proposed today: there is not enough uncommitted cash to size them meaningfully alongside AMZN without manufacturing sub-$100 tickets. They remain live triggers for the next run if AMZN is not filled or cash frees up.
- `evidence_quality`: verified 1, computed 1, unverified 0.

**Excluded by design:** `profit_rotation-CIEN-QCOM` (sell CIEN $334.85 / buy QCOM $334.85) was in the compute output but is deliberately not proposed — CIEN's own thesis evidence is tagged **unverified**, CIEN is already -6.02% heading into a 9/3 print with the same "beat-and-fall" history as AVGO (13.3% implied move), and per this morning's dispatch its TARGET GAP signal should be treated with caution, not acted on. `profit_rotation-FLTW-META` (sell FLTW $297.09 / buy META $297.09) is also excluded this run for cash-priority reasons (AMZN and the MSFT/CLS pair already claim the available slots) — it stays live and unclamped for next dispatch. `entry_setup` candidates VST and ORCL (oversold_bounce, 38.7%/42.2% upside) have no live price/sizing this run (blocker: no fetch) — flagged in data_quality rather than sized.

## Risk-off check (Task 3)

`risk_off_status` = **normal**. Drawdown is -7.94% off the $44,873 peak — 0.06pt below the 8% warn threshold, closer than usual but not triggered; no defensive posture required, no forced trims, no target-cash escalation. Cash (8.47%) is back inside its normal 5-15% band after the stop-out five sessions ago. Sentiment band is **greed** (score 66.1) — supportive of the selective profit/structural trims above (AVGO, BX, MSFT) but not "extreme greed," so this is not a mandated defensive lead; drift and thesis continue to drive sizing as usual. Aggregate open risk (11.95% of book) is modestly above the 10% derisk-queue cap — worth monitoring, not yet an action trigger on its own.

## Summary (for the user)

Overnight, 11 real trades deployed most of the book's cash — only ~$1,433 remains for new ideas, so today's proposals lean on self-funding pairs rather than fresh buys. Two trims (AVGO, BX) address the same structural SPV financing overhang that now sits on both names since BX's re-entry — both realize tax losses, not profits, so treat them as risk management, not profit-taking. One cluster swap moves AMD money to NVDA, the AI Semis/Fabs relative-strength leader, ahead of NVDA's earnings tomorrow — a deliberate, small-size bet into that binary. One rotation pair sells stretched MSFT into laggard-but-strengthening CLS, fully self-funded. The single new-cash idea, AMZN, uses most of the remaining deployable pool at full un-clamped size, which is why three other live conviction candidates (GLW, TER, WDC) sit out this round rather than get sized to token amounts. CIEN is deliberately excluded from any rotation given its unverified thesis and the AVGO/CIEN "beat-and-fall" earnings pattern heading into its 9/3 print. Risk-off is not triggered, but drawdown (-7.94%) is close enough to the 8% warn line to watch closely into next week's earnings cluster.

```json
{"policy_draft": null,
 "proposals": [
   {"action": "SELL", "ticker": "AMD", "size_usd": 279.80, "price_at_proposal": null,
    "rationale": "Cluster laggard in AI Semis/Fabs (-11.3pp rel. strength), thesis watch; re-entry itself flagged as contradicting the strategist's 2026-08-12 no-re-add ruling. Rotate to cluster's relative-strength leader.",
    "trigger_type": "cluster_rotation", "trigger_bucket": "live", "pair_id": "cluster_rotation-AMD-NVDA", "pair_role": "sell",
    "size_wanted_usd": 279.80, "clamped_by": null, "stop_price_usd": null, "exited_on": null,
    "evidence_quality": {"verified": 2, "computed": 2, "unverified": 0}},
   {"action": "BUY", "ticker": "NVDA", "size_usd": 279.80, "price_at_proposal": null,
    "rationale": "Cluster's relative-strength leader (+7.4pp), thesis strengthening (secondary verified). Small deliberate size into NVDA's 8/26 earnings (6.06% implied move) -- trigger fired on relative strength, not timed to the print.",
    "trigger_type": "cluster_rotation", "trigger_bucket": "live", "pair_id": "cluster_rotation-AMD-NVDA", "pair_role": "buy",
    "size_wanted_usd": 279.80, "clamped_by": null, "stop_price_usd": null, "exited_on": null,
    "evidence_quality": {"verified": 2, "computed": 2, "unverified": 0}},
   {"action": "TRIM", "ticker": "AVGO", "size_usd": 289.19, "price_at_proposal": 361.49,
    "rationale": "Structural SPV-financing overhang ($370bn 2029 stress ceiling), carried alone by AVGO since BX's exit/re-entry cycle. Cap-independent per catalyst_threat design. Realizes a cost-basis LOSS, not profit -- do not describe as profit-taking. AVGO also reports 9/2 with a beat-and-fall history; trim is consistent with, not contrary to, that risk.",
    "trigger_type": "catalyst_threat", "trigger_bucket": "live", "pair_id": null, "pair_role": null,
    "size_wanted_usd": 289.19, "clamped_by": null, "stop_price_usd": null, "exited_on": null,
    "evidence_quality": {"verified": 0, "computed": 1, "unverified": 1}},
   {"action": "TRIM", "ticker": "BX", "size_usd": 285.64, "price_at_proposal": 142.82,
    "rationale": "Same SPV exposure as AVGO, thesis watch, secondary-verified BofA downgrade + own deal friction. Realizes a cost-basis LOSS, not profit. Chosen over the compute layer's profit_rotation-BX-AMAT pair to avoid two simultaneous sell orders on the same small position -- AMAT buy leg deferred to a future run.",
    "trigger_type": "catalyst_threat", "trigger_bucket": "live", "pair_id": null, "pair_role": null,
    "size_wanted_usd": 285.64, "clamped_by": null, "stop_price_usd": null, "exited_on": null,
    "evidence_quality": {"verified": 1, "computed": 1, "unverified": 0}},
   {"action": "SELL", "ticker": "MSFT", "size_usd": 437.92, "price_at_proposal": null,
    "rationale": "Stretched (ahead of SMH, up on month), thesis watch/unverified; recently dropped out of TARGET GAP while remaining PEER LEADER. Self-funds the CLS buy leg.",
    "trigger_type": "profit_rotation", "trigger_bucket": "live", "pair_id": "profit_rotation-MSFT-CLS", "pair_role": "sell",
    "size_wanted_usd": 437.92, "clamped_by": null, "stop_price_usd": null, "exited_on": null,
    "evidence_quality": {"verified": 0, "computed": 2, "unverified": 1}},
   {"action": "BUY", "ticker": "CLS", "size_usd": 424.65, "price_at_proposal": 297.5001,
    "rationale": "Laggard (-3.7pp) with strengthening thesis (secondary verified) -- yet to rally. Funded by MSFT sale proceeds, not new cash.",
    "trigger_type": "profit_rotation", "trigger_bucket": "live", "pair_id": "profit_rotation-MSFT-CLS", "pair_role": "buy",
    "size_wanted_usd": 424.65, "clamped_by": null, "stop_price_usd": 254.9576, "exited_on": null,
    "evidence_quality": {"verified": 1, "computed": 2, "unverified": 1}},
   {"action": "BUY", "ticker": "AMZN", "size_usd": 1186.73, "price_at_proposal": 262.76,
    "rationale": "Conviction-average add, medium tier (score 51.9), thesis strengthening (secondary verified), PEER LEADER, +22.5% vs analyst target. Blended entry $266.82 clears stop $246.52 -- add not refused. Consumes ~83% of the $1,433.29 deployable-for-ideas cash pool this run, crowding out GLW/TER/WDC conviction_average candidates until more cash frees up.",
    "trigger_type": "conviction_average", "trigger_bucket": "live", "pair_id": null, "pair_role": null,
    "size_wanted_usd": 1186.73, "clamped_by": null, "stop_price_usd": 246.5214, "exited_on": null,
    "evidence_quality": {"verified": 1, "computed": 1, "unverified": 0}}
 ],
 "scorecard_read": null,
 "deemphasize_buckets": [],
 "data_quality": [
   "entry_setup candidates VST (38.7% upside, RSI14=3) and ORCL (42.2% upside, RSI14=12) are live triggers with no live price/ATR fetched this run (blocker noted in compute_triggers.json) -- not sized, need a price fetch before proposing.",
   "profit_rotation-CIEN-QCOM and profit_rotation-FLTW-META are live in compute_triggers.json but deliberately not proposed this run -- CIEN on unverified-thesis + beat-and-fall earnings-pattern grounds (9/3 print), FLTW/META on cash-priority grounds. Both remain live for next dispatch.",
   "conviction_average candidates GLW ($281.11), TER ($286.23), and WDC ($196.76, already ATR-clamped from $242.39 wanted) are live but unsized this run purely on cash-priority grounds after AMZN and the MSFT/CLS pair -- not evidentiary exclusions.",
   "rsi14 and rel_strength_1m caches are 13 days stale (compute_triggers.json) -- oversold_reversion, overbought_distribution, and laggard_rotation are structurally suppressed this run, not evaluated as zero-signal.",
   "AVGO's catalyst_threat evidence is tagged unverified at the source level; the trigger firing is computed and satisfies the evidence gate, but the underlying SPV-stress claim itself has not been independently cross-confirmed beyond the original 247wallst.com report."
 ]}
```

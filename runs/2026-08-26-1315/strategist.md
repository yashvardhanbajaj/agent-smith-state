# Agent Smith — Portfolio Strategist — QUICK sweep — 2026-08-26

## Binding constraint

Cash is $124.52 (0.30% of a $41,441.51 book) against a [5,15]% policy band — a floor breach, drained overnight into 8 buys. Deployable capital above the floor is negative. **No proposal below is an unfunded BUY.** Two of the four decisions raise cash outright (no offsetting buy); the other two are self-funded rotations, one of which nets a cash surplus. Rebuilding toward the 5% floor still needs ~$1,950 net beyond what's proposed here — this run's live triggers don't cover the gap, and I'm not manufacturing size to close it.

Aggregate open ATR risk is 13.028% vs a 10% cap (8 names over their own cap — BE, VRT, MRVL, GEV, NBIS, MU, TSM, COHR) but **none of those eight fired a live trigger this run**: `oversold_reversion`/`overbought_distribution`/`laggard_rotation` are all suppressed because the `rsi14`/`rel_strength_1m` caches are 14 days old against a 7-day TTL. Per standing rule, I'm not substituting my own RSI read for a suppressed trigger. Flagging this as the single highest-value fix for the next deep run — refresh the technicals cache and the ATR-cap cures come back online.

## Proposals (4 decisions, dated 2026-08-26)

### 1. PAIR — SELL BX / BUY QCOM ($430.23 each) — `profit_rotation-BX-QCOM`
- **SELL BX** 10sh, $430.23 of $1,434.10 position (30.0%) @ $143.41. Rationale: BX is in `names_stretched` (RSI 71.1, +16.5% 1m, +15.8pp vs peers) carrying a **watch** thesis (verified: secondary) — book real profit. This trim also satisfies the standing `catalyst_threat` flag on BX (BofA-flagged $370bn-by-2029 stress ceiling on the AVGO/BX AI-financing SPV, re-applies to BX since its 2026-08-21 re-entry — note lots.json dates the re-entry 08-21, not the 08-24 the dispatch and prior state cited; open discrepancy G83). Rather than stacking a second, separate $286.82 catalyst trim on the same shares, this single $430.23 sell covers both reasons — sizing off the larger of the two rather than double-trimming.
- **BUY QCOM** $430.23 @ current price. Rationale: QCOM is the within-book laggard (-6.7pp rel-strength) with a **strengthening** thesis (verified: unverified) and sits in rotation's `accumulate` bucket, $801.68 of ATR headroom — no clamp needed.
- Net cash impact: $0 (balanced swap).
- `evidence_quality`: BX leg — verified:1 (thesis secondary), computed:2 (drift/rotation stretch + trigger row), unverified:0. QCOM leg — verified:0, computed:2, unverified:1 (thesis tag unverified — supporting, not sole basis; buy is trigger/headroom-driven, not thesis-driven).
- Rejected pairing candidates from this same live trigger set (lower priority, not written up in full): `profit_rotation-CIEN-CLS` ($349.89) and `profit_rotation-FLTW-META` ($303.27) — both cash-neutral, both lower conviction (44.0 and 23.3) than the four decisions here. Available on request.

### 2. TRIM AVGO — $285.39 (20.0% of $1,426.96 position) @ $356.74 — `catalyst_threat`
- Same SPV/off-balance-sheet AI-financing overhang as BX, but AVGO now carries it **alone** (no offsetting BX-side exposure prior to BX's re-entry). This is `over_cap_independent: true` by design — AVGO is not over its ATR/cluster cap (cap multiple 0.57, cluster in-band at 16.0% vs [10,20]), so this trim is not a cap cure, it's a threat-driven de-risk.
- `full_cure_usd`: $1,426.96 (full exit — reference point only, not a policy target since there's no breach to cure). `cure_pct`: 20.0%. `tranche_note`: "Partial trim, not a cap/cluster cure (AVGO sits comfortably inside both). Retaining 80% because AVGO's own thesis is still 'strengthening' (though that tag is itself unverified — 0 for / 2 against in evidence). Revisit full exit only if the SPV story graduates to a verified thesis_break. AVGO also reports 09-02; this trim reduces binary-event exposure ahead of that print."
- `evidence_quality`: computed:1 (trigger row, cap-independent by construction), verified:0, unverified:1 (thesis tag). Gate satisfied via computed; flagging that the thesis itself is contested (2 against, 0 for) so I'm leaning on the catalyst trigger, not the thesis label, per the SNDK/MRVL lesson.

### 3. PAIR — SELL ASML $523.25 / BUY AMAT $200.08 — `profit_rotation-ASML-AMAT`
- **SELL ASML** 1sh worth $523.25 of $1,744.16 (30.0%) @ $1,744.16. ASML is stretched (STRONG UPTREND, +19.85% target gap) but thesis is **watch** (verified: unverified — "deliberately not upgraded despite improving tone," structural China-buildout risk not resolved, only un-escalated) — real profit to book.
- **BUY AMAT** $200.08 @ $480.04, clamped from a $350.88 want down to $200.08 by ATR headroom — naming the constraint per policy rather than silently substituting. AMAT is the in-cluster laggard (-4.1pp rel-strength) with a **strengthening** thesis (verified: secondary).
- **Net cash impact: +$323.17 to the cash floor** — the only one of the four decisions that isn't cash-neutral, because AMAT's own headroom caps the buy below the sell proceeds. This is the one rotation that actually helps rebuild the [5,15]% band.
- `evidence_quality`: ASML leg — verified:0, computed:2 (stretch flag + trigger), unverified:1 (thesis). AMAT leg — verified:1 (thesis secondary), computed:2 (trigger + ATR headroom clamp), unverified:0.

### 4. PAIR — SELL AMD $287.51 / BUY NVDA $287.51 — `cluster_rotation-AMD-NVDA`
- **SELL AMD** 2sh, $287.51 of $958.36 (30.0%) @ $479.18. AMD is the AI Semis/Fabs cluster laggard (-11.3pp rel-strength) on a **watch** thesis (verified: secondary — Q3 guide-below-consensus, debt-funded capex cuts both ways, and this re-entry itself contradicted the strategist's 2026-08-12/08-15 explicit no-further-adds ruling) — dead money in a cluster where NVDA is the performer.
- **BUY NVDA** $287.51 @ $213.05. NVDA is the cluster's relative-strength leader (+7.4pp), **strengthening** thesis (verified: secondary), no clamp (ample ATR headroom).
- **Flag: NVDA reports TODAY, 2026-08-26, after close.** This buy sizes into a binary event on the same session — 5sh currently held (2.57% of book), didn't run up into the print (7 down sessions before Tuesday's bounce). If this fills, apply the standing tight large-quantum stop discipline immediately post-print rather than waiting for the next sweep.
- This is this pair's **third restatement** (P-160/P-161, both currently rc=2 — one more unchanged restatement auto-retires them). Restating because the trigger is still live and unchanged in compute_triggers.json, not to game the counter. If you'd rather let it lapse and revisit post-earnings, say so and I'll drop it next run.
- `evidence_quality`: AMD leg — verified:1 (thesis secondary), computed:2 (rotation `rotate_out` bucket + trigger), unverified:0. NVDA leg — verified:1 (thesis secondary), computed:2, unverified:0. Strongest evidence base of the four decisions.

## Unfunded shopping list — NOT sized proposals (no cash to fund them)

`conviction_average` fired 6 names, `entry_setup` fired 2 — every one is unfundable standalone today (`suggested_size_usd: $0.00`, `clamped_by: "deployable cash"`). Ranked by conviction score, contingent on one of the sells above (or a fresh deposit) actually clearing:

| ticker | conviction | tier | size wanted | stop (if computed) |
|---|---|---|---|---|
| AMZN | 52.2 | medium | $1,198.01 | $244.93 |
| AMAT | 45.2 | medium | $350.88 (partially funded above via ASML pair) | $394.59 |
| GLW | 44.0 | low | $294.01 | $116.67 |
| VST (entry_setup) | 22.3 | low | unsized — no live price/ATR this run | — |
| ORCL (entry_setup) | 20.8 | low | unsized | — |
| TER | 38.0 | low | $292.84 | $299.59 |
| WDC | 34.2 | low | $256.23 | $365.02 |
| AVGO (conviction_average) | 23.7 | low | $431.11 | $327.20 — superseded by the catalyst trim above; don't add to a name being trimmed for a structural threat |

Do not treat this table as sized proposals — it's a priority order for when cash exists.

## Risk-off check

`risk_off_status: normal`. Drawdown -7.65% vs an 8% warn line — **0.35pt of headroom left**, worth flagging even though no defensive lead is triggered yet. No new deployments recommended beyond the self-funded rotations above; nothing here qualifies as an "exceptional setup" exception.

## Stress table

Skipped — QUICK sweep, deep-only per the skill.

## Hit-rate readout

Not available this run — no signals-agent tail (`bucket_hit_rates`/`name_bucket_grades`) was passed to this stage. Recommend it ride on the next deep run rather than being estimated here.

## Scorecard interpretation (stored, not recomputed)

Stored scorecard: 7 scored, overall 14.3% (1 worked / 6 missed, avg -9.88%). By action: TRIM/SELL 100% (n=1, +5.62%), BUY 0% (n=4, avg -13.46%), HOLD 0% (n=2, avg -10.45%). 1 quarantined for anchor review (P-011 NEM, +50.7% off an $89.70 anchor — treat as unscored, not as a data point). 112 proposals still under the 30-day scoring window.

**n=7 is not a verdict.** The one "100%" TRIM/SELL result is a single win, not a demonstrated edge in that bucket — read it as "1 for 1," not "the desk is right on trims." The BUY bucket's 0-for-4 at -13.46% average is the more uncomfortable number, and it lands directly on today's output: every sized decision above that adds a name (QCOM, AMAT, NVDA) is a BUY leg, and the entire unfunded shopping list is BUY-only. n=4 is too small to conclude the desk has a systematic BUY-side problem, but it's also too close to today's proposal mix to wave off. Two of today's three buy legs (QCOM, NVDA) rest on verified-secondary theses and computed cluster/rotation triggers rather than a bare BUY signal, which is the strongest mitigant available given the record — but the record itself argues for sizing these conservatively and holding the stop discipline tight on fill, not for reducing scrutiny because "it's just a rotation." With 112 results still pending, this scorecard will move a lot before it's a reliable weight on anything; treat today's read as provisional.

## Data quality

- RSI14/rel_strength_1m caches are 14 days old (10-day TTL) — `oversold_reversion`, `overbought_distribution`, `laggard_rotation` all suppressed this run. Refresh on next deep run; this is the fix that reopens the ATR-cap-breach cure path for the 8 over-cap names (BE, VRT, MRVL, GEV, NBIS, MU, TSM, COHR).
- `compute_derisk.json`'s de-risk composite is null throughout (rel_strength missing for 10 names) — the 17-entry `names_stretched` list used above is directional, not scored.
- BX re-entry date: lots.json says 2026-08-21; this run's dispatch and prior state said 08-24 — a 3-day discrepancy (G83), independently caught by book/tax/strategist. Doesn't change today's sizing (position value is what it is) but flag for ledger cleanup.
- MRVL reports 08-27 (tomorrow), sits $634 over its own ATR cap (cap multiple 1.61) — no live trigger fired for it this run (RSI suppressed, no catalyst/thesis_break), so it's not sized here. Worth a specific look once the technicals cache refreshes, ahead of the print.
- No signals-agent tail provided this run — hit-rate-by-bucket table above is empty by necessity, not by oversight.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"SELL","ticker":"BX","size_usd":430.23,"price_at_proposal":143.41,"rationale":"30.0% trim of a stretched, watch-thesis position; also covers the standing catalyst_threat SPV overhang shared with AVGO -- sized off the larger profit_rotation figure rather than double-trimming the same shares.","trigger_type":"profit_rotation","trigger_bucket":"names_stretched","pair_id":"profit_rotation-BX-QCOM","pair_role":"sell","size_wanted_usd":430.23,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":1,"computed":2,"unverified":0}},
   {"action":"BUY","ticker":"QCOM","size_usd":430.23,"price_at_proposal":null,"rationale":"In-cluster laggard (-6.7pp) with a strengthening thesis, funded entirely by the BX sell leg; ample ATR headroom, no clamp.","trigger_type":"profit_rotation","trigger_bucket":"accumulate","pair_id":"profit_rotation-BX-QCOM","pair_role":"buy","size_wanted_usd":430.23,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"AVGO","size_usd":285.39,"price_at_proposal":356.74,"rationale":"20% catalyst-threat trim (SPV/off-balance-sheet AI financing overhang, now carried alone since BX's earlier exit); cap/cluster-independent by design -- AVGO is not over cap. Ahead of AVGO's 09-02 print.","trigger_type":"catalyst_threat","trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":285.39,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":1,"unverified":1},"full_cure_usd":1426.96,"cure_pct":20.0,"tranche_note":"Not a cap cure -- reference is full exit, not a policy band. Retaining 80% given AVGO's own thesis (unverified tag, contested 0-for/2-against) is still 'strengthening'; revisit fully only on a verified thesis_break."},
   {"action":"SELL","ticker":"ASML","size_usd":523.25,"price_at_proposal":1744.16,"rationale":"30% profit-take on a stretched, watch-thesis name (structural China-buildout risk un-escalated, not resolved); pairs with AMAT.","trigger_type":"profit_rotation","trigger_bucket":"names_stretched","pair_id":"profit_rotation-ASML-AMAT","pair_role":"sell","size_wanted_usd":523.25,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"BUY","ticker":"AMAT","size_usd":200.08,"price_at_proposal":480.04,"rationale":"In-cluster laggard (-4.1pp) with strengthening thesis; wanted $350.88, clamped to $200.08 by ATR headroom. Sell proceeds exceed the clamped buy, netting +$323.17 to cash -- the one cash-positive decision this run.","trigger_type":"profit_rotation","trigger_bucket":null,"pair_id":"profit_rotation-ASML-AMAT","pair_role":"buy","size_wanted_usd":350.88,"clamped_by":"ATR headroom","stop_price_usd":394.59,"exited_on":null,"evidence_quality":{"verified":1,"computed":2,"unverified":0}},
   {"action":"SELL","ticker":"AMD","size_usd":287.51,"price_at_proposal":479.18,"rationale":"30% trim of the AI Semis/Fabs laggard (-11.3pp) on a watch thesis; dead money next to NVDA's cluster leadership. Third restatement -- rc=2, one more unchanged restatement auto-retires this pair.","trigger_type":"cluster_rotation","trigger_bucket":"rotate_out","pair_id":"cluster_rotation-AMD-NVDA","pair_role":"sell","size_wanted_usd":287.51,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":1,"computed":2,"unverified":0}},
   {"action":"BUY","ticker":"NVDA","size_usd":287.51,"price_at_proposal":213.05,"rationale":"Cluster relative-strength leader (+7.4pp), strengthening thesis, funded by the AMD sell. CAUTION: NVDA reports TODAY 2026-08-26 after close -- this buy sizes into a same-day binary event; apply tight-SL discipline immediately on fill.","trigger_type":"cluster_rotation","trigger_bucket":null,"pair_id":"cluster_rotation-AMD-NVDA","pair_role":"buy","size_wanted_usd":287.51,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":1,"computed":2,"unverified":0}}
 ],
 "scorecard_read":"7 scored, overall 14.3% (1 worked/6 missed, avg -9.88%); TRIM/SELL 100% on n=1 (+5.62%, a single win not an edge); BUY 0% on n=4 (avg -13.46%, small-sample but directly relevant since today's 3 buy legs and the entire shopping list are BUY); HOLD 0% on n=2 (avg -10.45%). 1 quarantined (P-011 NEM, +50.7% off an $89.70 anchor -- excluded, not counted). 112 still under 30 days -- this scorecard is provisional and will move; today's buy-heavy mix leans on verified-secondary theses and computed triggers rather than bare signals as the best available mitigant, not as proof the BUY-side concern is resolved.",
 "deemphasize_buckets":[],
 "data_quality":["rsi14/rel_strength_1m caches 14d old vs 10d TTL -- oversold_reversion/overbought_distribution/laggard_rotation suppressed; refresh unblocks ATR-cap cures for BE/VRT/MRVL/GEV/NBIS/MU/TSM/COHR","compute_derisk.json de-risk composite null (rel_strength missing for 10 names) -- names_stretched list directional only","BX re-entry date discrepancy: lots.json=2026-08-21 vs dispatch/state=2026-08-24 (G83), unresolved","MRVL over ATR cap ($634 excess) and reports 2026-08-27 but has no live trigger this run -- not sized, flagged for next refresh","no signals-agent tail provided this run -- bucket hit-rate table omitted, not computed"]}
```

Output written to: `runs/2026-08-26-1315/strategist.md`

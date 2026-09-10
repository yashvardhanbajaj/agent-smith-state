# Portfolio Strategist — Quick Sweep, 2026-09-10-0331

## Headline
Book $43,611 (equity $42,083 + wallet $1,529). Cash 3.5% vs [5,15]% band -- still short.
AI Semis/Fabs cluster breached: 34.16% vs [23,33]% band, $0 room. Aggregate open risk 9.71%
vs 10% cap (tight, not breached). Sentiment 65.7 GREED. Correction state: pullback (-6.70%
book drawdown, past a quarter of the 8% warn line but nowhere near it). Risk-off status:
**normal** -- no defensive posture required, but cash-rebuild stays the standing priority.
Gate AMBIGUOUS, post-close context only.

17 proposals already open (P-231..P-260). Nearly every live trigger this run maps onto one
of them -- see REFRESH tags below. Deployable cash is $0.00, so every unpaired BUY (GOOG,
AMAT-oversold, KLAC-trend, APH-trend, CIEN/APH/AMAT-conviction) is clamped to $0 regardless
of setup quality; only the three self-funded rotation pairs and the standalone catalyst/
overbought TRIMs are currently executable at nonzero size.

## VRT -- flagged prominently, no proposal
VRT fell -9.61% today (confirmed live quote, -2.2x ATR) on a STRONG DOWNTREND signal fire,
but smith-signals found **no catalyst news** for the move. Thesis stays WATCH: real
fundamentals are pulling one way (Q2 +24% YoY, FY26 guide raised to $14B, a $1.45B
acquisition) and today's price action plus a lone 2026-09-07 insider sale pull the other,
with no resolving evidence either way. Rotation reads VRT net_signal 0, not overbought
(RSI14 67.2), within cap (cap_multiple 0.738) -- nothing here computes to a sell. Per this
desk's standing rule, price alone without a catalyst does not trigger an action. **Watch,
don't act** -- if tomorrow's session doesn't produce a corroborating catalyst (a filing,
a competitor read-across, a channel check), treat today as noise; if one appears, this
becomes a live thesis_break candidate on the next run, not this one.

## Proposals (all sizes from compute_triggers.json / compute_rotation.json -- not recomputed)

**Catalyst-threat TRIMs (REFRESH of P-250/251/255/256/257/260) -- staleness flag.**
All six share one catalyst: CXMT reaching HBM3E risk production, first reported 2026-09-01,
last freshly confirmed 2026-09-07 -- so the underlying report is **9 days old**, only
re-stamped, not re-verified, on the 07th. Ran `smith_math.py gaps --query "CXMT unverified
catalyst"` before sizing these (required for catalyst_threat per SOP): no exact CXMT-specific
false-alarm precedent, but G30 (CXMT/memory catalyst-monitoring gap, closed) and G58
(unverified qualitative claims propagating into sized proposals -- the evidence-gate framework
this section now runs under) are the closest hits. Source is a single secondary outlet
(techtimes.com), risk-production/qualification-stage only, no unit count, not yet in any
supplier contract price -- genuinely unverified, but the trims are sized modest (~20% each)
and cap-independent by design, so I'm refreshing them rather than pulling them. Given this
desk's own TRIM/SELL track record (see scorecard read below, 14.3% accuracy on n=14), treat
these as risk-reduction on a real if unconfirmed threat, not an alpha call.

1. TRIM ASML $432.38 @ $1,729.52 (watch thesis, cluster at $0 ceiling room) -- refresh P-256.
2. TRIM MU $411.18 @ $1,027.77 (watch thesis, cap_multiple 1.037) -- refresh P-250.
3. TRIM TER $383.90 @ $383.69 (strengthening thesis, cap_multiple 1.106) -- refresh P-255.
4. TRIM AMAT $282.08 @ $468.85 -- refresh P-257. **Tension flag**: AMAT also carries an open
   BUY, P-231 ($400, conviction_average, oversold RSI14 33.3, thesis strengthening, rotation
   bucket is `null` -- not `accumulate`, so the 2a-i override does not shield it). Both are
   live, both cap-independent of each other's logic (one prices a structural risk, one prices
   a technical dip on an intact thesis). Net effect if both execute is close to a wash
   (~$118 net buy). Recommend the user pick one direction rather than running both.
5. TRIM SKHY $198.63 @ $198.63 (=full mkt value, 20% trim per trim_fraction) -- refresh P-251.
   **Sharpest tension of the six**: SKHY is today's standout (+7.05%, BREAKOUT + STRONG
   UPTREND + PEER LEADER + NEW TAILWINDS, on an HBM supply/pricing-power upgrade) and sits in
   rotation's `accumulate` bucket, not overbought (RSI14 64.9<70). The desk is proposing to
   trim it on a 9-day-old *competitive-threat* catalyst the same day it rallied on a *fresh*
   pricing-power tailwind in the same commodity. Both are real and don't cancel (financing-
   structure risk vs. today's operating news), but this is the one of the six I'd deprioritize
   first if only one has to wait for a fresher catalyst read.
6. TRIM LRCX $189.50 @ $315.84 -- refresh P-260. Same accumulate-bucket tension noted by the
   trigger itself (strengthening thesis, RSI14 53.3, not overbought); cap-independent catalyst
   logic still applies, flagged not blocked.

**Overbought profit-take (REFRESH of P-243).**
7. TRIM NVDA $279.59 @ $223.67 -- RSI14 70.4 (crossed overbought), +8.1% on the month, real
   gain to protect. Deliberately cap-independent (`over_cap_independent: true`) -- this is
   the carve-out case 2a-i explicitly allows (genuinely overbought), not a cap reflex.

**Self-funded cluster rotations (REFRESH of P-241/242, P-252/253) -- fully funded, no cash dependency.**
8. SELL AMD $468.99 @ market / BUY KLAC $468.99 @ $182.91 -- AI Semis/Fabs, ladder-driven
   (2026-09-08, medium confidence): ladder ranks AMD #8/10 (Q3 guide read below consensus,
   ~$5bn debt raise levering an unowned capex build) vs KLAC #2/10 (process-control/metrology
   intensity scaling with GAA + advanced packaging). pair_id cluster_rotation-AMD-KLAC.
9. SELL AVGO $218.63 @ market / BUY LITE $218.63 @ $988.98 -- AI Networking/Optics, direct
   relative-strength read (not ladder-driven): AVGO cluster laggard -13.3pp with watch
   thesis, LITE cluster leader +45.1pp with strengthening thesis. pair_id
   cluster_rotation-AVGO-LITE.

**Profit rotation (REFRESH of P-258) -- buy leg still starved of room.**
10. SELL MSFT $147.49 @ market (in names_stretched, watch thesis) / BUY KLAC $0.00, clamped
    by cluster ceiling room (AI Semis/Fabs has $0 headroom per drift table). The sell leg
    stands on its own merits (real profit to book on a stretched, watch-thesis name); the buy
    leg stays open only because KLAC's thesis case doesn't expire when its funding does.
    pair_id profit_rotation-MSFT-KLAC.

**Oversold BUYs, funding-blocked (REFRESH of P-235; AMAT covered under item 4 above).**
11. BUY GOOG $0.00 (wanted, clamped by zero deployable cash) @ $328.38 -- RSI14 28.9, thesis
    strengthening, $4,260 of ATR headroom sitting unused purely for lack of cash. Note the
    irony: GOOG is simultaneously a live oversold_reversion BUY target and a shadow
    laggard_rotation candidate (-13.1pp vs SMH) -- both readings agree, only funding is
    missing. If cash is deliberately rebuilt (items 1-3, 5-7, 10 raise roughly $2,325 net if
    all execute), GOOG is the standing first call on redeployment.

**New idea, unsized (not yet open).**
12. WATCH CORZ (entry_setup, conviction low at 20.8) -- +49.5% vs analyst target, RSI14 31
    oversold, but this run has **no live price/ATR for CORZ** (blocker on the trigger row
    itself). Not sizing on a stale/missing anchor. Carry to next run for a price fetch before
    proposing a number.

**Shadow, advisory only (not hit-rate validated -- SOP 2c).**
13. NBIS: raise stop from $192.86 to $207.83 (breakeven) -- shadow `profit_ratchet`, refresh
    of P-254 (already open as HOLD). Up +15.6% vs a $207.83 basis but the current stop sits
    *below* breakeven; $74.85 of gain is at risk to a retracement that would turn a real
    winner into a realised loss. This is bookkeeping, not a new call.

## Risk-off check
`risk_off_status: normal` (compute_drift.json). Drawdown -6.70% of total book vs an 8% warn
line -- inside it, not close. No defensive posture triggered. Standing items regardless of
risk-off status: cash 3.5% vs [5,15]% floor (short by ~$650 to reach the 5% floor on a
$43,611 book) and AI Semis/Fabs cluster breached +6.16pt with $0 room. Neither is an
emergency; both are why the catalyst TRIMs and the MSFT sell leg above are worth executing
even setting the CXMT staleness question aside -- they're the cash-rebuild path.

## Hit-rate readout (journal.json bucket_hit_rates -- not recomputed)
- MOMENTUM+VOLUME: 20.0% (n=15) -- **recommend de-emphasis** (below 40% over >=5 entries).
- TARGET GAP: 36.8% (n=19) -- **recommend de-emphasis** (below 40% over >=5 entries).
- OVERSOLD BOUNCE: 66.7% (n=3) -- encouraging, but n<5 so no formal recommendation either way.
- BREAKDOWN: n=1, skipped (below the 3-entry floor).

This lines up with today's signals-tail note that MU/CLS/COHR/TER carry F-grade signals on
their live buckets (weak historical hit rate) while NVDA/LITE/MRVL carry A-grade -- MU and
TER both appear in the catalyst TRIMs above, which is a separate (structural-threat) basis
from the weak momentum bucket, but worth knowing the desk's technical read on both names has
a poor track record independent of the CXMT story.

## Scorecard interpretation (proposals.json, as_of 2026-09-09 -- preserved, NOT recomputed)
`score` refused to write this run (32 graded rows vs 33 on record, a 1-row shrink not chased
down) so this is yesterday's scorecard, one day stale. Figures, always with n:
- Overall: 36.4% accuracy (n=33: 12 worked / 18 missed / 3 neutral), avg benefit -5.72%.
- TRIM/SELL: **14.3% accuracy (n=14)**, avg benefit -14.47%. Weak, and consistent across the
  desk's history -- the catalyst TRIMs proposed above should be read as risk-reduction on
  scale-appropriate size (each ~20% of position), not as a confident directional call. This
  record is exactly why none of them are sized full-position.
- BUY: 62.5% accuracy (n=16), avg benefit +2.89%. Meaningfully better -- supports leaning
  into GOOG/AMAT oversold BUYs the moment cash allows, more than it supports the TRIMs.
- HOLD: 0.0% (n=3) -- too small a sample to act on, noted only.
- 4 rows quarantined pending anchor review (3x SNDK, 1x NEM) -- excluded from the above,
  not resolved this run.
- 0 of 33 graded rows carried a benchmark anchor (pre-2026-09-07 history) -- graded on raw
  move, not alpha vs SMH. Every proposal in this run carries `benchmark_price_at_proposal`
  ($574.29, live SMH) so future scoring of today's batch will be alpha-aware.

Net read: the desk's SELL/TRIM calls have not been reliable: size trims modestly and treat
them as risk management, and weight the BUY-side conviction (GOOG, AMAT, cluster-rotation
buy legs) more heavily once funding exists.

## Stress table
Skipped -- QUICK mode per SOP Task 4 (deep-only).

## LTCG check
No live deferrals to propose. Per standing note, the earliest open lot in this book is
2026-07-15, putting the 24-month LTCG boundary at mid-2028 -- nothing is close enough to
warrant a hold-for-LTCG flag this run.

## Data quality
- `score` scorecard is 1 day stale (32 vs 33 graded-row mismatch, not chased down this run).
- CORZ entry_setup has no live price/ATR this run -- sizing deferred.
- VRT's -9.61% move today has no catalyst attribution from smith-signals -- treated as
  unexplained, not actioned.
- CXMT HBM3E catalyst underlying 6 TRIM proposals is 9 days old (2026-09-01), re-stamped
  not re-verified on 2026-09-07; single secondary source, no primary corroboration.
- AMAT carries simultaneous open BUY (P-231) and TRIM (P-257) with no desk resolution --
  flagged for the user to pick a direction.

```json
{"policy_draft":null,
 "stress_table":{"as_of":"2026-09-10",
   "anchored_to":{"us10y_pct":4.837,"vix":16.46,"dxy":98.752,"fed_rate_pct":null,"fed_stance":null},
   "scenarios":[],
   "data_quality":["stress table skipped -- QUICK mode per SOP Task 4 (deep-only)"]},
 "proposals":[
   {"direction":"TRIM","ticker":"ASML","size_usd":432.38,"price_at_proposal":1729.52,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-256. catalyst_threat: CXMT HBM3E risk-production report, 9 days old (2026-09-01), re-stamped not re-verified 2026-09-07, single secondary source (techtimes.com), risk/qualification-stage only, not in supplier contract pricing. gaps-checked (smith_math.py gaps --query CXMT unverified catalyst): no exact precedent, closest are G30 (CXMT catalyst-monitoring gap) and G58 (unverified-claims evidence gate). Watch thesis, cluster at $0 ceiling room, cap-independent by design.",
    "trigger_type":"catalyst_threat","pair_id":null,"pair_role":null,
    "size_wanted_usd":432.38,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"direction":"TRIM","ticker":"MU","size_usd":411.18,"price_at_proposal":1027.77,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-250. Same CXMT catalyst_threat as ASML (see gaps check above). Watch thesis, over_cap materiality real (cap_multiple 1.037, ~3.7% over cap) but the trim is priced on the catalyst, not the cap breach.",
    "trigger_type":"catalyst_threat","pair_id":null,"pair_role":null,
    "size_wanted_usd":411.18,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"direction":"TRIM","ticker":"TER","size_usd":383.90,"price_at_proposal":383.69,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-255. Same CXMT catalyst_threat. Strengthening thesis, cap_multiple 1.106 (real cap breach) reinforces but does not drive the trim -- catalyst is cap-independent.",
    "trigger_type":"catalyst_threat","pair_id":null,"pair_role":null,
    "size_wanted_usd":383.90,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"direction":"TRIM","ticker":"AMAT","size_usd":282.08,"price_at_proposal":468.85,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-257. Same CXMT catalyst_threat. TENSION FLAG: AMAT also carries open BUY P-231 ($400, conviction_average, RSI14 33.3 oversold, thesis strengthening, rotation bucket null -- not accumulate, so 2a-i does not shield it from this trim). Both live and cap-independent of each other's logic; net effect if both execute is roughly a wash (~$118 net buy). Recommend the user pick one direction.",
    "trigger_type":"catalyst_threat","pair_id":null,"pair_role":null,
    "size_wanted_usd":282.08,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"direction":"TRIM","ticker":"SKHY","size_usd":198.63,"price_at_proposal":198.63,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-251. Same CXMT catalyst_threat. SHARPEST TENSION of the six: SKHY rallied +7.05% today (BREAKOUT+STRONG UPTREND+PEER LEADER+NEW TAILWINDS) on an HBM pricing-power upgrade -- the same commodity the 9-day-old competitive-threat catalyst concerns, arguing the opposite direction. Rotation bucket is accumulate, not overbought (RSI14 64.9<70), per 2a-i cap alone would not justify a trim here -- but this proposal rests on the catalyst, not the cap. Of the six catalyst trims, this is the one I'd defer first pending a fresher catalyst read.",
    "trigger_type":"catalyst_threat","pair_id":null,"pair_role":null,
    "size_wanted_usd":198.63,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"direction":"TRIM","ticker":"LRCX","size_usd":189.50,"price_at_proposal":315.84,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-260. Same CXMT catalyst_threat. Rotation bucket accumulate, strengthening thesis, RSI14 53.3 not overbought -- tension flagged by the trigger itself; catalyst logic is cap/cluster-independent by design so the trim stands, priority is a judgement call.",
    "trigger_type":"catalyst_threat","pair_id":null,"pair_role":null,
    "size_wanted_usd":189.50,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"direction":"TRIM","ticker":"NVDA","size_usd":279.59,"price_at_proposal":223.67,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-243. overbought_distribution: RSI14 70.4 (crossed overbought), +8.1% on the month. Deliberately cap-independent (over_cap_independent=true) -- the genuinely-overbought carve-out under 2a-i, not a cap reflex; comfortably inside its cap.",
    "trigger_type":"overbought_distribution","pair_id":null,"pair_role":null,
    "size_wanted_usd":279.59,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"direction":"SELL","ticker":"AMD","size_usd":468.99,"price_at_proposal":null,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-252. cluster_rotation sell leg, AI Semis/Fabs, ladder-driven (2026-09-08, medium confidence): ladder ranks AMD #8/10 -- Q3 guide read below consensus (2026-08-11), ~$5bn debt raise levering capex it does not own. Desk is overriding the raw 1m price read, which is worst-in-cluster.",
    "trigger_type":"cluster_rotation","pair_id":"cluster_rotation-AMD-KLAC","pair_role":"sell",
    "size_wanted_usd":468.99,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"direction":"BUY","ticker":"KLAC","size_usd":468.99,"price_at_proposal":182.91,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-253. cluster_rotation buy leg, fully funded by the AMD sell leg. Ladder ranks KLAC #2/10 (leader): process-control/metrology intensity scales fastest with GAA + advanced packaging. conviction_score 60.8 (medium tier).",
    "trigger_type":"cluster_rotation","pair_id":"cluster_rotation-AMD-KLAC","pair_role":"buy",
    "size_wanted_usd":468.99,"clamped_by":null,"stop_price_usd":166.2286,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":0}},
   {"direction":"SELL","ticker":"AVGO","size_usd":218.63,"price_at_proposal":null,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-241. cluster_rotation sell leg, AI Networking/Optics, NOT ladder-driven -- direct relative-strength read: AVGO is the cluster laggard (-13.3pp vs SMH), watch thesis, dead money in this cluster.",
    "trigger_type":"cluster_rotation","pair_id":"cluster_rotation-AVGO-LITE","pair_role":"sell",
    "size_wanted_usd":218.63,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"direction":"BUY","ticker":"LITE","size_usd":218.63,"price_at_proposal":988.98,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-242. cluster_rotation buy leg, fully funded by the AVGO sell leg. Cluster performer (+45.1pp vs SMH), strengthening thesis, conviction_score 50.8 (medium tier).",
    "trigger_type":"cluster_rotation","pair_id":"cluster_rotation-AVGO-LITE","pair_role":"buy",
    "size_wanted_usd":218.63,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"direction":"SELL","ticker":"MSFT","size_usd":147.49,"price_at_proposal":null,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-258. profit_rotation sell leg: MSFT in names_stretched (compute_derisk.json) with a watch thesis -- real profit to book. Buy leg (KLAC) stays clamped to $0.00 by AI Semis/Fabs's $0 cluster ceiling room; sell leg stands on its own merits regardless.",
    "trigger_type":"profit_rotation","pair_id":"profit_rotation-MSFT-KLAC","pair_role":"sell",
    "size_wanted_usd":147.49,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"direction":"BUY","ticker":"KLAC","size_usd":0.0,"price_at_proposal":182.91,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-258 buy leg. Clamped to $0.00 by cluster ceiling room (AI Semis/Fabs breached, $0 room per compute_drift.json). Conviction case (60.8, medium tier) is unaffected by the funding gap -- stays open pending cluster room freeing up (e.g. if the catalyst TRIMs above execute).",
    "trigger_type":"profit_rotation","pair_id":"profit_rotation-MSFT-KLAC","pair_role":"buy",
    "size_wanted_usd":220.0,"clamped_by":"cluster ceiling room","stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"direction":"BUY","ticker":"GOOG","size_usd":0.0,"price_at_proposal":328.38,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-235. oversold_reversion: RSI14 28.9 (deeply oversold), thesis strengthening, $4,260 ATR headroom unused. Clamped to $0.00 -- deployable_cash_usd is $0.00 this run. Also a shadow laggard_rotation candidate (-13.1pp vs SMH), same read reinforcing. First call on redeployment once cash rebuilds (items 1-3,5-7,10 above raise ~$2,325 net if all execute).",
    "trigger_type":"oversold_reversion","pair_id":null,"pair_role":null,
    "size_wanted_usd":1276.0,"clamped_by":"deployable cash","stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":0}},
   {"direction":"HOLD","ticker":"CORZ","size_usd":0.0,"price_at_proposal":null,
    "benchmark_price_at_proposal":null,
    "rationale":"NEW, not yet open. entry_setup: +49.5% vs analyst target, RSI14 31 oversold, but conviction is low (20.8) and this run has no live price/ATR for CORZ. Not sizing on a missing/stale anchor -- carry to next run for a price fetch.",
    "trigger_type":"entry_setup","pair_id":null,"pair_role":null,
    "size_wanted_usd":null,"clamped_by":"no live price this run","stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":1,"unverified":1}},
   {"direction":"HOLD","ticker":"NBIS","size_usd":0.0,"price_at_proposal":240.35,
    "benchmark_price_at_proposal":574.29,
    "rationale":"REFRESH of open P-254 (shadow profit_ratchet, not yet hit-rate validated per SOP 2c). Recommend raising the stop from $192.86 to $207.83 (breakeven) -- up +15.6% vs a $207.83 basis but the current stop sits below breakeven, putting $74.85 of gain at risk to a retracement. Bookkeeping, not a new directional call.",
    "trigger_type":"profit_ratchet","pair_id":null,"pair_role":null,
    "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":207.826,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"direction":"HOLD","ticker":"VRT","size_usd":0.0,"price_at_proposal":null,
    "benchmark_price_at_proposal":null,
    "rationale":"NO ACTION -- flagged prominently. -9.61% today (confirmed live quote, -2.2x ATR), STRONG DOWNTREND fired, but no catalyst found. Thesis stays WATCH: strong fundamentals (Q2 +24% YoY, FY26 guide raised to $14B, $1.45B acquisition) in genuine, unresolved tension with the drop and a lone 2026-09-07 insider sale. Not overbought/not over cap/net_signal 0 -- nothing computes to a sell. Price alone without a catalyst does not trigger action; watch for a corroborating catalyst next run.",
    "trigger_type":null,"pair_id":null,"pair_role":null,
    "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":1,"unverified":1}}
 ],
 "scorecard_read":"As of 2026-09-09 (preserved, score refused to write this run -- 32 vs 33 graded rows, 1-row shrink not chased down). Overall 36.4% (n=33: 12 worked/18 missed/3 neutral), avg benefit -5.72%. TRIM/SELL 14.3% (n=14), avg benefit -14.47% -- weak and consistent with prior runs; the 7 TRIMs proposed here are sized as risk-reduction (~20% each), not alpha calls, because of this record. BUY 62.5% (n=16), avg benefit +2.89% -- meaningfully stronger, supports leaning into GOOG/AMAT-oversold once cash frees up more than it supports the TRIM batch. HOLD 0.0% (n=3), sample too small to act on. 4 rows (3x SNDK, 1x NEM) remain quarantined pending anchor review, excluded from these figures. 0 of 33 graded rows carried a benchmark anchor (pre-2026-09-07 history) -- every proposal in this run carries benchmark_price_at_proposal ($574.29 SMH) so this batch will score alpha-aware.",
 "deemphasize_buckets":["MOMENTUM+VOLUME","TARGET GAP"],
 "data_quality":[
   "score scorecard is 1 day stale (32 vs 33 graded-row mismatch, not chased down this run) -- treated as current-enough per dispatch note.",
   "CORZ entry_setup has no live price/ATR this run -- sizing deferred, not proposed.",
   "VRT's -9.61% move today has no catalyst attribution -- flagged, not actioned.",
   "CXMT HBM3E catalyst underlying 6 TRIM proposals is 9 days old (2026-09-01), re-stamped not re-verified on 2026-09-07, single secondary source, no primary corroboration -- gaps-checked (G30, G58 closest precedents).",
   "AMAT carries simultaneous open BUY (P-231, $400) and TRIM (P-257, $282.08) with no desk resolution -- flagged for the user to pick a direction.",
   "OVERSOLD BOUNCE bucket (66.7%, n=3) below the 5-entry floor for a formal de-emphasis recommendation either way -- reported only.",
   "Stress table skipped -- QUICK mode."
 ]}
```

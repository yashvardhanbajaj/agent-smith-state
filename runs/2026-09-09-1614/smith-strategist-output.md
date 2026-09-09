# Portfolio Strategist — Priced Refresh, 2026-09-09 14:36Z (intraday, ~10:36am ET)

Mode: quick / priced-refresh sub-mode. This is NOT a fresh Stage-1 sweep — book/risk/drift/rotation/triggers/derisk/sentiment
below are all recomputed against **live intraday prices as of 14:36Z**. Thesis verdicts, the sector map, and signal buckets
are carried forward from the 07:51Z full sweep (each cited with its own `reviewed_on` stamp). No crosscheck.json (no Wave
1/2 this dispatch) and no out_macro.json (macro is deep-only) — both absent by design, not a gap.

## Headline change since 07:51Z: cash has fallen through the floor

`compute_drift.json`: cash is **2.71%** of total book vs the policy's 5–15% band — `cash_breach: true`. `compute_triggers.json`
carries `deployable_cash_usd: 0.0` and `deployable_cash_for_ideas_usd: 0.0` across the board. This morning's run had cash
enough to fund P-235 (Buy GOOG, $287.95); as of this refresh **every standalone BUY idea in the fresh trigger set prices at
suggested_size_usd = $0.00, clamped_by "deployable cash"** — GOOG and AMAT oversold_reversion, KLAC/NVDA/APH trend_entry,
and CIEN/APH/AMAT/GOOG conviction_average all show a real setup with no funding behind it right now. **Only paired trades
(profit_rotation, cluster_rotation) are actually executable in size**, because the buy leg is funded off the sell leg, not
the wallet. Risk-off status itself is still `normal` (drawdown -5.25%, well inside the -8% warn line) — this is a cash
mechanics constraint, not a risk-off signal.

Sentiment score: **65.9** (neutral-to-firm, not extreme-greed/extreme-fear territory) → drift and thesis drive sizing as
usual, no sentiment-led override.

## Proposals

### IDEAS (ranked by conviction; capped at 5 for the dashboard's IDEA panel)

**1. TRIM TER — $381.25 (catalyst_threat, NEW since 07:51Z)**
Price $381.04, RSI14 48.1 (neutral), thesis strengthening. CXMT reached HBM3E risk-production/qualification-stage volume
~1yr ahead of the 2027 consensus timeline (techtimes.com, 2026-09-01, carried forward/last confirmed 2026-09-07) — a
structural threat to the memory-tooling demand curve TER's testers are levered to. Cap-independent by design (TER is not
over cap: cap_multiple 1.081, i.e. barely over — but that's not the rationale here, the catalyst is). Precedent check run
(`smith_math.py gaps --query "CXMT HBM3E export control"`): no direct contradiction found; closest precedent is G30
(catalyst-monitoring gap, closed) — nothing here undercuts the claim, but the catalyst itself remains "risk-production
volume only, not mass production, no unit count disclosed" per its own sourcing, i.e. still an early-stage read.
evidence_quality: {"verified": 0, "computed": 3, "unverified": 1} (RSI/price/size are computed; the catalyst claim is a
single secondary news source, not independently verified — advisory flag, not a block).
`benchmark_price_at_proposal`: 575.62 (SMH).

**2. TRIM ASML — $435.19 (catalyst_threat, NEW since 07:51Z)**
Price $1,740.77, RSI14 49.1, thesis **watch** (not strengthening) — same CXMT catalyst as above, but here it lands on a
name whose thesis was already softening independent of this catalyst, which is the stronger case of the two new entries.
evidence_quality: {"verified": 0, "computed": 3, "unverified": 1}. `benchmark_price_at_proposal`: 575.62.

**3. TRIM AMAT — $282.74 (catalyst_threat, NEW since 07:51Z) — flagged tension, size with eyes open**
Price $469.95, RSI14 33.3 (oversold), thesis strengthening. Same CXMT catalyst, but AMAT is simultaneously showing an
**oversold_reversion BUY setup** (RSI<35, thesis strengthening, technical dip not a fundamental break) and a
**conviction_average BUY** — both currently unfunded (cash breach) rather than genuinely retired. This is a real
three-way conflict on one name: structural threat (TRIM) vs. technical dip (BUY) vs. conviction add (BUY), and the compute
layer does not resolve it — it hands over all three legs and leaves the call to me. I'm sizing the TRIM because
catalyst_threat is deliberately cap/cluster-independent and the highest-consequence trigger this desk fires, but the two
BUY reads stand on the record too: if the CXMT catalyst is priced in and doesn't develop further, AMAT at RSI 33 was the
better trade. Not a clean idea — flagging it as one, not resolving it as a formula would.
evidence_quality: {"verified": 0, "computed": 4, "unverified": 1}. `benchmark_price_at_proposal`: 575.62.

**4. PAIRED: SELL MSFT $147.88 / BUY KLAC $147.88 — profit_rotation, NEW pair since 07:51Z**
`pair_id: profit_rotation-MSFT-KLAC`. MSFT is in the stretched cohort with a watch thesis — real profit to book. KLAC is
-5.7pp vs benchmark on a strengthening thesis (KLAC conviction_score 62.5, medium tier) — yet to rally. This is the one
BUY idea actually fundable right now, because it draws on the sell leg rather than the empty cash band.
Retires when either MSFT drops out of the stretched cohort or KLAC's thesis leaves intact/strengthening.
evidence_quality: {"verified": 0, "computed": 4, "unverified": 0}. `benchmark_price_at_proposal`: 575.62 both legs.

**5. TRIM LRCX — $190.21 (catalyst_threat, NEW since 07:51Z) — flagged tension**
Price $317.01, RSI14 53.3, thesis strengthening. Same CXMT catalyst; LRCX is simultaneously in rotation's `accumulate`
bucket (net_signal +2: NEW TAILWINDS + PEER LEADER) on the same strengthening thesis. Per the standing rule (2a-i /
2d), I would normally decline to trim a name whose own bucket argues for adding — but that rule is written for ATR
cap-mechanics trims, and catalyst_threat is explicitly exempted from cap/cluster gating for a reason (it's meant to be
urgent). I'm sizing it small (trim_fraction 0.2, same as the others) rather than declining it outright, and naming the
tension rather than picking a side silently. Weakest of the five ideas — if the desk has to drop one for the 5-slot cap,
drop this one first.
evidence_quality: {"verified": 0, "computed": 4, "unverified": 1}. `benchmark_price_at_proposal`: 575.62.

### Already-open from the 07:51Z run — status under fresh prices (not re-proposed, referenced only)

- **P-243 (TRIM NVDA, overbought_distribution)** — still live at fresh prices: RSI14 70.4, +8.1% on the month. Fresh
  suggested size $281.12 vs the morning's $286.10 — small downward tick with the price move, same idea, same trigger.
  No action needed beyond noting the size drift.
- **P-252/P-253 (cluster_rotation, SELL AMD / BUY KLAC, AI Semis/Fabs)** — still live, ladder-driven (1d old, medium
  confidence). Fresh size $469.40 vs morning $455.17 — ticked up ~3% with price. Unchanged trade.
- **P-241/P-242 (cluster_rotation, SELL AVGO / BUY LITE, AI Networking/Optics)** — still live. Fresh size $218.09 vs
  morning $214.81 — ticked up ~1.5%. Unchanged trade.
- **P-250 (TRIM MU, catalyst_threat)** — still live, unchanged trigger, fresh size $414.12 vs morning $400.18.
- **P-251 (TRIM SKHY, catalyst_threat)** — still live. SKHY carries the same accumulate-bucket tension as LRCX above
  (SKHY is in rotation's accumulate bucket on a strengthening thesis) — this was already flagged when P-251 was written
  and is unchanged.
- **P-254 (NBIS profit_ratchet / STOP_RAISE)** — shadow trigger, $0 sized (it's a stop instruction, not a buy/sell). Still
  applicable: NBIS stop sits at $196.75, below its $209.23 cost basis — a retracement would turn a +17.2% winner into a
  realized loss. Not re-proposed; flagging that this is still true and unactioned.

### Housekeeping (sized, not ranked against ideas)

- **GOOG oversold_reversion (BUY)** — RSI14 28.9, thesis strengthening, technically valid — but **now unfunded** (see cash
  note above). This matches/updates P-235 (opened this morning at $287.95); the setup hasn't cleared, the funding has.
  No new proposal — flagging the funding gap on the existing one.
- **AMAT oversold_reversion (BUY)** — same story, also unfunded now, also entangled with the catalyst_threat trim above
  (idea #3). Not sizing separately.

### Flags on the intraday move named in the dispatch

- **VRT (-5.3% intraday)**: no live trigger fired on VRT (not over cap, not oversold, not in a bucket). Its thesis is
  `watch`, `unverified`, reviewed 2026-09-08 with a single note ("1 insider sold in last 60 days, no insider buying during
  drawdown") — that thesis read is now ~1 day old against a same-day 5%+ move it doesn't speak to at all. Not proposing
  anything on VRT this refresh — flagging that the qualitative read here is thinner than the price action, worth a fresh
  smith-thesis pass next full sweep rather than acting on stale watch-status text now.
- **MRVL (+5.6% intraday)**: thesis strengthening, reviewed 2026-09-08 (1 day old, relatively fresh), `verified: secondary`.
  Rotation table shows MRVL over cap (cap_multiple 1.135, headroom -$254.37) in the `accumulate` bucket — per the 2a-i
  rule, an over-cap name with a strengthening thesis and a bullish net signal (PEER LEADER) is over cap *because it's
  winning*, not because it's mispriced. No trim proposed on cap mechanics alone, correctly. No live trigger fired either.
  No action.
- **META (+4.95% intraday)**: thesis `intact`, `verified: secondary`, evidence dated **2026-08-12** — nearly 4 weeks
  stale against today's move. Rotation shows META net_signal -2 (STRONG DOWNTREND, PEER LAGGARD, NEW HEADWINDS bearish,
  one OVERSOLD BOUNCE bullish), RSI14 34.1, not over cap. No live trigger fired on META this refresh (no lots.json entry
  either — profit_ratchet/scale_out_ladder structurally can't compute for it, per data_quality). This is the clearest
  case in this refresh of price outrunning the qualitative read: a 5% move on a name whose thesis text is a month old and
  already carries an unresolved evidence-against tension ("FCF-down-vs-capex-up tension structural, untested until next
  print"). Not proposing a trade on META — flagging it for the next full smith-thesis pass rather than sizing on stale
  text.

## Risk-off status

`risk_off_status: normal` (drawdown -5.25%, warn line -8%, risk-off line -12%). No defensive lead required. Cash breach
(2.71% vs 5–15% band) is a funding constraint on new BUYs, not a risk-off trigger — treated separately above.
`correction_state: pullback` (book drawdown past a quarter of the warn line) — smith-rebound is flagged for dispatch this
run per `compute_triggers.json`'s own data_quality note; its rebound candidates (SNDK, CIEN, TER) are all flagged
"loud names being loud, not obvious dislocations" (fell <1.5x their own ATR) — context, not a proposal basis here.

## Hit-rate readout (carried from 07:51Z `compute_journal.json` — NOT recomputed this refresh)

| bucket | n | hit rate | note |
|---|---|---|---|
| OVERSOLD BOUNCE | 3 | 66.7% | keep — small n, but strong; the GOOG/AMAT oversold_reversion ideas sit in this bucket |
| TARGET GAP | 19 | 36.8% | below 40% over ≥5 — candidate for de-emphasis |
| MOMENTUM+VOLUME | 15 | 20.0% | below 40% over ≥5 — candidate for de-emphasis |
| BREAKDOWN | 1 | — | skip, n<3 |

## Scorecard interpretation (stored, from `proposals.json`, as_of 2026-09-09 — NOT recomputed this refresh; DRAM's
unresolvable quote blocked a full rescoring pass this morning, per dispatch)

Overall accuracy 36.4% (n=33). Split badly by direction: **BUY 62.5% (n=16, avg benefit +2.89%)** vs **TRIM/SELL 14.3%
(n=14, avg benefit -14.47%)** vs HOLD 0.0% (n=3). 4 rows quarantined for anchor review. This is a standing pattern, not
new to this run, and it bears directly on today's batch: 5 of the 5 IDEA-panel proposals above are TRIMs, sitting in the
desk's historically worst-performing bucket. That doesn't mean don't trim — the catalyst_threat logic for TER/ASML/AMAT/
LRCX is a fresh, specific, sourced threat rather than a repeat of whatever drove the 14.3% figure — but it's a reason to
size these as proposed (small, 20% trim_fraction) rather than aggressively, and a reason for the user to weight BUY-side
conviction (the MSFT→KLAC rotation leg, and the still-unfunded GOOG/AMAT oversold dips) at least as seriously as the
TRIM-side ideas above.

```json
{"policy_draft":null,
 "stress_table":null,
 "proposals":[
   {"direction":"TRIM","ticker":"TER","size_usd":381.25,"price_at_proposal":381.04,"rationale":"CXMT HBM3E structural threat catalyst, cap-independent trigger; precedent check run, no contradiction found (closest: G30, closed).","trigger_type":"catalyst_threat","trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1},"benchmark_price_at_proposal":575.62},
   {"direction":"TRIM","ticker":"ASML","size_usd":435.19,"price_at_proposal":1740.7731,"rationale":"Same CXMT catalyst landing on an already-watch thesis -- strongest of the new catalyst_threat entries.","trigger_type":"catalyst_threat","trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1},"benchmark_price_at_proposal":575.62},
   {"direction":"TRIM","ticker":"AMAT","size_usd":282.74,"price_at_proposal":469.9494,"rationale":"CXMT catalyst_threat sized despite a live conflicting oversold_reversion+conviction_average BUY read on the same name (both currently unfunded); flagged as a genuine three-way tension, not resolved as a formula.","trigger_type":"catalyst_threat","trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":4,"unverified":1},"benchmark_price_at_proposal":575.62},
   {"direction":"SELL","ticker":"MSFT","size_usd":147.88,"price_at_proposal":null,"rationale":"Stretched cohort, watch thesis -- profit_rotation sell leg funding the KLAC buy leg.","trigger_type":"profit_rotation","trigger_bucket":null,"pair_id":"profit_rotation-MSFT-KLAC","pair_role":"sell","size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":3,"unverified":0},"benchmark_price_at_proposal":575.62},
   {"direction":"BUY","ticker":"KLAC","size_usd":147.88,"price_at_proposal":184.4394,"rationale":"Laggard (-5.7pp) with strengthening thesis, funded by MSFT profit_rotation sell leg -- the one BUY idea actually fundable given the cash breach.","trigger_type":"profit_rotation","trigger_bucket":null,"pair_id":"profit_rotation-MSFT-KLAC","pair_role":"buy","size_wanted_usd":null,"clamped_by":null,"stop_price_usd":167.6185,"exited_on":null,"evidence_quality":{"verified":0,"computed":4,"unverified":0},"benchmark_price_at_proposal":575.62},
   {"direction":"TRIM","ticker":"LRCX","size_usd":190.21,"price_at_proposal":317.0133,"rationale":"CXMT catalyst_threat sized small despite LRCX sitting in rotation's accumulate bucket on the same strengthening thesis -- weakest of the five ideas, drop first if the 5-slot cap binds.","trigger_type":"catalyst_threat","trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":4,"unverified":1},"benchmark_price_at_proposal":575.62},
   {"direction":"HOLD","ticker":"GOOG","size_usd":0,"price_at_proposal":327.3644,"rationale":"oversold_reversion setup still valid (RSI 28.9, thesis strengthening) but unfunded -- cash 2.71% is below the 5% floor as of this refresh, down from whatever supported P-235 this morning. Matches P-235, not re-proposed as new money.","trigger_type":"oversold_reversion","trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":0,"clamped_by":"deployable cash","stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":3,"unverified":0}},
   {"direction":"HOLD","ticker":"VRT","size_usd":0,"price_at_proposal":null,"rationale":"-5.3% intraday move with no live trigger; thesis is watch/unverified, reviewed 2026-09-08, thin against today's move. No action -- flag for next thesis pass.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":1,"unverified":1}},
   {"direction":"HOLD","ticker":"META","size_usd":0,"price_at_proposal":null,"rationale":"+4.95% intraday move; thesis intact but evidence dated 2026-08-12 (~4 weeks stale), unresolved FCF-vs-capex tension. No live trigger, no lots.json entry. No action -- flag for next thesis pass.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":1,"unverified":1}}
 ],
 "scorecard_read":"Stored scorecard (proposals.json, as_of 2026-09-09, not recomputed -- DRAM's unresolvable quote blocked a full rescoring pass): overall 36.4% (n=33); BUY 62.5% (n=16, avg +2.89%) vs TRIM/SELL 14.3% (n=14, avg -14.47%) vs HOLD 0.0% (n=3); 4 rows quarantined for anchor review. Today's IDEA panel is TRIM-heavy (4 catalyst_threat trims) sitting in the desk's historically weakest bucket -- sized small (20% trim_fraction) accordingly, and the one fundable BUY (KLAC via MSFT rotation) should carry at least equal weight in the user's own read.",
 "deemphasize_buckets":["TARGET GAP","MOMENTUM+VOLUME"],
 "data_quality":["cash 2.71% below 5% policy floor as of 14:36Z -- all standalone BUY ideas (GOOG/AMAT oversold_reversion, KLAC/NVDA/APH trend_entry, CIEN/APH/AMAT/GOOG conviction_average) price at $0 suggested size, clamped_by deployable cash","AMAT carries three simultaneous, contradictory live triggers (catalyst_threat TRIM, oversold_reversion BUY, conviction_average BUY) -- flagged, not resolved as a formula","LRCX and SKHY catalyst_threat trims both fight their own rotation accumulate-bucket status on a strengthening thesis -- both sized small and flagged","VST has no live RSI/ATR/beta this run -- excluded from trigger screens by data quality, not by judgment","hit-rate table and scorecard both carried forward from the 07:51Z run / proposals.json as-of stamp, not recomputed this refresh per dispatch instructions"]}
```

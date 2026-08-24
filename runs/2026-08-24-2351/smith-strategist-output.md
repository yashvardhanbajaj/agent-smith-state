# Agent Smith — Portfolio Strategist (scoped run, 2026-08-24)

Scope: TASK 2 sized proposals only (TASK 3-6 skipped per dispatch). This is the first live run of the 2026-08-24 conviction-driven trigger rebuild. Thesis/signal inputs are cached as of last deep review, not freshly re-verified today — flagged per-proposal where relevant.

Cash context: book cash 30.08% vs normal band 5-15% (post-stop-event regime, 4 sessions since the 08-18 stop-out); `deployable_cash_for_ideas_usd` = $10,363.42. `risk_off_status` = normal. Ample room to fund the buys below without a cash-band conflict.

## Proposals

**1. REENTRY — BUY NVDA — $399.42 @ $210.18** (stop $193.87)
Cleared the reentry bar the same day it was exited (2026-08-24). Thesis strengthening (unverified, 1-for/0-against), +44.1% vs analyst target, surprise history +4.61% avg (print pending). Sized off target weight per `reentry` mechanics (suggested_size_usd copied verbatim, no clamp). Note: thesis tag is unverified — treat conviction score (42.5, low tier) as the primary basis, not the qualitative thesis claim alone.
`evidence_quality: {"verified":0,"computed":1,"unverified":1}`

**2. REENTRY — BUY SKHY — $124.08 @ $156.31** (stop $117.26)
Exited and re-cleared same day. Thesis strengthening (unverified, 2-for/1-against — contested, not lead evidence). Cluster AI Memory/Storage. Sizing copied verbatim from `suggested_size_usd`, no clamp.
`evidence_quality: {"verified":0,"computed":1,"unverified":1}`

**3. PROFIT_ROTATION (paired) — SELL MSFT $434.90 @ market / BUY CLS $216.75 @ $296.54** (pair_id profit_rotation-MSFT-CLS)
MSFT is stretched (in `names_stretched`) carrying only a watch thesis — real profit to book, not an ATR-cap reflex. CLS is a -3.7pp laggard with a strengthening thesis (unverified) yet to rally — buy leg's own conviction score 35.0 (low tier), stop $254.14. Rendered and retired as one decision. Both theses are unverified qualitative tags; the pairing itself rests on computed drift/rotation data (stretched-cohort membership, relative-strength gap), which is the verified leg of the evidence.
`evidence_quality: {"verified":0,"computed":1,"unverified":2}`

**4. CLUSTER_ROTATION (paired) — SELL AMD $283.94 @ market / BUY TER $283.94 @ $375.73** (pair_id cluster_rotation-AMD-TER, cluster AI Semis/Fabs)
AMD is the cluster laggard (-11.3pp) on a watch thesis with a **secondary-verified** evidence base: Q3 guide read below consensus, a $5B debt raise that levers the balance sheet, and — directly on point — the strategist's own 2026-08-15 ruling of HOLD/no-further-adds on AMD. This proposal only sells AMD, so it's consistent with that prior ruling rather than contradicting it. TER is the cluster's relative-strength leader (+7.5pp) with a strengthening (unverified) thesis, conviction 27.9, stop $307.20. This is the strongest-evidenced proposal in this batch.
`evidence_quality: {"verified":1,"computed":1,"unverified":1}`

**5. CATALYST_THREAT — TRIM AVGO — $294.75 @ $368.44** (trim_fraction 0.2, cap-independent)
Broadcom in talks for a $70-80bn AI-financing debt SPV (Blackstone/Apollo, backstopping Anthropic compute), building on the June $35bn platform; BofA's stress ceiling is $370bn in senior debt by 2029 against AVGO's own on-balance-sheet debt of just $83.7bn (08-17 WSJ baseline). AVGO's thesis carries this as evidence_against already (BofA bond-rating downgrade over the same XPV exposure), and since BX's 08-17 exit AVGO now carries the exposure alone. Trigger fires independent of any ATR-cap breach, per design. Data quality note: AVGO's thesis object itself is tagged unverified overall, but the catalyst is sourced to a live URL and is the computed trigger basis — sizing rests on the computed trim_fraction, not the thesis label.
`evidence_quality: {"verified":0,"computed":1,"unverified":1}`

## Skipped / considered and passed over
- **BX catalyst_threat trim** ($286.75) — same underlying AVGO/XPV catalyst, but BX is already the sell leg of `profit_rotation-BX-AMAT`. Running both would double-count one thesis event into two separate sell actions on the same name; the profit_rotation pairing is the more complete decision (sells BX AND redeploys into AMAT), so it's preferred. Not included as a 6th proposal.
- **profit_rotation-FLTW-QCOM** and **profit_rotation-NOW-META** — both live and well-formed, but held back to keep this batch inside the 5-idea dashboard cap; FLTW-QCOM and NOW-META are lower conviction (30.4 and 24.6) than the four included ideas plus the two reentries. Worth surfacing on the next run if cash remains undeployed.
- **conviction_average GLW/AMAT/AMZN/WDC** (5 more live rows) — not elevated individually since three of the five (MSFT-CLS→CLS, BX-AMAT→AMAT) already ride into this batch via the rotation pairs; standalone AMZN ($501.53, conviction 31.6) is the next-best candidate if more ideas are wanted.
- **entry_setup QBTS/RGTI** — live but conviction low-tier (20.8/20.0) and RGTI is blocked on missing live price/ATR this run; not sized.
- **trend_breakdown BABA** — live TRIM signal (conviction -0.8, "none" tier) on a watch thesis with a genuine EPS miss; excluded here only for batch-size reasons, not evidence quality — flagging for next run.

## Data quality
- RSI14 and 1m relative-strength caches are 12 days old (>10d threshold) — `oversold_reversion`/`overbought_distribution` structurally suppressed this run, not zero-signal.
- Thesis/signal inputs reused from last deep review per dispatch instructions — not freshly re-verified today. Most cited theses carry `verified: unverified`; only AMD and META in this batch carry secondary verification.
- RGTI entry_setup has no live price/ATR this run (blocker noted, not sized).

```json
{"policy_draft":null,
 "proposals":[
  {"action":"BUY","ticker":"NVDA","size_usd":399.42,"price_at_proposal":210.18,
   "rationale":"Reentry — cleared bar same-day as exit (2026-08-24); thesis strengthening (unverified); +44.1% vs analyst target; sized off target weight per reentry mechanics, no clamp.",
   "trigger_type":"reentry","trigger_bucket":"live","pair_id":null,"pair_role":null,
   "size_wanted_usd":399.42,"clamped_by":null,"stop_price_usd":193.87,"exited_on":"2026-08-24",
   "evidence_quality":{"verified":0,"computed":1,"unverified":1}},
  {"action":"BUY","ticker":"SKHY","size_usd":124.08,"price_at_proposal":156.31,
   "rationale":"Reentry — cleared bar same-day as exit; thesis strengthening but contested (2 for/1 against, unverified); sized verbatim off suggested_size_usd, no clamp.",
   "trigger_type":"reentry","trigger_bucket":"live","pair_id":null,"pair_role":null,
   "size_wanted_usd":124.08,"clamped_by":null,"stop_price_usd":117.2638,"exited_on":"2026-08-24",
   "evidence_quality":{"verified":0,"computed":1,"unverified":1}},
  {"action":"SELL","ticker":"MSFT","size_usd":434.90,"price_at_proposal":null,
   "rationale":"Profit rotation sell leg — stretched (names_stretched) with only a watch thesis; real profit to book, paired with CLS buy.",
   "trigger_type":"profit_rotation","trigger_bucket":"live","pair_id":"profit_rotation-MSFT-CLS","pair_role":"sell",
   "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
   "evidence_quality":{"verified":0,"computed":1,"unverified":2}},
  {"action":"BUY","ticker":"CLS","size_usd":216.75,"price_at_proposal":296.5422,
   "rationale":"Profit rotation buy leg — laggard (-3.7pp) with strengthening (unverified) thesis, yet to rally; conviction 35.0 low tier.",
   "trigger_type":"profit_rotation","trigger_bucket":"live","pair_id":"profit_rotation-MSFT-CLS","pair_role":"buy",
   "size_wanted_usd":216.75,"clamped_by":null,"stop_price_usd":254.1367,"exited_on":null,
   "evidence_quality":{"verified":0,"computed":1,"unverified":2}},
  {"action":"SELL","ticker":"AMD","size_usd":283.94,"price_at_proposal":null,
   "rationale":"Cluster rotation sell leg — cluster laggard (-11.3pp), watch thesis with secondary-verified evidence (guide below consensus, leveraged debt raise, strategist's own 08-15 no-further-adds ruling); dead money in AI Semis/Fabs, rotate to the cluster's performer.",
   "trigger_type":"cluster_rotation","trigger_bucket":"live","pair_id":"cluster_rotation-AMD-TER","pair_role":"sell",
   "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
   "evidence_quality":{"verified":1,"computed":1,"unverified":0}},
  {"action":"BUY","ticker":"TER","size_usd":283.94,"price_at_proposal":375.7302,
   "rationale":"Cluster rotation buy leg — cluster's relative-strength leader (+7.5pp) with strengthening (unverified) thesis; conviction 27.9 low tier.",
   "trigger_type":"cluster_rotation","trigger_bucket":"live","pair_id":"cluster_rotation-AMD-TER","pair_role":"buy",
   "size_wanted_usd":283.94,"clamped_by":null,"stop_price_usd":307.197,"exited_on":null,
   "evidence_quality":{"verified":1,"computed":1,"unverified":0}},
  {"action":"TRIM","ticker":"AVGO","size_usd":294.75,"price_at_proposal":368.4404,
   "rationale":"Catalyst threat, cap-independent — Broadcom's $70-80bn AI-financing debt SPV (Blackstone/Apollo, backstops Anthropic compute) vs $83.7bn own on-balance-sheet debt; BofA stress ceiling $370bn; AVGO now carries this exposure alone since BX's 08-17 exit. Trim fraction 0.2 per compute layer.",
   "trigger_type":"catalyst_threat","trigger_bucket":"live","pair_id":null,"pair_role":null,
   "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
   "evidence_quality":{"verified":0,"computed":1,"unverified":1}}
 ],
 "scorecard_read":null,
 "deemphasize_buckets":[],
 "data_quality":["RSI14/rel-strength caches 12d old (>10d threshold) -- oversold_reversion/overbought_distribution structurally suppressed this run","thesis/signal inputs reused from last deep review, not freshly re-verified today per dispatch scope","RGTI entry_setup has no live price/ATR this run -- setup valid but not sized","TASK 3 (risk-off), TASK 4 (stress table), TASK 5 (hit-rate), TASK 6 (scorecard) skipped per scoped dispatch"]}
```

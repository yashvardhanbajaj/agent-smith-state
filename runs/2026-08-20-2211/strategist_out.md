# Portfolio Strategist — 2026-08-20 (quick, intraday)

**CORRECTION CARRIED FORWARD.** The orchestrator's original brief cited AI-capex 75.30% and a Compute/Hyperscaler cluster breach of -10.74pt; both were classification artifacts (GOOG/META/WDC/NBIS/SKHY sat Unclassified). Re-run `compute_drift.json` is used throughout below: **AI-capex 88.155%** (above the pre-cascade 86.8%), **Compute/Hyperscaler 17.915% — IN BAND**, and **AI Memory/Storage is now the only cluster breach**, -7.368pt under its floor (7.632% vs [10,20] target 15%). Nothing about the risk-cap math, the four catalyst_threat triggers, or the drawdown changes.

## Policy draft
Not applicable — policy exists and is confirmed (`policy_confirmed: true`, no defects).

## Answering the six questions directly

**1. Is the book mis-risked, and what's the cheapest fix?**
Yes, on the volatility-budget axis specifically. Aggregate open ATR risk is 13.968% against a 10% cap — $5,842.81 of open risk on a $41,830.51 book, $1,659.76 over budget. Nine names carry their own cap breach: NVDA, TSM, GEV, VRT, COHR, BE, NBIS, MRVL, MU. There is no cash to fund a cure any other way, so this has to come from trims. The honest framing the orchestrator asked for: the $14,011 two-day deployment did **not** de-risk the book's factor concentration — AI-capex went from 86.8% to 88.155%, *above* the pre-cascade level, because GOOG/META/NBIS are demand-side AI-capex (hyperscalers buying the very capex chain the book already owns), not diversifiers. The only genuine non-AI-capex addition in the entire deployment is HOOD at 1.14% of book. Whether ~88% single-factor exposure is acceptable is a mandate call, not a math call — the policy caps AI-capex at 100%, so this isn't a policy breach, and the user has been explicit that this is meant to be an aggressive single-bet book. I'm not proposing to unwind the concentration; I'm proposing to cure the volatility-budget overshoot, which is a separate problem. Cheapest fix: trim the four names already flagged by a live, stock-moving catalyst (BE, GEV, VRT — see Q2) plus one discretionary cut on thesis quality (NBIS — see Q3). Those five trims pull roughly $2,000-2,050 of market value out of the most fragile names (derisk-queue ranks 1, 3, 4, 8) and meaningfully close the risk gap without touching the largest, best-supported positions (NVDA, TSM, MRVL, MU) beyond what's already proposed via P-125 and the profit_ratchet stop-raises.

**2. Four catalyst_threat triggers on GEV/VRT/BE/AVGO — priced in or reason to reduce?**
Reason to reduce, not fully priced. The WSJ $3T off-balance-sheet story broke 2026-08-17 and the power/cooling complex sold off same-day (GEV -6.90%, BE -9.97%, VRT -6.80%). Three of the four names were then *added to* on 08-19/08-20 during the redeployment — that's buying into a name the desk's own trigger engine still flags as under active structural threat, and it happened because the deployment was executed as a cash-clearing exercise, not a catalyst-aware one. The story itself hasn't resolved: it's a structural balance-sheet characterization (off-balance-sheet leases + purchase commitments, ~$1.2T/quarter growth) that plays out over quarters, not a one-day headline that decays. The compute layer's `retires_when` condition for all four is "no longer appears in a structural-threat factor catalyst" — that hasn't happened. I'd trim GEV/VRT/BE now (they're also individually over their ATR cap, so the trim does double duty) and trim AVGO too even though it isn't over cap — the catalyst is explicitly cap-independent by design (G56/2b), and AVGO sits comfortably inside its cap, which is exactly the "preferred candidate" case the trigger framework calls out.

**3. NBIS.**
This is the one I'd push back hardest on. Sequence: stopped out 08-18 at $259.90, re-entered 4sh at ~$217.88 two days later, then added 3sh more at ~$220.22 — now 7sh, $690.29 over its ATR cap (1.846x), thesis `watch` with an **empty evidence_for** and an explicit `evidence_against` reading "thesis untested against the stop-triggering move," down 3.91% today at $215.15. Per G58: an unverified thesis verdict resting on a discrete event doesn't outrank a computed breach — and here there isn't even a verdict to outrank anything with, just an acknowledged information gap. Re-entering after a stop is a legitimate call (whipsaw happens), but doubling that re-entry with a second add, past cap, with zero fresh evidence, on a name that's currently the worst-performing thing in the book today, is the discretionary-buy pattern the stored scorecard shows losing money (see Task 5/6 below — BUY accuracy is 20% on n=5). I'm proposing a trim back toward cap. This isn't a cap-mechanics trim dressed up — it's a thesis-quality call that happens to align with the computed breach, which is exactly the situation G58 says to size off the breach.

**4. NVDA into earnings (4 sessions) and MRVL (reports 08-27, position just raised 50%).**
NVDA: already covered by open proposal P-125 (trim $576, framed on earnings + extreme-greed regime, cap breach as size justification only) — still valid, still nearly exactly sized to today's $557.61 headroom deficit. I'm reaffirming it rather than duplicating it. MRVL is the sharper case: earnings 08-27 (7 days out), the position was raised 4sh→6sh in the last 48 hours (re-entry-after-stop per smith-ledger's correction), it's now 1.368x over cap, and today's `profit_ratchet` shadow trigger flags the stop ($193.69) sitting *below* breakeven ($198.47) on a name up 21.6%. The existing open proposal P-114 ("Trim MRVL scale-out rung," `scale_out_ladder`, $550.65, dated 08-17) no longer matches reality — today's trigger run shows zero `scale_out_ladder` hits, and the position P-114 was sized against has since changed (more shares added, which directly contradicts a standing trim call). I'd flag P-114 for review/likely dismissal and not simply carry it forward unexamined — see Task 5.

**5 & 6.** See the review and interpretation sections below.

## Sized proposals (5)

**1. TRIM BE — $321.17** (sell ~1.6sh at $200.73)
`catalyst_threat`, live. Worst-positioned name in the book on the derisk queue (rank 1, derisk_score 125.0, fragility 100.0) and the largest cap overshoot (2.168x, -$865.21 headroom). WSJ $3T off-balance-sheet story named BE explicitly; -9.97% on the 08-17 headline day. Thesis strengthening (unverified this run) — cited as context, not as the basis; the catalyst and the cap breach carry the size. 20% trim per the trigger's own sizing. Recently opened lot, no LTCG relevance.
`evidence_quality: {"verified":0,"computed":2,"unverified":1}`

**2. TRIM GEV — $381.95** (sell ~0.4sh at $952.515)
`catalyst_threat`, live. Same WSJ catalyst (-6.90% on 08-17), 1.247x over cap. Thesis strengthening (unverified this run, supporting only).
`evidence_quality: {"verified":0,"computed":2,"unverified":1}`

**3. TRIM VRT — $363.26** (sell ~1.4sh at $259.47)
`catalyst_threat`, live. Same catalyst (-6.80% on 08-17), 1.567x over cap, thesis `watch`.
`evidence_quality: {"verified":0,"computed":2,"unverified":1}`

**4. TRIM AVGO — $291.12** (sell ~0.8sh at $363.90)
`catalyst_threat`, live, **cap-independent** — AVGO sits at 0.576x cap, comfortably inside it. Same WSJ catalyst; the trigger design deliberately doesn't gate a profit-take on a breach, and a name inside its cap is the *preferred* candidate here, not a marginal one — flagging that explicitly so this doesn't read as a breach cure. Cluster (AI Networking/Optics) is in-band; no cluster tension. This supersedes the stale open P-121 ($152, sized before the position/headroom moved) — recommend dismissing P-121 in favor of this fresh, larger, trigger-matched size.
`evidence_quality: {"verified":0,"computed":1,"unverified":1}`

**5. TRIM NBIS — ~$645 (3 of 7sh at $215.15)**
No formal live trigger fired (RSI 54.3 neutral, no thesis_break — verdict is `watch`, not `broken`). Discretionary, sized off the computed cap breach ($690.29 deficit) per G58, since the thesis carries an empty evidence_for and an explicit "untested against the stop-triggering move" — a genuine information gap, not a verified view either way. Nearest whole-share sizing (3sh) unwinds the second, less-justified add while keeping the first re-entry position open (thesis stays live, just smaller). Down -3.91% intraday; recently opened lots, no LTCG relevance.
`evidence_quality: {"verified":0,"computed":2,"unverified":1}`

Combined, these five trims pull roughly $2,002 out of the five most fragile/threatened names on the derisk queue (BE #1, COHR-adjacent territory, NBIS #3, VRT #4, and AVGO by catalyst) without touching NVDA, TSM, MRVL, MU beyond what's already open (P-125, profit_ratchet stop-raises). Rough risk-budget effect: applying each name's own stop-distance% to its trim (BE 28.24%, GEV 13.66%, VRT 18.04%, AVGO 8.28%, NBIS 25.64%) removes on the order of $310-330 of open ATR risk — a partial cure, not a full one, consistent with the standing tranche/no-one-shot stop-loss style. It does not fully close the $1,659.76 gap; MSFT (P-119, still valid) and NVDA (P-125, still valid) sit alongside these as the other open levers.

## Review of open proposals (Task 5)

| ID | Action | Status today | Recommendation |
|---|---|---|---|
| P-028 | ASML trim-watch (07-29) | Stale — ASML shows STRONG UPTREND now, not the STRONG DOWNTREND this was written against; not over cap (0.0x) | **Dismiss** — three weeks stale, signal reversed |
| P-104 | Raise MU stop (profit_ratchet, 08-17) | MU is now down -4.73% on the month, not up 15.4% — the gain the stop-raise was protecting may no longer exist; MU doesn't appear in today's profit_ratchet list at all | **Flag for review** — premise likely stale, re-check MU's current gain/basis before treating as live |
| P-114 | Trim MRVL scale-out rung (`scale_out_ladder`, 08-17, $550.65) | Today's triggers show zero `scale_out_ladder` hits; MRVL position was subsequently *increased* (4→6sh), directly contradicting an open trim call | **Flag for review/likely dismiss** — position facts have moved past this proposal; today's `profit_ratchet` stop-raise (MRVL, shadow) is the current live signal, not this |
| P-117 | Raise TER stop (profit_ratchet, 08-17) | TER still up (+8.28% 1m), thesis strengthening, `STRONG UPTREND`+`PEER LEADER`, zero capital | **Keep open** — still valid |
| P-119 | Trim MSFT (`overbought_distribution`, 08-19, $360) | Matches today's live trigger almost exactly ($362.50). RSI 78.8 caveat: sourced from the 2026-08-12 cache, 8 days stale — discounted accordingly, but the trigger still fired independent of the stale stretch score (abs return +24.7% this month is not stale) | **Keep open**, flag RSI staleness in the rationale |
| P-120 | Buy QCOM (`laggard_rotation` shadow, pair leg B of P-119, $360) | QCOM still laggard, within cap (headroom $310.92), self-funded from the MSFT sell leg — doesn't depend on the now-dead deployable cash | **Keep open** — pair still coherent |
| P-121 | Trim AVGO ($152, catalyst_threat, 08-19) | Superseded by today's larger, fresher-sized trigger ($291.12) | **Dismiss**, replaced by proposal 4 above |
| P-122 | Buy AMZN ($700, "Compute/Hyperscaler -7.17pt under floor") | **Dead premise** — Compute/Hyperscaler is now in-band (17.915% vs [15,25]) after the correction; the cluster hole this was written to fill no longer exists. Also unfunded (deployable cash is $0). | **Dismiss** |
| P-123 | Buy GLW ($539, dip-in-cluster) | AI Networking/Optics already in-band; no funding source | **Dismiss** — unfunded, rationale weakened |
| P-124 | Buy IREN ($111, open_flag re-entry) | No funding source; modest size doesn't change that | **Dismiss** — hold as a watch note until an actual cash event, not an open proposal |
| P-125 | Trim NVDA ($576, earnings+regime framing, 08-19) | Still valid — NVDA earnings 08-26 (4 sessions), extreme_greed unchanged, headroom deficit now $557.61 (essentially matches the proposed size) | **Keep open**, reaffirmed |

Net: three buys (P-122/123/124) are recommended for dismissal because their funding premise (deployable cash) is now zero and, for P-122 specifically, the cluster breach it cited no longer exists post-correction. Two trims (P-121, superseded; P-028, stale) recommended for dismissal/replacement. Two profit_ratchet stop-raises (P-104, P-114) flagged for review because the underlying gain/position facts have moved. Three (P-117, P-119/P-120 pair, P-125) stand unchanged.

## Risk-off status
`risk_off_status: normal` per compute_drift.json — drawdown is -6.78% against a -25% risk-off trigger, well inside bounds. This is **not** a risk-off situation in the policy's terms, but the ATR aggregate-risk breach (13.968% vs 10%) is a real, independent signal that doesn't need risk-off framing to justify the trims above — it's a volatility-budget problem, not a drawdown-trigger problem, and I've treated it as such rather than manufacturing urgency it doesn't carry. LTCG check: earliest open lot is 2026-07-15 (per the orchestrator's brief), boundary mid-2028 — no live LTCG deferrals apply to any trim above; all are short-term lots regardless.

One flag worth surfacing since it echoes a precedent: HOOD (1.14%, `watch`) has **no policy cluster that honestly fits** and is sitting Unclassified pending a user decision. The identical situation with IONQ was opened 2026-08-17 and never resolved before IONQ was stopped out — the decision window closed itself. Recommend the user either assign HOOD a cluster/band or explicitly decide to leave it perpetually unclassified, rather than let it default the same way again.

## Stress table (approximate — macro desk did not run this cycle)

`smith-macro` is deep-mode-only and this is a quick run, so there's no live Fed/10-yr regime read to anchor the rate-sensitive rows to. The table below is a static approximation from clusters/betas/weights only — labelled as such, not decision-grade for sizing.

| Scenario | Est. impact | Most exposed |
|---|---|---|
| AI-capex pause | ~-15% to -18% ($6,300-$7,500) | GEV, VRT, BE (power/cooling, most catalyst-sensitive already), NVDA, TSM, MRVL, AVGO, COHR — essentially the 88% AI-capex sleeve |
| Rates +100bp | ~-8% to -12% ($3,300-$5,000) | MSFT, NOW (long-duration software multiples), NVDA, TER (high-multiple semis), GEV/VRT/BE (financing-dependent capex build-out) |
| Tariff/export-control escalation | ~-5% to -7% ($2,100-$2,900) | TSM, ASML, AMAT, LRCX, NVDA (China/Taiwan-exposed fabs & equipment), BABA (0.6%, direct China exposure) |
| USD/INR ±3% | ≈0% on the USD-reported book. In INR terms: a 3% INR depreciation (USD/INR up) raises the book's INR-equivalent net worth by ~3%; INR appreciation lowers it by ~3% — this is a currency-translation effect on net worth, not a book P&L effect. | N/A — book-wide, currency-driven |

## Hit-rate readout (from compute_journal.json, precomputed — not recalculated here)

- **TARGET GAP: 31.2% (n=16)** — below the 40% de-emphasis line over ≥5 entries. **Recommend de-emphasizing this bucket** as a standalone conviction source going forward.
- **MOMENTUM+VOLUME: 50.0% (n=4)** — under the n=5 threshold for a de-emphasis call; no action, just noting it's roughly coin-flip on a small sample.
- OVERSOLD BOUNCE (n=1) skipped — below the n=3 floor.

## Interpretation of the stored proposal-outcome scorecard (n=8, do not recompute)

`smith_math.py score` has already written: overall 25.0% (n=8, 2 worked / 5 missed / 1 neutral, avg -3.54%). By direction: TRIM 100% (n=1, +7.5% avg benefit), BUY 20% (n=5, -4.35% avg benefit), HOLD 0% (n=2, -7.02% avg benefit). 71 proposals are still under 30 days and not yet in the scoring window — this is a very early read.

n=8 is too small to treat as a verdict on the desk's judgment, and the TRIM "100%" figure is a single data point, not a pattern — it would be a mistake to read it as "trims always work." What the sample does support, directionally and consistent with the user's standing complaint about cap-mechanics-driven proposals: **discretionary BUYs are the weak link** (4 of 5 missed, -4.35% average). That's relevant to today specifically because I'm proposing zero BUYs — deployable cash is $0 and sentiment is extreme_greed, both of which independently argue against new BUY proposals right now, and the scorecard gives a third, weaker but consistent reason not to force one. It also bears on the P-122/123/124 dismissals above: those were discretionary dip-buys of exactly the type the record shows underperforming, now additionally unfunded. I'd weight this as a soft prior, not a rule, until the sample grows past the 71 still-pending proposals.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"TRIM","ticker":"BE","size_usd":321.17,"price_at_proposal":200.73,"rationale":"catalyst_threat (live): WSJ $3T off-balance-sheet AI-commitments story named BE explicitly, -9.97% on the 08-17 headline day; also worst derisk-queue rank (1, score 125.0) and largest cap overshoot in book (2.168x, -$865.21 headroom). Thesis strengthening cited as context only, not basis.","trigger_type":"catalyst_threat","trigger_bucket":"trim_risk_cap","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"GEV","size_usd":381.95,"price_at_proposal":952.515,"rationale":"catalyst_threat (live): same WSJ catalyst, -6.90% on 08-17; 1.247x over ATR cap. Thesis strengthening cited as context only.","trigger_type":"catalyst_threat","trigger_bucket":"trim_risk_cap","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"VRT","size_usd":363.26,"price_at_proposal":259.47,"rationale":"catalyst_threat (live): same WSJ catalyst, -6.80% on 08-17; 1.567x over ATR cap. Thesis watch.","trigger_type":"catalyst_threat","trigger_bucket":"trim_risk_cap","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"AVGO","size_usd":291.12,"price_at_proposal":363.90,"rationale":"catalyst_threat (live), cap-independent by design -- AVGO sits inside its cap (0.576x), which the trigger framework treats as the preferred, not marginal, candidate. Same WSJ catalyst. Cluster in-band, no tension. Supersedes stale P-121 ($152, pre-move sizing) -- recommend dismissing P-121.","trigger_type":"catalyst_threat","trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":1,"unverified":1}},
   {"action":"TRIM","ticker":"NBIS","size_usd":645.44,"price_at_proposal":215.145,"rationale":"No live trigger (thesis watch, not broken; RSI 54.3 neutral). Discretionary, sized off the computed $690.29 cap deficit per G58 since thesis has empty evidence_for and an explicit untested-against-the-stop-move evidence_against -- an information gap, not a verified view. 3sh (nearest whole-share) unwinds the second, less-justified 08-20 add while keeping the first re-entry open. Down -3.91% intraday.","trigger_type":null,"trigger_bucket":"trim_risk_cap","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}}
 ],
 "scorecard_read":"Stored scorecard (n=8, not recomputed): overall 25.0% (2 worked/5 missed/1 neutral, avg -3.54%); TRIM 100% (n=1, +7.5% avg -- single data point, not a pattern); BUY 20% (n=5, -4.35% avg -- the weak link); HOLD 0% (n=2, -7.02% avg). 71 proposals still under the 30-day scoring window. n=8 is too small for a verdict, but directionally supports zero BUY proposals this run -- consistent with $0 deployable cash and extreme_greed sentiment, which are the primary reasons, not the scorecard.",
 "deemphasize_buckets":["TARGET GAP"],
 "data_quality":["Corrected: AI-capex 88.155% (was misreported as 75.30% pre-correction), above pre-cascade 86.8% -- deployment increased single-factor concentration, did not reduce it","Corrected: Compute/Hyperscaler is now IN BAND (17.915%); AI Memory/Storage (-7.368pt) is now the sole cluster breach, with no live trigger and no cash to fund a cure -- flagged, not proposed","rel_strength_1m/rsi14 stamped 2026-08-12, 8 days stale; MSFT's RSI 78.8 (overbought_distribution) drawn from that stale cache -- trigger still honored since abs_return (+24.7%) is current, but stretch scoring generally discounted this run","smith-macro did not run (quick mode) -- stress table is a static approximation, not anchored to a live regime read","HOOD (1.14%) has no honest policy-cluster fit, left Unclassified pending user decision -- same unresolved-flag pattern as IONQ on 08-17, which was stopped out before the decision was made","P-104 (MU profit_ratchet stop-raise) and P-114 (MRVL scale-out trim) both rest on premises (gain size / position size) that appear to have moved since 08-17 -- flagged for review, not carried forward as-is","beta missing for WDC and HOOD (2 held names) per compute_risk.json -- excluded from aggregate risk beta context"]}
```

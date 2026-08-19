# Agent Smith — Portfolio Strategist, 2026-08-19 (quick, post-cascade)

Policy is confirmed (as_of 2026-08-06) — no bootstrap needed. This run follows the largest stop-loss cascade the book has had: 10 of 11 position changes on 2026-08-18 were `Order Type: stop` firing inside SMH's -4.09% session (MRVL, AVGO, MU, TER cut; ARM, DRAM, IONQ, NBIS, ORCL, SKHY fully exited); SNDK was a deliberate Monday sell. That is the tight-large-quantum stop discipline working as designed, not a judgment call to relitigate.

Book: 28 names · equity $29,936.60 · cash $12,282.25 (29.09% vs [5,15]% band) · total book $42,218.85 · drawdown -5.915% from $44,873.02 peak · aggregate open ATR risk 8.626% vs 10% cap · sentiment **extreme_greed** (urgency 1.25x).

**Orchestrator correction applied**: Tuesday's proximate cause is treated as UNRESOLVED for rates (30Y fell 2.4bp, 10Y fell 1.8bp that day — no rate shock occurred). The best-evidenced named trigger is the WSJ 2026-08-17 $3T off-balance-sheet AI-commitment report (structural, affects AVGO/GEV/BE/VRT = 14.78% of equity). "Rates spiked Tuesday" is not used as a rationale anywhere below.

**Stretch-cache caveat honoured**: `names_stretched` and RSI values are stamped 2026-08-12, 7 days and one -4.09% session stale. This makes COHR's "stretched" (+10.31% 1m cached) read backwards — it fell 12.75% Tuesday and its Q4 beat, so it is **not** treated as a distribution candidate below. MSFT's RSI 78.8 is the least-affected stale read since MSFT actually rose Tuesday (+0.27%), so it is the one overbought reading I still act on.

---

## 1. Proposal review — 14 open, 11 retired, 3 stand

The stop cascade zeroed or resolved most of last week's live proposals. Reviewed against today's book (28 held tickers) and today's compute:

| Proposal (date) | Verdict | Why |
|---|---|---|
| Hard stop ORCL @$139.14 (08-15) | **RETIRE** | ORCL fully exited by stop 08-18 — no position left |
| Raise MU stop to cost basis (08-17 AM) | **RETIRE** | MU's cap breach (2.167x) this was anchored to is resolved — MU now 0.418x cap, headroom +$654.51 after the stop cut it |
| TRIM ORCL $177.50 (08-17 PM, QCOM pair sell leg) | **RETIRE** | ORCL exited — pair's sell leg is dead |
| BUY QCOM $177.50 (08-17 PM, ORCL pair buy leg) | **RETIRE, replaced below** | Funding leg dead; QCOM's own laggard_rotation trigger still fires today — re-proposed fresh, funded differently (see #2) |
| TRIM SKHY $900 (08-17 PM) | **RETIRE** | SKHY fully exited by stop 08-18 |
| TRIM MU $500 (08-17 PM) | **RETIRE** | Same resolved cap breach as above; explicitly "mechanics-only, no live trigger" per its own text — exactly the proposal type the user has asked this desk to stop leading with |
| TRIM DRAM $450 (08-17 PM) | **RETIRE** | DRAM fully exited by stop 08-18 |
| TRIM SNDK $280 (08-17 PM) | **RETIRE** | SNDK fully exited (deliberate Monday sell) |
| TRIM MRVL $550.65 (08-17 PM) | **RETIRE** | MRVL was cut in the cascade; cap breach (1.468x) it cited is resolved — now 0.809x, headroom +$204.29 |
| STOP_RAISE SKHY (08-17 PM) | **RETIRE** | SKHY exited |
| STOP_RAISE TER (08-17 PM) | **RETIRE** | TER is now a $1.10 dust position (0.00273sh, confirmed by both compute_derisk and this run's signals data_quality) — the +15.9%-gain-at-risk premise no longer applies to a position this size |
| STOP_RAISE DRAM (08-17 PM) | **RETIRE** | DRAM exited |
| **Trim AVGO $318.58** (08-17, catalyst_threat) | **KEEP, resize** | AVGO wasn't in the stop cohort, still held, catalyst_threat is still live per fresh compute — but sized before Tuesday's move; fresh compute prices it at $152.00 (see #3) |
| **TRIM MSFT $359.69** (08-17, overbought_distribution) | **KEEP** | Still live, fresh compute reprices it at essentially the same $361.22 (see #1) |

Net: this run's proposal list below (7 items) supersedes the 3 survivors with today's numbers and adds the rest fresh.

---

## 2. Sized proposals

Cash math: **$5,949.42 deployable above band, $1,487.36 max single deploy.** The set below nets to roughly **$622 of net cash use** (trims add back $1,088, buys use $1,710) — deliberately not the full $5,949.42. Why the rest stays parked: (a) the pre-market gate is ESCALATING and confirmed **not downgraded**, one session after the largest cascade this book has had; (b) NVDA — 40.5% AI Semis/Fabs cluster, book's largest position — reports in 5 sessions; (c) AI Semis/Fabs is already over its own ceiling (40.52% vs [25,35]), so more capital there is unwanted regardless of cash; (d) smith-rebound itself excluded NVDA/TSM/QCOM/LRCX (`cluster_full`), GEV/BE (`risk_cap_exceeded`), and CLS (`broken_trend`) from further stage-in, and found homes for only $1,350 of the $5,949 — the screen didn't run dry from laziness, it ran dry because most of what's left over-cap or over-band. The July precedent (mass stop-out 07-24 → rally back; 07-28 crash → 07-30/31 rip) argues against panic-deploying the rest in one shot. **Recommendation: hold the remaining ~$5,300 as staged dry powder, revisit next run and specifically after NVDA's 08-26 print clears** — this is not idle cash management, it's tranche discipline per the user's own stop-loss-style preference (deploy staged around binary events, never in one shot).

### 1. TRIM MSFT — $360 · overbought_distribution, live
Price at proposal: $481.63. RSI14 78.8 (>70), +24.7% on the month — real gain, cap-independent (MSFT sits at 0.427x its own ATR cap, this is not a risk-cap trim). Compute/Hyperscaler cluster is -7.17pt under floor; no intra-cluster rotation target exists (every other Compute/Hyperscaler name has already run). Cited as tension only, not support — trim-anyway-and-deepen-underweight is the honest tradeoff here, not a third option. Pair leg A of a book-profit/rotate-to-laggard pair (pair_id `P-ROT-0819`).
`evidence_quality: {verified:0, computed:2, unverified:0}`

### 2. BUY QCOM — $360 · laggard_rotation, shadow
Price at proposal: $160.19. Bottom-quartile 1m relative strength (-6.7pp vs SMH — hasn't run), thesis strengthening, within ATR cap (headroom $359.82). Shadow trigger, not yet hit-rate validated — scored zero on trigger contribution regardless of this write-up. Sized to the smaller of MSFT's sell proceeds ($360) and QCOM's own headroom ($359.82) = $359.82. Pair leg B of `P-ROT-0819`. This is the book-profit-and-rotate pairing the desk has been asked to lead with, not a cap/cash mechanic.
`evidence_quality: {verified:0, computed:2, unverified:1}`

### 3. TRIM AVGO — $152 · catalyst_threat, live
Price at proposal: $380.00. BofA downgraded Broadcom's bond rating (Marketweight) over the XPV off-balance-sheet AI financing platform (Blackstone/Apollo, Anthropic compute) — stress-tested exposure up to $370bn, ~$42bn extreme-loss case (2026-08-11, now reinforced not superseded by the 08-17 WSJ $3T book-wide report). Cap-independent: AVGO carries $1,789 of headroom, not over cap. **Tension surfaced, not suppressed**: thesis is "strengthening" (real Q2 beat, 48% revenue growth) and AVGO's rotation bucket is currently null (not `accumulate`), so this does not hit the accumulate-vs-strengthening exclusion in 2d — proceed. Resized down from the prior $318.58 ask to the fresh 20%-of-position computed figure.
`evidence_quality: {verified:0, computed:2, unverified:2}` — two of three cited inputs are unverified narrative (BofA downgrade, WSJ report); computed RSI/headroom data anchors the size. Flagging per the evidence gate rather than treating the narrative as proven.

### 4. BUY AMZN — $700 · rebound stage-in
Price at proposal: $259.45. Compute/Hyperscaler is -7.17pt under its floor. Ample ATR headroom ($1,859), dip only -0.7%, support at $256.39/$248.62. Not earnings-adjacent, thesis strengthening (Q2 beat, capex raised to $220B — unverified tag, supporting only).
`evidence_quality: {verified:0, computed:2, unverified:1}`

### 5. BUY GLW — $539 · rebound stage-in
Price at proposal: $159.90. AI Networking/Optics is in-band (12.81%) so this isn't a floor cure — sized on dip-in-line-with-peer-median and support at $151.83/$139.01. Thesis strengthening (Q2 core EPS +30%, Truist upgrade — unverified tag).
`evidence_quality: {verified:0, computed:2, unverified:1}`

### 6. BUY IREN — $111 · rebound stage-in
Price at proposal: $42.00. Thin ATR headroom ($110.87 — this is essentially the position's own cap ceiling, hence the small size), support at $39.30. Standing re-entry interest from the 08-12 open_flag remains open and this satisfies it modestly rather than chasing.
`evidence_quality: {verified:0, computed:2, unverified:1}`

### 7. TRIM NVDA — $576 · earnings risk-management (not a mechanics-only cap trim)
Price at proposal: $219.74. NVDA is the book's largest position (11.01%, inside the 12% single-name cap but the largest overweight/breach name in the book) sitting 1.212x its ATR risk cap (-$575.81 headroom, computed) inside a cluster (AI Semis/Fabs, 40.52%) that is itself over its ceiling (+10.52pt, computed) — trimming here cures a real cluster overage rather than fighting one. Reports in 5 trading days (2026-08-26, **verified** via live stockanalysis.com check 2026-08-19, matches cache). Sentiment reads extreme_greed (computed) — per the desk's own greed-regime rule, lead profit-booking with the largest overweight/breach name, which this is. This is deliberately framed around the earnings binary and the extreme-greed regime, with the cap breach as size justification, not the lead reason — the standing complaint against pure ATR-cap trims is honoured, not overridden. Thesis remains strengthening/STRONG UPTREND; this is a partial trim to cap, not a thesis call.
`evidence_quality: {verified:1, computed:3, unverified:0}`

---

## 3. Re-entry question: AI Memory/Storage

Cluster is at 1.57% against a [10,20] floor (-13.43pt) — effectively liquidated. Thesis says stopped-out-not-broken (MU's WATCH was always CXMT-capacity-driven, not ASP; HBM3E flat within basis through 08-05; 2027 HBM contract forecasts +80-150% unchanged). Rebound says stay out this week on all 11 exited/trimmed names.

**One recommendation, with the condition attached: honour the stay-out through this week; do not re-enter Memory/Storage this run.** The floor breach is real but it is one session old — re-entering into a name that just triggered a stop, in the same week, with the exact same book-level setup (85%+ AI-capex, tight stops) that produced Tuesday's cascade, is the specific pattern rebound's rule exists to prevent. Revisit at the next run using MU (still held, thesis intact, not fully exited) as the natural vehicle rather than re-adding SNDK from zero — MU already carries the cluster's live thesis and needs no new-position decision. Size any re-entry in a tranche, not the $600-800 that a floor-cure calculation alone would suggest, given the ATR-cap history on this specific cluster (MU/SNDK/DRAM were 3 of the largest cap-breach proposals of the last two weeks).

## 4. NVDA into earnings — view

See proposal #7 above for the sized action. The one-line view: strengthening thesis, STRONG UPTREND, no live distribution trigger fired (RSI14 62.2, well under the 70 overbought threshold — this is not an overbought_distribution case), but it is the largest position in an over-ceiling cluster, running a real $575.81 cap excess, five sessions from a confirmed print, inside an extreme-greed regime. That combination is worth a partial trim back toward cap ahead of the print — not a thesis downgrade, not a full exit, and not framed as a cap-mechanics trim in isolation.

## 5. BABA — earnings tomorrow (2026-08-20, confirmed)

**No action merited.** Position is $256.30 / 0.79% of equity — below the book's own $400 dust threshold (friction_score 30 in the derisk queue). No live or shadow trigger fires for BABA in today's compute (not in oversold/overbought/catalyst/thesis_break, RSI14 58.0 — neutral). An earnings event on a sub-1%-weight position is immaterial to book risk either direction; sizing any action around it would be manufacturing activity the position doesn't warrant. The open_flags earnings-date conflict (08-20 FMP vs 08-28 cached web) is now resolved — 08-20 confirmed correct via live stockanalysis.com check; close that flag.

## 6. Risk-off status

`risk_off_status: normal`. Drawdown -5.915% against a -25% risk-off trigger (and an 8%/12% warn/risk-off drawdown ladder per policy — worth noting -5.915% is inside even the 8% warn line). No defensive posture required; normal deployment discipline applies, which is what proposals 1-7 reflect.

## 7. Stress table (approximate, static — smith-macro did not run this quick pass)

This is a quick sweep; the macro desk (deep-only) did not run, so there is no live Fed/10-yr regime read to anchor the rate-sensitive rows. Falling back to static beta/cluster assumptions as instructed, flagged accordingly.

| Scenario | Est. impact | Most exposed |
|---|---|---|
| AI-capex pause | -13% to -16% of total book (86.8% of equity is AI-capex, avg cluster beta well above 1) | NVDA, GEV, COHR, BE, TSM (top 5 of the derisk queue by fragility) |
| Rates +100bp | -6% to -9% on AI Power/Cooling/DC Infra (14.9% equity, debt/capex-funded growth) plus -3% to -5% broader semis multiple compression. **No live macro read this pass — static assumption only.** Amplified for GEV/BE/VRT/CEG/AVGO by the WSJ $3T off-balance-sheet financing overlay (structural, independent of a rate shock) | GEV, BE, VRT, CEG, COHR |
| Tariff/export-control escalation | -8% to -10% of total book (AI Semis/Fabs is 40.5% of equity and directly exposed: Taiwan fab dependence, export licensing) | TSM, ASML, NVDA, AMD, LRCX |
| USD/INR ±3% | ≈0% on the USD-reported book itself. In INR terms: a 3% INR depreciation raises the book's INR-value net worth by ~3%; a 3% INR appreciation lowers it by ~3%. Not a book risk, a currency-translation effect on net worth. | n/a |

## 8. Hit-rate readout (journal script, not recomputed)

Buckets with ≥3 scored entries: **TARGET GAP** n=15, 46.7% hit rate. **MOMENTUM+VOLUME** n=4, 50.0% hit rate. (OVERSOLD BOUNCE n=1, skipped — under the 3-entry floor.) Neither clears the de-emphasis bar (below 40% over ≥5 entries), so no bucket is recommended for de-emphasis this run. Separately, and this matters for how to read today's own output: this run's signals scan flagged TARGET GAP on 25 of 28 names — that is mechanical (stale analyst targets book-wide after Tuesday's drop), not fresh conviction, and none of today's 7 proposals above cite TARGET GAP as a rationale.

## 9. Scorecard interpretation (stored, not recomputed)

`smith_math.py score` last ran 2026-08-04 and wrote: overall accuracy 12.5% on **n=8** scored proposals (TRIM 0% n=1, BUY 20% n=5 avg -1.48%, HOLD 0% n=2 avg -4.93%, overall avg -1.95%). 60 proposals are still under the 30-day scoring window and are not yet judged either way — this is not a verdict on the desk's current method, it is an early read on n=8 with a large unscored backlog behind it, most of it generated after the trigger-framework change (2026-08-17) this run is operating under. Practical read: treat the desk's own historical hit rate as **not yet informative** — it's too small a sample, pre-dates the current trigger discipline, and should not be used to size confidence up or down on today's 7 proposals. Worth re-running `score` again once a meaningful slice of the post-08-17 trigger-typed proposals clears 30 days; that's the sample that will actually test this framework.

```json
{"policy_draft":null,
 "proposals":[
  {"action":"TRIM","ticker":"MSFT","size_usd":360,"price_at_proposal":481.63,"rationale":"RSI14 78.8 (>70), +24.7% 1m -- real gain, cap-independent (0.427x cap). Compute/Hyperscaler -7.17pt under floor cited as tension only, no intra-cluster rotation target exists. Pair leg A, book-profit/rotate-to-laggard.","trigger_type":"overbought_distribution","trigger_bucket":null,"pair_id":"P-ROT-0819","pair_role":"sell_leg","evidence_quality":{"verified":0,"computed":2,"unverified":0}},
  {"action":"BUY","ticker":"QCOM","size_usd":360,"price_at_proposal":160.19,"rationale":"Bottom-quartile 1m rel strength (-6.7pp vs SMH), thesis strengthening, within cap (headroom $359.82). Shadow trigger, scored zero on trigger contribution. Sized to smaller of MSFT sell proceeds and QCOM headroom. Pair leg B.","trigger_type":"laggard_rotation","trigger_bucket":null,"pair_id":"P-ROT-0819","pair_role":"buy_leg","evidence_quality":{"verified":0,"computed":2,"unverified":1}},
  {"action":"TRIM","ticker":"AVGO","size_usd":152,"price_at_proposal":380.00,"rationale":"BofA bond downgrade over XPV off-balance-sheet AI financing (2026-08-11), reinforced by 08-17 WSJ $3T report. Cap-independent, $1,789 headroom. Tension surfaced: thesis strengthening, rotation bucket currently null (not accumulate) so no 2d exclusion applies. Resized down from prior $318.58 ask to fresh 20%-of-position compute.","trigger_type":"catalyst_threat","trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":2}},
  {"action":"BUY","ticker":"AMZN","size_usd":700,"price_at_proposal":259.45,"rationale":"Compute/Hyperscaler -7.17pt under floor. Ample headroom ($1,859), dip only -0.7%, support $256.39/$248.62. Rebound stage-in.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
  {"action":"BUY","ticker":"GLW","size_usd":539,"price_at_proposal":159.90,"rationale":"AI Networking/Optics in-band; sized on dip-in-line-with-peer-median and support $151.83/$139.01. Rebound stage-in.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
  {"action":"BUY","ticker":"IREN","size_usd":111,"price_at_proposal":42.00,"rationale":"Thin ATR headroom ($110.87), support $39.30. Satisfies standing 08-12 re-entry open_flag modestly rather than chasing. Rebound stage-in.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
  {"action":"TRIM","ticker":"NVDA","size_usd":576,"price_at_proposal":219.74,"rationale":"Largest position (11.01%), 1.212x ATR cap (-$575.81 headroom) inside an over-ceiling cluster (AI Semis/Fabs +10.52pt) -- trim cures real cluster overage. Earnings 2026-08-26 (5 sessions, verified via live check). Extreme-greed regime -> lead profit-booking with largest overweight name per policy. Framed on earnings + regime, cap breach as size justification only, not a mechanics-only trim.","trigger_type":null,"trigger_bucket":"trim_risk_cap","pair_id":null,"pair_role":null,"evidence_quality":{"verified":1,"computed":3,"unverified":0}}
 ],
 "scorecard_read":"Stored scorecard (as_of 2026-08-19, last scored 2026-08-04): overall 12.5% accuracy on n=8 (TRIM 0% n=1, BUY 20% n=5 avg -1.48%, HOLD 0% n=2 avg -4.93%, overall avg -1.95%). 60 proposals still under the 30-day window, unscored. Sample too small and too pre-dated (before the 08-17 trigger-framework change) to be informative about the desk's current method -- treat as not yet a verdict, re-run score once post-08-17 trigger-typed proposals clear 30 days.",
 "deemphasize_buckets":[],
 "data_quality":["11 of 14 open proposals retired this run: 8 because their tickers (ORCL, SKHY, DRAM, SNDK) were fully exited in the 08-18 stop cascade, 3 because the ATR-cap breach they were sized against (MU x2, MRVL) was itself resolved by the stop cutting the position. Full list and reasons in section 1 of the prose output.","TER is now a $1.10 / 0.00273sh dust position (confirmed independently by compute_derisk and this run's signals output) -- worth a cleanup decision (round to zero or hold as a rounding residual) outside this proposal set.","Stress table is static/approximate -- smith-macro (deep-only) did not run this quick pass, no live Fed/10-yr regime read available to anchor the rate-sensitive rows.","bucket_hit_rates read from compute_journal.json (present in the run directory though not in the read_these_files map) since it is the deterministic journal-script output this task requires -- not recomputed."]}
```

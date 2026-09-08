# Portfolio Strategist — 2026-09-08 (Deep, Wave 3)

Book: equity $39,606.56, wallet $2,703.02, total $42,309.58. Cash 6.39% (band-legal, but $0 deployable above floor — every buy below is a rotation leg). Aggregate open risk 9.894% vs 10% cap. AI-capex 95.42% of equity, no cluster breach. Drawdown -0.28%, risk_off **normal**. Third consecutive deep run on the same Friday 09-04 closes; this run's -$112.61 move is 100% FX, not price. No proposal below is sized off a signal already sized twice.

## Policy
Confirmed, valid, no defects. No bootstrap needed.

## Drift vs Policy
No position or cluster breaches. Tightest cluster ceiling room: AI Power/Cooling $255, AI Semis/Fabs $480, AI Networking/Optics $525. Compute/Hyperscaler sits on its 10% **floor** with $3,626 of room — the most in the book, and where cost-of-capital exposure (CPI 09-11, FOMC 09-15/16) concentrates because two of its four members (NBIS, IREN) rent capital rather than self-fund. AI-capex at 95.42% is 4.58pp under its 100% cap — not a breach, but there is no room to add capex exposure without trimming capex exposure first, mechanically.

Six names over individual ATR cap: GEV (1.535x), BE (1.6x), MRVL (1.106x, cap-exempt), TER (1.056x), NBIS (1.468x), COHR (1.26x). Per the 09-07 fix, cap alone is not actionable on a strengthening thesis with a bullish/net-signal-1 read and RSI≤70 — that rules out GEV and MRVL as trim candidates on cap mechanics (both `accumulate` bucket). BE and TER sit in `trim_risk_cap` (flat/no-tailwind signal) and remain legitimate cap trims if sized, but neither has a live trigger this run pushing for it, so I am not proposing either — flagged for monitoring only. NBIS and COHR are addressed below on non-cap grounds.

## Cluster Ladders — New This Run
Three ladders built (medium confidence → `rank` authority: ordering drives cluster_rotation, sell leg still needs a `watch` thesis).

- **AI Semis/Fabs** (leader TER, laggard INTC by WFE-spend share): replaces the prior price-driven AMD→NVDA pair with **Sell INTC → Buy KLAC**, ladder-driven. INTC is the only cluster member that is a net WFE *consumer* running negative economics (trailing EPS -$2.09, margin -19.8%). The still-open **P-237 (Sell AMD)** rests on AMD being the laggard — the ladder ranks AMD 8th of 10, not last, and its own tension note flags this. I am not creating a duplicate AMD proposal, but P-237's premise is now disputed by the newer, more granular ladder evidence; worth revisiting P-237 against INTC as the better-evidenced sell leg.
- **AI Networking/Optics** (leader LITE, laggard APH): the ladder explicitly does **not** endorse the still-open P-241/P-242 (Sell AVGO → Buy LITE). Intra-cluster AVGO is +5.19pp — second-best of seven, not a laggard — and its watch status is a financing-overhang/guide fact, not a competitive one (Q3: +86% revenue, AI semis +221% YoY). The trigger engine re-emitted the same Sell AVGO → Buy LITE pair this run at `ladder_driven: false` only because no ladder-ranked sell leg qualified (APH and CIEN are both `strengthening`) — it fell back to the stale price rule and reproduced the trade the ladder disputes. **I am not proposing a new AVGO/LITE leg and flag P-241/P-242 for reconsideration**: the buy leg (LITE) still has ladder support as cluster leader, but the sell leg's stated rationale (AVGO as laggard) does not survive the ladder's own ranking.
- **Compute/Hyperscaler**: partial ranking (2 of 4 members). MSFT ranked 1st carries a `watch` thesis with an *empty* evidence_against array — genuine ambiguity, not a contradiction to resolve here. NBIS is the cluster's largest position (3.97%) and lowest-ranked member, over cap at 1.47x, and now the book's second-highest-beta name (2.317) with CPI/FOMC five sessions out. That combination (largest + weakest-ranked + over cap + high-beta + cost-of-capital catalyst window) is a legitimate risk-reduction case independent of the disputed cluster mechanics — see proposal below.

Two new shadow triggers logged, not sized: `cluster_bench_rotation` INTC→AMKR (never-held name, track before sizing), `cluster_consolidation` COHR→LITE (ladder judges these one bet — same InP/EML constraint, same $2bn NVDA tie, same catalyst calendar, 4.76% of equity expressed twice; worth a future single-name consolidation review, not a trade today).

## Risk-Off Read
`risk_off_status: normal`. No forced defensive posture. Two things temper that read: (1) catalyst returned zero new events over the long weekend — `factor_catalysts` was wiped (REPLACE semantics), taking live `catalyst_threat` from 6→0. That is an absence of new evidence, not confirmation nothing is wrong; I am not treating 0 threats as an all-clear. (2) Scout flags STMPA.PA -2.91% overnight — STM (4.58% of equity) should gap down at the open; no action proposed pre-open on a single overnight print, watch the print.

## Sized Proposals

**1. TRIM — NVDA — overbought_distribution (live, cap-independent)**
Size $286.10 (25% trim_fraction, pre-sized) @ $228.8814. RSI14 70.4, +8.1% on the month, +6.34pp vs SMH. Genuinely overbought and up — the deliberately cap-independent case; NVDA is *not* over its ATR cap, this is a pure profit-take. Retires when RSI14 <60 or NVDA is no longer up on the month.
`evidence_quality: {verified:0, computed:2, unverified:0}` — RSI/return/cap status are all computed.
`benchmark_price_at_proposal: 567.01, benchmark_ticker: "SMH"`.

**2. TRIM — NBIS — cluster-floor risk concentration (non-cap-mechanics rationale)**
Size $500 (below the $501.49 over-cap gap, conservative) @ live NBIS price. Rationale: largest position in Compute/Hyperscaler (3.97%), lowest-ranked member on the cluster's own ladder, `watch` thesis, over cap 1.468x, now second-highest beta in the book (2.317) behind only COHR, and the cluster's rent-vs-self-fund split means NBIS/IREN specifically (not MSFT/GOOG) carry the cost-of-capital exposure into CPI (09-11) and FOMC (09-15/16) five sessions out. This is explicitly **not** a cap-alone trim — net_signal is +1 (PEER LEADER bucket) and RSI14 57.8 is not overbought, so per the 09-07 fix I would normally exclude it on cap mechanics; the override here is the concentration + calendar case, stated explicitly rather than smuggled in via the cap multiple.
`evidence_quality: {verified:0, computed:3, unverified:0}`.
`benchmark_price_at_proposal: 567.01, benchmark_ticker: "SMH"`.

**3. PAIR — cluster_rotation: Sell INTC ($430.40) → Buy KLAC ($430.40) — ladder-driven, live**
INTC ranked #9/10 (laggard, net WFE consumer, negative economics); KLAC ranked #2/10 (leader, rising process-control intensity at GAA/advanced packaging). `pair_id: cluster_rotation-INTC-KLAC`. Note: the ladder's own tension log flags that KLAC's rank-2 and the thesis's "strengthening" agree with each other but neither has a cached 1-month return — two agreeing views that have not been priced this run; RSI14 37.2 is the one dissenting observable. Proceeding on ladder + thesis convergence but naming the gap.
`evidence_quality: {verified:0, computed:2, unverified:1}`.
Sell leg `benchmark_price_at_proposal: 567.01`, buy leg same, `benchmark_ticker: "SMH"`.

**4. PAIR — profit_rotation: Sell MSFT ($149.50) → Buy KLAC ($149.50) — live**
MSFT in `names_stretched` with a `watch` thesis (real profit to book); KLAC laggard (-5.7pp) with strengthening thesis. Note this competes for the same KLAC buy-leg capacity as proposal 3 and the still-open P-236 (Buy KLAC, trend_entry, $587.54) — all three cite KLAC independently but the desk's $587.54 deployable-cash ceiling for ideas cannot fund all of them. Present as an alternative funding source (sell MSFT instead of INTC) rather than an incremental add; the user should pick one KLAC funding leg, not stack three.
`evidence_quality: {verified:0, computed:2, unverified:0}`.
`benchmark_price_at_proposal: 567.01, benchmark_ticker: "SMH"`.

**5. HOLD — AVGO/LITE pair (P-241/P-242) — flag for reconsideration, no new leg proposed**
Per the ladder tension above, the sell leg's rationale (AVGO as cluster laggard) does not survive the new ladder ranking (AVGO ranks 2nd of 7 on intra-cluster relative strength). Recommend revisiting P-241 against the ladder before it fires; not re-proposing a competing trade.

*(Oversold-reversion BUYs on GOOG/AMAT and the APH trend_entry are real live triggers but carry `suggested_size_usd: $0` or are fully cash-clamped with no incremental headroom beyond what's already allocated above — logged, not separately sized, to avoid a 6th idea competing for the 5-slot IDEA cap with weaker conviction than 1-4.)*

## Six-Scenario Stress Table (macro-anchored where possible)

| Scenario | Impact % | Most exposed | Mechanism | Basis |
|---|---|---|---|---|
| AI-capex pause | -18% to -12% | GEV, BE, NBIS, TER | 95.4% AI-capex concentration; a pause hits power/infra and hyperscaler-capex-linked names first | static_assumption |
| Rates +100bp | -9% to -5% | NBIS, IREN, VRT | Rent-vs-self-fund split from the hyperscaler ladder: NBIS/IREN carry cost-of-capital exposure directly; live 10y already +12.4bp/1m into a hawkish-cached Fed | live |
| Tariff/export-control escalation | -14% to -7% | TSM, ASML, AMAT, LRCX | Semicap/foundry supply chain is the most exposed to a fresh control tightening | static_assumption |
| USD/INR ±3% | ~0% (USD book) | — | Book is USD-reported; a ±3% INR move has ~0% effect on USD net worth but a directly proportional effect on INR-terms net worth (±3% on $42,309.58 ≈ ±₹1.2L equivalent) | static_assumption |
| Soft CPI/hawkish-surprise week (09-11/09-15-16) | -6% to -3% | NBIS, IREN, VRT, BE | Macro tail's own regime read: rate-sensitive names "pressured first and hardest" into the CPI+FOMC window; defensives relatively favored as rotation destination | live |
| Asia/memory-chain soft patch | -5% to -2% | MU, TSM (indirect), STM | Macro tail flags soft Asia overnight (Nikkei -1.7%) hitting memory/semicap directly; STMPA.PA already -2.91% overnight per scout | live |

Anchored to: US10Y 4.784% (+12.4bp/1m), VIX 15.69, DXY 98.954, Fed 3.63% hawkish. Options PCR/max-pain null this run (not estimated).

## Hit-Rate / Scorecard Interpretation (consumed from proposals.json, not recomputed)

Stored scorecard as_of 2026-09-08: **overall 27.6% (n=29)**. By direction: **TRIM/SELL 18.2% (n=11, avg benefit -12.19%)**, **BUY 40.0% (n=15, avg benefit +0.15%)**, **HOLD 0% (n=3)**. `alpha_scored_count: 0` — none of the 29 were graded vs SMH; all 29 were graded on absolute move because `benchmark_price_at_proposal` capture only started 2026-09-07. In a tape where SMH ran hard, absolute grading is exactly the condition that makes every trim look like a bigger miss than it may have been on an alpha basis — but that caveat does not explain away an 18.2% trim hit rate on n=11 with a -12.19% average benefit; both are real and both are stated. 3 rows are quarantined for anchor review (excluded from the above). This is the first run where every new BUY/TRIM/SELL proposal carries `benchmark_price_at_proposal`, so the next scorecard should start separating alpha from market beta — until then, weight the trim signal here as directionally informative but not yet alpha-clean, and treat the desk's own trim conviction with appropriate caution relative to its BUY conviction.

## Data Quality / Open Items
- catalyst returned 0 events (long weekend), wiping live `catalyst_threat` from 6→0 — absence of evidence, not evidence of absence.
- Options PCR/max-pain null this run.
- P-237 (Sell AMD) and P-241/P-242 (Sell AVGO→Buy LITE) are open proposals whose stated rationale is now disputed by the new cluster ladders — flagged for reconsideration, not duplicated or unilaterally altered.
- KLAC has 3 separate funding paths proposed/open this run (P-236, proposal 3, proposal 4) against a single $587.54 deployable-cash ceiling — pick one, do not stack.
- AI Semis/Fabs and Compute/Hyperscaler ladder tensions (KLAC unpriced, AMAT ladder+thesis both disagree with price, MSFT rank-1-on-watch) are pre-declared in `state.cluster_ladders[*].thesis_tensions` — read directly, not re-derived here.

```json
{"policy_draft":null,
 "stress_table":{"as_of":"2026-09-08",
   "anchored_to":{"us10y_pct":4.784,"vix":15.69,"dxy":98.954,"fed_rate_pct":3.63,"fed_stance":"hawkish"},
   "scenarios":[
     {"scenario":"AI-capex pause","impact_pct_low":-18.0,"impact_pct_high":-12.0,"most_exposed":["GEV","BE","NBIS","TER"],"mechanism":"95.4% AI-capex concentration; pause hits power/infra and hyperscaler-capex-linked names first","basis":"static_assumption","note":""},
     {"scenario":"Rates +100bp","impact_pct_low":-9.0,"impact_pct_high":-5.0,"most_exposed":["NBIS","IREN","VRT"],"mechanism":"rent-vs-self-fund cluster split; NBIS/IREN carry cost-of-capital exposure directly, live 10y already +12.4bp/1m into hawkish-cached Fed","basis":"live","note":""},
     {"scenario":"Tariff/export-control escalation","impact_pct_low":-14.0,"impact_pct_high":-7.0,"most_exposed":["TSM","ASML","AMAT","LRCX"],"mechanism":"semicap/foundry supply chain most exposed to fresh control tightening","basis":"static_assumption","note":""},
     {"scenario":"USD/INR ±3%","impact_pct_low":0.0,"impact_pct_high":0.0,"most_exposed":[],"mechanism":"USD-reported book; ~0% USD effect, proportional effect in INR-terms net worth only","basis":"static_assumption","note":"≈±₹1.2L equivalent in INR terms on $42,309.58 total book"},
     {"scenario":"Soft CPI/hawkish-surprise week (09-11/09-15-16)","impact_pct_low":-6.0,"impact_pct_high":-3.0,"most_exposed":["NBIS","IREN","VRT","BE"],"mechanism":"macro regime read: rate-sensitive names pressured first and hardest into CPI+FOMC window; defensives relatively favored","basis":"live","note":""},
     {"scenario":"Asia/memory-chain soft patch","impact_pct_low":-5.0,"impact_pct_high":-2.0,"most_exposed":["MU","TSM","STM"],"mechanism":"soft Asia overnight (Nikkei -1.7%) hitting memory/semicap chain; STMPA.PA -2.91% overnight already flagged","basis":"live","note":""}
   ],
   "data_quality":["options PCR/max-pain unavailable this run","rate/tariff/capex-pause rows are static rule-of-thumb ranges, not re-derived this run"]},
 "proposals":[
   {"direction":"TRIM","ticker":"NVDA","size_usd":286.10,"price_at_proposal":228.8814,"rationale":"RSI14 70.4 overbought and +8.1% on the month; cap-independent profit-take, NVDA is not over its ATR cap","trigger_type":"overbought_distribution","trigger_bucket":"overbought_distribution","pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0},"benchmark_price_at_proposal":567.01,"benchmark_ticker":"SMH"},
   {"direction":"TRIM","ticker":"NBIS","size_usd":500.0,"price_at_proposal":213.90,"rationale":"Largest position in Compute/Hyperscaler (3.97%), lowest-ranked ladder member, watch thesis, over cap 1.468x, book's 2nd-highest beta (2.317); cluster's rent-vs-self-fund split concentrates cost-of-capital risk here into CPI/FOMC week -- explicitly not a cap-alone trim (net_signal +1, RSI not overbought), override stated on concentration+calendar grounds","trigger_type":"conviction_exit","trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":3,"unverified":0},"benchmark_price_at_proposal":567.01,"benchmark_ticker":"SMH"},
   {"direction":"SELL","ticker":"INTC","size_usd":430.40,"price_at_proposal":null,"rationale":"Cluster ladder ranks INTC #9/10: only member net-consuming WFE with negative economics (EPS -$2.09, margin -19.8%)","trigger_type":"cluster_rotation","trigger_bucket":"cluster_rotation","pair_id":"cluster_rotation-INTC-KLAC","pair_role":"sell","size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1},"benchmark_price_at_proposal":567.01,"benchmark_ticker":"SMH"},
   {"direction":"BUY","ticker":"KLAC","size_usd":430.40,"price_at_proposal":185.1239,"rationale":"Cluster ladder ranks KLAC #2/10: process-control/metrology intensity rises fastest at GAA and advanced packaging; note KLAC has no cached 1-month return this run -- rank and thesis agree but neither is priced","trigger_type":"cluster_rotation","trigger_bucket":"cluster_rotation","pair_id":"cluster_rotation-INTC-KLAC","pair_role":"buy","size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1},"benchmark_price_at_proposal":567.01,"benchmark_ticker":"SMH"},
   {"direction":"SELL","ticker":"MSFT","size_usd":149.50,"price_at_proposal":498.32,"rationale":"Stretched (names_stretched) with watch thesis -- alternative KLAC funding leg to INTC; do not stack with proposal 3 or open P-236","trigger_type":"profit_rotation","trigger_bucket":"profit_rotation","pair_id":"profit_rotation-MSFT-KLAC","pair_role":"sell","size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0},"benchmark_price_at_proposal":567.01,"benchmark_ticker":"SMH"},
   {"direction":"BUY","ticker":"KLAC","size_usd":149.50,"price_at_proposal":185.1239,"rationale":"Laggard (-5.7pp) with strengthening thesis; funded by MSFT profit-take as alternative to INTC leg -- pick one funding source, not both","trigger_type":"profit_rotation","trigger_bucket":"profit_rotation","pair_id":"profit_rotation-MSFT-KLAC","pair_role":"buy","size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0},"benchmark_price_at_proposal":567.01,"benchmark_ticker":"SMH"},
   {"direction":"HOLD","ticker":"AVGO","size_usd":0,"price_at_proposal":null,"rationale":"Open P-241/P-242 sell-leg rationale (AVGO as cluster laggard) disputed by new ladder: AVGO ranks 2nd of 7 intra-cluster, watch status is financing/guide-driven not competitive -- flag for reconsideration, no new leg proposed","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,"evidence_quality":{"verified":0,"computed":1,"unverified":1}}
 ],
 "scorecard_read":"Stored scorecard as_of 2026-09-08, n=29 overall: overall 27.6%, TRIM/SELL 18.2% (n=11, avg benefit -12.19%), BUY 40.0% (n=15, avg benefit +0.15%), HOLD 0% (n=3). alpha_scored_count=0 -- all 29 graded on absolute move, not vs SMH, since benchmark capture only started 2026-09-07; in a tape where SMH ran hard this makes trims look worse than their true alpha may be, but that caveat does not erase an 18.2% trim hit rate on n=11 -- both facts stand. 3 rows quarantined for anchor review. This run is the first where every new proposal carries benchmark_price_at_proposal, so the next scorecard can finally separate alpha from beta.",
 "deemphasize_buckets":[],
 "data_quality":["catalyst returned 0 events over the long weekend, wiping live catalyst_threat 6->0 -- absence of new evidence, not an all-clear","options PCR/max-pain null this run","P-237 and P-241/P-242 open proposals have rationale disputed by new cluster ladders -- flagged, not altered or duplicated","KLAC has 3 competing funding paths (P-236 open, and two proposals here) against a single $587.54 deployable-cash ceiling"]}
```

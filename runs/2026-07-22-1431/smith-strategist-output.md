# smith-strategist — Stage 2 output (quick sweep, 2026-07-22, run 2026-07-22-1431)

## Policy status
Policy draft still unconfirmed and now genuinely stale: it predates BABA's new position/cluster and today's real sizing moves (AMAT->dust, QCOM 6->14sh, GLW 19->10sh, CIEN 3.39->1.39sh, GEV rebuilt). **Policy draft awaiting confirmation — run Agent Smith interactively to confirm.** All drift analysis below is provisional against this unconfirmed draft. Two cluster-taxonomy items need user confirmation before they're binding (G11): the draft's "Compute/Hyperscaler" line, and BABA's new "China Consumer/Cloud" classification (currently floating as "Unclassified" in compute_drift.json at 1.423%, actually just BABA at 1.42% weight).

## Read on the two live breaches driving everything below
Cash is *below* its floor (1.109% vs 3–15% band) and AI-capex-chain concentration is *above* its cap (98.577% vs 90%) — simultaneously. That combination means the right move is to raise cash by trimming inside the overweight AI-capex cluster, not to deploy fresh cash into it. This shapes all five proposals: two sized trims that fix both breaches at once, and three deliberate "hold, don't add" calls on names that look attractive on thesis/target-gap grounds but would make both breaches worse.

## Proposals

**1. Trim SNDK ~$1,500 (approx. 1.0 share at an implied ~$1,554/sh — see data-quality note)**
SNDK is the largest position (11.45% wt) and sole driver of the AI Memory/Storage cluster breach (27.158% actual vs 15–25% band, +2.158pt over ceiling). Thesis just downgraded it intact→WATCH on a severe peer-laggard read, and signals confirm PEER LAGGARD + MOMENTUM/VOLUME deterioration with no analyst target computable this run (data gap — sizing is drift/thesis-driven, not target-driven). A ~$1,500 trim pulls the cluster to ~23.5% (back inside band with buffer) and lifts wallet cash from $457.77 to ~$1,958 (~4.8% of book, inside the 3–15% band) — closing both the cluster breach and the cash-floor breach in one action. LTCG timing cannot be assessed — lots.json is empty (G1); treat this trim as untimed until tax-lot data exists.

**2. Exit ORCL ~$530 (full remaining stake, 4sh, implied ~$133/sh)**
ORCL now carries three concurrent red flags: BREAKDOWN, a fresh 21-Jul credit downgrade, and a new PEER LAGGARD read vs XLK (-8.5%). The open defensive-stance flag from prior runs stays actionable. Position is small (~1.3% wt) so a clean full exit is simpler than a partial trim, and it adds further to the cash rebuild alongside proposal #1 (combined ~$2,030 raises cash to ~6.1%, comfortably mid-band).

**3. Hold — do not add IREN despite STRENGTHENING thesis + book's largest target gap (+49%)**
IREN was just upgraded WATCH→STRENGTHENING on $2.8B in new AI-cloud contracts, and AI Networking/Optics is technically under-band (14.846% vs 15–25%, -0.154pt, marginal). Ordinarily this would be a clean add. But cash is below floor and ai_capex_pct is above cap — adding here (IREN is capex-chain) worsens the exact breach the SNDK/ORCL trims are meant to fix. Recommend revisiting after proposals #1–2 land and cash is rebuilt; this is the top candidate for that follow-up deployment, not a rejection of the thesis.

**4. Hold — no fresh deployment into AI Power/Cooling/DC Infra despite the largest cluster underweight (-8.674pt, 6.326% vs 10–20% band)**
GEV was just rebuilt to real size and reconfirmed STRENGTHENING, and this cluster is the most under-target in the book. Same constraint as #3 applies: GEV is AI-capex-chain, and the portfolio has zero cash to deploy without breaching the cap further. Flagging structurally, not sizing: thesis's own verdict this run is that BABA is the *only* non-AI-capex-chain name in the book ("no meaningful uncorrelated ballast") — this underweight cluster is a symptom of that same concentration, not a separate opportunity to chase with fresh capex-chain names.

**5. No size change on BABA — flag only**
BABA (new position, 5sh, 1.42% wt) is carrying OVERSOLD BOUNCE + TARGET GAP + PEER LEADER signals and is the book's only real diversifier by factor exposure. It shows as "Unclassified" in the drift table pending user confirmation of the "China Consumer/Cloud" cluster line (G11). No sizing action proposed this run — it's freshly bought and cash is constrained — but once confirmed, this is the more logical destination for future fresh cash than another AI-capex name, given the concentration read in #4.

## Risk-off status
**normal** — concur with compute_drift.json, no override. Drawdown is 0.0% (new peak this run), and the "AMBIGUOUS" gate classification this run traces to NQ futures (-0.76%) marginally tripping a loose pre-market heat-check threshold, not underlying volatility — VIX itself is calm at 17.44 (+2.29% vs Monday's close). No basis to tighten beyond the two structural (non-market-driven) breaches already addressed above. Note: smith-rebound failed twice this run (stalled on dispatch and retry) — treated as a data gap, no rebound-candidate proposals fabricated in its absence.

## Hit-rate readout
Empty this run. journal.json's bucket_hit_rates is `{}` — per the journal's own note, all 37 tracked entries are still younger than the 30-day scoring window (the earliest 07-12 cohort only crossed the 7-day mark on 07-19); nothing reaches 30d until mid-August. No buckets currently meet the ≥3-scored-entries bar, so no de-emphasis recommendation this run.

## Proposal outcomes
Not applicable — this task is scoped to deep-mode or monthly runs; this is a quick sweep. Skipped.

## Data quality notes
- SNDK and ORCL price_at_proposal figures are implied (this run's stated/last-known weight × total book value, divided by last-known share count from state.json), not independently re-fetched from a live quote source this run — kept within the quick-mode tool-call budget. Treat as approximate, not execution-grade.
- BABA's cluster ("China Consumer/Cloud") and the draft policy's "Compute/Hyperscaler" line both await user confirmation (G11).
- LTCG timing unavailable for all trim candidates — lots.json is empty (G1).

```json
{"policy_draft":null,"proposals":[
 {"action":"Trim SNDK","size_usd":1500,"price_at_proposal":1554.44,"rationale":"Largest position (11.45% wt) driving AI Memory/Storage cluster breach (27.158% vs 15-25% band); thesis downgraded intact->WATCH on severe peer-laggard; no analyst target computable (data gap); trim closes cluster breach and cash-floor breach together (cash 1.109% -> ~4.8%)."},
 {"action":"Exit ORCL (full remaining stake)","size_usd":530,"price_at_proposal":132.82,"rationale":"BREAKDOWN + fresh 21-Jul credit downgrade + new peer-laggard vs XLK (-8.5%); open defensive-stance flag stays actionable; small position makes full exit cleaner than partial trim; adds to cash rebuild."},
 {"action":"Hold - no add to IREN","size_usd":0,"price_at_proposal":null,"rationale":"STRENGTHENING thesis + book's largest target gap (+49%) + cluster underweight (AI Networking/Optics -0.154pt) would normally support an add, but cash is below floor (1.109% vs 3-15%) and ai_capex_pct is above cap (98.577% vs 90%); IREN is capex-chain, adding worsens both breaches; revisit after SNDK/ORCL trims land."},
 {"action":"Hold - no add to GEV / AI Power-Cooling-DC Infra cluster","size_usd":0,"price_at_proposal":null,"rationale":"Largest cluster underweight in the book (-8.674pt) and GEV just reconfirmed STRENGTHENING, but GEV is capex-chain and cash/capex caps are both breached; thesis notes BABA is the only non-AI-capex-chain name in the book, so this underweight is a symptom of concentration, not a fundable opportunity right now."},
 {"action":"Flag BABA cluster for confirmation, no size change","size_usd":0,"price_at_proposal":115.97,"rationale":"Only non-AI-capex-chain name in book (1.42% wt), OVERSOLD BOUNCE + TARGET GAP + PEER LEADER signals, shows as Unclassified pending user confirmation of new 'China Consumer/Cloud' cluster (G11); logical destination for future fresh cash but not sized this run given cash constraint and recency of purchase."}
],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["SNDK/ORCL price_at_proposal are implied from weight/value-over-last-known-share-count, not independently re-fetched this run (quick-mode budget)","bucket_hit_rates empty - all journal entries younger than 30d scoring window per journal.json note","BABA China Consumer/Cloud cluster and draft policy Compute/Hyperscaler line await user confirmation (G11)","LTCG lot dates unavailable, all trims untimed for tax purposes (G1)"]}
```

# Agent Smith — Portfolio Strategist — Quick Sweep — 2026-07-24

Policy status: **unconfirmed draft** (policy.json `confirmed:false`, as_of 2026-07-12). All drift analysis and proposals below are **provisional — draft policy**. Two open items on the draft itself: G11 (the "Compute/Hyperscaler" cluster target/band was added to the draft on 2026-07-18 without user confirmation), and the draft's own notes flag it as stale given the book has churned significantly since 07-12 (28→24 holdings, five full exits today). Recommend a full policy re-look at the user's convenience — not urgent enough to block this run's proposals, but the max_ai_capex_factor_pct=90% ceiling in particular deserves a hard look given it's sitting 30pts above the draft's own 60% sane-diversification flag threshold.

No policy bootstrap needed — a draft already exists.

## Context this run
Five full exits today (LITE, META, GOOG, BABA, STM) plus trims to AMD and QCOM converted ~$5,600 of equity into cash. Book (excl. wallet) $35,655.38, down from $41,748.44, but total book (equity+cash) is roughly flat (-1.1%) — this was a reallocation, not value destruction. 24 positions remain, and per smith-thesis, **100% of them now sit in AI-capex-chain clusters** — BABA's exit removed the portfolio's last non-AI-capex sleeve.

## Sized Proposals (2026-07-24) — for review only, none executed

**1. TRIM SNDK ~$1,000** (from ~$4,732 position, ~13.271% weight → ~10.8% post-trim)
Price reference: $1,589.40 (last confirmed print, 07-22 journal entry — no fresher live quote pulled this run; **confirm current price before considering execution**, this exact name (SNDK) had a stale-price false-breach incident on 07-18 per policy.json notes, so double-check before acting).
Rationale: dual breach — SNDK alone breaches the 12% single-position cap (13.271%, +1.271pt) and is the largest driver of the AI Memory/Storage cluster breach (31.502% vs [15,25]% band, +11.502pt over). No adverse signal or thesis change on SNDK this run — this is a pure rebalancing trim, not a thesis call. LTCG timing cannot be assessed (G1 — lots.json empty, no lot dates), so no deferral recommendation is possible; this is sized as a straight trim rather than a "defer toward LTCG boundary" call.
Caveat: $1,000 is a **partial** fix. It brings SNDK comfortably under its cap but only pulls the cluster from 31.5% to an estimated ~29.5% — still above the 25% band top. Full cluster resolution would require also trimming MU, DRAM, or EWY, but all three show improving signals this run (MU: TARGET GAP retained; DRAM and EWY shed PEER LAGGARD tags) — none are trim candidates on this run's evidence. Cluster breach carries forward as a watch item.

**2. DEPLOY ~$900 into GEV** (AI Power/Cooling/DC Infra)
Rationale: this cluster is the largest floor breach in the book (8.284% vs [10,20]% band, target 15%, -6.716pt under) — and GEV just flipped to STRONG UPTREND + MOMENTUM+VOLUME + TARGET GAP post-earnings (+4.69% today), the strongest signal cluster in this run's signal_history. Combines a real cluster-underweight need with a genuinely strengthening signal, not just a rebalancing mechanic. Est. post-trade cluster weight ~10.5% — brings it to the low edge of band, not fully to target; more room remains for a future run.

**3. DEPLOY ~$700 into COHR** (AI Networking/Optics)
Rationale: this cluster is also under its floor (14.833% vs [15,25]% band, -5.167pt), COHR is an existing, already-held position (no new-name onboarding risk) with a watchlist-flagged setup (+20.0% upside), and — importantly — COHR has **no earnings this week**, unlike GLW and TER (both report 07-28) which are in the same cluster and are better left untouched into their prints rather than sized up right now. Est. post-trade cluster weight ~16.5% — closes the floor breach.

**4. HOLD ~$5,057 in cash (no further deployment this run)**
After the trim + two adds above, remaining cash is estimated at ~$5,057 (~12.2% of total book), still comfortably inside the [3,15]% band. Reasons to hold rather than fully redeploy the idle pile: (a) four earnings prints land within the next week on held names — GLW/TER 07-28, QCOM 07-29, LRCX 07-29 — sizing up into binary events is exactly the kind of exceptional-setup exception this book doesn't need right now; (b) drawdown is -14.878%, only 0.122pt from the policy's 15% warn threshold (see Risk-Off Check below) — a reason for some restraint even though the status line reads "normal"; (c) the Compute/Hyperscaler cluster is also under its floor (4.233% vs [5,15]% band, -5.767pt) but the only two constituents are ORCL (mixed/negative signals, see verdict below) and IREN (no fresh catalyst flagged this run) — no clean deployment candidate exists there today, so it's left unaddressed rather than forced.

## Diversification question (AI-capex concentration, 100% vs 90% cap)
Explicitly checked whether a genuinely uncorrelated candidate exists in this run's watchlist output: **no.** BABA (the strongest-upside re-entry candidate at +40.1%) is itself flagged AI-capex-adjacent per its own thesis line and would not fix the concentration problem even on re-entry. SNPS (oversold, +33.8%, fresh Buy) is EDA/chip-design software — still value-chain-correlated to AI capex spend, not a clean diversifier. IBM (+21.4%) is closer to genuinely different exposure (enterprise/hybrid infrastructure) but carries its own red flag (-25% post-earnings crash 07-14, watchlist calls it a value-trap risk) — not a clean pick either. The policy's own "Diversified/Regional ETF" cluster sits at 0% vs a 5% target (a complete, standing miss), but no specific ETF ticker (CQQQ/AIA) was scanned by watchlist this run, and the FMP ETF-constituent tool remains blocked (G19), so constituent AI-exposure can't be verified anyway. **Bottom line: diversification away from the AI-capex chain is not available from this run's data — say so plainly rather than force BABA or SNPS into that role.** Recommend the deep-mode scout's diversifier-candidate bench be checked specifically for this on the next deep review.

## ORCL signal verdict
ORCL carries four live tags this run: BREAKDOWN, TARGET GAP, PEER LAGGARD, and a brand-new OVERSOLD BOUNCE off a real catalyst ($7B DoD contract). Verdict: **hold, no action** — the new bounce signal is real but does not yet offset the standing breakdown and debt-headwind flags; this reads as a name to watch for confirmation (does the bounce hold, does the debt overhang show resolution), not a rebalancing trigger today. Position is tiny (1.192% weight) — not a trim candidate, and the mixed/negative signal profile means it's not an add candidate either despite sitting in an under-target cluster (Compute/Hyperscaler, see proposal 4 discussion above).

## Risk-Off Check
`risk_off_status: normal` per compute_drift.json. However, drawdown is **-14.878%, only 0.122pt from the policy's 15% warn threshold** — close enough that it should be flagged explicitly even though the computed status doesn't yet trip. Proposals above are sized modestly (largest single new deployment $900) and cash is held back rather than fully redeployed, consistent with treating this as a soft-caution zone rather than a green light for aggressive redeployment. No defensive/stop-level actions triggered at "normal" status.

## Hit-Rate Readout
journal.json currently has 47 entries; `bucket_hit_rates` and `name_bucket_grades` are both empty — no bucket has reached the 30d scoring window yet. Earliest cohort (07-12, 11 entries) crosses 30d around 2026-08-11. Only 3 entries are "scored," and those are position-exit closures (DELL/DLR/VRT), not price-target verdicts. **Nothing to report this run** — all buckets currently have 0 scored entries, below the ≥3 threshold for inclusion. Revisit after 2026-08-11.

## Proposal Outcomes
Not applicable — quick sweep (this task runs in deep mode or monthly per the skill's cadence rules).

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim SNDK","size_usd":1000,"price_at_proposal":1589.40,"rationale":"Breaches 12% single-position cap (13.271%) and is the largest driver of the AI Memory/Storage cluster breach (31.502% vs [15,25]% band); no thesis/signal deterioration, pure rebalancing trim; LTCG timing unavailable (G1)."},
   {"action":"Deploy into GEV","size_usd":900,"price_at_proposal":1002.30,"rationale":"AI Power/Cooling/DC Infra cluster is the largest floor breach (8.284% vs [10,20]% band); GEV flipped to STRONG UPTREND+MOMENTUM+VOLUME+TARGET GAP post-earnings this run."},
   {"action":"Deploy into COHR","size_usd":700,"price_at_proposal":285.29,"rationale":"AI Networking/Optics cluster under floor (14.833% vs [15,25]% band); COHR already held, watchlist +20.0% upside setup, no earnings this week unlike cluster-mates GLW/TER (07-28)."},
   {"action":"Hold cash, no further deployment","size_usd":5057,"price_at_proposal":null,"rationale":"Four earnings prints in the next week on held names (GLW/TER 07-28, QCOM 07-29, LRCX 07-29); drawdown 0.122pt from warn threshold; no clean candidate for the remaining Compute/Hyperscaler floor breach this run."}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["SNDK price_at_proposal is last-confirmed (07-22 journal), not a fresh live quote this run — confirm before any execution given prior 07-18 stale-price false-breach incident on this exact name (see policy.json notes)","No bucket in journal.json has reached the ≥3 scored-entry threshold yet — hit-rate readout empty this run, revisit after 2026-08-11","No genuinely uncorrelated (non-AI-capex-chain) diversifier candidate found in this run's watchlist output — BABA and SNPS are both AI-capex-adjacent, IBM carries independent value-trap risk; FMP ETF-constituent tool still blocked (G19) so the Diversified/Regional ETF cluster's 0%-vs-5%-target gap can't be filled with a verified pick this run","Compute/Hyperscaler cluster floor breach (-5.767pt) left unaddressed — only ORCL (mixed signals) and IREN (no fresh catalyst) sit in this cluster, neither is a clean deployment candidate this run","Policy draft flagged stale by its own notes (composition churned 28→24 holdings since 07-12 as_of date) and remains unconfirmed (G11 open re: Compute/Hyperscaler cluster line)"]}
```

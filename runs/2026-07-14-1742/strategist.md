# Agent Smith — Portfolio Strategist (QUICK sweep)
Run: 2026-07-14 ~08:12am ET / pre-open · Mode: quick · Policy: present, unconfirmed (provisional draft, all drift analysis below is provisional under a policy the user hasn't confirmed)

## Policy status
No bootstrap needed — policy.json exists (confirmed: false). All cluster-target/band language below is still a **draft the user has not signed off on**. Notable gaps in the draft worth flagging while it's open for edits: there is no defined cluster for the gold/diversifier complex (NEM/GLD/B/AEM) even though the book already holds a live tranche program in it — recommend the user add a "Diversifiers/Non-AI-capex" cluster with its own target/band before the next confirm, otherwise NEM/GLD buys will always sit outside the drift table.

## Sized proposals (today, 2026-07-14; prices live via yfinance at time of this pass)

1. **TRIM TSM ~$700** (price_at_proposal $421.58; position is ~$3,508, 10.32% of book) — first tranche only, not a full correction.
   Rationale: AI Semis/Fabs cluster is 14.1pt over its 30% target (44.1% actual, band 25-35, ~$4,800 excess to target / ~$3,100 to just the band top) — the largest breach in compute_drift.json. TSM also carries a fresh EARNINGS PROXIMITY signal (prints Jul 16, 2 days out) — trimming ahead of a binary event reduces idiosyncratic risk on the single largest position while chipping at the cluster overweight. Because the combined AI-capex factor is already breached (94.3% vs 90% cap), this trim is sized to *fund reallocation within the AI-capex envelope* (see #2) rather than sit in cash, which is separately over-band.
   LTCG: lots.json is empty — cannot check individual lots against the 24-month boundary this run (known gap G1). Flag for the user to confirm no near-boundary lots exist before executing.

2. **BUY VRT ~$500 (re-entry)** (price_at_proposal $305.87) — funded by the TSM trim above.
   Rationale: AI Power/Cooling/DC Infra is 6.5pt under target (8.5% vs 15%, band 10-20; GE Vernova alone *is* effectively this entire cluster today — single-name concentration risk worth noting separately). VRT's watchlist re-entry setup shows +18.9% target-gap upside with "uniformly positive post-exit news" — the analyst read is that the original exit was macro/technical, not thesis-driven, consistent with today's finding that none of the four exits (ETN/ANET/DLR/VRT) had a bearish trigger. Because this reallocates TSM proceeds into another AI-capex-chain name, it is net-neutral on the AI-capex factor (94.3% stays ~94.3%) while directly repairing two cluster breaches (Semis/Fabs down, Power/Infra up) at once — the single most efficient move available today.

3. **Reaffirm NEM $350 (diversifier tranche 2/3)** (price_at_proposal $93.10, vs $95.29 when opened yesterday — modestly cheaper entry now).
   Rationale: cash is 29.77% vs the [3,15]% band — $5,021 over the hard 15% ceiling on the $33,993 book (or ~$7,060 to reach a comfortable band-midpoint of 9%, which roughly reconciles with the ~$7,400 figure floated going into this run, methodology-dependent on which target point is used). NEM sits outside the AI-capex factor entirely, so it cures cash without adding to the already-breached 94.3%/90% AI-capex cap — the one lever that doesn't fight the AI-capex ceiling. Carried forward from 2026-07-13, unchanged size, better price.

4. **Reaffirm GLD $250 (diversifier tranche 3/3)** (price_at_proposal $367.13, vs $377.01 when opened yesterday).
   Rationale: same cash-breach / AI-capex-cap logic as #3. Completes the 3-tranche gold-complex build queued from the prior run.

### Holds / watch-only (no dollar action, but explicitly flagged)

5. **HOLD — no further SNDK accumulation.** Thesis downgraded intact→watch this run; it's now a real 7.4% position (grown off sustained accumulation) with no analyst target available and a -12.6% intraday whipsaw today (SK Hynix Nasdaq-listing competition + profit-taking, despite a +251% revenue beat on 07-13). Per policy, watch-status names outrank drift as trim candidates and should never be added to — this is a stop-buying flag, not yet a sell signal, since there's no thesis break, just elevated volatility and no valuation anchor.

6. **HOLD — no further EWY accumulation.** Watch status escalated (-8.45% today on top of the 07-13 KOSPI crash), yet the position has been growing (6→10sh) right through the deterioration — worth the user's attention as a pattern. Look-through concentration matters here: DRAM ETF (~25% Samsung + ~22% SK Hynix swap exposure) and EWY (~47% Samsung+SK Hynix) correlate materially, so real Korea-memory concentration exceeds what the headline cluster weights show.

7. **WATCH — no DLR re-entry yet.** Watchlist shows the same +18.9% target-gap upside as VRT, but the signal is mixed (dilutive equity raise funding an otherwise-positive acquisition). With risk-off status at "warn," this pass sizes only the cleaner setup (VRT); DLR waits for the raise terms/dilution impact to clarify.

8. **NOTE — residual cash breach not force-cured this run.** Tranches #3-4 only address ~$600 of the ~$5,000-7,000 excess. The AI-capex cap breach blocks deploying more into the underweight AI clusters beyond the TSM→VRT reallocation without making that breach worse, and the book is only 1.2pt from the hard risk-off drawdown trigger (see below) — treating some of the excess cash as deliberate ballast rather than forcing it into unproven names is the more disciplined call. Full cash-band cure should wait for a deep-mode run (scout's diversifier bench) or for the drawdown to move away from the risk-off boundary.

**Flagged, not actioned:** NOW is pre-market -7.95% with nothing in the current news feed explaining it (signals new_flag). Too speculative pre-open to size; revisit after the print confirms.

## Risk-off status
compute_drift.json: **risk_off_status = warn**. Drawdown is -23.824% against a 25% risk_off trigger — only **1.2 points** from the hard threshold, and already well past the 15% warn line. Raising this proactively even though the status hasn't flipped: proposals above are already tightened accordingly (no new deployments outside the two small, already-open diversifier tranches and one high-conviction re-entry; DLR held back; SNDK/EWY frozen). If drawdown crosses -25% on the next run, expect this desk to lead with defensive trims ranked broken > watch (SNDK, EWY first) over pure over-band trims, suggested stop-levels on the top 3 positions (TSM $3,508/10.3%, DRAM $3,445/10.1%, GEV $2,878/8.5%), and a compressed cash target toward the 15% band ceiling rather than the midpoint.

## Stress table
Skipped — quick mode. Deep mode (with smith-macro's live regime read) required for the anchored version.

## Hit-rate readout
bucket_hit_rates and name_bucket_grades are both empty this run — too early to score (consistent with proposals.json noting first outcomes land ~2026-08-12). No bucket has ≥3 scored entries yet; nothing to de-emphasize. Revisit next run.

## Proposal outcomes / scorecard
Quick mode — not a scheduled scorecard run (deep/monthly only). For continuity: six items remain open from 2026-07-13 (NEM tranche 2/3, GLD tranche 3/3, two of which are reaffirmed above at updated prices; plus four $0 hold/watch notes), all still too fresh to score.

## Data quality notes
- G1: LTCG per-lot dates unavailable (lots.json empty) — cited above for the TSM trim.
- G4: gold ticker is B (Barrick), not GOLD — not relevant to this run's NEM/GLD tickers but stated for hygiene.
- G5: DRAM/EWY/SNDK betas default to 1.0 (no yfinance beta field) — book beta 1.384 may understate true volatility given today's SNDK/EWY moves.
- G8 (new, confirmed this run): compute script's qty_changes/est_net_flows loop misses full exits (ticker present in prior snapshot, absent in current) — ETN/ANET/DLR/VRT's exits were only caught by manual diff. Needs a script fix: iterate prior_holdings keys not in current positions, emit as qty_changes with current_qty=0. Flagging for the orchestrator/user to action outside this pass.
- Cash-excess dollar figure is target-point-dependent ($5,021 to hard ceiling vs $7,060 to band-midpoint) — used both above for transparency rather than false precision.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim TSM","size_usd":700,"price_at_proposal":421.58,"rationale":"AI Semis/Fabs cluster +14.1pt over target (44.1% vs 30%, band 25-35); TSM earnings in 2 days (event-risk reduction); funds reallocation rather than adding cash to an already-breached cash band; AI-capex factor already at 94.3%/90% cap so proceeds are redeployed within-envelope, not added to it."},
   {"action":"Buy VRT (re-entry)","size_usd":500,"price_at_proposal":305.87,"rationale":"AI Power/Infra cluster -6.5pt under target (8.5% vs 15%, band 10-20); watchlist target_gap_reentry +18.9% upside with uniformly positive post-exit news suggesting the prior exit was macro/technical not thesis-driven; funded by TSM trim so net-neutral on the AI-capex factor while repairing two cluster breaches at once."},
   {"action":"Reaffirm NEM diversifier tranche 2/3","size_usd":350,"price_at_proposal":93.10,"rationale":"Cash 29.77% vs [3,15]% band, ~$5,021-7,060 excess depending on target point; NEM sits outside the AI-capex factor so it cures cash without worsening the 94.3%/90% AI-capex cap breach; carried forward from 07-13 at a cheaper entry."},
   {"action":"Reaffirm GLD diversifier tranche 3/3","size_usd":250,"price_at_proposal":367.13,"rationale":"Same cash-breach / AI-capex-cap-avoidance logic as NEM tranche; completes the queued 3-tranche gold-complex build at a cheaper entry than 07-13."},
   {"action":"Hold - no further SNDK accumulation","size_usd":0,"price_at_proposal":1673.97,"rationale":"Thesis downgraded intact to watch this run; real 7.4% position, no analyst target, -12.6% whipsaw today despite a strong earnings beat 07-13 - watch-status names are never add candidates regardless of drift."},
   {"action":"Hold - no further EWY accumulation","size_usd":0,"price_at_proposal":168.02,"rationale":"Watch status escalated (-8.45% today on top of 07-13 KOSPI crash) while the position kept growing 6 to 10sh; DRAM+EWY look-through Korea-memory concentration exceeds headline cluster weights."},
   {"action":"Watch - no DLR re-entry yet","size_usd":0,"price_at_proposal":177.92,"rationale":"Same +18.9% target-gap upside as VRT but mixed signal (dilutive equity raise funding the acquisition); risk-off warn status argues for sizing only the cleanest setup this pass."},
   {"action":"Note - residual cash excess not force-deployed","size_usd":0,"price_at_proposal":null,"rationale":"AI-capex cap breach blocks further redeployment into underweight AI clusters beyond the TSM-to-VRT reallocation; drawdown is 1.2pt from the risk-off trigger, so holding extra cash as ballast is reasonable pending a deep-mode scout run for non-AI-capex candidates."}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["G1: lots.json empty, LTCG lot-dates unavailable","G5: DRAM/EWY/SNDK betas defaulted to 1.0, book beta 1.384 may understate true vol","G8: compute script qty_changes loop misses full exits (ETN/ANET/DLR/VRT) - needs fix to also iterate prior_holdings keys absent from current positions","Cash-excess dollar figure is target-point-dependent: $5,021 to hard 15% ceiling vs $7,060 to 9% band-midpoint"]}
```

# Agent Smith — Portfolio Strategist (Deep Review, 2026-07-31)

## Policy status
Policy remains an **unconfirmed draft** (`confirmed: false`, last touched 2026-07-28). Nothing below waits on that confirmation — proposals are for your review regardless — but note the cluster targets, the two-regime cash band, and the risk-cap framework all still need your explicit sign-off. All drift/cluster reads in this run are run against that draft.

## The headline
Yesterday's US relief rally + this morning's Asia melt-up (KOSPI +17.9%, TAIEX +7.98%, Nikkei +4.03%) pushed **11 of your positions over their individual 2xATR20 risk caps**, and the book's aggregate open risk is now **15.05% vs a 10% cap (+5.05pt over)**. Both catalyst and thesis agree the primary driver was Microsoft's Azure beat re-igniting AI-capex-financing confidence — real, structural-positive for the theme — but everything else (KOSPI's snapback, SK Hynix's beat-and-miss, the insider buy) is soft, and **nothing addresses the CXMT/DUV structural threat that caused the original crash**. Per thesis, most of the over-cap names moved in lockstep with SMH/KOSPI with zero name-specific resolving fact — this is a bounce to sell into, not a re-rating to chase.

This is the classic "sell the bounce" setup: the rally itself is what created the excess risk, and the rally itself is the funding source to trim it down.

---

## Proposals (for your review — none executed)

**1. Trim SNDK ~$1,300 / MU ~$900 / DRAM ~$900 (combined ~$3,100) — mechanical-bounce Memory/Storage cluster**
Largest risk-cap offenders: SNDK is 4.13x its cap (ATR20 15.6%, the highest-vol name in the book), MU 2.47x, DRAM 2.53x. All three are still WATCH thesis, all three are peer-relative-strength laggards (-11 to -26pp vs SMH per signals) despite the 2-day bounce, and catalyst confirms zero fresh HBM/CXMT-resolving fact. This also directly cuts the AI Memory/Storage cluster breach (24.2% vs the 20% band ceiling, +9.2pt over target) — one trim, two breaches addressed. Sized as a partial cure (~59% of the three names' combined $5,296 excess), not a full flatten, since the underlying Azure-beat catalyst is genuinely positive for the AI-capex chain broadly.

**2. Trim ASML ~$700 / COHR ~$340 (combined ~$1,000) — mechanical-bounce Semis/Optics laggards**
ASML 1.67x cap, COHR 1.35x cap. Both WATCH thesis, both peer laggards, both cluster-in-band (Semis 33.6% in [25,35], Optics 17.2% in [10,20]) so this is pure name-level risk discipline, not cluster repair. (ARM is technically over-cap at 1.01x but the excess is $7 — not worth a dedicated trim; note it, don't act on it.)

**3. Light trim MRVL ~$400 / VRT ~$150 / NVDA ~$150 / AMD ~$100 / NBIS ~$100 (combined ~$900) — genuine-improvement names, risk-cap discipline only, not conviction reduction**
Flag: the orchestrator's mechanical-bounce grouping placed MRVL alongside SNDK/DRAM/MU, but thesis independently upgraded MRVL to STRENGTHENING today on real non-price evidence (Nvidia/Trainium, record revenue) — I'm treating MRVL per the more current per-name thesis read, not the coarser bucket, and sizing its trim far lighter than group 1's names as a result. NVDA is the peer leader (+15.3pp vs SMH) with a fresh target-gap setup (35.6% upside) — trim here is purely to bring the 1.11x cap excess back to par, not a signal on the name. AMD trims small ahead of its 08-04 binary earnings (4 trading days out) — reduce single-name risk into a known catalyst, don't fight the STRENGTHENING thesis. VRT is STRENGTHENING but a peer laggard, with its own fresh 39.5% target-gap upside — smallest trim of the group. NBIS was just upgraded to STRENGTHENING (Nvidia 9.3% stake + contract-backed debt raise) — token trim only.

**4. Exit ORCL ~$480 (full remaining stake, 4 shares)**
Thesis is BROKEN, not WATCH — the 07/24 oversold bounce off the DoD contract failed and the debt-headwind/breakdown thesis stands confirmed. This is now the **third** consecutive deep review recommending this exact exit (07-22, 07-23, 07-27 all made the same call; ORCL is still held). Position is tiny (1.33% weight) so the P&L stakes are low, but a broken thesis outranks drift regardless of size, and repeatedly re-proposing an unactioned exit without flagging the pattern isn't useful — flagging it now explicitly.

**5. Redeploy freed capital: GOOGL top-up ~$1,200, remainder ~$4,380 to cash**
Trims 1-4 free roughly $5,580. Compute/Hyperscaler is your worst cluster miss today — 9.24% vs a 20% target (band [15,25]), **-10.76pt under floor** — and GOOGL is the only Hyperscaler name in the book (6.9% weight, plenty of room under both its own band and the 12% single-position cap). A $1,200 top-up narrows the underweight without solving it outright — no second Hyperscaler name has been screened yet (recommend scout runs one next cycle: AMZN/MSFT are the obvious gaps). The larger remainder (~$4,380) goes to cash, not into the diversifier bench (NEM 38.9% upside, clean) — sentiment is greed-but-calm, not extreme fear, so this isn't a "back up the truck" signal, and cash is genuinely thin (5.4%, low end of the [5,15]% normal band) heading into AMD's binary earnings on 08-04 with only ~5.4% buffer against a miss. Rebuilding cash here is the higher-priority use of the freed capital than a new diversifier position today.

**CEG — no action, explicitly**
One day post-entry (bought 07-28) is too soon to add or trim. Thesis just got its first line (WATCH, nuclear/clean generation, fresh leverage concerns flagged) and the reversal-buy-watch signal is untested. Revisit after 08-06 earnings (date now confirmed, was estimated 08-10). Holding, not proposing.

---

## Risk-off status — partial pushback on "normal"
`compute_drift.json` reads risk_off_status: **normal**, and on its own terms (drawdown -8.35% vs a 15% warn / 25% risk-off threshold) that's correct — you're nowhere near the drawdown-based risk-off trigger. **But that shouldn't be read as "book is fine."** The aggregate open-risk-cap breach (15.05% vs 10%, 1.5x cap) is a separate, position-level control that's firing hard right now, independent of the drawdown gate, and it's firing specifically because 11 names rallied into their stops in two sessions. Read this as: no emergency de-risking ladder trigger, but a live, ordinary-course risk-cap breach that the proposals above are sized to fix. Cash at 5.4% (low end of band) is the third data point pointing the same direction — don't treat "normal" as license to sit on hands into AMD's 08-04 print.

---

## Stress table (approximate — deep mode only, anchored to macro where possible)

| Scenario | Est. portfolio impact | Most exposed |
|---|---|---|
| AI-capex pause | ~-18.9% of total book (~-$7,770) — 94.6% AI-capex exposure × assumed -20% cluster move. Macro's tail didn't carry a specific `cluster_impact.ai_capex_chain` read this run (see data_quality) so this falls back to the static -20% assumption, unadjusted. | SNDK, DRAM, MU, ASML, MRVL |
| Rates +100bp | ~-1.5% of total book (~-$620) — anchored to macro's 10yr at 4.663% (+24.5bps/month, already climbing independent of the FOMC hold) and the priced-in hold; tempers a blind +100bp shock since the move is partly already underway, applied to the ~15% of book in high-beta/long-duration names | VRT, CEG, NBIS, IREN |
| Tariff/export-control escalation | ~-2.5% to -3% of total book (~-$1,050 to -$1,200) — China-revenue-exposed names at an assumed -15% | ASML, TSM, EWY, MRVL |
| USD/INR ±3% | ~0% on the USD-reported book itself (holdings and cash are USD). In INR terms for your net worth: a 3% INR depreciation adds ~3% to the book's INR value; a 3% INR appreciation subtracts ~3% — pure translation effect, no US-side portfolio action implied either way | n/a (translation only) |

## Hit-rate readout
Signals' tail for this run didn't carry bucket_hit_rates/name_bucket_grades with ≥3 scored entries — no bucket cleared the reporting threshold this run. Nothing to de-emphasize; nothing to report.

## Proposal-outcome scorecard
Checked proposals.json against today's date (2026-07-31): the earliest dated proposal (TSM top-up, 07-13) is 18 calendar days old — **none have reached the 30-day scoring mark yet**. Scorecard stays empty until mid-August; will populate starting with the 07-13 batch (TSM, LRCX, CRDO, VRT) around 08-12.

## Data quality
- MRVL bucket reconciliation: orchestrator's rotation/central-decision framing placed MRVL in the mechanical-bounce group; thesis independently upgraded it to STRENGTHENING same-run. Resolved by treating it per the fresher per-name thesis read (proposal 3), flagging the conflict rather than silently picking one.
- Macro tail lacked an explicit `cluster_impact.ai_capex_chain` figure this run — AI-capex-pause stress scenario used the static -20% fallback per the task's own fallback rule, not macro's live read.
- G1 (LTCG): lots.json has only 4 seeded lots (GOOG, AVGO, TSM, ASML, all opened 2026-07-28) — no trim candidate above has an LTCG-boundary date available; none of today's trim proposals are LTCG-deferrable on current data.
- G18 (SPY/QQQ max-pain) and G32 (INDmoney feed staleness) both stand as previously logged, unchanged this run.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim SNDK","size_usd":1300,"price_at_proposal":null,"rationale":"4.13x risk cap (largest excess $2,061.54), ATR20 15.6% highest-vol name in book, WATCH thesis, peer laggard -25.9pp vs SMH, zero resolving fact per catalyst, cures part of Memory/Storage cluster +9.2pt breach"},
   {"action":"Trim MU","size_usd":900,"price_at_proposal":null,"rationale":"2.47x risk cap, WATCH thesis, peer laggard, HBM3E ASP still -51% from peak with no fresher print, mechanical co-movement with SMH/KOSPI per thesis"},
   {"action":"Trim DRAM","size_usd":900,"price_at_proposal":null,"rationale":"2.53x risk cap, WATCH thesis, peer laggard, same Memory/Storage cluster breach as SNDK/MU"},
   {"action":"Trim ASML","size_usd":700,"price_at_proposal":null,"rationale":"1.67x risk cap, WATCH thesis, peer laggard, cluster in-band so pure name-level risk discipline"},
   {"action":"Trim COHR","size_usd":340,"price_at_proposal":null,"rationale":"1.35x risk cap, peer laggard -11 to -26pp range, Optics cluster in-band, name-level risk-cap cure"},
   {"action":"Light trim MRVL","size_usd":400,"price_at_proposal":null,"rationale":"2.25x risk cap but thesis upgraded to STRENGTHENING today (Nvidia/Trainium, record revenue) -- sized lighter than mechanical-bounce group despite orchestrator's bucket placement"},
   {"action":"Light trim VRT","size_usd":150,"price_at_proposal":null,"rationale":"1.43x risk cap, STRENGTHENING thesis but peer laggard signal, fresh 39.5% target-gap upside per watchlist -- smallest trim in genuine-improvement group"},
   {"action":"Light trim NVDA","size_usd":150,"price_at_proposal":null,"rationale":"1.11x risk cap, peer leader +15.3pp vs SMH, fresh 35.6% target-gap upside -- trim is cap-cure only, not a signal on the name"},
   {"action":"Light trim AMD","size_usd":100,"price_at_proposal":null,"rationale":"1.22x risk cap, STRENGTHENING thesis but 08-04 binary earnings in 4 trading days -- reduce single-name risk into a known catalyst"},
   {"action":"Light trim NBIS","size_usd":100,"price_at_proposal":null,"rationale":"1.24x risk cap, just upgraded to STRENGTHENING (Nvidia 9.3% stake, contract-backed debt raise) -- token trim only"},
   {"action":"Exit ORCL (full remaining stake)","size_usd":480,"price_at_proposal":null,"rationale":"Thesis BROKEN, third consecutive deep review recommending this exit (07-22, 07-23, 07-27), tiny 1.33% weight -- broken thesis outranks drift regardless of size"},
   {"action":"Top up GOOGL","size_usd":1200,"price_at_proposal":null,"rationale":"Compute/Hyperscaler cluster -10.76pt under floor, only Hyperscaler name in book, ample room under both cluster band and 12% single-position cap, funded by trims above"},
   {"action":"Rebuild cash buffer","size_usd":4380,"price_at_proposal":null,"rationale":"Cash 5.4% at low end of [5,15]% normal band, AMD 08-04 binary earnings is the live catalyst risk for a 100%-AI-capex book with thin dry powder, greed band is calm-not-euphoric so no urgency to fully redeploy today"}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["MRVL reclassified from orchestrator's mechanical-bounce bucket to genuine-improvement group per thesis's same-run STRENGTHENING upgrade -- flagged, not silently resolved","AI-capex-pause stress scenario used static -20% fallback, macro tail lacked explicit cluster_impact.ai_capex_chain figure this run","G1: lots.json only covers 4 lots (GOOG/AVGO/TSM/ASML, all 07-28) -- no LTCG-boundary data for any trim candidate above","No bucket in signals' tail reached the >=3 scored-entry hit-rate threshold this run","No proposal in proposals.json has reached the 30d mark yet -- earliest is 18 days old (07-13); scorecard empty by design, not by omission"]}
```

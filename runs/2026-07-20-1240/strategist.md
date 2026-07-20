# Portfolio Strategist — US Book (Deep) — 2026-07-20, run 2026-07-20-1240

Book value: $38,879.56 (live-corrected, G3). All proposals below are for review only — nothing here is executed.

## 0. Policy Draft Status — needs your confirmation

policy.json exists but `confirmed: false` (as_of 2026-07-12, already stale — book has turned over 28→29 holdings with heavy composition change since). This run's drift table used its targets/bands as-is; treat all drift language below as **provisional — draft policy**, not a confirmed mandate. Specific points needing your sign-off, not just a rubber stamp:

- **max_ai_capex_factor_pct = 90%** — the policy's own notes admit this was "generous" when set (rounded up from 88.5% actual) and sits 30pt above the drafter's own 60% sane-diversification threshold. It is now breached at **99.203%** — essentially the whole book is one macro bet. Decide: (a) confirm 90% as a real ceiling and commit to trimming toward it, or (b) acknowledge the book is intentionally a concentrated AI-capex bet and raise the cap explicitly (with eyes open) rather than carrying a number nobody intends to defend.
- **AI Power/Cooling/DC Infra target 15% / band [10,20]** — actual is 3.726%, the single worst cluster miss on the book (-11.27pt). Confirm this target still reflects intent; if power/cooling conviction has genuinely cooled, lower the target instead of carrying a permanent large breach.
- **Compute/Hyperscaler cluster line (target 10%, band [5,15])** — added 2026-07-18 without confirmation (G11). Needs explicit sign-off or removal.
- **max_single_position_pct = 12%** — not currently binding (SNDK, the largest position, is 10.48%), no change needed, just confirm.
- **cash_band [3,15]%** — a default, not derived from the book. Currently breached at 0.06% (effectively zero cash). Confirm the band itself before treating this as an actionable breach magnitude.
- **prefer_ltcg = true / 24-month boundary** — cannot be operationalized until lots.json is populated (G1, standing since 2026-07-12).

No new policy bootstrap performed this run (a policy already exists) — the above is refinement guidance, not a rewrite. I have not altered policy.json.

## 1. Sized Proposals (for your review — none executed)

**1. Trim SNDK ~$700** (live price $1,354.82 — down sharply from the $1,842.10 anchor used in the still-open 2026-07-18 proposal; that stale figure should be treated as superseded by this one). Rationale: AI Memory/Storage cluster is over its band top (25.811% vs [15,25], +0.811pt over-band = ~$315 of the breach is priced into this trim); SNDK remains the book's largest single position (10.48%) and is called out again this run as a peer-relative laggard (-22.3% vs SMH); trimming a chain name also chips at the AI-capex cap breach (99.203% vs 90%) and is the primary lever to rebuild cash from its current 0.06%. LTCG: G1 stands (lots.json empty) — cannot confirm holding period before executing; SNDK also has a documented 3x qty-whipsaw-in-48h pattern from mid-July, so lots are plausibly short-term anyway — check lot dates in the app before trimming regardless of what this note assumes.

**2. Trim AMAT ~$350** (price $529.66, today's flag). Rationale: fresh STRONG DOWNTREND + INSIDER ACTIVITY + a new MOMENTUM+VOLUME journal entry today, on top of a recurring insider-selling flag that has now appeared across multiple runs (CEO block sales, unresolved) — this signal deterioration outranks the nominal analyst-target upside ($623.06). AI Semis/Fabs cluster is at the top of its band (34.33%/[25,35]) with zero headroom per thesis factor flags, so this trim also creates room rather than just reacting to price. Proceeds route to cash/diversifier below. LTCG: G1 stands, check lot dates before executing.

**3. Deploy ~$300 into NEM** (live price $89.70, target $133.00, +32.6% upside — scout's top-ranked clean diversifier). Rationale: Diversified/Regional ETF cluster sits at 0% (vs 5% target) — the one cluster on the book with zero exposure; NEM carries no AI-capex overlap, directly working against the 99.2% factor-concentration breach rather than just moving money within the same bet. Sized small (not a full tranche) because cash is the more urgent priority this run (see #4) and NEM is itself rate-sensitive on the other side (gold vs real rates) in a hawkish-Fed backdrop — a starter position, not a conviction sizing.

**4. Route remaining ~$750 of trim proceeds to cash, and hold — no new AI-capex-chain deployment this run** (defers the still-open 2026-07-18 "Stage into VRT ~$600 @ $310" proposal). Rationale: cash is at 0.06% vs a [3,15]% band — effectively zero dry powder, the most severe breach on the book in practical terms; GOOGL earnings land in 2 trading days (2026-07-22) as an explicit volatility catalyst for the whole AI-capex chain per macro's `cluster_impact`, and the Fed stance is hawkish with the 10-yr rising — not a backdrop for adding to the very cluster (Power/Cooling/DC Infra) that's both underweight and rate-sensitive. Rebuilding cash first, revisiting VRT/Power-Infra after GOOGL earnings clears, is the more defensible sequencing. (Two other 2026-07-18 open items — "Trim CIEN to fund META" and "Stage into META ~$500" — are unaffected by this note and remain open/unfunded pending cash; not re-litigated this run.)

**Net effect of 1-4**: ~$1,050 raised from trims, ~$300 redeployed to a genuine diversifier, ~$750 to cash (cash would move from ~$23 to ~$770 — still short of the $1,166 band floor (3%), but a real step, not a token one).

No proposal here adds to a broken-thesis name — `thesis_changed` is empty this run (28/29 unchanged, none newly broken), so nothing on the book is currently flagged BROKEN; AMAT's trim is signal-driven (insider + downtrend), not a thesis-break call.

## 2. Risk-Off Check

`compute_drift.json` risk_off_status = **normal** (drawdown 0.0%, vs warn/risk-off thresholds) — but that 0.0% is a pre-open/no-tick artifact (Friday's close carried forward, book tail's own caveat), not a genuine at-peak reading. Separately, and not to be conflated with the drift gate: smith-macro's independent market-regime read is **risk_off** (hawkish Fed + rising 10-yr + SPX off its 52-week high + elevated SPY/QQQ put skew) — a market-wide hedging posture, not a portfolio-drawdown signal. Net stance: the portfolio's own gate hasn't fired, but given (a) the macro regime read, (b) the AI-capex cap breach, and (c) near-zero cash, this run's proposals lean toward trims, cash-rebuild, and one small clean-diversifier tranche rather than any new AI-capex-chain adds — consistent with a "tighten, don't deploy into the same bet" posture even though the formal risk-off gate is "normal."

## 3. Stress Table (approximate, macro-anchored — deep mode)

| Scenario | Est. portfolio impact | Most exposed |
|---|---|---|
| AI-capex pause (-20% assumed cluster move) | -19.8% / -$7,713 | Combined AI-capex clusters (99.2% of book) — SNDK, AMAT, AMD, MRVL, COHR, VRT, NVDA. Macro's `cluster_impact.ai_capex_chain` reads "pressured" already (hawkish Fed + rising 10yr compressing forward multiples), so no discount applied to the -20% base case — if anything this is a floor, not a stretch, with GOOGL earnings (Jul 22) as the near-term trigger. |
| Rates +100bp | -5.8% / -$2,263 | Approximated via the top-10 holdings (58.2% of book, high-beta: AMD 2.47, MRVL 2.20, NVDA 2.21, COHR 2.04, VRT 2.03) × -10%. Anchored to macro's live 10-yr (4.541%, +7.8bps/1mo) and hawkish FOMC stance — a further +100bp from here (10yr toward ~5.5%) is a real tail, not an arbitrary base. No full per-name weight table available this run, so this is cluster/top10-approximated, not name-by-name. |
| Tariff/export-control escalation | ~-6% / -$2,330 (rough) | China-revenue-exposed names inside AI Semis/Fabs (TSM, ASML, AMAT, LRCX, QCOM, AMD) — assumed -15% on the China-exposed sub-slice (~40% of book, very approximate, no per-name China-revenue % available). |
| USD/INR ±3% | ~0% on the USD book; real for your INR net worth | This is a USD-reported book — a ±3% INR move doesn't change the $38,879.56 figure. In INR terms, a 3% INR depreciation vs USD (currently 96.4825) would add roughly ₹112,600 to this asset's rupee value (and the reverse on INR appreciation) — a currency effect on your net worth, not a portfolio-management signal. |
| Broad market correction (SPX -15%) | ~-21.8% / -$8,456 | Book-beta-adjusted using the ~1.4-1.5 portfolio beta estimate from this run's refreshed betas (not yet folded into compute_book.json's still-default 1.0) — driven by the same high-beta top10 as the rates scenario. |
| Single-name shock: SNDK -30% | -3.1% / -$1,222 | SNDK only (10.48% weight) — but note this compounds directly into the AI Memory/Storage cluster breach and the AI-capex cap, so a real SNDK drawdown would ease two drift breaches even as it hurts P&L. |

All figures are approximate scenario arithmetic, not modeled/hedged outcomes — sized to show relative exposure, not to predict precision.

## 4. Hit-Rate Readout

No hit-rate data this run. `journal.json`'s `bucket_hit_rates`/`name_bucket_grades` are both empty per smith-signals — insufficient scored history (standing gap, portfolio tracking only started 2026-07-12). Nothing to de-emphasize yet; will populate once entries age past their scoring windows.

## 5. Proposal-Outcome Scorecard

No proposals have reached the 30d/90d scoring window yet. Oldest open proposal (2026-07-13, "Trim MU...") is 7 days old; the earliest cohort scores at ~2026-08-12. `proposals.json`'s own scorecard already carries `trim_accuracy_30d/add_accuracy_30d/overall_accuracy_30d` as null — consistent with this read, not fabricating a rate here.

Qualitative note (not a scored accuracy figure): of proposals closed as fulfilled/executed so far — TSM top-up, LRCX restore, CRDO re-entry, VRT re-entry (07-13/07-14), STM trim and COHR deploy (07-17/07-18) — all matched real user trades directionally, and the MRVL re-entry proposal was correctly *not* taken (user agreed, citing the double insider-sell flag this note also relied on). That's a directional read, not a price-target scorecard.

## Data Quality
- G1: lots.json empty — LTCG boundary checks unavailable for any trim proposal above; flagged per-proposal.
- G3: INDmoney feed staleness vs live quotes (worst this run — 25/29 names diverged >3%); live-corrected $38,879.56 used throughout, per holdings.json.
- G11: Compute/Hyperscaler cluster line added to draft policy 2026-07-18 without confirmation — flagged in the policy section above.
- SNDK/DRAM beta unavailable from any source (book tail, genuine gap) — excluded from the stress-table beta-weighted scenarios' underlying assumptions where relevant.
- ARM (3.77) / IREN (4.28) betas computed but discarded — exceed the 0-3.5 plausibility band, not ingested.
- Rates+100bp and tariff/export-control scenarios use top10/cluster-level approximation, not full per-name weights (no complete name-by-name weight tail was available to the strategist this run) — flagged as lower-precision than the AI-capex-pause and USD/INR lines.
- SNDK price used ($1,354.82, live yfinance quote) supersedes the stale $1,842.10 anchor carried in the still-open 2026-07-18 proposal in proposals.json — that record should be updated/closed by the orchestrator, not left as the active anchor.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim SNDK","size_usd":700,"price_at_proposal":1354.82,"rationale":"AI Memory/Storage cluster over band top (25.811% vs [15,25]); largest single position (10.48%) and renewed peer-laggard (-22.3% vs SMH); reduces AI-capex cap breach (99.203% vs 90%) and rebuilds near-zero cash (0.06% vs [3,15]%). LTCG unresolved, G1."},
   {"action":"Trim AMAT","size_usd":350,"price_at_proposal":529.66,"rationale":"Fresh STRONG DOWNTREND + INSIDER ACTIVITY + new MOMENTUM+VOLUME journal entry, recurring unresolved insider-selling flag outranks nominal analyst-target upside; AI Semis/Fabs cluster at top of band (34.33%/[25,35]) with zero headroom. LTCG unresolved, G1."},
   {"action":"Deploy into NEM","size_usd":300,"price_at_proposal":89.70,"rationale":"Diversified/Regional ETF cluster at 0% vs 5% target; NEM is scout's top clean diversifier (no AI-capex overlap), directly working against the 99.2% factor-concentration breach. Sized small given cash is the more urgent priority."},
   {"action":"Hold -- no new AI-capex-chain deployment (defers 2026-07-18 VRT stage-in ~$600); route remaining ~$750 trim proceeds to cash","size_usd":750,"price_at_proposal":null,"rationale":"Cash at 0.06% vs [3,15]% band is the most severe practical breach; GOOGL earnings in 2 trading days is an explicit AI-capex-chain volatility catalyst per macro cluster_impact; hawkish Fed + rising 10yr argue against adding to the underweight but rate-sensitive Power/Cooling/DC Infra cluster right now."}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["G1 lots.json empty -- LTCG unresolved for all trim proposals","G3 INDmoney staleness, live-corrected value used","G11 Compute/Hyperscaler cluster added without confirmation","SNDK/DRAM beta unavailable (genuine gap)","ARM/IREN betas discarded, exceed 0-3.5 plausibility band","stress table rates/tariff scenarios approximated at cluster/top10 level, no full per-name weight tail available","stale SNDK price anchor ($1,842.10) in the still-open 2026-07-18 proposals.json entry superseded by this run's live $1,354.82 -- record should be reconciled by orchestrator","no proposals yet reached 30d/90d scoring window, first cohort scores ~2026-08-12"]}
```

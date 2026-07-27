# Agent Smith — Portfolio Strategist (Deep Review, 2026-07-27)

## Policy status
Policy is **NOT confirmed** (`confirmed: false`). All drift/breach analysis below is provisional pending your sign-off — including known gap G11 (the Compute/Hyperscaler cluster line was added to the draft without your confirmation). No policy edits made here; treat every breach reference as "vs draft policy," not settled targets. No new bootstrap needed — a draft already exists.

## Sized Proposals (for your review — none executed)

**1. Trim MRVL ~$300** — price_at_proposal: not in embedded tail, use last close (fallback: state.json if needed before executing). Rationale: AI Semis/Fabs cluster is +8.7pt over its 35% band ceiling; MRVL carries a STRONG DOWNTREND signal and is named among today's "worst laggards" (thesis tail), with no earnings-proximity buffer (unlike LRCX/TER/QCOM, already de-risked into their prints). Unlike NVDA — which is genuinely leading the sector (RS +17.6, NEW TAILWINDS) and should not be trimmed into a cluster breach — MRVL is a laggard funding source. Modest size: no position-level breach exists (position_breaches: []), so this is a cluster-level nudge, not a forced sale.

**2. Deploy ~$700 of idle cash into GOOG near watchlist levels** — target-gap 24.35% upside, Compute/Hyperscaler cluster (-7.6pt underweight, the book's most under-owned cluster). This addresses two breaches at once: cash at 46.09% vs [3,15]% ceiling, and the Compute/Hyperscaler underweight. Sized deliberately small (not a full redeployment) — the 07-29 FOMC decision lands the same day as LRCX/QCOM earnings, a single-day catalyst convergence macro flags explicitly; hawkish Fed + 10yr at 4.679% (+27.7bps/mo) argues for staging entries into that date, not committing size ahead of it.

**3. Exit ORCL (full remaining small position)** — thesis is BROKEN, not watch: standing debt-headwind/breakdown thesis, and the 7/24 oversold-bounce off the $7B DoD contract win FAILED — stock continued lower 7/25 despite positive news, confirming the break rather than a reversal. STRONG DOWNTREND signal persists. Per standing rule, thesis-broken names outrank pure drift breaches as trim candidates regardless of size (ORCL carries no position or cluster breach on its own — this is a thesis exit, not a rebalancing trim). Exact dollar size should be confirmed against the live lot in state.json before execution; small weight keeps tax/realization impact minor. LTCG check: lots.json is unseeded (gap G1) — no holding-period data available to assess STCG/LTCG differential on this exit; flagging the gap rather than estimating blind.

**4. Deploy ~$400 into NEM (clean diversifier bench)** — beta 0.48, zero AI-capex overlap, 42.72% target-gap upside per scout. This is the cleanest available lever against the standing single-factor risk (100% of the equity sleeve sits in the AI-capex chain per thesis tail) and doesn't compete with the FOMC/earnings-convergence timing risk in proposal #2, since gold has no correlation to that catalyst. Sized small relative to the $18.6k cash pile deliberately — sentiment is "greed" (66.7), not "extreme greed," so this is a partial, not full, redeployment signal.

**5. Hold MU — no add, revisit after Aug 5 earnings** — the 38.9% analyst target-gap is real, but thesis status is WATCH (downgraded from strengthening), driven by the HBM3E ASP collapse (-51% peak-to-current) making DDR5 contract pricing now more profitable than HBM3E — a live margin-mix headwind. TrendForce's 2027 volume/mix forecast (+80-150% contract surge) is a bull case, but it is not confirmed yet and the print is ~9 days out. Per standing rule, WATCH names do not get added to regardless of drift or upside gap; defer the add/trap decision to Q3 earnings.

## Risk-off status
`risk_off_status: normal` — **confirmed, not overridden**. Drawdown is -5.857% off total-book peak, well inside the 8% warn / 12% risk-off thresholds. The severe cash-ceiling breach (46.09% vs [3,15]%) is a structural/allocation issue, not a drawdown event, and correctly does not trigger risk-off machinery on its own — the two metrics are independent by design. That said, given the 07-29 FOMC+earnings convergence two days out, proposals above are sized conservatively (staged, not full redeployment) as a matter of prudence, not because risk-off status demands it.

## Stress Table (approximate, macro-anchored — deep mode)

| Scenario | Est. portfolio impact | Most exposed |
|---|---|---|
| AI-capex pause | ~-10.8% of total book (≈ -$4,260) — combined AI-capex exposure is 53.9% of total book; assumed -20% cluster move tempered by macro's near-term tailwind read (futures gap-up pre-open) against the 07-29 FOMC+earnings "blast radius" | NVDA, SNDK, VRT, MRVL |
| Rates +100bp | ~-2.2% of total book (≈ -$885) — anchored to macro's 10yr at 4.679% (+27.7bps/mo) and hawkish FOMC stance rather than a blind +100bp from an arbitrary base; high-beta long-duration names (SNDK β2.566, DRAM β2.202, ARM β1.756) drive most of the move | SNDK, DRAM, ARM, MRVL |
| Tariff/export-control escalation | ~-1.6% of total book (≈ -$630) — China-revenue-exposed / supply-chain names, assumed -15% on the affected sub-set | EWY, ASML, LRCX, AMAT |
| USD/INR ±3% | ~0% on the USD-reported book (correct — no direct exposure) | — |
| USD/INR ±3% (INR-terms net worth) | A 3% INR depreciation vs USD adds ~+3% to this book's value in INR terms (US assets more valuable in INR); a 3% INR appreciation subtracts ~3% in INR terms | Whole book (currency pass-through, not stock-specific) |

Note: AI-capex pause and rates scenarios are explicitly anchored to smith-macro's live regime read (10yr level, hawkish FOMC stance, cluster_impact) rather than static assumptions; tariff scenario falls back to a static -15% assumption (no live macro figure available for it).

## Hit-rate readout
No bucket has ≥3 scored entries this run — journal's newest additions (QCOM, LRCX, TER, all EARNINGS PROXIMITY) were just flagged today and aren't due for 30d/90d scoring yet. `unchanged_count: 5` signals from prior runs persist without new resolution. No de-emphasis recommendation this run — insufficient scored history.

## Proposal-outcome scorecard
Checked proposals.json: all entries fall between 2026-07-13 and 2026-07-20 — the oldest is 14 days old, short of the 30-day scoring mark (first eligible ~2026-08-12). **No proposals are due for 30d/90d scoring this run.** All prior proposals (TSM top-up, LRCX restore, CRDO re-entry, VRT re-entries x2, COHR deploy, and others through 7/20) remain open/pending. Will score at or after 2026-08-12.

## Data quality notes
- G1: lots.json unseeded — LTCG proximity unavailable for the ORCL exit and all trim candidates; cited rather than re-derived.
- G11: Compute/Hyperscaler cluster line in draft policy still unconfirmed by user.
- G18: SPY/QQQ max-pain unavailable both names.
- price_at_proposal for MRVL trim and ORCL exit not available in embedded tails or scout's bench (scout's live pricing only covers diversifier candidates) — flagged as a gap rather than estimated; confirm live price before execution.
- Proposal sizes are directional/approximate, intentionally rounded — not exact share counts.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim MRVL","size_usd":300,"price_at_proposal":null,"rationale":"AI Semis/Fabs cluster +8.7pt over band; MRVL STRONG DOWNTREND, named worst-laggard, no earnings-proximity buffer unlike LRCX/TER/QCOM"},
   {"action":"Deploy into GOOG","size_usd":700,"price_at_proposal":null,"rationale":"Cash 46.09% vs 15% ceiling; Compute/Hyperscaler cluster -7.6pt underweight; GOOG target-gap 24.35%; sized small ahead of 07-29 FOMC+earnings convergence"},
   {"action":"Exit ORCL","size_usd":null,"price_at_proposal":null,"rationale":"Thesis BROKEN -- 7/24 oversold bounce off $7B DoD contract failed, stock continued lower 7/25; standing debt-headwind/breakdown thesis confirmed, not reversed; thesis-broken outranks drift regardless of size; LTCG unknown (gap G1)"},
   {"action":"Deploy into NEM","size_usd":400,"price_at_proposal":null,"rationale":"Clean diversifier, beta 0.48, zero AI-capex overlap, 42.72% upside; addresses 100%-AI-capex single-factor risk independent of FOMC timing; greed band not extreme-greed so partial not full redeployment"},
   {"action":"Hold MU, no add","size_usd":0,"price_at_proposal":null,"rationale":"Thesis WATCH not broken -- HBM3E ASP margin-mix headwind unresolved until Aug 5 earnings; 38.9% target gap is real but WATCH names are not added to regardless of upside gap"}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["G1: lots.json unseeded, LTCG unavailable for ORCL exit and trim sizing","G11: Compute/Hyperscaler cluster target unconfirmed by user","G18: SPY/QQQ max-pain unavailable","price_at_proposal null for MRVL trim and ORCL exit -- not covered by scout's live-price bench, confirm before execution","no proposals reach 30d scoring threshold this run (oldest is 14 days old); first eligible ~2026-08-12"]}
```

# Portfolio Strategist — Stage 2 (quick sweep, run 2026-07-23-1907)

Policy status: present, unconfirmed draft (policy.json). No bootstrap needed this run — proceeding on the existing draft targets. Drift analysis remains "provisional — draft policy" until the user confirms policy.json.

## Central reconciliation: rebound's stage-in bench vs actual cash

Cash is effectively zero: wallet $36.14, cash_pct 0.086% vs a 3% floor ($1,257.70 needed at today's $41,923.47 book) — a $1,221.56 shortfall just to reach the floor, before any redeployment. This is *worse* than yesterday (1.109%) because the GEV wallet-buy consumed the remainder.

smith-rebound's headroom math ($3,635-type figures) was computed against cluster/policy bands, not against the real $36.14 wallet — none of its five stage-ins ($500 GEV / $500 VRT / $400 LITE / $400 COHR / $500 META, $2,300 total) are fundable today without first raising cash. Decision: (a)+(b) combined — restate yesterday's still-open SNDK trim and ORCL exit as explicit prerequisites, and resize the rebound bench down to what those proceeds can actually fund, in priority order, rather than proposing the full $2,300.

Math: SNDK trim ($1,500) + ORCL exit ($530) = $2,030 raised. Reserve $1,221.56 to clear the cash floor → $808 left for redeployment. That funds roughly one rebound stage-in near its proposed size, not four. AI Power/Cooling/DC Infra is the single worst cluster breach on the book (-8.065pt, worse than Networking/Optics at -5.253pt), and VRT is trading right at rebound's flagged support ($300.45 vs live $303.07) — it gets the $808, sized to ~$500 with a buffer left in cash. LITE, COHR, and META stage-ins have no funding path this run and are deferred, not rejected.

## GEV — specific read

The user bought more GEV today (1.0008→1.3950sh, +$394, wallet-funded) on the same day its thesis flipped STRENGTHENING→WATCH (Q2 EPS miss despite guidance raise, -7.4% today, lost STRONG UPTREND, now PEER LAGGARD vs XLU). Reads as a coincidence of timing (buy likely queued/decided before the earnings reaction, or a same-day average-in that didn't yet price the print) rather than a deliberate buy-the-dip-on-bad-news call — but the effect is the same regardless of intent: the position was just added to, into a softening thesis, same day. That argues for zero further GEV exposure regardless of size, independent of the cash question. Rebound's $500 GEV suggestion is declined outright: not "deferred for lack of cash" but "no, on thesis-timing grounds" — WATCH is not BROKEN, so the existing (now-larger) position stays, but this is not a name to average further until Q3 execution is confirmed.

## Proposals (dated 2026-07-23, quick sweep)

1. **Trim SNDK ~$1,500** @ $1,605.38 (live) — restates 2026-07-22's open proposal. AI Memory/Storage is the largest cluster breach on the book (27.008% actual vs 20% target, band top 25%, +7.008pt over target); SNDK is the single largest position and a renewed peer-laggard; trimming addresses the cluster breach, the AI-capex-factor breach (98.61% vs 90% cap), and funds the cash floor simultaneously. LTCG: lot-purchase dates unavailable (G1) — cannot confirm whether any lot is within 6 months of the 24-month Indian LTCG boundary; flagged rather than assumed either way.

2. **Exit ORCL ~$530** @ $125.03 (live, down -1.6% today) — restates 2026-07-22's open proposal. Thesis is BREAKDOWN (unchanged), fresh 21-Jul credit downgrade, and a new peer-laggard read vs XLK; small position makes a full exit cleaner than a partial trim, and it adds directly to the cash rebuild alongside the SNDK trim. LTCG: same gap, G1.

3. **Hold — no further GEV add**, despite smith-rebound's $500 stage-in suggestion. GEV was already added to today ($394, wallet-funded) on the same day its thesis downgraded to WATCH; adding more compounds a position that just grew into a weaker thesis, and GEV/Power-Cooling-DC-Infra is capex-chain exposure the book is already over-concentrated in (ai_capex 98.61% vs 90% cap). This hold stands regardless of cash availability.

4. **Stage into VRT ~$500** @ $303.07 (live, essentially at rebound's flagged $300.45 support) — contingent on proposals 1-2 executing first and clearing the cash floor. AI Power/Cooling/DC Infra is the worst cluster breach on the book (-8.065pt) with GEV now off the table as a fix (proposal 3); VRT is rebound's next-best vehicle for that cluster and the only one of its four remaining bench names this run's freed cash can actually cover (~$808 available after the floor reserve, leaving a small buffer).

5. **Defer LITE ($400) / COHR ($400) / META ($500) stage-ins** — no funding path this run even after the SNDK/ORCL trims and the VRT stage-in above; all three remain valid rebound setups (support levels intact, none on the thesis-WATCH stay-out list) and should be revisited once cash is rebuilt further or a subsequent trim frees more room.

## Risk-off status

Normal. Drawdown 0.0%, new portfolio peak today ($41,923.47), beta 1.493. No risk-off tightening triggered by drift or drawdown thresholds. The cash-floor breach argues for discipline (fund the floor before any new deployment, as above) but this is a policy-band issue, not a drawdown/risk-off one — sentiment band is "greed" (65.4), not extreme, so no sentiment-driven reframing of these proposals either (per policy, extreme_greed/extreme_fear framing only; greed is neutral-treatment).

## Hit-rate readout

Not scoreable this run. journal.json's `bucket_hit_rates` is empty — no bucket has ≥3 entries with an actual worked/missed price-target verdict yet. The only "scored": true entries (DELL, DLR, VRT) were closed via position-exit bookkeeping, not price-target outcomes, and are explicitly noted in the journal as non-verdicts. The earliest cohort (2026-07-12) crosses the 30-day scoring window around 2026-08-12 — nothing to de-emphasize yet.

## Proposal outcomes / scorecard

Not applicable this run (quick sweep, not deep/monthly). proposals.json's own scorecard confirms zero proposals have reached the 30d/90d scoring window (earliest open cohort is 2026-07-13, 30d mark ~2026-08-12).

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim SNDK","size_usd":1500,"price_at_proposal":1605.38,"rationale":"AI Memory/Storage cluster over target by 7.008pt (27.008% vs 20%, band top 25%); largest single position and renewed peer-laggard; funds cash floor and reduces ai_capex breach (98.61% vs 90% cap). LTCG unresolved, G1. Restates 2026-07-22 open proposal."},
   {"action":"Exit ORCL (full remaining stake)","size_usd":530,"price_at_proposal":125.03,"rationale":"Thesis BREAKDOWN persists, fresh credit downgrade, peer-laggard vs XLK; small position better exited fully; adds to cash rebuild. LTCG unresolved, G1. Restates 2026-07-22 open proposal."},
   {"action":"Hold - no further GEV add","size_usd":0,"price_at_proposal":984.94,"rationale":"Position already added to today ($394, wallet-funded) same-day as thesis downgrade STRENGTHENING->WATCH; declining rebound's $500 suggestion on thesis-timing grounds, independent of cash constraint."},
   {"action":"Stage into VRT (contingent on SNDK/ORCL trims clearing cash floor first)","size_usd":500,"price_at_proposal":303.07,"rationale":"Worst cluster breach on the book (AI Power/Cooling/DC Infra, -8.065pt) with GEV ruled out as the fix; VRT at rebound's flagged support ($300.45); only bench name the ~$808 post-floor cash can cover."},
   {"action":"Defer LITE/COHR/META stage-ins - no funding path this run","size_usd":0,"price_at_proposal":null,"rationale":"After SNDK/ORCL trims, cash floor reserve, and the VRT stage-in, no cash remains; all three stay valid setups for a future run once more cash is freed."}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "risk_off_status":"normal",
 "hit_rate_summary":"no buckets scoreable yet -- bucket_hit_rates empty, earliest cohort crosses 30d window ~2026-08-12",
 "deemphasize_buckets":[],
 "data_quality":["SNDK/ORCL/VRT prices refreshed live via yfinance this run (SNDK $1,605.38, ORCL $125.03, VRT $303.07), all within plausible day-move bands of prior anchors","GEV price_at_proposal left at rebound's cited support level ($984.94) since no further add is being proposed","lots.json empty -- LTCG boundary checks unavailable for SNDK/ORCL trims, cite G1","rebound's headroom_usd_total_book figures do not net against actual wallet cash ($36.14) -- reconciled manually this run, flagging for orchestrator to correct at source"]}
```

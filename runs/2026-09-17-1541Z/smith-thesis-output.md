# smith-thesis — 2026-09-17-1541Z (quick, delta vs prior_findings_since 2026-09-16T21:25Z)

## 1. Thesis table

**Status changes this run: NONE.** Today's broad relief rally (VIX -11.2%, SMH +2.57%, Asia +0.7-1.4%) is not itself a thesis event for any name, per dispatch instruction, and no new fundamental fact surfaced that would move a verdict.

**Notable delta, status unchanged — COHR (strengthening):**
- Stop-out executed today: 3sh sold @$295 (stop order), position cut from 2.98% to ~2.01% wt (src: holdings.json/INDmoney transaction, as_of 2026-09-17).
- New evidence_against not previously logged in COHR's file: GLW's $2bn ATM equity program triggered an "optics-peer read-through" hitting COHR -11% same session (src: 247wallst.com, as_of 2026-09-14; catalyst:9744ffb8fe/68ffcdcb21, reaffirmed unresolved 2026-09-16). COHR's own Q4 beat/raise (2026-08-12) is untouched — this is contagion from a peer's financing event, not a COHR-specific fundamental break.
- Read: thesis intact (AI-optics demand, beat-and-raise quarter), but the stock is failing to fully participate in today's rally and carries an unresolved peer-contagion overhang. Not upgraded to WATCH — no COHR-specific negative fact, only sector read-through plus a mechanical stop. Flagging for next run to watch whether COHR decouples from GLW once the ATM issue resolves.

**Reviewed this run, concluded unchanged:** MU (WATCH), GLW (WATCH), GEV (WATCH), VRT (WATCH), TER (STRENGTHENING), AMAT (STRENGTHENING), ASML (WATCH), BE (STRENGTHENING), MSFT (STRENGTHENING).
- GEV/VRT: GLJ Research's contested Street-low Sell ($470 PT) on GEV remains an unresolved single-shop outlier vs GEV's own guidance raise — no new fact since 2026-09-14/16, WATCH stands on the independent SEC-EDGAR trailing-NI quality flag, not the GLJ call.
- TER: open_flags' 2026-08-19 "dust position" entry is stale/superseded (position is actually 5.0027sh/6.12% wt) — orchestrator hygiene issue, not a thesis matter; flagged again in data_quality below (also flagged by smith-signals this run).
- BE: rel_sigma +2.9 today (extreme outperformance) is consistent with the already-logged S&P 500 inclusion tailwind (effective 2026-09-21) and index-add positioning — not a new fact, no status action.
- MU: see HBM reconciliation below — confirms, does not change, the existing WATCH.

**Rest unchanged (15 names, no re-examination needed this run — no live signal, no open proposal, no news in window):** TSM, GOOG, KLAC, CLS, WDC, MRVL, APH, QCOM, LITE, ALAB, AMZN, STM, NOW, AMD, CIEN.

## 2. Factor cluster table (equity-basis weights, post-COHR-stop)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | TSM, ASML, TER, KLAC, AMAT, QCOM, AMD | 41.0% |
| AI Networking/Optics | MRVL, APH, LITE, ALAB, COHR, GLW, CIEN | 17.6% |
| Compute/Hyperscaler | GOOG, MSFT, AMZN | 14.7% |
| AI Power/Cooling/DC Infra | VRT, GEV, BE | 10.1% |
| AI Memory/Storage | WDC, MU | 7.7% |
| Compute/Hyperscaler OEM | CLS | 4.6% |
| Analog/Industrial Semis | STM | 2.5% |
| Enterprise Software | NOW | 1.9% |

Combined AI-capex chain (all clusters above except Analog and Enterprise Software) = **~95.6% of book**, essentially unchanged from prior runs. AI Semis/Fabs alone sits at 41.0%, still well above its 33% policy ceiling (already flagged by the orchestrator 2026-09-17 as a mechanical side-effect of other clusters shrinking, not a new buy — no new action here). Co-movement check: today's rally lifted the AI-capex clusters together with SMH (+2.57%) as expected for a single-factor book; no name bucked the tape in either direction.

## 3. Single-factor risk verdict

This remains, in substance, one bet: a ~95.6%-weighted wager that AI-datacenter capex keeps compounding, expressed across the whole value chain (fabs/tools, memory, optics/networking, power/cooling, and the hyperscalers buying the capacity). A broad AI-capex pause or de-rate — not a stock-specific event — would hit nearly the entire book simultaneously, exactly as seen on both the Amodei-essay selloff and today's relief rally moving almost every name in the same direction. The only genuinely uncorrelated slice is NOW (1.9%, enterprise software, demand-side not supply-side of the AI buildout) — STM (2.5%, analog/industrial) is a partial diversifier at best since it still carries semiconductor-cycle beta. Neither is large enough to meaningfully dampen the book's factor concentration.

## 4. HBMTracker reconciliation (MU only — EWY/DRAM not held)

Re-read `/Users/yb/Claude/HBMTracker/consumer_view.json` this run (generated_at 2026-09-15, staleness_days 0 for the run; HBM3/HBM3E price_staleness_days 0 as of 2026-09-15, HBM4 still 41 days stale/suspect-band per C2 — unchanged from last run, no fresher HBM4 figure available).

- **Metric:** HBM3E $/GB, stack-derived basis, mid $9.00/GB (band $8-10), tier1 source but per known-gap G12 the 2026-09-15 row is Silicon-Analysts-only (tier2 in substance despite the row-level tier1_corroborated flag) — treat with the caution the file itself prescribes.
- **Within-basis trend:** flat, 0.0% from 2026-07-19 to 2026-09-15 (`trend_pct_within_basis`).
- **Cross-basis check:** `cross_basis_change_is_meaningless: true` for HBM3E confirmed — the contract_quote segment (2025-06-30 $18.50 → 2026-01-15 $15.00, -18.92% within that basis) is NOT comparable to the stack-derived segment; no peak-to-current figure spanning the two was used.
- **Corrections checked:** C1 (phantom -51% HBM3E decline, resolved as a basis-splice artifact) and C2 (HBM4 band-spans-bases artifact) — both re-read, neither newly triggered by this run's data.
- **Verdict conflict:** none. MU's WATCH is driven by CXMT structural/capacity risk (qualification-stage HBM3E shipments to Alibaba/Cambricon, ~1yr ahead of the 2027 consensus timeline), not by ASP — a flat within-basis ASP does not contradict a capacity-risk WATCH.
- **Direction: no_action.** Forward context carried unchanged: DDR5>HBM3E profitability crossover (2026-04-21, TrendForce) and 2027 HBM contract prices forecast 80-150% higher (TrendForce, 2026-06-02) both remain in force and argue for eventual upside, but are not yet in the priced series.

## 5. Data quality (cap 6)
- TER's 2026-08-19 open_flags "dust position" entry is stale/superseded (actual position 5.0027sh/6.12% wt) — needs orchestrator cleanup; also flagged independently by smith-signals this run.
- HBM4 leg remains 41 days stale and suspect-band (C2) — not used in any verdict.
- HBM3/HBM3E 2026-09-15 row is Silicon-Analysts-only (tier2 in substance) per G12 despite a misleading tier1_corroborated flag — weighted accordingly, not with tier1 confidence.
- COHR's continued underperformance vs. today's broad rally is unexplained beyond the GLW-contagion read; no COHR-specific negative news found in this run's narrow budget — worth a dedicated check next run if it persists.
- No FMP/EDGAR verification calls spent this run (no status change met the G58 trigger); all "unverified" tags carried forward are pre-existing, not new gaps.

```json
{"thesis":{"changed":{"COHR":{"status":"strengthening","thesis":"RECONCILED. Optical/photonics for AI datacenter interconnect. Q4 FY26 beat rev/EPS with guide raised above the beaten quarter; today's stop-out (3sh@$295, now 2.01% wt) reflects an unresolved GLW-driven optics-peer contagion, not a COHR-specific break.","evidence_for":[{"claim":"Q4 FY26 revenue $2.05B beat $2.025B consensus, EPS $1.74 beat $1.65 consensus; guided Q1 rev $2.2-2.4B/EPS $1.85-2.05, above the just-reported quarter","date":"2026-08-12","source":"stockanalysis.com/stocks/cohr"},{"claim":"CEO cites AI-datacenter demand as outstanding, 7 consecutive quarters of record revenue","date":"2026-08-07","source":"INDmoney news"}],"evidence_against":[{"claim":"stop-out sold 3sh @$295 today, position cut 2.98%->2.01% wt, on a day the broad tape (SMH +2.57%) rallied -- COHR failed to fully participate","date":"2026-09-17","source":"holdings.json / INDmoney transaction"},{"claim":"GLW's $2bn ATM equity program triggered an optics-peer read-through, COHR -11% same session; catalyst reaffirmed unresolved as of 2026-09-16","date":"2026-09-14","source":"247wallst.com via catalyst:9744ffb8fe"}],"verified":"secondary","verified_against":"stockanalysis.com/stocks/cohr (earnings); INDmoney transaction record (stop-out)","verified_on":"2026-09-17","note":"Status unchanged (strengthening) -- no COHR-specific negative fact, only peer contagion + a mechanical stop. Precedent check not run (no status change)."}},"unchanged_count":24,"reviewed_unchanged":["MU","GLW","GEV","VRT","TER","AMAT","ASML","BE","MSFT"]},
 "sector_map":{"changed":{},"unchanged_count":25},
 "etf_constituents_updates":{},
 "findings_reaffirmed":["thesis:MU","thesis:GLW","thesis:GEV","thesis:VRT","thesis:TER","thesis:AMAT","thesis:ASML","thesis:BE","catalyst:9744ffb8fe","catalyst:ce8fa6cd04","catalyst:aa6e4a3cf0"],
 "ai_capex_pct":95.6,
 "factor_flags":["AI Semis/Fabs cluster ~41.0% of book, still above its 33% policy ceiling as a mechanical side-effect of other clusters shrinking -- orchestrator-flagged 2026-09-17, no new dispatch action this run","combined AI-capex chain exposure ~95.6% of book -- a datacenter-capex pause or broad de-rate hits nearly the entire book at once, as both the Amodei-essay selloff and today's relief rally demonstrated in opposite directions"],
 "thesis_tensions":[{"metric":"HBM3E usd_per_gb_mid, stack-derived","current_value":9.0,"basis":"stack_derived","trend_within_basis_pct":0.0,"verdict_conflict":"none -- MU WATCH is driven by CXMT capacity risk, not ASP; flat ASP does not conflict","direction":"no_action","reconciliation":"flat within-basis trend (2026-07-19 to 2026-09-15) is consistent with the existing WATCH rationale; C1/C2 basis-splice corrections re-checked, neither newly triggered; HBM4 leg still 41d stale/suspect-band, not used","corrections_checked":["C1","C2"]}],
 "data_quality":["TER open_flags dust-position entry (08-19) stale/superseded, needs orchestrator cleanup (also flagged by smith-signals)","HBM4 leg 41d stale, suspect-band (C2), excluded from all verdicts","HBM3/HBM3E 2026-09-15 row is tier2-only in substance (G12) despite a misleading tier1_corroborated flag","COHR underperformance vs. today's rally unexplained beyond GLW contagion -- no COHR-specific news found in this run's narrow budget","no G58 verification calls spent this run -- no status change met the trigger"]}
```

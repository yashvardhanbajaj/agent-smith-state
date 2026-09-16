# Smith Thesis & Factor — 2026-09-16 pre-open (quick), FOMC decision day

## 1. Thesis table — QUICK MODE: no status changes this run

Checked all 9 names signals flagged as having dropped STRONG DOWNTREND/MOMENTUM+VOLUME?/PEER LAGGARD
overnight (ASML, GEV, KLAC, TER, AMAT, APH, STM, GLW, CIEN) against yesterday's (2026-09-15) thesis
verdicts. **Verdict: no change on any of the 9, or on any other held name.** The overnight bounce (Asia
+0.7-1.4%, VIX -1.3% to 16.98, ES/NQ +1.1/+1.4%) is macro/technical — a washout of Monday's FOMC-eve +
Amodei-essay sentiment shock, not a fundamental resolution:

| Ticker | Verdict (unchanged) | Why the bounce doesn't move it |
|---|---|---|
| GLW | WATCH | $2B dilutive ATM equity program (filed 09-11) is a standing financing-structure catalyst, untouched by a price bounce — dilution risk doesn't reverse because the stock does. Expires 09-29. |
| GEV | WATCH | GLJ Research's Sell/$470PT (09-14) is a contested-but-real analyst view on backlog margin mix, not sector beta; the same-day guidance raise it's stacked against is already in evidence_for. Unresolved either way. |
| STM | WATCH | Underlying driver was a fundamental Q3 guide_below_consensus (vs $3.78B Street), not sentiment — the stock recovering ~0.3% premarket doesn't undo a guide miss. Peer-laggard flag correctly resolved (rel_sigma back above -1.0); the guide-driven WATCH stands on its own. |
| ASML | WATCH | Already carrying a "China-structural-risk-not-resolved-only-un-escalated" evidence_against line from 09-15; today's bounce (+1.04% premarket) adds nothing new to that read. |
| TER | STRENGTHENING | Q3 guide already well above consensus (fundamental strengthening call, unrelated to yesterday's -12.13% print). compute_triggers' catalyst_threat (CXMT) stays open as a structural watch item — the bounce doesn't touch that either. |
| AMAT | STRENGTHENING | Same logic — Q3/Q4 beat+guide already the basis for strengthening; yesterday's PEER LAGGARD flag was sector beta and has now cleared, consistent with (not causal to) the standing verdict. |
| KLAC, APH, CIEN | STRENGTHENING (quiet, status-only) | No name-specific catalyst crossed the watermark for any of the three; CIEN's own 09-03 beat+guide_above_consensus (earnings_facts cache) is the actual fundamental basis, and today's +4.6% premarket (largest mover in the group) is a continuation of that, not new information. |

Rest of book (18 names: AMZN, AVGO, MRVL, MSFT, MU, WDC, AMD, BE, NBIS, COHR, ALAB, TSM, VRT, CLS, QCOM,
GOOG, LITE, NOW): **unchanged, no new evidence crossing the 2026-09-16 watermark.** All reviewed_on
2026-09-15 by the prior run; nothing in this morning's signals/rebound tails names a fresh fundamental
catalyst for any of them.

**FOMC caveat (not a verdict driver today):** the decision lands ~14:00 ET today; 84-92% hike odds are
already priced across venues per prior_findings (catalyst:786fb3d78e, catalyst:b87bc240d0). Nothing here
is contingent on the outcome — this run is pre-decision. A surprise (hold, or hawkish-beyond-priced
dot-plot) could reopen today's bounce this afternoon; that's a signals/catalyst re-check, not a thesis
re-write, unless it produces a name-specific fundamental development.

## 2. Factor cluster table (compute_drift.json, script-owned — cited not recomputed)

| Cluster | % of total book | % of invested equity |
|---|---|---|
| AI Semis/Fabs | 27.10% | 33.04% |
| AI Networking/Optics | 19.20% | 23.41% |
| AI Power/Cooling/DC Infra | 13.64% | 16.63% |
| Compute/Hyperscaler | 10.53% | 12.84% |
| AI Memory/Storage | 5.30% | 6.46% |
| Compute/Hyperscaler OEM | 3.11% | 3.79% |
| Analog/Industrial Semis | 1.80% | 2.19% |
| Enterprise Software | 1.36% | 1.65% |

**Combined AI-capex chain (Semis+Networking+Power+Hyperscaler+Hyperscaler OEM+Memory) = 78.9% of total
book, 96.2% of invested equity** (smith-rebound's same-run figure, reaffirmed). A datacenter-capex pause
or sentiment shock hits ~79 cents of every book dollar at once. Co-movement check: yes — all 9 bounce
names plus the broader cluster tracked SMH's overnight +1.34% premarket move directionally; Monday's drop
(SMH -4.75%) and today's recovery both read as beta, not idiosyncratic dispersion within the AI-capex set.

## 3. Single-factor risk verdict

This book is functionally one bet dressed as 27 tickers. 96.2% of invested equity sits inside the
AI-capex-chain factor; Monday's -4.75% SMH day and this morning's +1.34% premarket bounce moved the large
majority of holdings together, in the same direction, confirming the cross-name correlation this factor
implies rather than testing it. The largest genuinely uncorrelated slice is NOW (Enterprise Software,
1.65% of equity) plus the ~18% cash/wallet position — everything else, including "diversifier"-flavored
names like MSFT/GOOG/AMZN, still sits inside the same demand chain (hyperscaler capex → semis/optics/power
→ memory). Today's bounce does not change this read; it is the same factor moving in the other direction.

## 4. HBMTracker reconciliation (MU only — EWY/DRAM not held)

consumer_view.json generated_at 2026-09-15T07:50:00Z, staleness_days=0 (same dataset MU's thesis was
reviewed against yesterday — no new data since). HBM3E stack-derived basis: $9.00/GB mid on 2026-07-19,
2026-08-05, AND 2026-09-15 — trend_pct_within_basis = 0.0%, flat. Contract_quote basis (older, pre-basis-
change) separately shows -18.92% 2025-06-30→2026-01-15; cross_basis_change_is_meaningless=false but the
two segments are NOT chained per correction C1 (2026-08-05 phantom -51% artifact) — no single headline
trend quoted. Tier-1, tier1_corroborated=true throughout. No new corrections opened since C1/C2.

Verdict conflict: MU thesis is WATCH (structural CXMT capacity-share risk), while within-basis ASP is
flat, not falling — this is branch (c), **no_action**: the WATCH is not an ASP call, it's about CXMT
reaching HBM3E risk production ~1yr ahead of consensus (prior_findings catalyst:dca7246842, still not
expired, reaffirmed). Supply-structure context (unchanged since last read): MU is HBM4-Vera-Rubin
qualified but holds only a "single digits to low teens" allocation share vs SK Hynix 60-70%/Samsung
25-30% — MU's WATCH-worthy exposure is allocation-share thinness, not price. Forward forecast context:
DDR5-over-HBM3E profitability crossover (2026-04-21 TrendForce) and 2027 HBM contract prices expected
80-150% higher remain the standing bull case, unchanged. **No thesis action from this run's HBM data.**

## Data quality
- No smith-catalyst/smith-quality dispatch this run (quick mode) — leaned on 2026-09-15 prior_findings
  for anything requiring fresh news verification; none of today's 9 bounce names needed a fresh fetch
  since the move is confirmed macro/technical by signals' own bucket-clearing, not contested.
- HBMTracker data is identical to what MU's 09-15 thesis entry was already reviewed against — treated as
  reaffirmed, not re-derived, per prior_findings_rule.
- No G58 verification calls spent this run (no status change triggered the recipe).

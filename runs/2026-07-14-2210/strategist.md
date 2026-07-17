# Portfolio Strategist — 2026-07-14 (QUICK sweep)

Policy is present but unconfirmed (`policy_confirmed: false`) — all drift analysis below is **provisional** pending your sign-off on targets/bands. No bootstrap needed; policy exists, just unratified.

## Proposals (all for review only — nothing executed)

1. **Trim TER ~$350** — peer-laggard threshold breached (−8% vs SOXX) even after today's +4.34% bounce; TARGET GAP + STRONG UPTREND signals conflict with the laggard read, so this is a trim-watch, not a thesis break. Feeds the AI Semis/Fabs overweight (41.78% vs [25,35]%, +11.78pt over band).
2. **Trim QCOM ~$300** — PEER LAGGARD signal plus its earnings date is still unconfirmed (data-quality flag open since 07-12); reduces exposure to an undated print inside the breached Semis/Fabs cluster.
3. **Right-size MRVL ~$250** — new position already −18.6% peer-relative laggard vs SOXX on day one of ownership; not a thesis break, but the entry looks premature. Trim back rather than let a same-day laggard compound inside an already 11.8pt-overweight cluster.
4. **Deploy ~$700 into CIEN** — AI Networking/Optics is the one underweight breach (14.65% vs [15,25]%, −5.35pt) and CIEN already carries a TARGET GAP signal; cash is breached at 19.2% vs [3,15]% band despite today's heavy deployment, so this puts idle wallet cash to work inside the underweight cluster rather than adding to Semis/Fabs.
5. **Deploy ~$500 into CQQQ** — Diversified/Regional ETF is underweight (1.97% vs 5% target, −3.0pt) and, per thesis agent's factor flags, sits outside the 8-name AI-capex chain (compute/semicap/memory/optics/power/neocloud/EMS/EWY). This is the one deployment lever that also chips at the AI-capex breach (95.0% vs 90% cap) instead of adding to it.

Net effect if all five execute: ~$900 trimmed out of the Semis/Fabs overweight, ~$1,200 redeployed into the two underweight/non-capex-chain slots, wallet cash drops from ~$6,636 to ~$5,436 (≈15.7% of book) — meaningful progress toward the [3,15]% band without fully closing it in one pass, consistent with staying under the AI-capex cap.

LTCG check: lots.json is empty (known gap **G1**) — cannot evaluate whether any of these trims cross the 24-month Indian LTCG boundary. Treat trim timing as tax-blind until lot dates are seeded.

No thesis-broken names in the book this run (VRT and MU both re-opened as strengthening; SNDK re-exited to dust on a whipsaw, not a fundamental break — G6 applies, already at zero so no trim needed). Sentiment band is "greed," not "extreme_greed," so no sentiment-led profit-booking override — proposals above are drift/signal-driven as normal.

## Risk-off status

`risk_off_status: normal`. Drawdown −10.99%, well inside policy thresholds — no defensive posture required, proposals above are standard rebalancing, not risk-off triage.

## Stress table

N/A — quick mode, no smith-macro dispatched (G2).

## Hit-rate readout

Not available this run — the signals tail did not carry `bucket_hit_rates`/`name_bucket_grades` (journal scoring history is likely still thin, per orchestrator note). Skipping rather than manufacturing a readout; revisit once buckets have ≥3 scored entries.

## Proposal outcomes / scorecard

N/A — quick mode (outcomes tracked in deep/monthly runs only).

## Data quality notes

- price_at_proposal left null for all five proposals — no scout dispatched this quick run, no live prices in the embedded slices.
- QCOM and LRCX earnings dates still unconfirmed (open since 07-12); LRCX running +4.73% into an undated print at 6.09% weight — not proposed for action this run but worth flagging for the next macro/signals pass.
- Cluster-level position weights for TER/QCOM/MRVL not itemized in this quick-mode slice; trim sizes above are approximate and should be checked against actual position size before execution.

```json
{"policy_draft":null,"proposals":[{"action":"Trim TER","size_usd":350,"price_at_proposal":null,"rationale":"Peer-laggard threshold breach (-8% vs SOXX) despite today's bounce; TARGET GAP signal conflicts; feeds AI Semis/Fabs overweight (+11.78pt over band)."},{"action":"Trim QCOM","size_usd":300,"price_at_proposal":null,"rationale":"PEER LAGGARD signal; earnings date unconfirmed (data-quality gap open since 07-12); reduces undated-print exposure inside breached Semis/Fabs cluster."},{"action":"Trim MRVL","size_usd":250,"price_at_proposal":null,"rationale":"New position already -18.6% peer-relative laggard on day one; premature sizing inside an 11.8pt-overweight cluster; not a thesis break."},{"action":"Deploy into CIEN","size_usd":700,"price_at_proposal":null,"rationale":"AI Networking/Optics underweight (-5.35pt vs band) plus TARGET GAP signal; cash breached at 19.2% vs [3,15]% band, puts idle wallet cash to work in the underweight cluster."},{"action":"Deploy into CQQQ","size_usd":500,"price_at_proposal":null,"rationale":"Diversified/Regional ETF underweight (-3.0pt); sits outside the AI-capex chain per thesis factor flags, chips at the 95.0% vs 90% AI-capex cap breach."}],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],"data_quality":["price_at_proposal null for all proposals -- no scout dispatched this quick run","QCOM and LRCX earnings dates unconfirmed (open since 07-12), LRCX weight 6.09% running into undated print","G1: lots.json empty, LTCG timing unfulfillable for trim proposals","hit-rate readout skipped -- signals tail lacked bucket_hit_rates/name_bucket_grades this run"]}
```

# Agent Smith — Portfolio Strategist (QUICK sweep, 2026-08-24)

Policy is present, confirmed, and valid (no defects) — no bootstrap needed. Total book $41,800.83, cash 6.627% (normal band [5,15]), drawdown -6.846% from peak, AI-capex 83.688% of invested equity (cap 100%, no breach). Sentiment: **extreme_greed** (score 71.7), action hint "propose profit-booking on overweight/breach names." Gate = AMBIGUOUS, which is why smith-rebound ran this cycle.

## BX cluster classification — needs your explicit call, not sized around

smith-thesis put BX (10sh, re-entered, real re-buy per ledger) into a brand-new "Financials/Alt-Asset Diversifier" satellite cluster with **no policy band**, status WATCH. The reasoning: BX is not a clean non-AI-capex diversifier — it shares the same XPV off-balance-sheet AI-financing tail risk (Blackstone/Apollo funding Anthropic compute, $35bn/1GW scaling to 20GW by 2028) that drove BofA's 08-11 bond downgrade on AVGO. With BX previously the book's only sizeable genuine diversifier and now reclassified, the AI-capex concentration ratio dropped from ~89% to 83.7% — that is a **reclassification, not a risk reduction**. Unconfirmed 08-20 news has BX still in financing talks on this same platform. BX sits at rank 18 in the extreme-greed stretch queue (+16.54% abs, +15.81pp rel) but has no computed trigger and no policy band to breach, so I am not proposing a trim or add — I'm flagging the classification/band decision for you. Until you set a band, this cluster is invisible to drift math by design.

## The 08-18 semis-rout stop-loss cascade — one event, not four

smith-ledger confirms CLS and TER's fractional-dust holdings are **ordinary stop-loss sells**, not corporate actions (compute_book's heuristic false-flagged them). Combined with COHR's full exit ($1,727.84) and IREN's full exit ($820.00), that's four names stopped out in roughly one week, all traceable to the same 08-18 semis rout. smith-thesis and smith-signals independently corroborate: no idiosyncratic negative news for COHR, IREN, or CLS — COHR beat and raised its guide *through* its own exit, IREN's coverage was uniformly positive. This is your tight-SL style working exactly as designed (confirmed 2026-07-27) against one correlated volatility event, not four separate thesis failures. TER is the one exception with a real headwind (Baird downgrade 08-21) layered on top of the mechanical stop. None of the four are proposed for re-entry this run (see stay-out list below) — sizing discipline, not thesis, is the binding constraint.

## Proposals (7 — see note on count below)

Count exceeds the usual 3-5 because the mandatory catalyst_threat screen fired on four names simultaneously off one factor story, plus three smith-rebound "average-in near support" candidates carried over from the AMBIGUOUS-gate dispatch. Both sets are independently evidenced; I did not shrink either to hit a round number.

### Catalyst-driven trims (live trigger: `catalyst_threat`, cap-independent by design)

All four cite the same WSJ factor story: nine Big Tech firms carry ~$3T in off-balance-sheet AI financing commitments (leases not-yet-in-service + purchase commitments) vs ~$600bn trailing capex, growing ~$1.2T/quarter — this triggered same-day de-risking in behind-the-meter power names (GEV -6.90%, BE -9.97%, VRT -6.80% on 2026-08-17) and carries directly into AVGO via the XPV financing platform.

**1. TRIM BE — $403, 2026-08-24, price $201.56**
BE is the most stretched name in the book by a wide margin (derisk_score 125.0, rank 1 of 33; ATR cap_multiple 2.723x, headroom -$1,275.51). Thesis strengthening (Q2 beat, raised guide) but that does not override an active catalyst threat plus the largest cap overage in the book. trigger_type: catalyst_threat. Evidence: verified 0, computed 2 (catalyst_threat entry, ATR cap/headroom), unverified 1 (thesis note).

**2. TRIM GEV — $396, 2026-08-24, price $988.00**
Same catalyst; over cap 1.295x (headroom -$450.85); derisk rank 7. Thesis strengthening but not the lead input here — the trigger and the cap overage are. trigger_type: catalyst_threat. Evidence: verified 0, computed 2, unverified 1.

**3. TRIM VRT — $367, 2026-08-24, price $262.09**
Same catalyst; over cap 1.584x (headroom -$676.10); derisk rank 4. Thesis is WATCH with a **contested** verdict (Q2 EPS beat but revenue missed by ~$110M, verified secondary against stockanalysis.com) — per the qualifier, a contested verdict is a supporting input, not the lead one, so I am sizing off the computed breach + catalyst, not the thesis status. trigger_type: catalyst_threat. Evidence: verified 1, computed 2, unverified 0.

**4. TRIM AVGO — $295, 2026-08-24, price $368.65**
This is the cleanest example of the trigger you asked for: AVGO is **not** over its ATR cap (cap_multiple 0.584, headroom +$1,049.60) — this is a pure profit-take on a name that had a genuinely good run (RSI 65.3, +8.3pp relative strength, +9.03% absolute on the month), independent of any cap mechanics. It also happens to carry the BofA XPV bond-downgrade overhang alone now that BX has exited the same financing platform. trigger_type: catalyst_threat. Evidence: verified 0, computed 2, unverified 1 (thesis evidence_against, tagged unverified).

### Staged average-ins (smith-rebound sourced — macro-driven dips, not idiosyncratic, real risk-cap headroom)

RSI-based oversold_reversion/overbought_distribution were both **empty this run** — the RSI cache is 12 days old (max 10d for a live trigger), so that mandatory screen is structurally suppressed, not silent because nothing qualified. These three are the closest available analog: technical support levels with genuine ATR headroom, staged small rather than sized to full headroom, consistent with the standing "stage in tranches, size for stop-out probability" preference.

**5. BUY QCOM — $300, 2026-08-24, price ~$162.00**
Near $159.80 support. Real risk-cap headroom $808.30 — sizing well under headroom as a first tranche. Cluster AI Semis/Fabs is within band (no breach). trigger_type: null (not a scored trigger bucket this run). Evidence: verified 0, computed 1 (headroom), unverified 2 (support-level read, thesis note).

**6. BUY WDC — $150, 2026-08-24, price ~$462.35**
Near $356.48 support. Real risk-cap headroom only $174.18 (tighter than the cluster figure — sized to the tighter one per rule). This also nudges the AI Memory/Storage cluster, which is under its floor (-6.83pt, actual 8.17% vs target 15%, band [10,20]) — a small step in the right direction, not a cure. trigger_type: null. Evidence: verified 1 (thesis secondary), computed 1 (headroom), unverified 1 (support-level read).

**7. BUY GLW — $90, 2026-08-24, price ~$152.54**
Near $139.93 support. Real risk-cap headroom only $93.45 — sized essentially to the cap. Cluster AI Networking/Optics within band. trigger_type: null. Evidence: verified 0, computed 1 (headroom), unverified 2 (support-level read, thesis note — the -50%-from-peak claim in this name's evidence_against is itself flagged single-source/unconfirmed, so treated as color, not basis).

### Not proposed — explicit stay-outs

COHR (thesis-watch overrides — its own exit had no thesis-break evidence, but sizing discipline says wait for a real setup), IREN (single-session dip too thin, 3rd re-entry cycle — standing watchlist interest stays open per your 2026-08-03 instruction, but this isn't the trigger), MRVL / GEV / BE (already over their own ATR cap — GEV/BE are sized above as trims, not adds), CLS / TER (dust-quantity flag resolved as real stop-loss sells, still too thin a dip to size).

### Not proposed — ATR-cap-only overages with no catalyst/thesis support this run

NVDA, TSM, MRVL, NBIS, MU are all over their ATR risk cap in compute_book.json (`trim_risk_cap` bucket) but fired no live catalyst_threat or thesis_break trigger this run. Per your standing preference (proposal-trigger-preference, confirmed 2026-08-17), these are **not** sized as pure cap-cure trims — noted for monitoring only, not proposed.

### Rotation pairs — none available this run

`laggard_rotation` (the shadow buy leg) is empty — suppressed by the same stale rel_strength cache (age 12d, n=31) that knocked out the RSI screens. There is no qualifying buy-leg candidate to pair against a sell leg from `overbought_distribution` (also empty) or derisk's `names_stretched`. No pair proposals this run.

### LTCG

No live deferrals. Earliest open lot is 2026-07-15 — the 24-month LTCG boundary is mid-2028. Nothing near the 6-month window.

## Risk-off status

**Normal.** Drawdown -6.846% is well inside the 8% warn threshold; no defensive posture required. One thing worth flagging alongside this: aggregate ATR open risk is running at 12.511% against a 10% cap (compute_risk.json) — a book-wide volatility-budget overage, driven mainly by BE ($569.21 open risk), MRVL ($374.92), NBIS ($395.27), and VRT ($330.97). The four catalyst trims above (BE, GEV, VRT, AVGO) knock a meaningful chunk off this aggregate as a side effect, even though they weren't sized for that purpose.

## Hit-rate readout (journal.json bucket_hit_rates, all-time; buckets with n<3 skipped)

- **TARGET GAP**: n=16, 31.2% hit rate. Below the 40%-over-≥5-entries de-emphasis threshold — **recommend de-emphasizing this bucket** as a standalone trigger going forward.
- **MOMENTUM+VOLUME**: n=4, 50.0% hit rate. Reportable (n≥3) but below the n≥5 bar for a de-emphasis call either way — leave as-is, watch it.
- OVERSOLD BOUNCE: n=1, skipped (below minimum n=3 to report).
- 7-day interim trend (labeled interim, not a basis for action): MOMENTUM+VOLUME 40.0% (n=15), OVERSOLD BOUNCE 75.0% (n=4), TARGET GAP 29.4% (n=17) — directionally consistent with the all-time read; TARGET GAP stays weak.

## Interpretation of the stored proposal scorecard (proposals.json, as of 2026-08-24 — read, not recomputed)

Scorecard: overall 30d accuracy 14.3% (n=7: 1 worked, 6 missed). By direction — TRIM/SELL 100% (n=1, avg benefit +7.81%), BUY 0% (n=4, avg benefit -11.92%), HOLD 0% (n=2, avg benefit -8.59%). 72 proposals are still under the 30-day window; 9 were dismissed by the user and correctly excluded (a user override isn't a strategist error); P-011 BUY NEM is quarantined pending anchor-price review and correctly excluded from the aggregate.

Read this cautiously. n=1 for the 100% TRIM figure and n=2 for HOLD are not findings — they're single data points dressed as rates. The one pattern with enough breadth to take seriously is BUY: 0 for 4, average benefit -11.92%, in a run where sentiment has sat at extreme_greed. That's a small-sample warning, not proof the desk's BUY logic is broken, but it argues for exactly what this run did — leaning on cap-independent profit-taking (the AVGO trim) and small staged adds rather than large fresh BUY conviction calls, until the scored sample grows past single digits per bucket. With 72 of ~88 total proposals still unscored, this scorecard represents a small, early slice of the desk's real track record — treat it as a caution flag to keep watching, not a verdict to act on today.

## Data quality / known gaps carried into this run

- RSI cache 12 days old (>10d max) — oversold_reversion and overbought_distribution structurally suppressed this run, not evidence of "nothing qualified."
- rel_strength_1m cache also 12 days stale (n=31) — laggard_rotation suppressed, which is why no rotation pair could be built, and overbought_distribution's "genuinely up" gate would have degraded to price-only had it fired.
- BX has no lots.json entry — profit_ratchet/scale_out_ladder cannot be computed for it (no cost basis); consistent with the cluster-classification gap above.
- G80 (open): shadow-scored triggers (profit_ratchet, scale_out_ladder) are structurally exempt from condition-based auto-retirement — none fired this run, so moot for now, but flagged for whoever picks up G80.
- G81 (open): the proximate cause of the 2026-08-18 semis rout is still unresolved and the first answer (30-yr UST hitting a 19-year high) was already flagged wrong by an earlier run — the cascade-cluster read above treats 08-18 as one correlated event without asserting a settled cause.
- BABA earnings-date conflict (open_flags) — resolved by smith-signals this run (08-20 print confirmed, -8.57% post-earnings reaction), superseding the earlier 08-28 vs 08-20 date conflict.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"TRIM","ticker":"BE","size_usd":403,"price_at_proposal":201.56,"rationale":"Live catalyst_threat trigger (WSJ $3T off-balance-sheet AI financing story, same-day de-risking 2026-08-17); largest ATR cap overage in the book (2.723x, headroom -$1,275.51) and highest derisk_score (125.0, rank 1/33). Thesis strengthening but not the lead input -- trigger and cap overage are.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"GEV","size_usd":396,"price_at_proposal":988.00,"rationale":"Same catalyst_threat trigger; over cap 1.295x (headroom -$450.85); derisk rank 7.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"VRT","size_usd":367,"price_at_proposal":262.09,"rationale":"Same catalyst_threat trigger; over cap 1.584x (headroom -$676.10); derisk rank 4. Thesis WATCH is contested (EPS beat, revenue miss) so it is a supporting input only -- sized off the computed breach and trigger, not the thesis status.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":1,"computed":2,"unverified":0}},
   {"action":"TRIM","ticker":"AVGO","size_usd":295,"price_at_proposal":368.65,"rationale":"Cap-independent profit-take: AVGO is NOT over its ATR cap (0.584x, headroom +$1,049.60) -- pure catalyst_threat trigger on a name up 9.03% on the month (RSI 65.3, +8.3pp relative strength), now carrying the XPV/BofA bond-downgrade overhang alone post-BX-exit.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"BUY","ticker":"QCOM","size_usd":300,"price_at_proposal":162.00,"rationale":"smith-rebound: near $159.80 support on macro-driven (not idiosyncratic) weakness. Real risk-cap headroom $808.30, sized as a small first tranche. Not a scored trigger bucket this run -- oversold_reversion suppressed on stale RSI.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":1,"unverified":2}},
   {"action":"BUY","ticker":"WDC","size_usd":150,"price_at_proposal":462.35,"rationale":"smith-rebound: near $356.48 support. Real risk-cap headroom $174.18 (tighter than cluster headroom, sized to the tighter figure). Also nudges the AI Memory/Storage cluster floor breach (8.17% vs 15% target) in the right direction -- not a cure.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":1,"computed":1,"unverified":1}},
   {"action":"BUY","ticker":"GLW","size_usd":90,"price_at_proposal":152.54,"rationale":"smith-rebound: near $139.93 support. Real risk-cap headroom only $93.45, sized to the cap.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":1,"unverified":2}}
 ],
 "scorecard_read":"n=7 scored, overall 14.3% (1 worked/6 missed). TRIM 100% (n=1) and HOLD 0% (n=2) are single-digit samples, not findings. BUY 0% (n=4, avg -11.92%) is the one pattern with enough breadth to weigh, and it argues for cap-independent profit-taking plus small staged adds over large fresh BUY conviction calls -- which is what this run did. 72 of ~88 total proposals remain unscored (<30d); treat the scorecard as an early caution flag, not a verdict.",
 "deemphasize_buckets":["TARGET GAP"],
 "data_quality":["RSI cache 12d stale (>10d max) -- oversold_reversion/overbought_distribution structurally suppressed, not evidence nothing qualified","rel_strength_1m cache 12d stale (n=31) -- laggard_rotation suppressed, no rotation-pair buy leg available this run","BX has no lots.json entry -- profit_ratchet/scale_out_ladder not computable for it; BX cluster/band remains a user decision (flagged, not sized)","G80 open: shadow triggers exempt from auto-retirement, moot this run (none fired)","G81 open: 2026-08-18 semis-rout proximate cause unresolved; cascade-cluster read above treats it as one correlated event without asserting a settled cause"]}
```

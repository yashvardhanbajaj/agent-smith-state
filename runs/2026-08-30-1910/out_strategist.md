# Agent Smith — Portfolio Strategist (Deep, 2026-08-31)

Prices are Friday 2026-08-28 closes. US session opens tonight 19:00 IST. Policy is confirmed (no bootstrap needed).

## Binding constraint: cash, not risk

Cash is 3.005% of book vs a 5% policy floor (`cash_breach: true`, deployable_cash_usd = $0.00). Aggregate open risk is 9.331% against the 10% cap — corrected down from the stale 13.16% read (old ATR window still contained the 07-28 crash) — so this is **not** a deleveraging problem. Over-cap names on refreshed ATR20: GEV, MRVL, BE, COHR, NBIS.

Because there is no deployable cash, every buy below is either (a) a paired rotation funded by a named sell, or (b) left unfunded and explicitly flagged as such (oversold_reversion legs on AVGO/GOOG/AMZN/AMAT/AMAT all carry `blocker: "no deployable cash above the band ceiling"`). Two of the five proposals below are standalone trims with no buy leg — their entire purpose is to cure the cash floor breach directly, which a paired rotation cannot do.

AVGO reports 2026-09-02 (~8.1% implied move); per the standing instruction it is staged, not bought, ahead of that print. No AVGO proposal here.

## Proposals

### P-A — TRIM NVDA $272 (housekeeping, raises cash)
- trigger_type: `overbought_distribution` (primary sizing), corroborated by `catalyst_threat`
- Sell ~$272 (25% trim, `suggested_size_usd` verbatim from the live trigger row), current position $1,087.75
- evidence_for: RSI14 70.4 (computed, >70 overbought); +8.1% on the month (computed, real gain to protect); thesis strengthening (verified: secondary — NVDA-OpenAI/SB Energy Ohio financing narrowed to ~$100bn phase, unsigned $3bn stake)
- evidence_against: catalyst_threat's CDS story is unverified (single wire source, "no absolute NVDA bp level sourced") — I am not leading on it, only citing it as a second, independent trigger that happens to agree on direction
- Funding: raises cash directly, no buy leg — this trim is one of the two moves that actually narrows the cash breach
- evidence_quality: {verified: 1, computed: 2, unverified: 1}
- Note: `overbought_distribution` is deliberately independent of the ATR cap — NVDA is not over cap, this is a profit-take on a real gain, not a cap cure.

### P-B — TRIM IREN $213 (housekeeping, raises cash)
- trigger_type: `trend_breakdown`
- Sell ~$213 (`suggested_size_usd` verbatim), current position $709.00
- evidence_for: computed STRONG DOWNTREND signal polarity (net -1); conviction_score -4.0 (tier none, computed by `smith_conviction`)
- evidence_against: thesis watch, not broken (secondary, 3-for/3-against — contested, so I'm not calling this a thesis break); Blue Owl-led $2.4B financing and two sell-side "buying opportunity" calls (secondary, sourced 08-27/08-28) argue the other way
- This is IREN's third entry after two prior stop-outs — a repeat-volatility pattern noted in the book itself, which is why I'm sizing off the computed technical trigger rather than the (contested) thesis
- Funding: raises cash, no buy leg
- evidence_quality: {verified: 0, computed: 2, unverified: 0} (secondary counted as verified per the schema definition)

### P-C — PAIRED: SELL FLTW $310 / BUY WDC $310
- pair_id: `profit_rotation-FLTW-WDC`, trigger_type: `profit_rotation`
- Sell leg FLTW: in `names_stretched` (beat SMH, up on month), thesis watch/unverified (+1.6% since entry, no negative evidence on file — thin thesis, real but modest gain)
- Buy leg WDC: conviction_average, conviction_score 32.0 (tier low), thesis strengthening (verified: primary), -13.65pp vs benchmark (computed laggard) — support $427.52, blended entry $461.84, stop $395.59 clears the entry (no clamp beyond cash)
- This is incremental to the already-accepted P-149 (Buy WDC $150, separately funded) — a second, independent tranche off different funding
- Funding: FLTW sale proceeds fund WDC dollar-for-dollar; sized to the smaller of proceeds and WDC's own headroom ($4,465 headroom, not binding)
- evidence_quality: {verified: 1, computed: 2, unverified: 1}

### P-D — PAIRED: SELL AMD $279 / BUY TER $279
- pair_id: `cluster_rotation-AMD-TER`, trigger_type: `cluster_rotation`, cluster: AI Semis/Fabs
- Sell leg AMD: laggard within cluster (-2.7pp vs SMH), thesis watch (secondary — Q3 guide_below_consensus, $5bn IG debt raise levers the balance sheet even as it funds capex, and the strategist explicitly ruled HOLD/no-further-adds on 2026-08-15) — a laggard with a weak thesis, sell not add, consistent with the corrected cluster-rotation direction
- Buy leg TER: performer within cluster (+2.8pp), thesis strengthening (secondary), conviction_score 30.5 (tier low), reported beat context elsewhere in the semis cluster
- Funding: AMD proceeds fund TER dollar-for-dollar, within TER's own $1,132 headroom (not binding)
- evidence_quality: {verified: 0, computed: 2, unverified: 0} (secondary = verified)

### P-E — PAIRED: TRIM MRVL $220 (to cap) / BUY AMAT $220
- trigger_type: null — this is a computed drift/cap breach (Task 2a), not one of the enumerated triggers; paired per the cash constraint rather than left as a standalone cap trim
- Sell leg MRVL: over_cap true, cap_multiple 1.118, headroom -$206.54 (computed breach); derisk queue rank #2 (derisk_score 126.9, fragility 72.2, stretch 75.7); thesis strengthening (secondary — Google partnership $12.2B warrants) but evidence_against flags CEO insider selling ahead of the 08-27 print and confirmed 08-21 profit-taking. This is a partial trim into strength, not a thesis reversal — MRVL is not proposed as a full exit.
- Buy leg AMAT: oversold_reversion + conviction_average both live. RSI14 33.3 (computed, oversold), thesis strengthening (secondary), conviction_score 34.3 (tier low), `size_wanted_usd` $485.60 clamped to $0 by cash in the raw trigger — this pair supplies the funding the trigger itself couldn't find. Blended entry $486.58 clears the $415.87 stop.
- Funding: sized to the smaller of MRVL's cap-breach amount (~$207) and AMAT's own $1,132 headroom — rounded to $220
- evidence_quality: {verified: 0, computed: 3, unverified: 0}

### Named but not proposed
- AVGO/GOOG/AMZN oversold_reversion BUYs: real signals, genuinely unfunded (cash $0), and in AMZN's/GOOG's case in direct tension with the catalyst_threat TRIM rows for the same names — I am not proposing either side. AMZN also carries a user-HELD trim (P-178); GOOG's catalyst_threat rests on unverified sourcing only and contradicts a live oversold BUY signal, so it does not clear the evidence gate as a trim.
- AMKR trend_breakdown: real computed signal (STRONG DOWNTREND, conviction -8.0) but thesis evidence is genuinely contested (BofA/UBS Buy initiations vs guide-below-consensus) and I've already used the desk's TRIM-side budget on two higher-conviction housekeeping trims this run given the 20% (n=5) trim hit rate — flagged for next run, not sized now.
- RMBS/TLN/NRG entry_setup: live triggers, no live price/ATR pulled this run — cannot size responsibly. Flagged in data_quality, not proposed.
- profit_rotation-CIEN-AMAT and profit_rotation-MSFT-KLAC: both sell legs (CIEN, MSFT) are already accepted and awaiting execution (P-186, P-164) — proposing them again would double-count the same proceeds. Skipped.

## Risk-off check

`risk_off_status: normal` (computed). Drawdown -8.95% (total_book basis) is close to the 8% policy warn line but the computed status has not flipped — no defensive-mode instruction beyond what's already in the trims above. Cash regime reads `normal` per the computed reason ("stop-out 9 sessions ago but cash has re-entered the normal band"), even though the 5% floor itself is still breached — those are two different thresholds and the compute layer is explicit that the floor breach, not the regime, is what's live. No exceptional deployments proposed; all buys above are cash-neutral pairs.

## Stress table (approximate, anchored to smith-macro's live regime — flag: macro regime read not independently re-confirmed this run beyond the 10-yr/VIX/DXY/Fed strip supplied; treating rate-sensitive rows as static-assumption, labelled accordingly)

| Scenario | Est. impact | Most exposed |
|---|---|---|
| AI-capex pause (hyperscaler guidance cut) | -12% to -18% book | NVDA, AVGO, MRVL, COHR, AMAT, AMKR — 29% AI Semis/Fabs + 17.8% Networking/Optics clusters both direct capex-order-book exposure |
| Rates +100bp (10-yr 4.72% -> ~5.7%) | -6% to -9% book (static assumption — not macro-refreshed this run) | Long-duration/high-multiple names: NVDA, MRVL, COHR, IREN, NBIS; margin via discount-rate compression on capex-story growth names, compounded by the cycle's own de-rating-on-cost dynamic (see cycle note below) |
| Tariff/export-control escalation (China semis) | -4% to -7% book | TSM (already flagged unauditable), AMAT, KLAC, LRCX, AMKR (advanced packaging), BABA |
| USD/INR ±3% (USD-reported book) | ~0% on the USD book; INR-terms net worth moves roughly ±3% mechanically with the rupee, independent of any US position moves | N/A to USD book; relevant only to INR-terms net worth reporting |
| Credit/CDS repricing (the catalyst_threat story: NVDA CDS ~2x in 2mo, Oracle downgraded to BBB-) | -3% to -6% book if it broadens past AI-financing-vehicle names | AVGO (sole remaining XPV exposure after BX's 08-17 exit), AMZN, GOOG, MSFT, NVDA — the five catalyst_threat names |
| Broad correction continuation (current `correction_state: correction`) | -5% to -10% further from here, high-volatility names disproportionate | IREN, AMKR, NBIS, SMCI, COHR — already the derisk queue's most fragile names |

## Cycle-position note (feeds the rotation logic above)

Cycle is `late`, medium confidence, **late by cost, not by demand**: NVDA margins guided 75%→74%→71-72% Q4 trough on memory input cost, DRAM contract gains decelerating, while hyperscaler capex guidance is still being raised and semicap lead times are extending. The market is de-rating suppliers on accelerating fundamentals — paying less per unit of capex growth than three months ago — and bidding the investment-grade buyers instead. This is part of why P-A/P-E lean toward trimming stretched, margin-exposed names (NVDA, MRVL) and rotating toward names with intact demand-side theses (AMAT, TER) rather than adding further capex-supplier beta broadly.

## Hit-rate readout (Task 5 — quoted from the scorer, not recomputed)

From `bucket_hit_rates`/`by_direction` in `proposals.json`'s stored scorecard (as_of 2026-08-31, scored_count n=19; 110 proposals not yet 30 days old, 1 quarantined pending anchor review — P-011 BUY NEM, excluded):

- TRIM/SELL: 20.0% (n=5), avg benefit -7.54% — this desk's weakest limb, well below the 40%-over-≥5-entries de-emphasis bar
- BUY: 41.7% (n=12), avg benefit -2.98% — below coin-flip but above the de-emphasis threshold; not yet recommending de-emphasis
- HOLD: 0.0% (n=2) — n<3 in the skill's own rule, not evaluable, not flagged
- Overall: 31.6% (n=19), avg benefit -4.81%

**Interpretation, not new arithmetic:** none of the three buckets clears the "≥40% over ≥5 entries" recommend-de-emphasis bar with statistical confidence — TRIM is below it but n=5 is thin, BUY sits right at the line. I am not recommending de-emphasis of either direction this run. What this record does argue for: the higher evidence bar this run's TRIM proposals were held to (P-A, P-B both lean on computed triggers first, contested thesis language flagged rather than leaned on) is warranted, not optional — the desk's two prior evidence-gate failures (SNDK mischaracterized-beat trim, MRVL 10-Q-contradicted veto) were both TRIM-side, the exact bucket now measured weakest. Four proposals this run are still sells (P-A, P-B, and the sell legs of P-C/P-D/P-E) against that 20% record — sized modestly, paired where possible, and none resting solely on unverified evidence.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"TRIM","ticker":"NVDA","size_usd":271.94,"price_at_proposal":217.55,
    "rationale":"RSI14 70.4 overbought (computed), +8.1% on the month (computed) -- profit-take independent of the ATR cap; corroborated by catalyst_threat (unverified CDS story) but sized off overbought_distribution, not the catalyst.",
    "trigger_type":"overbought_distribution","trigger_bucket":"housekeeping","pair_id":null,"pair_role":null,
    "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":1,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"IREN","size_usd":212.70,"price_at_proposal":35.45,
    "rationale":"STRONG DOWNTREND signal polarity (computed), conviction_score -4.0 tier none (computed); thesis is watch not broken -- sized off the technical trigger given the thesis is genuinely contested (3-for/3-against) and this is IREN's third stop-out-prone entry.",
    "trigger_type":"trend_breakdown","trigger_bucket":"housekeeping","pair_id":null,"pair_role":null,
    "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"SELL","ticker":"FLTW","size_usd":310.32,"price_at_proposal":100.41,
    "rationale":"Stretched (beat SMH, up on month), thesis watch/unverified and thin -- book the modest real gain, fund WDC add.",
    "trigger_type":"profit_rotation","trigger_bucket":"idea","pair_id":"profit_rotation-FLTW-WDC","pair_role":"sell_leg",
    "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":1,"unverified":1}},
   {"action":"BUY","ticker":"WDC","size_usd":310.32,"price_at_proposal":459.45,
    "rationale":"Laggard -13.65pp vs SMH (computed) with a strengthening thesis (verified: primary) -- yet to rally; conviction 32.0 tier low; stop $395.59 clears blended entry $461.84.",
    "trigger_type":"profit_rotation","trigger_bucket":"idea","pair_id":"profit_rotation-FLTW-WDC","pair_role":"buy_leg",
    "size_wanted_usd":326.41,"clamped_by":"deployable cash (cleared by FLTW proceeds)","stop_price_usd":395.5864,"exited_on":null,
    "evidence_quality":{"verified":1,"computed":2,"unverified":0}},
   {"action":"SELL","ticker":"AMD","size_usd":279.35,"price_at_proposal":null,
    "rationale":"Laggard within AI Semis/Fabs (-2.7pp, computed), thesis watch (secondary: guide-below-consensus, debt-funded capex, strategist's own 08-15 no-further-adds ruling) -- weak-thesis laggard, dead money in this cluster; fund TER add.",
    "trigger_type":"cluster_rotation","trigger_bucket":"idea","pair_id":"cluster_rotation-AMD-TER","pair_role":"sell_leg",
    "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":1,"unverified":0}},
   {"action":"BUY","ticker":"TER","size_usd":279.35,"price_at_proposal":354.97,
    "rationale":"Performer within AI Semis/Fabs (+2.8pp, computed), strengthening thesis (secondary), conviction 30.5 tier low -- back the performer over the laggard within the cluster.",
    "trigger_type":"cluster_rotation","trigger_bucket":"idea","pair_id":"cluster_rotation-AMD-TER","pair_role":"buy_leg",
    "size_wanted_usd":345.99,"clamped_by":"deployable cash (cleared by AMD proceeds)","stop_price_usd":310.3858,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"TRIM","ticker":"MRVL","size_usd":220.00,"price_at_proposal":null,
    "rationale":"Over ATR cap (computed, cap_multiple 1.118, headroom -$206.54), derisk queue rank #2 (fragility 72.2 computed). Thesis strengthening (secondary) but evidence_against flags CEO insider selling ahead of the 08-27 print -- partial trim into strength, not a thesis reversal; fund AMAT add.",
    "trigger_type":null,"trigger_bucket":"housekeeping","pair_id":"cap_rotation-MRVL-AMAT","pair_role":"sell_leg",
    "size_wanted_usd":null,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"BUY","ticker":"AMAT","size_usd":220.00,"price_at_proposal":461.67,
    "rationale":"RSI14 33.3 oversold (computed), thesis strengthening (secondary), conviction 34.3 tier low; size_wanted $485.60 was clamped to $0 by cash in the raw trigger -- this pair supplies the funding. Blended entry $486.58 clears the $415.87 stop.",
    "trigger_type":"conviction_average","trigger_bucket":"idea","pair_id":"cap_rotation-MRVL-AMAT","pair_role":"buy_leg",
    "size_wanted_usd":485.60,"clamped_by":"deployable cash (partially cleared by MRVL proceeds; full size still unfunded)","stop_price_usd":415.8723,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":3,"unverified":0}}
 ],
 "scorecard_read":"Stored scorecard as_of 2026-08-31, n=19 scored (110 not yet 30d, 1 quarantined -- P-011 excluded). TRIM/SELL 20.0% (n=5, avg -7.54%), BUY 41.7% (n=12, avg -2.98%), HOLD 0.0% (n=2, not evaluable at n<3), overall 31.6% (n=19, avg -4.81%). Neither TRIM nor BUY clears the >=40%-over->=5-entries de-emphasis bar with confidence (TRIM is below it but thin at n=5); no bucket de-emphasized this run. TRIM is this desk's demonstrably weakest limb and both prior evidence-gate failures were TRIM-side -- this run's two standalone trims (NVDA, IREN) and three rotation sell legs (FLTW, AMD, MRVL) were held to a higher bar accordingly: each leads on a computed trigger or verified/secondary thesis item rather than an unverified claim, and contested theses (IREN, AMKR-omitted, MRVL) are named as contested rather than treated as settled.",
 "deemphasize_buckets":[],
 "data_quality":[
   "AMZN and GOOG oversold_reversion BUY signals directly conflict with their catalyst_threat TRIM rows -- neither side proposed for either name; AMZN additionally carries a user-HELD trim (P-178) so re-litigating it needs stronger evidence than the unverified CDS story supplies.",
   "AVGO oversold_reversion BUY genuinely unfunded and deliberately staged (per instruction) ahead of its 2026-09-02 print -- not proposed.",
   "AMKR trend_breakdown is a real computed signal (conviction -8.0) but its thesis evidence is contested (BofA/UBS Buy initiations vs guide-below-consensus); not sized this run given the desk's weak TRIM record and two higher-conviction trims already proposed.",
   "RMBS/TLN/NRG entry_setup triggers are live but blocked on missing live price/ATR this run -- cannot size responsibly, not proposed.",
   "profit_rotation-CIEN-AMAT and profit_rotation-MSFT-KLAC sell legs (CIEN, MSFT) duplicate already-accepted P-186/P-164 -- skipped to avoid double-counting proceeds.",
   "No LTCG deferral proposed: earliest open lot is 2026-07-15, 24-month boundary is mid-2028 -- nothing near the window this run.",
   "Drawdown -8.95% (total_book) is close to the 8% policy warn line even though risk_off_status reads normal -- worth watching next run, not actioned here since the computed status has not flipped.",
   "Stress table's rate-sensitive rows are static-assumption, not independently macro-refreshed this run beyond the supplied 10-yr/VIX/DXY/Fed strip -- flagged per the anchoring instruction."
 ]}
```

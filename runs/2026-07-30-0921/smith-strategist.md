# Agent Smith — Portfolio Strategist
Quick sweep | US book (INDmoney) | 2026-07-30 intraday | gate=STABILIZING

## Policy status
policy.json exists but is **still unconfirmed (`confirmed:false`)**. Not redrafting this run — cluster targets/bands from the existing draft were usable for the drift math above and are treated as provisional. All drift-based reasoning below is against that unconfirmed draft.

## Sized proposals (5)

**1. Trim MU ~$700** (846.41/sh, live)
AI Memory/Storage cluster is 4.9pt over its band top (24.901% vs 20% cap / 9.9pt over the 15% target — compute_drift breach). MU is +14.5% today alone (739 -> 846.41) on the SMH relief rally; signal tail flags STRONG UPTREND + TARGET GAP but also PEER LAGGARD on 1m — today's pop hasn't erased the drawdown, and smith-thesis is explicit that the 07-30 rally is "a broad beta bounce (VIX unwind) NOT thesis-confirming," with MU still WATCH (CXMT threat walked back by sell-side, not resolved). Given two stop-outs already this run-cycle in this same memory/CXMT complex, this book's tight-SL/large-quantum style argues for banking some of today's +14.5% rather than holding through the next leg. LTCG: no lot data for MU in lots.json — cite **G1** (pre-07-28 lots unknown), can't assess holding-period impact.

**2. Trim SNDK ~$500** (1244.64/sh, live)
Same cluster breach. SNDK is +22.5% today (1015.89 -> 1244.64), the largest single-day move in the book. Signal tail: STRONG UPTREND + PEER LAGGARD only (no TARGET GAP flag — less remaining analyst-target runway than MU), so a partial trim locks in an outsized one-day gain while sell-side turning constructive (Jefferies/Bernstein constructive on CXMT, UBS initiating SK Hynix Buy) argues against a full exit. G1 gap cited for lots.

**3. Trim DRAM ~$300** (50.55/sh, live, Roundhill Memory ETF)
Smallest tranche, basket exposure (+12.7% today). Combined with #1/#2, this closes ~$1,500 of the cluster's ~$1,947 band-overage (to 20% cap) — deliberately leaves the cluster still mildly over band rather than chasing to hard-zero, consistent with the constructive CXMT-walkback framing. G1 gap cited.

**4. Deploy GOOGL ~$700 (tranche 1 of a staged fill)** (332.39/sh, live, -1.3% today)
Compute/Hyperscaler cluster is 5.0pt under its band floor (9.958% vs 15% floor / 10pt under the 20% target) — the largest underweight in the book. Catalyst tail explicitly frames today's GOOGL weakness as "rotation not new information," a catch-down from the 07-23 capex-overhang print, not a fresh idiosyncratic miss — distinct in kind from QCOM's genuine guidance cut below. Watchlist flags peer MSFT as "already rallied hard today on its own Azure beat, less fresh," making GOOGL the less-chased mega-cap fill for this cluster gap, consistent with the book's preference for lower-vol mega-caps when filling cluster gaps. Sized as tranche 1 only (~35% of the ~$2,003 gap to band floor) because smith-signals still carries a fresh NEW HEADWINDS flag on GOOGL — watch for that to clear before adding tranche 2. Cash stays inside its 5-15% band after this buy (10.808% -> ~9.0%).

**5. Initiate META ~$450 (token tranche, new diversifier position)** (535.23/sh, live, -8.6% today — still falling)
Not currently held. Watchlist flags it as a standout: oversold-bounce setup, 35.4% upside, near-52wk low on a Q2 miss, and today's SMH +6.9% rally has genuinely not touched it (down another 8.6% today on top of that, in fact — the weakness is idiosyncratic, not beta). Structural case: smith-thesis flags the equity sleeve at 100% AI-capex-chain concentration with cash now only 10.8%, well below the book's historical ~45.8%-style hedge level — META is demand-side/non-supply-chain and is a genuine diversification lever, not another chain name. Given META is still actively falling today, this is sized as a small first tranche only, per the book's staged-deployment/DCA discipline — not a full initiation. Cash stays inside band after the buy.

No proposal targets QCOM despite its fresh, genuinely idiosyncratic miss (FQ3 guide cut, memory-cost-inflation margin squeeze, STRONG DOWNTREND + NEW HEADWINDS) — position is ~1.27% of book (~$500), too small for a discrete sized action this run. Flagged as a watch item only.

No proposal trims the other 7 ATR-over-cap names (ASML, MRVL, VRT, AMD, COHR, TER, NBIS) outside Memory/Storage. Per this run's guidance, the over_cap flag is mechanical (2xATR20 sizing, not a drift or thesis signal) and re-weighed against the fresh signals tail — most of these names flipped STRONG DOWNTREND->STRONG UPTREND today, and their clusters (AI Semis/Fabs, AI Networking/Optics, Compute/Hyperscaler OEM) are all within band, unlike Memory/Storage. COHR in particular carries STRONG UPTREND + TARGET GAP (37.8% upside per watchlist, on the held position) — an over-cap flag alone doesn't justify trimming a name with room to run and an in-band cluster. Recommend tightening stops on these 7 rather than sizing trims, given the book's known stop-out-prone style, but that's a risk-management note, not a sized proposal.

## Risk-off check
`risk_off_status: normal` (compute_drift). Drawdown -11.469% (total-book) sits inside the policy's warn threshold. No defensive lead required; proposals above are sized normally, not tightened.

## Stress table
Not run — deep-mode only (smith-macro was not dispatched this quick sweep).

## Hit-rate readout
No bucket has reached the ≥3-scored-entries threshold yet (journal.json note: "No bucket has >=3 scored entries yet" as of 2026-07-27; oldest entries are 18 days old as of today, scoring begins at 30d). Nothing to report or de-emphasize this run.

## Proposal-outcome scorecard
Not run — task scope is deep-mode-or-monthly; this is a quick intraday sweep. proposals.json was not read this pass.

```json
{"policy_draft":null,"proposals":[
 {"action":"Trim MU","size_usd":700,"price_at_proposal":846.41,"rationale":"AI Memory/Storage cluster 4.9pt over band top (24.901% vs 20% cap); MU +14.5% today on SMH relief rally but signal tail still PEER LAGGARD (1m) and smith-thesis flags today's rally as beta bounce not thesis-confirming, MU stays WATCH; book already had two stop-outs this cycle in this complex, argues for trimming into today's strength."},
 {"action":"Trim SNDK","size_usd":500,"price_at_proposal":1244.64,"rationale":"Same cluster breach; SNDK +22.5% today, largest single-day move in book; signal shows no TARGET GAP (less runway than MU); partial trim only given sell-side turning constructive on CXMT (Jefferies/Bernstein/UBS)."},
 {"action":"Trim DRAM","size_usd":300,"price_at_proposal":50.55,"rationale":"Completes ~$1,500 of the cluster's ~$1,947 band-overage close, deliberately leaving it mildly over band given constructive CXMT walk-back; ETF/basket exposure, smallest tranche."},
 {"action":"Deploy GOOGL (tranche 1)","size_usd":700,"price_at_proposal":332.39,"rationale":"Compute/Hyperscaler cluster 5.0pt under band floor, largest underweight in book; catalyst tail frames today's GOOGL -1.3% as rotation/catch-down not a fresh miss (unlike QCOM); MSFT peer already ran hard today making GOOGL the less-chased fill; sized as tranche 1 only pending NEW HEADWINDS signal clearing."},
 {"action":"Initiate META (token tranche)","size_usd":450,"price_at_proposal":535.23,"rationale":"Standout watchlist oversold-bounce (35.4% upside), still falling -8.6% today despite SMH +6.9% rally -- idiosyncratic not beta; addresses 100% AI-capex-chain concentration flagged by smith-thesis with cash well below historical hedge level; sized as token first tranche per staged-deployment/DCA discipline given continued weakness."}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["Proposal-outcome scorecard and stress table not run -- quick intraday sweep, both are deep/monthly-scoped tasks","Hit-rate readout empty -- no journal bucket has reached >=3 scored entries yet (oldest entries 18 days old, scoring begins at 30d)","G1 (LTCG lots pre-07-28 unknown) cited for MU/SNDK/DRAM trim proposals -- no lot data available to assess holding-period/STCG-vs-LTCG impact","G32 (INDmoney feed stale, book reconstructed from yfinance, 0.22% divergence) -- $ figures in this output trusted per orchestrator note, no independent re-check done here","G38 (BE/GLW/MKSI still Unclassified 5.255% pending next-run cluster resolution) -- AI Power/Cooling/DC Infra's 7.681pt underweight is likely partly stale since BE's reclassification into that cluster hasn't landed in compute_drift.json yet; no proposal sized against that cluster this run for that reason"]}
```

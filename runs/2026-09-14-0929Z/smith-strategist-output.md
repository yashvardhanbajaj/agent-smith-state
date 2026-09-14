# Agent Smith — Portfolio Strategist, Deep Run 2026-09-14 (pre-open, gate ESCALATING)

## Context read
Book drawdown -3.98% (risk_off_status: **normal**, warn line is -8%) — this is the book's own computed measure and it is NOT flashing red. Separately, smith-scout's macro regime read is **risk_off**: VIX +13.8% today, NQ futures -1.84% (double ES's -0.80%), KOSPI -3.26%, optics cluster -6.25% overnight, all landing directly ahead of a hawkish-stance FOMC decision (09-15/16, 57% hike-hold-vs-cut odds priced). These are two different gauges and they currently disagree — book-level drawdown math says "normal," pre-market macro tape says "risk-off setup." Read that tension as: no defensive trims are *forced* by policy, but new deployment sizing should stay conservative and lean on the pre-sized, ATR-clamped trigger numbers rather than push past them.

Cash is 23.47% vs the 5-15% band (cash_breach true, but cash_regime "normal" — no stop-out in the last 15 sessions). AI-capex concentration 95.98% of equity, under its 100% cap. No position-level cap breaches this run. No thesis status changes (0 broken, thesis tiering shows the standard book).

**Nine proposals are already open in the queue** (P-261 ASML, P-263 TER, P-264 AMAT, P-281 COHR, P-282 MSFT, P-284 NBIS, P-286 AMD, P-288 VRT, P-290 AVGO) — none yet accepted/held/dismissed. This run's catalyst_threat table (ASML/TER/AMAT/MU) and several rotation legs (ASML→TER, NBIS→MSFT, AVGO→LITE, AMD→ALAB) collide directly with those tickers. Per the standing rule against re-proposing a decided-or-pending row, I am **not** re-issuing trims/buys on ASML, TER, AMAT, AMD, COHR, MSFT, NBIS, VRT, or AVGO this run — those idea slots are occupied. The catalyst_threat MU line ($185.04, China export-control CXMT thread) is also folded into the profit_rotation MU pair below rather than raised twice.

## Proposals

**1. BUY TSM — $1,461.62 @ $418.71** (trigger: trend_entry, live)
Semis-cluster leader story this run (dispatch note: leader TSM / laggard AMAT). RSI14 56.9, signal polarity net +1 (STRONG UPTREND, PEER LEADER via rotation bucket "accumulate"), +3.74pp vs SMH. Thesis strengthening (unverified — July revenue +45% YoY, ~25% AI-chip price hike planned; not independently re-verified this run). Not clamped — full conviction size. Stop $398.78.
No open trim/buy on TSM in the queue.
Evidence: {"verified": 0, "computed": 2, "unverified": 1}

**2. BUY APH — $1,088.19 @ $80.50** (trigger: trend_entry, live)
Optics-cluster laggard with an intact/strengthening thesis (dispatch note: leader LITE / laggard APH) — per the organising rule, a laggard with a strengthening thesis is an opportunity, not dead money. RSI14 57.4 (not overbought), signal polarity net +1 (STRONG UPTREND), rotation bucket "accumulate", +1.5pp vs SMH. Thesis strengthening (unverified, 2 for/1 against). Stop $75.40.
Evidence: {"verified": 0, "computed": 2, "unverified": 1}

**3. PAIRED — SELL MU $277.56 / BUY KLAC $277.56 @ MU $185.02 (implied) / KLAC live** (trigger: profit_rotation, live, pair_id profit_rotation-MU-KLAC)
Sell leg: MU is in names_stretched with a watch thesis (also independently flagged this run in catalyst_threat off the same CXMT/China-HBM catalyst thread — folded in here rather than raised as a second line) — book real profit rather than trim on cap mechanics. Buy leg: KLAC is a laggard (-10.5pp) with a strengthening thesis, not clamped.
**Tax note (compute_taxcalc.json harvest_candidates):** MU does not appear in harvest_candidates (no unrealised loss flagged) — no lot-selection conflict; standard FIFO/HIFO sequencing applies to whichever lots are used at execution.
Evidence: {"verified": 0, "computed": 2, "unverified": 1}

**4. PAIRED — SELL SMCI $113.37 / BUY CIEN $113.37** (trigger: profit_rotation, live, pair_id profit_rotation-SMCI-CIEN)
Sell leg: SMCI stretched with a watch thesis, real profit to book (RSI14 60.5, PEER LEADER bucket but net_signal alone doesn't override the stretched/watch profit-take case). Buy leg: CIEN, strengthening thesis, comfortably inside cap (cap_multiple 0.002 — essentially a fresh position), not clamped.
No harvest_candidates entry for SMCI or CIEN — no tax-lot conflict to flag.
Evidence: {"verified": 0, "computed": 2, "unverified": 1}

## Risk-off check
Book-level risk_off_status is **normal** — no policy-mandated defensive trims. The macro-regime risk_off read (scout) argues for restraint on deployment size, which is already satisfied: none of today's BUY legs exceed their ATR/rotation-proceeds sizing, and two of the four ideas are self-funding rotations (sell-funds-buy) rather than net new cash deployment. Cash stays at 23.47%, well above band — no urgency to deploy further into an ESCALATING gate ahead of FOMC. Largest positions (ASML, TER, AMAT, AVGO, VRT) already carry open trim proposals from the standing queue; no new stops suggested here beyond those already on file.

## Stress table (2026-09-14, anchored to smith-scout's live regime read)

| Scenario | Impact | Most exposed | Mechanism | Basis |
|---|---|---|---|---|
| AI-capex pause | -22% to -14% | TSM, AVGO, MU, ALAB, LITE | 95.98% AI-capex concentration; ai_capex_chain "pressured first and hardest" per scout — NQ leading ES down, optics -6.25% overnight is this scenario's leading edge already showing | live |
| Rates +100bp | -12% to -7% | MSFT, GOOG, AMZN, long-duration compute names | US10Y +29.3bps trailing month already pricing this drift; hawkish FOMC stance into 09-15/16 decision is the live mechanism scout names directly | live |
| Tariff/export-control escalation | -9% to -4% | AMAT, ASML, MU, TSM | CXMT HBM3E qualification-stage shipments to Alibaba/Cambricon ~1yr ahead of 2027 consensus (catalyst_threat table); China export-control tax on AMAT named explicitly in this run's dispatch | live |
| USD/INR ±3% | ~0% on book (USD-reported); ±3% on INR-terms net worth | n/a — currency pass-through only | Book is 100% USD-denominated; INR move is a translation effect on the investor's home-currency net worth, not a book P&L event | static_assumption |

## Hit-rate readout (scorecard, refreshed this run — 58 graded, 29.3% overall 30d)
- TRIM/SELL: 34.5% (n=29, worked 10 / missed 14 / neutral 5, avg benefit -3.86%)
- BUY: 33.3% (n=21, worked 7 / missed 11 / neutral 3, avg benefit -3.09%)
- HOLD: 0.0% (n=8, worked 0 / missed 6 / neutral 2, avg benefit -11.51%) — below 40% threshold over ≥5 entries, but "worked" is poorly defined for a HOLD verdict in a falling-book regime; flag for review rather than de-emphasize a direction with no alternative action.
- Overall: 29.3% (n=58), 2 rows quarantined for anchor review.

**Interpretation:** This is a weak record — under a coin-flip on every bucket, and TRIM/BUY accuracy sit within a point of each other, so there's no signal that one direction is more reliable than the other right now. The HOLD bucket's 0% is the most concerning line but n=8 is thin and HOLD verdicts are structurally hard to grade as "worked" in a period where the book fell -3.98%. Given this record, today's four proposals should be read as sized, evidence-cited suggestions, not high-confidence calls — weight the desk's own track record into how aggressively you act on them, especially the two self-funding rotation pairs which at least avoid net new cash risk while the record is this soft.

## Data quality notes
- No `compute_valuation.json` / smith-quality output present this run (not a monthly-cadence run and no explicit valuation-check request) — 2a-iii's valuation-stretched screen could not be applied to the TSM/APH BUYs. Treat this as an open gap, not a clean pass.
- Thesis entries for TSM/APH/MU/KLAC/SMCI/CIEN are all tagged `verified: "unverified"` in shared/thesis.ed56088f.json — every proposal above rests on computed trigger math (RSI, rotation bucket, ATR sizing) as its primary evidence, with thesis status as a supporting, not sole, input, consistent with the evidence gate.
- Nine tickers (ASML, TER, AMAT, COHR, MSFT, NBIS, AMD, VRT, AVGO) were excluded from new proposals this run solely because they already carry open, undecided proposals (P-261/263/264/281/282/284/286/288/290) — this is a coverage note, not a signal judgment; the triggers still fired on them.

```json
{"policy_draft":null,
 "stress_table":{"as_of":"2026-09-14",
   "anchored_to":{"us10y_pct":4.975,"vix":18.02,"dxy":99.592,"fed_rate_pct":3.63,"fed_stance":"hawkish"},
   "scenarios":[
     {"scenario":"AI-capex pause","impact_pct_low":-22.0,"impact_pct_high":-14.0,"most_exposed":["TSM","AVGO","MU","ALAB","LITE"],
      "mechanism":"95.98% AI-capex concentration; ai_capex_chain pressured first and hardest per scout -- NQ leading ES down, optics -6.25% overnight is this scenario's leading edge already showing","basis":"live","note":""},
     {"scenario":"rates +100bp","impact_pct_low":-12.0,"impact_pct_high":-7.0,"most_exposed":["MSFT","GOOG","AMZN"],
      "mechanism":"US10Y +29.3bps trailing month already pricing this drift; hawkish FOMC stance into 09-15/16 decision is the live mechanism scout names directly","basis":"live","note":""},
     {"scenario":"tariff/export-control escalation","impact_pct_low":-9.0,"impact_pct_high":-4.0,"most_exposed":["AMAT","ASML","MU","TSM"],
      "mechanism":"CXMT HBM3E qualification-stage shipments to Alibaba/Cambricon ~1yr ahead of 2027 consensus; China export-control tax on AMAT named in this run's dispatch","basis":"live","note":""},
     {"scenario":"USD/INR +/-3%","impact_pct_low":0.0,"impact_pct_high":0.0,"most_exposed":[],
      "mechanism":"Book is 100% USD-denominated; INR move is a translation effect on investor's home-currency net worth (approx +/-3% there), not a book P&L event","basis":"static_assumption","note":"0% on the USD book itself"}
   ],
   "data_quality":["Rate-sensitive and AI-capex-pause rows anchored to scout's live regime read (cluster_impact); tariff row anchored to catalyst_threat table; USD/INR row is a static translation assumption, not re-derived"]},
 "proposals":[
   {"direction":"BUY","ticker":"TSM","size_usd":1461.62,"price_at_proposal":418.71,"benchmark_price_at_proposal":568.53,
    "rationale":"Semis-cluster leader (dispatch: leader TSM/laggard AMAT); RSI14 56.9, STRONG UPTREND + PEER LEADER, rotation bucket accumulate, +3.74pp vs SMH, thesis strengthening (unverified). Not clamped.",
    "trigger_type":"trend_entry","trigger_bucket":null,"pair_id":null,"pair_role":null,
    "size_wanted_usd":1461.62,"clamped_by":null,"stop_price_usd":398.7794,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"direction":"BUY","ticker":"APH","size_usd":1088.19,"price_at_proposal":80.50,"benchmark_price_at_proposal":568.53,
    "rationale":"Optics-cluster laggard (dispatch: leader LITE/laggard APH) with strengthening thesis -- organising rule treats this as opportunity not dead money. RSI14 57.4 not overbought, STRONG UPTREND, rotation bucket accumulate, +1.5pp vs SMH. Not clamped.",
    "trigger_type":"trend_entry","trigger_bucket":null,"pair_id":null,"pair_role":null,
    "size_wanted_usd":1088.19,"clamped_by":null,"stop_price_usd":75.3963,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"direction":"SELL","ticker":"MU","size_usd":277.56,"price_at_proposal":185.04,"benchmark_price_at_proposal":568.53,
    "rationale":"Stretched (names_stretched) with watch thesis -- real profit to book. Same CXMT/China-HBM catalyst thread independently flagged in this run's catalyst_threat table, folded in here rather than raised twice.",
    "trigger_type":"profit_rotation","trigger_bucket":null,"pair_id":"profit_rotation-MU-KLAC","pair_role":"sell_leg",
    "size_wanted_usd":277.56,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"direction":"BUY","ticker":"KLAC","size_usd":277.56,"price_at_proposal":null,"benchmark_price_at_proposal":568.53,
    "rationale":"Laggard (-10.5pp) with strengthening thesis -- yet to rally. Funded by MU sell proceeds (self-funding pair). Not clamped.",
    "trigger_type":"profit_rotation","trigger_bucket":null,"pair_id":"profit_rotation-MU-KLAC","pair_role":"buy_leg",
    "size_wanted_usd":277.56,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"direction":"SELL","ticker":"SMCI","size_usd":113.37,"price_at_proposal":null,"benchmark_price_at_proposal":568.53,
    "rationale":"Stretched (names_stretched) with watch thesis -- real profit to book despite PEER LEADER bullish bucket; RSI14 60.5 approaching overbought.",
    "trigger_type":"profit_rotation","trigger_bucket":null,"pair_id":"profit_rotation-SMCI-CIEN","pair_role":"sell_leg",
    "size_wanted_usd":113.37,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"direction":"BUY","ticker":"CIEN","size_usd":113.37,"price_at_proposal":null,"benchmark_price_at_proposal":568.53,
    "rationale":"Strengthening thesis, comfortably inside cap (cap_multiple 0.002 -- essentially a fresh position). Funded by SMCI sell proceeds (self-funding pair). Not clamped.",
    "trigger_type":"profit_rotation","trigger_bucket":null,"pair_id":"profit_rotation-SMCI-CIEN","pair_role":"buy_leg",
    "size_wanted_usd":113.37,"clamped_by":null,"stop_price_usd":null,"exited_on":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}}
 ],
 "scorecard_read":"58 graded, overall 29.3% 30d accuracy (TRIM/SELL 34.5% n=29, BUY 33.3% n=21, HOLD 0.0% n=8, 2 rows quarantined for anchor review). Weak record with no directional edge -- TRIM and BUY sit within a point of each other, near coin-flip. HOLD's 0% is thin (n=8) and structurally hard to grade as worked in a falling-book period. This run's proposals should be weighted as sized suggestions against a soft track record, not high-confidence calls; the two profit_rotation pairs are self-funding (no net new cash risk) which partly offsets that softness.",
 "deemphasize_buckets":[],
 "data_quality":["No compute_valuation.json/smith-quality output this run -- 2a-iii valuation-stretched screen not applied to TSM/APH BUYs","ASML/TER/AMAT/COHR/MSFT/NBIS/AMD/VRT/AVGO excluded from new proposals solely because open undecided proposals already exist on those tickers (P-261/263/264/281/282/284/286/288/290)","Thesis entries backing all six legs above are tagged verified:'unverified' in source data; sizing rests on computed trigger/rotation math, not on thesis claims"]}
```

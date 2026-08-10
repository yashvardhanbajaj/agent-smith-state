# Agent Smith — Portfolio Strategist (DEEP, 2026-08-10)

Policy confirmed — this run's drift analysis is **not** provisional. No policy bootstrap needed.

## Risk-off status
**NORMAL.** Drawdown -5.742% vs warn 8% / risk-off 12% thresholds (policy). No defensive-lead required. Proposals below are ordinary rebalancing, not risk-off triage — but sentiment (extreme greed, VIX-driven) still argues for leaning into profit-booking on the breached names rather than sitting still.

## Sized proposals (2026-08-10)

**1. TRIM SNDK ~$900** (~0.74 sh @ $1,212.38 last known fill 08-07, not a live quote — cash session not yet open)
Largest risk-cap excess in the book this run: 2.80x its ATR cap, ~$1,222 over headroom. Thesis WATCH-**elevated** (real FY1Q27 demand-guide miss 08-05, not beta noise) — WATCH-elevated names outrank pure drift breaches per policy. Extreme-greed sentiment (80.2) argues for booking profit into the over-cap names rather than waiting; SNDK is the standout. AI Memory/Storage cluster itself is in-band (17.90%) so this is a name-level risk-cap/thesis cure, not a cluster cure. LTCG: lot is 3 days old (08-07 buy) — no boundary proximity, prefer_ltcg not binding. **Flag:** derisk queue's -43.7% 1-month return figure for SNDK conflicts with a yfinance calendar reading of -29.8% — unreconciled, not picked between; treat SNDK's exact drawdown magnitude with caution until resolved.

**2. TRIM SKHY ~$500** (~3.6 sh @ $138.07 last known fill 08-07, not live)
WATCH-elevated: down ~9.2% since the 08-05 entry despite dominant 60-70% HBM4 Vera Rubin allocation share, with no adverse news found (flagged by thesis as unexplained). 1.87x its ATR cap, $733 headroom deficit — second-largest risk excess in the book. Position was already whipsawed once this week (stop-loss sold 5@$135, same-day re-buy 10@$138.07, net +5sh) — the book has been adding into a name whose weakness thesis can't yet explain. A trim here is a risk-discipline call, not a thesis-broken call. The SK Hynix $38bn plant news is 2027+ relief and doesn't ease current tightness, so it's not a reason to hold size steady.

**3. TRIM NVDA ~$650** (~3.3 sh @ ~$195 last known lot price, 07-28/07-30 fills — not a live quote)
Sentiment-led profit-booking per the extreme-greed hint: NVDA is the top position (8.58% of book), 1.21x its ATR risk cap ($562 headroom deficit), and AI Semis/Fabs is over its cluster ceiling (36.91% vs 30%, [25,35], +6.91pt). This trim cures both the risk cap and chips at the cluster ceiling simultaneously — no directional conflict. Peer-leader/strong-uptrend signal status is a reason to size this as a partial trim (cap-cure, not a signal call on the name), not a reason to skip it.

**4. ROTATE within AI Semis/Fabs: TRIM AMD ~$700 → ADD QCOM ~$380** (AMD ~1.4 sh @ $495.39 last known fill 08-06; QCOM ~2.4 sh @ $160.33, revalidated 08-07 — replaces PAIR-001/P-062+P-063 as constructed, see below)
AMD is 1.55x its ATR cap ($691 headroom deficit) — de-risk queue flags this as fragility-driven (vol/ATR), not thesis-driven; thesis is actually STRENGTHENING, so this is capped-size risk management, not a signal call. QCOM carries an OVERSOLD BOUNCE signal at 100% interim 7d hit rate (n=3, not yet 30d-validated) and sits in rotation.json's accumulate bucket. Sizing QCOM's add at $380 (not the full $700) mirrors P-063's own math — QCOM's own risk-cap headroom is ~$396, so anything larger creates a fresh breach next run. Because AMD and QCOM are **both** AI Semis/Fabs, this rotation is cluster-neutral — it doesn't touch the +6.91pt ceiling breach one way or the other — while the un-rotated $320 stays as cash, contributing toward curing the book's aggregate open-risk breach (12.674% vs 10% cap, ~$1,131 excess).

**5. HOLD CEG — do not execute P-062 this run.**
P-062 (Trim CEG $380, trigger_type=stretch, funding leg of PAIR-001) is not supported by this run's data the way it was on 08-06. Two problems: (a) this run's signals tail places CEG in **REVERSAL-BUY-WATCH (continuing)** — a bullish setup — which contradicts P-062's original cited basis of "a live STRONG DOWNTREND signal flag." That basis appears stale. (b) CEG sits in AI Power/Cooling/DC Infra, which is **under** its floor this run (8.27% vs 15%, [10,20], -6.73pt). P-062's own rationale already correctly disclaims the cluster as a reason to trim ("not a cluster-breach cure") and CEG is not on this run's risk-cap over_cap list either — so there is no live trigger holding this proposal up: not risk-cap, not cluster, and the stretch/signal basis has now reversed. Recommend parking P-062 rather than acting on it. Since P-063's QCOM funding is resolved independently via the AMD rotation above (#4), the PAIR-001 construct is superseded in full — both legs are addressed without executing the CEG leg.

No proposal here relies on lots.json's LTCG boundary — checked directly: every lot in the book is dated April–August 2026, so the earliest possible 24-month Indian LTCG boundary is ~22 months out for any holding. prefer_ltcg is not binding on any of the above.

## Stress table (approximate, macro-anchored — six scenarios)

| Scenario | Est. portfolio impact | Most exposed |
|---|---|---|
| AI-capex pause (-20% cluster move on AI-capex chain) | ~-16.9% of total book (-$7,159 on $35,795 of AI-capex-exposed equity, 93.6% of equity basis) | NVDA, AVGO, TSM, MU/SNDK/DRAM complex |
| Rates +100bp (high-beta/long-duration sleeve, -10%) | ~-7.7% of total book (-$3,250 on an estimated 85% of equity as rate-sensitive) | NVDA, AMD, ASML, growth-multiple names — anchored to macro's hawkish Fed (3.63%) + 10yr already +13bp/month; this is incremental pressure on an already-tightening backdrop, not a shock from a calm base |
| Tariff/export-control escalation (China-revenue sleeve, -15%) | ~-2.5% to -3% of total book (rough — precise per-name China-revenue weights not fully available this run) | TSM, ASML (China-DUV), BABA, MP |
| USD/INR ±3% | ~0% on the USD-reported book itself; in INR terms, a 3% rupee depreciation lifts the book's INR-equivalent value ~3%, a 3% appreciation cuts it ~3% — net worth effect only, not a US-book risk | N/A (currency pass-through) |
| Low-vol/extreme-greed mean-reversion (VIX shock, SMH -10%) | ~-10.0% of total book (-$4,243, book beta 1.106 vs SMH — SPX beta of 1.491 is flagged misleading for this book) | NVDA, COHR (unexplained +24% run), SNDK (highest single-name beta at 2.92 vs SMH), AMD |
| Memory/HBM demand air-pocket (CXMT oversupply / customer inventory correction, -25% on cluster) | ~-4.0% of total book (-$1,711 on $6,843 = 17.90% of equity in AI Memory/Storage) | SNDK, SKHY, MU, DRAM — all WATCH or WATCH-elevated this run |

Macro backdrop framing these: regime is risk_on_but_stretched (SPX near 52w high, VIX near 52w low, hawkish Fed, extreme greed) — the AI-capex chain is favored by current momentum but per smith-macro's own read is the most exposed segment if this low-vol/extreme-greed setup mean-reverts under rising yields. The book's thin diversifier bench (94.9% AI-capex concentration per thesis's broader count vs 93.623% per compute_drift's equity-only basis — both cited, not reconciled to one number) limits any real offset in that scenario.

## Hit-rate readout (INTERIM 7d only — not yet 30d-validated, label accordingly)
- OVERSOLD BOUNCE: 100.0% (n=4) — interim only
- TARGET GAP: 58.3% (n=12) — interim only
- MOMENTUM+VOLUME: 50.0% (n=12) — interim only, worth watching but not yet at the <40%/n≥5 de-emphasis bar

No bucket meets the de-emphasis threshold (persistently <40% over ≥5 scored entries) this run. All three are still in the interim (7d) window, not the 30d-validated window — treat directionally, not as settled edge.

## Proposal-outcomes scorecard
Per proposals.json's own tracker: still zero proposals in the 30d/90d scoring window. Oldest open cohort (2026-07-13) needs ~2026-08-12 to reach 30 days — two days out from today (2026-08-10). trim_accuracy_30d / add_accuracy_30d / overall_accuracy_30d remain null this run; nothing to score yet.

## Data quality flags
- SNDK 1-month return: -43.7% (derisk queue) vs -29.8% (yfinance calendar reading, per smith-signals) — unreconciled, flagged for the user rather than resolved here.
- AI-capex concentration reported on two bases this run: 93.623% of equity (compute_drift.json) vs 94.9% of book (smith-thesis's broader sub-cluster count) — both cited above, not merged into one figure.
- No live per-ticker quotes were embedded for held positions this run (Monday pre-open, cash session not yet open); proposal prices above use last known transaction fills from lots.json/proposals.json, explicitly flagged as not live.
- G55 (carried): MSFT unresearched, 11 uncaptured trades from 08-06/07 still open.
- G51 (carried): 2026-08-06 stop cascade — CLS took an unrelated -12.9% hit (dilutive offering), no stop fired.
- This run's own uncaptured-reason trades (SNDK +0.5sh, TER +3sh, ARM +3sh new, NBIS +3sh re-entry, INTC +5sh new) remain uncaptured despite email-confirmed fills — none of the proposals above depend on knowing the "why" behind these adds, but they're carried forward as a gap.

```json
{"policy_draft":null,
 "risk_off_status":"normal",
 "proposals":[
   {"id":"S-2026-08-10-01","action":"Trim SNDK","size_usd":900,"price_at_proposal":1212.38,"trigger_type":"thesis_watch_elevated+risk_cap","cluster":"AI Memory/Storage","rationale":"2.80x ATR risk cap (largest excess in book, ~$1,222), thesis WATCH-elevated on real FY1Q27 demand-guide miss, extreme-greed sentiment favors profit-booking; SNDK -43.7%/-29.8% 1m-return discrepancy flagged unreconciled; cluster itself in-band so this is a name-level cure."},
   {"id":"S-2026-08-10-02","action":"Trim SKHY","size_usd":500,"price_at_proposal":138.07,"trigger_type":"thesis_watch_elevated+risk_cap","cluster":"AI Memory/Storage","rationale":"1.87x ATR risk cap ($733 headroom deficit), WATCH-elevated on unexplained ~9.2% decline since 08-05 entry despite dominant HBM4 allocation share; book already whipsawed a stop-out/re-buy into this name this week; $38bn SK Hynix plant news is 2027+ relief, not a reason to hold size."},
   {"id":"S-2026-08-10-03","action":"Trim NVDA","size_usd":650,"price_at_proposal":195.0,"trigger_type":"sentiment_profit_booking+risk_cap+cluster_ceiling","cluster":"AI Semis/Fabs","rationale":"Extreme-greed sentiment hint leads with profit-booking on largest position; 1.21x ATR risk cap ($562 deficit) and AI Semis/Fabs over ceiling (+6.91pt) both cured directionally by the same trim, no conflict."},
   {"id":"S-2026-08-10-04a","action":"Trim AMD","size_usd":700,"price_at_proposal":495.39,"trigger_type":"risk_cap_fragility","cluster":"AI Semis/Fabs","rationale":"1.55x ATR risk cap ($691 deficit), de-risk queue flags this as fragility- not thesis-driven (thesis STRENGTHENING); funds paired QCOM add and residual cash toward the aggregate open-risk breach."},
   {"id":"S-2026-08-10-04b","action":"Add QCOM","size_usd":380,"price_at_proposal":160.33,"trigger_type":"signal_conviction","cluster":"AI Semis/Fabs","rationale":"OVERSOLD BOUNCE signal, 100% interim 7d hit rate (n=3, not 30d-validated); sized to QCOM's own ~$396 risk-cap headroom; cluster-neutral against AMD trim since both are AI Semis/Fabs -- replaces PAIR-001 (P-062/P-063) funding via CEG."},
   {"id":"S-2026-08-10-05","action":"Hold CEG, do not execute P-062","size_usd":0,"price_at_proposal":261.0,"trigger_type":"retire_stale_trigger","cluster":"AI Power/Cooling/DC Infra","rationale":"P-062's cited STRONG DOWNTREND basis has reversed to REVERSAL-BUY-WATCH (continuing) this run; CEG not on the risk-cap over_cap list; cluster is -6.73pt under floor. No live trigger remains; QCOM funding resolved independently via AMD rotation above."}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "stress_table":[
   {"scenario":"AI-capex pause (-20% cluster move)","impact_pct_of_book":-16.9,"impact_usd":-7159,"most_exposed":["NVDA","AVGO","TSM","MU","SNDK","DRAM"]},
   {"scenario":"Rates +100bp (high-beta/long-duration sleeve, -10%)","impact_pct_of_book":-7.7,"impact_usd":-3250,"most_exposed":["NVDA","AMD","ASML"],"note":"anchored to macro's hawkish Fed 3.63% + 10yr +13bp/month, incremental not shock-from-calm"},
   {"scenario":"Tariff/export-control escalation (China-revenue sleeve, -15%)","impact_pct_of_book":-2.75,"impact_usd":null,"most_exposed":["TSM","ASML","BABA","MP"],"note":"rough -- precise per-name China-revenue weights not fully available this run"},
   {"scenario":"USD/INR +/-3%","impact_pct_of_book":0.0,"impact_usd":0,"most_exposed":[],"note":"no direct USD-book effect; INR-terms net worth moves ~3% with the currency"},
   {"scenario":"Low-vol/extreme-greed mean-reversion (VIX shock, SMH -10%)","impact_pct_of_book":-10.0,"impact_usd":-4243,"most_exposed":["NVDA","COHR","SNDK","AMD"],"note":"book beta 1.106 vs SMH used, not the misleading 1.491 SPX beta"},
   {"scenario":"Memory/HBM demand air-pocket (CXMT oversupply, -25% on cluster)","impact_pct_of_book":-4.0,"impact_usd":-1711,"most_exposed":["SNDK","SKHY","MU","DRAM"]}
 ],
 "hit_rate_readout":[
   {"bucket":"OVERSOLD BOUNCE","hit_rate":100.0,"n":4,"window":"interim_7d"},
   {"bucket":"TARGET GAP","hit_rate":58.3,"n":12,"window":"interim_7d"},
   {"bucket":"MOMENTUM+VOLUME","hit_rate":50.0,"n":12,"window":"interim_7d"}
 ],
 "deemphasize_buckets":[],
 "data_quality":["SNDK 1m return -43.7% (derisk queue) vs -29.8% (yfinance calendar) unreconciled","AI-capex concentration reported on two bases: 93.623% of equity (compute_drift) vs 94.9% of book (smith-thesis) not merged","no live per-ticker quotes embedded this run (Monday pre-open); prices above are last known transaction fills, not live","G55 carried: MSFT unresearched, 11 uncaptured trades 08-06/07","G51 carried: 08-06 stop cascade, CLS unrelated -12.9% hit (dilutive offering), no stop fired","this run's own uncaptured-reason trades (SNDK+0.5sh, TER+3sh, ARM new, NBIS re-entry, INTC new) remain unexplained"]}
```

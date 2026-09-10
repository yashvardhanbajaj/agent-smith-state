# smith-thesis — 2026-09-10 QUICK sweep (Wave 2, post smith-signals)

Book: 31 US holdings (VST/FSLR stopped out 09-09, correctly absent from both holdings and this
thesis map — never carried entries here, nothing to mark exited). KLAC/QCOM added +2sh each 09-09.

## Thesis table — CHANGED this run

- **META** — intact -> **STRENGTHENING**. Compute/Hyperscaler; AI-capex demand-linked buyer, own
  Muse AI-agent platform launched 09-09. FOR: Muse launch + favorable lawsuit settlement (09-09)
  cleared 4 standing negative buckets (STRONG DOWNTREND/PEER LAGGARD/NEW HEADWINDS/OVERSOLD BOUNCE)
  in one +6.55% session (src: smith-signals 2026-09-10, INDmoney news). AGAINST: TARGET GAP
  persists even post-pop (target $754.77, +13.4% upside) — move is real but hasn't closed the
  valuation gap; 1.55% position, small book impact; pre-08-12 thesis text not in this run's slice
  (status-only tier), so this is effectively a fresh write, not a continuation — none found beyond
  that. verified: secondary (smith-signals aggregation of INDmoney news, 2026-09-10). Precedent
  check (smith_math.py gaps, query "reversal on positive catalyst") found no exact match; closest
  is G75 ("a price move is not a fundamental verdict") — upgrade is defensible here because two
  NAMED events drove it (product launch + settlement), not bare price action.
- **QCOM** — strengthening (unchanged), evidence populated for the first time. Diversifying from
  handsets into AI/datacenter CPUs and auto; position added +2sh @$175.44 on 09-09. FOR: RBC PT
  raise citing AI chip-partnership expansion (09-09); AWS partnership targeting $5B AI-chip revenue
  by FY27 (09-08) (src: smith-signals 2026-09-10 / INDmoney news). AGAINST: -1.17σ peer-laggard vs
  SMH persists despite the fresh positive news — catalyst hasn't moved the peer-relative reading
  yet (src: smith-signals 2026-09-10). verified: unverified.
- **KLAC** — strengthening (unchanged). Semicap process-control (AI Semis/Fabs); position now 8sh
  (3.48%) after 09-09 add. AGAINST (new): pulled back -3.21% the day after the add (now $182.91 vs
  $181.98 buy, essentially flat) — continues the "beats but sells off" pattern already on record
  (07-28 -9.6% AH post-beat, 07-09 5.3% swing); no negative company news found (src: INDmoney
  get_us_stocks_details, 2026-09-10). Existing FOR/AGAINST otherwise carried forward unchanged.
- **VRT** — WATCH (unchanged, evidence substantially rewritten). Thesis (was literally "unchanged"
  placeholder, now written): AI-datacenter power/cooling infra (UPS, thermal); $26B rev-by-2030
  target, FY26 guide raised to $14B on 24% Q2 growth, $1.45B Utility Innovation Holdings
  acquisition announced 09-02. FOR: Q2 rev +24% YoY, EPS +60% adj, guide raised (src: INDmoney news
  08-18); $26B-by-2030 target + DC-power acquisition (src: INDmoney news 09-02/09-08). AGAINST: 1
  insider sold in last 60 days, no buying into the drawdown (src: SEC Form 4, 09-07, carried
  forward); **-9.61% today, confirmed live (not a cache artifact — compute_buckets.json's cached
  bucket read lags the live price), with NO dated catalyst found in a fresh news pull (latest item
  09-08, positive) — largest unexplained single-day drop in the book this run, on a 4.37% position**
  (src: INDmoney get_us_stocks_details live quote + news, 2026-09-10); already ~32% off its 2026
  peak as of 08-28 despite that quarter's beat (src: INDmoney news 08-28) — a pre-existing
  distribution pattern, not new. verified: unverified. No status change made — genuinely mixed
  (real fundamentals vs. real unexplained weakness) — so no precedent-check gate applies.

## Reviewed, unchanged this run (examined vs today's signals/price data, verdict stands)

GEV, ASML, AMAT, SMCI, TSM, MRVL, AMD, ALAB, TER, NVDA, LRCX, STM, GOOG, NBIS, LITE, CLS, CIEN,
GLW, COHR, WDC, INTC, MSFT, BE, APH, AVGO, MU, SKHY — 27 names. None carried a fresh negative or
positive catalyst material enough to move a verdict; day moves (GEV -2.1%, ASML -2.0%, AMAT -0.8%,
SMCI -3.3% vs MRVL +4.3%, AMD +3.0%, TER +3.1%, ALAB +4.0%) read as broad within-factor dispersion
on a flat SMH day (+0.10%), not name-specific news.

## Factor cluster table (% of book, from holdings_trim.json weights x sector_map)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | NVDA,ASML,AMAT,TER,QCOM,TSM,AMD,LRCX,INTC,KLAC | 34.17% |
| AI Power/Cooling/DC Infra | GEV,VRT,BE | 17.26% |
| AI Networking/Optics | MRVL,AVGO,CIEN,GLW,COHR,LITE,ALAB,APH | 20.40% |
| Compute/Hyperscaler | MSFT,GOOG,NBIS,META | 10.26% |
| AI Memory/Storage | MU,WDC,SKHY | 9.54% |
| Compute/Hyperscaler OEM | CLS,SMCI | 4.10% |
| Analog/Industrial Semis | STM | 4.29% |

**Combined AI-capex chain (all clusters except Analog/Industrial Semis): ~95.73% of book.**
A datacenter-capex de-rating or pause event hits essentially the whole book at once. Co-movement
check: SMH itself was flat today (+0.10%), while book members ranged from VRT -9.6% to SKHY +7.1%
(~17pp spread) — today's action is idiosyncratic dispersion within the factor, not a factor-wide
move, but the underlying single-bet structure is unchanged.

## Single-factor risk verdict

This is, to a first approximation, one bet: ~96% of the book is levered to AI-capex spend across
semis, memory, optics, power-infra and the hyperscalers buying it, with only STM's Analog/
Industrial Semis sleeve (4.29%) genuinely outside that chain — and even STM's own bull case now
leans on AI-datacenter revenue targets (>$1B 2026, >$2B 2027), so the truly uncorrelated slice is
smaller than 4.29% in substance. The book does not need a sector-wide crash to feel pain: today
showed that even a flat SMH day produces ~17pp of dispersion among AI-capex names on idiosyncratic
news, so single-name catalyst risk (a KLAC-style post-print reset, a VRT-style unexplained air
pocket) is a live, recurring cost of this structure even before any factor-level correction.

## HBMTracker reconciliation (MU, SKHY — both currently held and HBM-sensitive; EWY/DRAM not held)

Source: consumer_view.json snapshot (embedded, `shared/hbm_tracker.json`). **Staleness flag:
max_price_staleness_days=33 (>30-day threshold) — oldest priced point 2026-08-05.** Reconciliation
below is weighted down accordingly; this is a stale-price situation, not a confirmed divergence.

- **MU** — metric: HBM3E ASP, current $9.00/GB mid, basis **stack_derived**, trend_within_basis
  0.0% (flat, 07-19 to 08-05). Thesis: WATCH, driven by CXMT structural/capacity risk (qualification-
  stage, per smith-catalyst 09-01), not ASP. verdict_conflict: none — flat-within-basis price data
  is consistent with a capacity-risk WATCH, not a price-driven one. direction: **no_action**.
  Corrections C1/C2 checked (both apply to hbm3e/hbm4 basis-splice artifacts, not to this flat read).
- **SKHY** — metric: HBM3E ASP (same series), current $9.00/GB, basis stack_derived, trend 0.0%.
  Thesis: STRENGTHENING, today +7.1% on BofA "tight HBM supply/pricing power" commentary (src:
  smith-signals). Apparent tension: thesis strengthening on a "tight supply" narrative while the
  tracker's own PRICED series is flat and 33 days stale. Reconciliation: **(c) measurement-basis /
  staleness artifact — no thesis action**. The tracker's own G6 known-gap already documents a
  TrendForce-reported HBM3E SPOT price ~4-5x LTA as of 2026-09-01 (~$2,100/36GB stack) that is
  deliberately NOT in the priced series (basis-splice risk per C1's lesson) — today's rally is
  directionally consistent with that spot-tightness story but not confirmable against fresh priced
  data since the tracker hasn't re-run past 08-05. Supply_structure (2026-06-05, unchanged): SK
  Hynix holds 60-70% of HBM4 Vera Rubin allocation vs Samsung 25-30%, Micron low-single-to-teens —
  SKHY captures the largest share of the current ramp, which is the structural reason a
  supply-tightness story disproportionately favors this name over MU. Caution: this desk has seen
  an uncorroborated "tight supply" claim drive a similar SKHY rally before (G8, 2026-09-06,
  Susquehanna DRAM/NAND forecast, never corroborated) — today's BofA-sourced note is a different,
  more identifiable source, but a full tier-1 corroboration was not attempted this run (budget).
  direction: no_action. Corrections C1/C2 checked.
- Forward context (unchanged, carried): 2026 HBM3E contract hike guided 18-22% (TrendForce);
  DDR5 profitability crossover already flagged 2026-04-21; 2027 HBM contract prices guided
  "multiples higher" (80-150%, TrendForce 06-02).

## data_quality

1. HBM tracker price series 33 days stale (threshold ~30) — MU/SKHY reconciliation weighted down
   accordingly; recommend an hbm-tracker refresh given SKHY's +7.1% "tight supply" move today.
2. VRT -9.61% today confirmed via live quote, not a cache artifact, but no dated catalyst found in
   a fresh news pull — recorded as an open evidence_against item, WATCH held pending a cause.
3. Task's "WHICH NAMES" list (MU, EWY, DRAM) is stale vs current holdings — SKHY (a direct holding
   with an explicit HBM4-allocation thesis) was included on substance; EWY/DRAM not currently held.
4. Budget: 1 batched get_us_stocks_details call (VRT+KLAC news), 1 smith_math.py gaps precedent
   check (META status change) — well under the soft cap; no other verification calls spent.
5. Prior thesis text for META, QCOM's evidence arrays, and VRT's one-liner were placeholder/absent
   in this run's slice — rewritten from scratch rather than carried forward blank.

```json
{"thesis":{"changed":{
  "META":{"status":"strengthening","thesis":"Compute/Hyperscaler; AI-capex demand-linked buyer, own Muse AI-agent platform launched 09-09","evidence_for":[{"claim":"Muse AI-agent launch + favorable lawsuit settlement cleared 4 standing negative buckets (STRONG DOWNTREND/PEER LAGGARD/NEW HEADWINDS/OVERSOLD BOUNCE) in one +6.55% session","date":"2026-09-09","source":"smith-signals 2026-09-10 sweep, INDmoney news"}],"evidence_against":[{"claim":"TARGET GAP persists post-pop, target $754.77 (+13.4% upside) -- move real but hasn't closed the valuation gap; 1.55% position, small book impact","date":"2026-09-10","source":"smith-signals 2026-09-10"}],"verified":"secondary","verified_against":"smith-signals 2026-09-10 sweep (INDmoney news feed)","verified_on":"2026-09-10","note":"Upgraded from intact. Prior full thesis text unavailable in this run's slice (status-only tier) -- effectively a fresh write. Precedent check (smith_math.py gaps, query 'reversal on positive catalyst') found no exact match; closest is G75 (price move != fundamental verdict) -- upgrade defensible here because two named events drove it, not bare price action.","reviewed_on":"2026-09-10"},
  "QCOM":{"status":"strengthening","thesis":"Diversifying from handsets into AI/datacenter CPUs and auto; added +2sh @$175.44 on 09-09","evidence_for":[{"claim":"RBC price-target raise citing AI chip-partnership expansion","date":"2026-09-09","source":"smith-signals 2026-09-10 / INDmoney news"},{"claim":"AWS partnership targeting $5B AI-chip revenue by FY27","date":"2026-09-08","source":"smith-signals 2026-09-10 / INDmoney news"}],"evidence_against":[{"claim":"-1.17 sigma peer-laggard vs SMH persists despite the fresh positive news -- catalyst hasn't moved the peer-relative reading yet","date":"2026-09-10","source":"smith-signals 2026-09-10"}],"verified":"unverified","verified_against":"","verified_on":"","note":"Evidence populated for the first time this run; status unchanged.","reviewed_on":"2026-09-10"},
  "KLAC":{"status":"strengthening","thesis":"Semicap process-control/inspection (AI Semis/Fabs); position now 8sh (3.48%) after 09-09 add","evidence_for":[{"claim":"Q4 FY26 revenue $3.66B, non-GAAP EPS $1.05 at/above guidance high end; $7B buyback announced","date":"2026-07-28","source":"INDmoney news + stockanalysis.com/stocks/klac"},{"claim":"Stifel raised PT $191->$270; consensus PT $231.78 (+28% upside), accelerating 2026-2027 growth guide","date":"2026-08-24","source":"INDmoney news + stockanalysis.com/stocks/klac"}],"evidence_against":[{"claim":"stock fell ~9.6% after-hours on the July 28 beat -- expectations-reset/valuation reaction, unresolved whether it recurs","date":"2026-07-28","source":"INDmoney news"},{"claim":"pulled back -3.21% the day after the 09-09 add (now $182.91 vs $181.98 buy, essentially flat) -- continues the beat-but-sells-off pattern; no negative company news found","date":"2026-09-10","source":"INDmoney get_us_stocks_details"}],"verified":"secondary","verified_against":"stockanalysis.com/stocks/klac + INDmoney news","verified_on":"2026-08-25","note":"Status unchanged; new pullback evidence added post-add.","reviewed_on":"2026-09-10"},
  "VRT":{"status":"watch","thesis":"AI-datacenter power/cooling infra (UPS, thermal management); $26B revenue-by-2030 target, FY26 guide raised to $14B on 24% Q2 growth, $1.45B Utility Innovation Holdings acquisition announced 09-02","evidence_for":[{"claim":"Q2 2026 revenue +24% YoY, adj EPS +60%; FY26 guidance raised to $14B on AI-datacenter demand","date":"2026-08-18","source":"INDmoney get_us_stocks_details news"},{"claim":"targeting $26B revenue by 2030; $1.45B acquisition of Utility Innovation Holdings to expand DC power offering","date":"2026-09-02","source":"INDmoney get_us_stocks_details news"}],"evidence_against":[{"claim":"1 insider sold in last 60 days; no insider buying during drawdown","date":"2026-09-07","source":"SEC Form 4"},{"claim":"-9.61% today, confirmed via live quote (not a cache artifact), with no dated catalyst found in a fresh news pull (latest item 09-08, positive) -- largest unexplained single-day drop in the book this run, 4.37% position","date":"2026-09-10","source":"INDmoney get_us_stocks_details live quote + news"},{"claim":"already ~32% off its 2026 peak as of 08-28 despite that quarter's beat -- pre-existing distribution pattern, not new","date":"2026-08-28","source":"INDmoney news"}],"verified":"unverified","verified_against":"","verified_on":"","note":"Status unchanged (genuinely mixed: real fundamentals vs. real unexplained weakness) -- no precedent-check gate applies since no status change made.","reviewed_on":"2026-09-10"}
 },"unchanged_count":27,"reviewed_unchanged":["GEV","ASML","AMAT","SMCI","TSM","MRVL","AMD","ALAB","TER","NVDA","LRCX","STM","GOOG","NBIS","LITE","CLS","CIEN","GLW","COHR","WDC","INTC","MSFT","BE","APH","AVGO","MU","SKHY"]},
 "sector_map":{"changed":{},"unchanged_count":31},
 "etf_constituents_updates":{},
 "ai_capex_pct":95.73,
 "factor_flags":["AI-capex chain ~95.73% of book -- a datacenter-capex de-rating event hits nearly the whole book at once","Largest genuinely uncorrelated slice is STM (Analog/Industrial Semis) at 4.29%, and even STM's own bull case leans on AI-datacenter revenue targets","SMH flat today (+0.10%) while book members ranged VRT -9.6% to SKHY +7.1% (~17pp spread) -- idiosyncratic dispersion within the factor, not a factor-wide move"],
 "thesis_tensions":[
   {"metric":"HBM3E ASP (stack-derived)","current_value":9.0,"basis":"stack_derived","trend_within_basis_pct":0.0,"verdict_conflict":"none -- MU's WATCH is driven by CXMT structural/capacity risk, not ASP","direction":"no_action","reconciliation":"Flat-within-basis price data is consistent with a capacity-risk-driven WATCH; price series is also 33 days stale so weighted down. No action.","corrections_checked":["C1","C2"]},
   {"metric":"HBM3E ASP (stack-derived) vs SKHY 'tight supply' rally","current_value":9.0,"basis":"stack_derived","trend_within_basis_pct":0.0,"verdict_conflict":"thesis STRENGTHENING on today's +7.1% 'tight HBM supply/pricing power' move while the priced series itself is flat and 33 days stale","direction":"no_action","reconciliation":"(c) measurement-basis/staleness artifact, not a confirmed divergence -- tracker's own G6 gap documents an unpriced HBM3E SPOT premium (~4-5x LTA, TrendForce 09-01) consistent in direction with today's move but not yet in the priced series (basis-splice risk); recommend hbm-tracker refresh, no thesis action this run.","corrections_checked":["C1","C2"]}
 ],
 "data_quality":["HBM tracker price series 33 days stale (>30-day threshold) -- MU/SKHY reconciliation weighted down accordingly","VRT -9.61% today confirmed live, no dated catalyst found -- WATCH held pending a cause","Task's WHICH-NAMES list (MU, EWY, DRAM) is stale vs current holdings; SKHY included on substance as a direct HBM-sensitive holding","Budget: 1 batched news call (VRT+KLAC) + 1 precedent-check call, well under soft cap","META/QCOM/VRT thesis text was placeholder or absent in this run's slice and was rewritten from scratch rather than carried forward blank"]}
```

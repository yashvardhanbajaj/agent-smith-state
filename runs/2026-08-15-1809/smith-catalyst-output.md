# Factor Catalyst Scan — 2026-08-15 (weekend, gate=STABILIZING)

Searches used: 6/6. Watermark 2026-08-13.

## Findings

1. **Optical complex decoupling on earnings, not sympathy.** 08-13: Coherent (COHR) fell on its own Q4
   print even as Ciena and Nokia rose on theirs — "Optics Stocks Divide" (247wallst, 08-13). This follows
   the 08-11/08-12 Lumentum-beat sympathy rally (COHR +9%, GLW +5%) the prior run attributed to pure
   read-through. Reading: the read-through call was right for one week, then the complex reverted to
   name-specific fundamentals. Book now carries CIEN+COHR+GLW+AVGO+MRVL = 12.77% of equity in this
   cluster — a single earnings-beat/miss pair no longer moves it as one block.
   Magnitude: COHR -12% same-session on its own numbers (247wallst 08-13); CIEN direction positive,
   exact % not disclosed in source. horizon=immediate, direction=ambiguous.

2. **NVDA-OpenAI financing guarantee cut roughly in half.** Reported 08-14: the datacentre financing
   guarantee under negotiation dropped from the $250bn figure (07-27) to below $120bn, explicitly to
   ease investor concern about NVDA's balance-sheet exposure; deal may sign this weekend (Gurufocus,
   citing Bloomberg/WSJ sourcing, 08-14). Magnitude: guarantee size cut >52% ($250bn -> <$120bn).
   horizon=structural, direction=tailwind (de-risks the circular-financing thesis concern flagged 07-28).

3. **NVDA earnings confirmed Aug 26, 2026** (Investing.com/StockTitan, 08-14 filings). 11 calendar days
   out. NVDA is 7.74% of equity with the book effectively at zero cash — largest single binary event on
   the calendar. horizon=immediate, direction=ambiguous. No magnitude beyond position size to report;
   this is a date-flag, not a repricing.

4. **Memory/DRAM contract pricing still strengthening, consistent with tracker.** TrendForce 08-13:
   "Samsung, SK hynix's HBM4 Push Puts HBM, General Memory Pricing in Spotlight for 2H Earnings."
   Samsung reportedly targeting a further ~20% DRAM ASP hike for Q3; SK Hynix has removed long-term
   contract price caps (diverging from Micron, which retains both floor and ceiling). TrendForce's
   Q3 QoQ DRAM guide of +13-18% sits inside the tracker's own 13-30% forecast band — no conflict.
   horizon=structural, direction=tailwind, affects MU/DRAM/SNDK/SKHY cluster (15.31% of equity).
   **Data quality flag:** one search result cited HBM4-to-NVIDIA cost at "$31-32/GB," which does not
   reconcile with consumer_view.json's corrected HBM4 stack-derived figure (~$10-14/GB, itself flagged
   suspect_band=true, correction C2). Different basis (likely fully-packaged module/logic cost vs raw
   stack) — not reported as a clean price point; tracker's corrected figure is authoritative per Theme-2
   rule. Tracker staleness = 10 days (last_run 2026-08-05), still under the 30-day degrade threshold.

5. **China DUV/CXMT — no fresh development since 08-13.** All CXMT/DUV/MATCH-Act coverage found dates
   to 07-28-08-02, already captured in prior runs (5 units 2026, ~20 in 2027 vs ASML's 131-tool/98.7%
   share base). Not re-reported as new; theme unchanged, thesis still "dented, not broken."

## Asia session (08-14 close, last session before this weekend gate)

KOSPI +2.42% to 6,977.94 — did not clear the 3% overnight-leadership threshold; named cause not
explicitly confirmed by sourced results this run (plausible memory-complex strength, same-day as the
TrendForce HBM4 pricing piece, but not stated as causal by any source found).
TAIEX -0.46% (-210.47pts to 45,811.01) — named cause confirmed: TSMC losing the 2,400 level
(BigGo Finance, 08-14).

## Theme list currency

Book composition has grown the optical/photonics footprint (CIEN, COHR, GLW, AVGO, MRVL = 12.77%
of equity) without a dedicated standing theme — proposing theme 7 below.

```json
{"catalysts":[
 {"headline":"Coherent falls on own Q4 earnings miss while Ciena/Nokia rise on theirs — optical complex decouples from pure sympathy trade","date":"2026-08-13","horizon":"immediate","direction":"ambiguous","affects":["COHR","CIEN"],"exposure_pct_equity":4.29,"exposure_pct_book":4.29,"magnitude":"COHR -12% same session (247wallst); CIEN higher, % not disclosed in source","source":"https://247wallst.com/investing/2026/08/13/optics-stocks-divide-coherent-and-cisco-drop-after-earnings-while-nokia-and-ciena-soar/","invalidates_proposal":null},
 {"headline":"NVDA-OpenAI datacentre financing guarantee cut from $250bn to below $120bn, deal near signing","date":"2026-08-14","horizon":"structural","direction":"tailwind","affects":["NVDA"],"exposure_pct_equity":7.74,"exposure_pct_book":7.74,"magnitude":"guarantee size reduced >52% ($250bn -> <$120bn)","source":"https://www.gurufocus.com/news/9036060/nvidia-nears-agreement-with-openai-on-data-center-financing","invalidates_proposal":null},
 {"headline":"NVDA Q2 FY27 earnings call confirmed for Aug 26, 2026","date":"2026-08-14","horizon":"immediate","direction":"ambiguous","affects":["NVDA"],"exposure_pct_equity":7.74,"exposure_pct_book":7.74,"magnitude":"11 calendar days out; book at ~0% cash to absorb a miss on a 7.74%-weight single name","source":"https://www.investing.com/news/assorted/nvidia-schedules-q2-fiscal-2027-earnings-call-for-august-26-432SI-4821803","invalidates_proposal":null},
 {"headline":"Samsung targets further ~20% DRAM Q3 hike; SK Hynix removes long-term contract price caps","date":"2026-08-13","horizon":"structural","direction":"tailwind","affects":["MU","DRAM","SKHY","SNDK"],"exposure_pct_equity":15.31,"exposure_pct_book":15.31,"magnitude":"TrendForce Q3 DRAM QoQ guide +13-18%, inside tracker's own 13-30% forecast band; consistent, no basis conflict","source":"https://www.trendforce.com/news/2026/08/13/news-samsung-sk-hynixs-hbm4-push-puts-hbm-general-memory-pricing-in-the-spotlight-for-2h-earnings/","invalidates_proposal":null}
],
 "asia_session":{"kospi_pct":2.42,"taiex_pct":-0.46,"nikkei_pct":null,"named_cause":"TAIEX: TSMC losing 2,400 level (BigGo Finance, 08-14). KOSPI: no source-confirmed named cause this run."},
 "theme_updates":{
   "propose_new_theme_7":{"name":"Optical/photonics AI networking","watch":"LITE/Cisco/Nokia earnings read-through vs name-specific results, transceiver capacity, AI interconnect demand","maps_to":["CIEN","COHR","GLW","AVGO","MRVL"],"reason":"cluster now 12.77% of equity across 5 names; 08-13 showed earnings-specific divergence (COHR miss vs CIEN beat) rather than uniform sympathy move — no existing theme captures this mechanism"},
   "theme_2_live_2026_08_13":"TrendForce: Samsung targeting further ~20% Q3 DRAM hike, SK Hynix removes long-term price caps (diverges from Micron). Consistent with tracker's 13-30% Q3 QoQ forecast. One search result's $31-32/GB HBM4-to-NVIDIA figure conflicts with tracker's corrected $10-14/GB stack-derived figure — excluded, different basis, unreconciled.",
   "theme_3_live_2026_08_14":"NVDA-OpenAI financing guarantee cut from $250bn to <$120bn, reducing circular-financing balance-sheet exposure vs the 07-27 figure; deal may sign this weekend.",
   "theme_6_live_2026_08_14":"KOSPI +2.42%, TAIEX -0.46% (TSMC-driven) on 08-14 close; neither cleared the 3% leadership threshold."
 },
 "searches_used":6,
 "data_quality":["HBM4-to-NVIDIA '$31-32/GB' figure from one search result does not reconcile with consumer_view.json's corrected HBM4 stack-derived figure (~$10-14/GB, suspect_band=true, correction C2) — different basis, not reported as a clean price point.","HBMTracker consumer_view.json staleness = 10 days as of this run (last_run 2026-08-05); under the 30-day degrade threshold but flagged for freshness."]}
```

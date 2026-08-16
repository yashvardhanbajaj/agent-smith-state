# Factor Catalyst Scan — 2026-08-16 (Sunday, deep run, market_session=CLOSED)

Searches used: 8/8 (2 WebFetch attempts on Tom's Hardware/TechPowerUp for CXMT date confirmation both blocked —
403/paywall; date approximated from cross-syndication timing, flagged below). Watermark 2026-08-15.
Asia also closed (Sunday) — no session data this run; Asia-first rule does not apply.

## Findings

1. **China DRAM capacity gap with Micron closes faster than the 07-28 DUV framing implied.** New research
   (syndicated across Tom's Hardware/TechPowerUp/OC3D/Yahoo/SemiAnalysis, dated on or just before 2026-08-16 —
   exact original publish date not independently pinned down after two blocked WebFetch attempts) puts CXMT's
   end-2026 DRAM capacity at ~350,000 wafer-starts/month vs Micron's ~375,000 (a 25k WSPM gap), up from a
   projected 40,000 WSPM in 2020. CXMT Q1 2026 DRAM share 8%, up from ~3% Q1 2025. Same sources project
   ~950,000 WSPM by 2030. **Counter-scale (load-bearing):** wafer starts are not bit-equivalent output — the
   same reporting explicitly flags CXMT runs on less-dense nodes with lower yields than Micron, so 350k CXMT
   wafers ≠ 350k Micron-equivalent wafers of DRAM bits. This is a capacity-convergence threat, not an
   output-parity one. horizon=structural, direction=threat. Separately, China's first domestically-built
   immersion DUV tools are reportedly beginning deliveries to CXMT/SMIC/Hua Hong this August (Wccftech,
   TrendForce 07-28 baseline unchanged: 5 units 2026, ~20 in 2027, vs ASML's 131 immersion tools/98.7% share;
   EUV untouched) — the delivery-timing detail is new, the magnitude is not.

2. **NVDA-OpenAI/SB Energy financing still unsigned as of Sunday.** WSJ (via Korea Times/Yahoo, 08-15) confirms
   the guarantee cut to a first-phase-only backstop (~$100bn credit support vs the $250bn July figure);
   CNBC (08-15) adds Nvidia is separately weighing a ~$3bn direct investment in SoftBank's SB Energy, the
   Ohio site's developer, as part of the same restructuring. Deal "could sign as early as this weekend"
   per WSJ — no signing confirmation found as of this run. horizon=structural, direction=tailwind (continues
   the de-risking trend flagged 08-14), but the binary (signed vs not) remains open into the 08-26 NVDA print.

3. **Memory $/GB cross-check: no conflict, no fresh catalyst.** siliconanalysts.com (Aug 2026 snapshot): HBM3
   ~$200/24GB stack, HBM3E ~$300/36GB, HBM4 ~$500/48GB — all reduce to the tracker's own corrected
   stack-derived bands (HBM3 $9.00/GB, HBM3E $9.00/GB, HBM4 defensible figure $10.42/GB per correction C2).
   Tracker staleness = 11 days (last_run 2026-08-05), still under the 30-day degrade threshold. Samsung
   reportedly hit ~80% HBM4 yield four months ahead of schedule — supply-side positive, but no clean date
   attached in this run's sources; not reported as a standalone catalyst (noise-vs-signal test failed).

4. **China chip-export policy: nothing new since watermark.** The Bloomberg piece on US review of offshore
   Nvidia-chip access via rental arrangements is dated 2026-08-07 — predates this run's 08-15 watermark and
   was already available to the 08-08-era runs. No fresh export-control development found this weekend.

5. **Hyperscaler capex: nothing dated this weekend.** All hits are general 2026 guidance already known
   (AMZN $200bn/GOOG $175-185bn/MSFT $110-120bn); no new guidance revision or datacentre-deferral story
   found for 08-15/08-16.

## Asia session
Markets closed (Sunday). kospi_pct/taiex_pct/nikkei_pct = null. Last live session was Friday 08-14
(already reported in the 08-15 run: KOSPI +2.42%, TAIEX -0.46% on TSMC weakness).

## Theme list currency
No material cluster-weight shift vs the 08-15 run (Memory 15.53%, AI Semis/Fabs 33.32%, unchanged). Theme 7
(optical/photonics, proposed 08-15) carries forward unmerged — no new information to add this run. Theme 1
and Theme 2 both get a `live_2026_08_16` update below.

```json
{"catalysts":[
 {"headline":"CXMT projected to close DRAM wafer-capacity gap with Micron to ~25k WSPM by end-2026 (350k vs 375k WSPM); Q1'26 DRAM share 8% vs ~3% Q1'25","date":"2026-08-16","horizon":"structural","direction":"threat","affects":["MU","DRAM","SNDK","SKHY"],"exposure_pct_equity":15.53,"exposure_pct_book":15.527,"magnitude":"25k WSPM gap vs Micron's 375k, but wafer starts are not bit-equivalent output -- CXMT node density/yield trail Micron per same sources; long-run trajectory ~950k WSPM by 2030","source":"https://www.tomshardware.com/pc-components/dram/cxmt-close-to-matching-microns-memory-capacity-in-2026-research-claims-would-put-china-on-track-to-become-worlds-second-largest-dram-producer","invalidates_proposal":null},
 {"headline":"China's first domestic immersion DUV tools begin deliveries to CXMT/SMIC/Hua Hong this August","date":"2026-08-16","horizon":"structural","direction":"threat","affects":["ASML","LRCX","AMAT","TER"],"exposure_pct_equity":10.55,"exposure_pct_book":10.549,"magnitude":"5 units 2026, ~20 in 2027 vs ASML's 131 immersion tools/98.7% share (2025 baseline, unchanged since 07-28); EUV untouched","source":"https://x.com/wccftech/status/2081799374838059269","invalidates_proposal":null},
 {"headline":"NVDA-OpenAI/SB Energy Ohio financing: guarantee narrowed to first-phase-only (~$100bn); Nvidia also weighing ~$3bn direct stake in SB Energy; not yet signed as of Sunday","date":"2026-08-15","horizon":"immediate","direction":"tailwind","affects":["NVDA"],"exposure_pct_equity":7.72,"exposure_pct_book":7.72,"magnitude":"guarantee narrowed from $250bn (07-27) to ~$100bn first-phase backstop; signing still pending 2+ days after WSJ's 'this weekend' framing","source":"https://www.koreatimes.co.kr/amp/world/20260815/nvidia-scales-back-funding-guarantee-for-ohio-openai-data-center-wsj-reports","invalidates_proposal":null}
],
 "asia_session":{"kospi_pct":null,"taiex_pct":null,"nikkei_pct":null,"named_cause":"markets closed, Sunday"},
 "theme_updates":{
   "theme_1_live_2026_08_16":"First domestic immersion DUV deliveries to CXMT/SMIC/Hua Hong reportedly begin this August -- timing now concrete, magnitude unchanged (5 units 2026 vs ASML 131 tools/98.7% share).",
   "theme_2_live_2026_08_16":"CXMT projected to end 2026 within 25k WSPM of Micron's DRAM capacity (350k vs 375k), share 8% vs 3% YoY -- wafer-start convergence, not bit-equivalent-output convergence (node/yield gap remains per same sources). $/GB cross-check against consumer_view.json shows no conflict this run.",
   "theme_7_carryforward":"Optical/photonics theme proposed 08-15 (CIEN/COHR/GLW/AVGO/MRVL, 12.77% of equity) -- no new information this run; still pending orchestrator merge."
 },
 "searches_used":8,
 "data_quality":["CXMT-vs-Micron capacity story's exact original publish date not confirmed -- two WebFetch attempts (Tom's Hardware, TechPowerUp) were blocked (403/paywall-stripped content); dated 2026-08-16 as a syndication-timing approximation, flag if precision matters downstream.","HBMTracker consumer_view.json staleness = 11 days as of this run (last_run 2026-08-05); under the 30-day degrade threshold but freshness flagged again.","China export-control review (Bloomberg, dated 08-07) predates this run's 08-15 watermark -- not reported as new, noted only to confirm it was checked."]}
```

# Signal Scan — 2026-08-15 (DEEP) — prices are Fri 08-14 close, market closed

## STRONG UPTREND (pos≥0.80)
- AMD — pos 0.839, +6.50% Fri (0.78x its 8.34% ATR — big headline, not extreme for AMD) — 2.214% wt — target $613.33, +16.1% upside. Also TARGET GAP (unchanged repeat).
- NBIS — pos 0.907, +8.88% Fri (0.69x its 12.82% ATR — proportionate, not a blowoff day) — 3.506% wt, **1.79x ATR risk cap** — target unavailable this run (data gap). See REVERSAL-TRIM WATCH below — this is the more important read on NBIS today.
- GEV — pos 0.801 (barely crossed), +1.32% Fri — 4.821% wt, **1.31x ATR risk cap** — target $1238.25, +14.1% (TARGET GAP just resolved, was 15%+ last run).
- TER — pos 0.819, +2.01% Fri — 2.825% wt, **1.03x ATR risk cap** — target $449.80, only +6.9% upside (no gap).
- ASML — pos 0.879 (near the 0.80 floor, not fresh), -0.21% Fri — 4.234% wt — target $2170.81, +15.1% (TARGET GAP right at the edge, unchanged repeat).
- FLTW — pos 0.874, -0.67% Fri — 2.378% wt — unchanged repeat, passive Taiwan-index exposure, no single-name read.
- CHANGED: TSM's prior STRONG UPTREND has faded — pos now 0.794 (was ≥0.80), day -0.96%. TARGET GAP still holds (+22.1%, target $547.09) — 5.919% wt, **1.06x ATR risk cap**.

## STRONG DOWNTREND (pos≤0.22)
- ORCL — pos 0.156, -3.65% Fri (-0.67x its 5.47% ATR, not a crash day — the breakdown is cumulative, not today's move) — 2.148% wt — target $247.17, tool-reported +39.1% upside (internally inconsistent with mean/current math, flagged in data_quality). Third+ consecutive run flagging this; open_flag "thesis BROKEN, exit unactioned" still stands. Curiously ORCL is simultaneously PEER LEADER (see below) — today's price breakdown hasn't yet erased the earlier-month rebound in the trailing-1m relative number; that will likely flip next refresh if weakness persists.

## NEW TAILWINDS (2+ distinct events, deduped per G58)
- MU — 2 distinct positive events since 08-13: (1) 08-14 upgrade to Buy + AI-demand revenue read, (2) 08-13 launch of a $250M fund to back AI startups. Both are demand/capital-allocation stories, not earnings. 5.442% wt, **2.04x ATR risk cap** (largest cap breach after SKHY). Target $1501.98, +35.3% upside (TARGET GAP, unchanged).

No HEADWINDS bucket fired — no ticker had 2+ distinct negative events in the 08-13→08-14 window (AVGO and NBIS each had exactly 1 negative-leaning item; see notes below).

## PEER-RELATIVE (peer_map corrected this run — see JSON tail; prior cache benchmarked everything to SMH regardless of assigned peer)
- MSFT — 1m +24.7% vs its own peer XLK +4.64% (fresh) = **+2.80σ**, the most extreme read in the book. RSI14 78.8 is a 08-12 cache value (3 days stale) — today's price is actually 10.5% below the 52wk high (pos 0.715) and only -0.30% Fri, so the extension isn't accelerating, but the peer-relative gap is enormous and 3.405% wt makes it worth flagging on its own even without a fresh trigger.
- BX — 1m +16.5% vs XLF +2.83% = **+1.72σ** — 1.711% wt. Friday -3.61% (Blackstone-specific: Project Eclipse review + insider sale, both dated 08-12, just outside this window) — leading its sector over the month but a rough single day.
- CEG — 1m +7.71% vs XLU -2.01% = **+1.29σ** — 1.915% wt. Still REVERSAL-BUY-WATCH (pos 0.293, near lows) — unchanged, no fresh catalyst since 08-06.
- NOW — 1m +20.9% vs XLK +4.64% = **+1.25σ** — 2.041% wt, unchanged repeat.
- ORCL — 1m +17.5% vs XLK +4.64% = **+1.02σ** — see STRONG DOWNTREND note above for the contradiction.
- AVGO — 1m +9.0% vs SMH -0.50% = **+1.00σ** (right at the line) — 3.83% wt. Friday -5.94% (-1.44x its 4.14% ATR, its biggest scaled move in the book today) on a VMware security-threat headline + AI-financing-risk concern (08-14), against still-strong Q2 AI revenue ($10.8B, +143% YoY) and a new $35B AI-infra financing initiative (08-13) — 1 negative + 1 positive distinct event, net mixed, no bucket fires either way.
- STM — 1m -14.75% vs SMH -0.50% = **-1.49σ, PEER LAGGARD** — 2.471% wt. Guide-below-consensus overhang from 07-23 still the live story; no new news this window.
- CHANGED (methodology fix, not a real move): AMZN's prior PEER LEADER tag no longer holds once benchmarked correctly to XLK — rel_sigma now +0.62, below the 1.0 line. Still TARGET GAP (+19.2%, unchanged).

## Optical/NBIS read-through check (user focus item)
Wednesday's NBIS +34.1%/CIEN +11.5% surge did NOT extend into Friday as a unified complex move — it's mixed: CIEN gave back -3.17% Friday (-0.39x its own ATR, an unremarkable pullback, not a reversal signal), COHR closed flat -0.43% after a mixed Q4 reaction (08-12/13: revenue beat + guide beat, but operating-cash-flow decline drove the sell-off — a *price reaction* to cash generation, not a results or guidance miss), GLW popped +4.70% Friday (0.45x its ATR, still within normal range) with no fresh news in-window, MRVL was flat (-0.07%), and AVGO — the name most exposed to the same complex — fell hard on company-specific issues (above). Verdict: the sector-wide read-through has faded/decoupled; what's left is idiosyncratic per name.

## TARGET GAP ≥15% (unchanged repeats, bucket 61.1% interim 7d hit rate, n=18)
NVDA +25.7% ($302.83, 7.739% wt, 1.20x cap), CLS +29.2% ($473.24), BABA +34.7% ($189.60), STM +24.1% ($71.52), COHR +17.4% ($394.62, **new** this run), AMAT +19.9% ($633.34, **new**), BE +15.9% ($273.51, **new**), IREN +46.1% ($81.73, **new**, largest gap in book), CIEN +24.2%/+31.95% tool-vs-computed discrepancy noted ($565.71), CEG +19.3% ($349.96).
RESOLVED this run (upside fell below 15%): MRVL (13.6%), VRT (13.1%), GEV (14.1% — now STRONG UPTREND instead), QCOM (14.9%, right at the margin — also its OVERSOLD BOUNCE resolved, pos 0.318 vs ≤0.30 needed).

## Data quality
- SKHY/DRAM: 52wk_low returned 0 (bad data) — guardrail applied, pos set to 0.5, cannot confirm prior BREAKOUT tag this run. SKHY analyst_forecast also empty.
- SNDK analyst_forecast returned empty this run (was previously covered by 26 analysts per thesis notes) — likely transient, no target cited; +7.39% Fri is only 0.47x its 15.6% ATR, unremarkable for this name despite the headline size. 1.779% wt, **1.11x ATR risk cap**.
- ORCL analyst_forecast internal math inconsistent (mean $247.17 vs current $150.52 implies +64.2%, tool field says +39.1%) — cited tool value, flagged not corrected.
- insiderTrades/form13F (FMP) are plan-gated on this account — could not pull Form-4 filings for the top-10; no insider-activity read this run (news-derived scan also found no fresh insider mentions for top-10 in-window).
- Self-calibration: SD(rel_sigma) = 0.77 across n=34 held names with ATR — slightly below the ~1.0 target band, mild under-firing bias (denominator running a touch wide). Not action-worthy, monitor.
- Peer ETF returns are a fresh 1mo pull ending 08-14; the cached rel_strength_1m values (abs_pct) are as-of 08-12 — a 2-day window mismatch, immaterial at this horizon.
- No EARNINGS PROXIMITY: nothing >5% weight reports within 7 trading days (nearest are NVDA/MRVL 08-26, AVGO 09-02).

## Still pending (pre-watermark, unresolved)
- ASML: China DUV is a multi-year structural risk, not resolved by the improving tone (thesis note stands).
- MU/SNDK: CXMT reconciliation and memory-cluster concentration (23.5%+) still open per prior flags.
- BX: Project Eclipse ($3B deal) under review + CLO insider sale (08-12) — outside this window, unresolved.
- COHR: cash-generation concern from 08-12/13 print still digesting, no follow-up news yet.

## Unchanged repeats (no material change vs last signal_history)
CIEN (TARGET GAP), CLS (TARGET GAP), BABA (TARGET GAP), NVDA (TARGET GAP), CEG (TARGET GAP + REVERSAL-BUY-WATCH), NOW (PEER LEADER), MSFT (PEER LEADER, intensified), BX (PEER LEADER), STM (TARGET GAP + PEER LAGGARD), ASML (STRONG UPTREND + TARGET GAP, both at the edge).

No INSIDER ACTIVITY, OVERSOLD BOUNCE, OVERBOUGHT PULLBACK, MOMENTUM+VOLUME, BREAKOUT, BREAKDOWN, POLICY IMPACT, or CAPITAL ROTATION signals fired this run — every large Friday % move checked out proportionate to (or below) its own ATR once scaled.

```json
{"signal_history":{"changed":{
  "MU":["TARGET GAP","NEW TAILWINDS"],
  "AMD":["TARGET GAP","STRONG UPTREND"],
  "GEV":["STRONG UPTREND"],
  "TER":["STRONG UPTREND"],
  "TSM":["TARGET GAP"],
  "MRVL":[],
  "VRT":[],
  "QCOM":[],
  "AMZN":["TARGET GAP"],
  "ORCL":["STRONG DOWNTREND","TARGET GAP","PEER LEADER"],
  "COHR":["TARGET GAP"],
  "AMAT":["TARGET GAP"],
  "BE":["TARGET GAP"],
  "IREN":["TARGET GAP"],
  "NBIS":["STRONG UPTREND","REVERSAL - TRIM WATCH"],
  "AVGO":["TARGET GAP","PEER LEADER"],
  "CEG":["TARGET GAP","REVERSAL - BUY WATCH","PEER LEADER"]
},"unchanged_count":9},
 "news_watermark":"2026-08-15","resolved_flags":[],"new_flags":[],
 "journal_new":[
   {"date":"2026-08-15","ticker":"COHR","bucket":"TARGET GAP","price_at_flag":325.83,"analyst_target":394.62,"day_atr_mult":-0.040,"rel_sigma":0.440,"normalized":true},
   {"date":"2026-08-15","ticker":"AMAT","bucket":"TARGET GAP","price_at_flag":507.18,"analyst_target":633.34,"day_atr_mult":-0.575,"rel_sigma":-0.140,"normalized":true},
   {"date":"2026-08-15","ticker":"BE","bucket":"TARGET GAP","price_at_flag":229.94,"analyst_target":273.51,"day_atr_mult":-0.188,"rel_sigma":-0.059,"normalized":true},
   {"date":"2026-08-15","ticker":"IREN","bucket":"TARGET GAP","price_at_flag":44.06,"analyst_target":81.73,"day_atr_mult":-0.141,"rel_sigma":0.410,"normalized":true},
   {"date":"2026-08-15","ticker":"NBIS","bucket":"REVERSAL - TRIM WATCH","price_at_flag":277.68,"analyst_target":null,"day_atr_mult":0.693,"rel_sigma":0.076,"normalized":true}
 ],
 "peer_map_updates":{
   "IREN":{"peer_etf":"XLK","label":"hyperscaler/compute (GPU-cloud pivot, new position)"},
   "STM":{"peer_etf":"SMH","label":"analog/industrial semis (no dedicated analog ETF, SMH closest liquid proxy)"},
   "TXN":{"peer_etf":"SMH","label":"analog/industrial semis (no dedicated analog ETF, SMH closest liquid proxy)"},
   "GLW":{"peer_etf":"SMH","label":"optical-interconnect (corrected from XLK — GLW's own sector_map cluster is AI Networking/Optics, matching CIEN/COHR who are already SMH-mapped)"}
 },
 "vol_normalization":{
   "ASML":{"atr20_pct":5.11,"day_atr_mult":-0.041,"rel_sigma":0.110,"threshold_pct":7.665},
   "GEV":{"atr20_pct":6.83,"day_atr_mult":0.193,"rel_sigma":-0.134,"threshold_pct":10.245},
   "TER":{"atr20_pct":9.12,"day_atr_mult":0.220,"rel_sigma":0.419,"threshold_pct":12.0},
   "AMD":{"atr20_pct":8.34,"day_atr_mult":0.779,"rel_sigma":-0.524,"threshold_pct":12.0},
   "NBIS":{"atr20_pct":12.82,"day_atr_mult":0.693,"rel_sigma":0.076,"threshold_pct":12.0},
   "FLTW":{"atr20_pct":1.89,"day_atr_mult":-0.354,"rel_sigma":null,"threshold_pct":2.835},
   "ORCL":{"atr20_pct":5.47,"day_atr_mult":-0.667,"rel_sigma":1.020,"threshold_pct":8.205},
   "MSFT":{"atr20_pct":3.12,"day_atr_mult":-0.096,"rel_sigma":2.800,"threshold_pct":7.176},
   "BX":{"atr20_pct":3.47,"day_atr_mult":-1.040,"rel_sigma":1.718,"threshold_pct":7.981},
   "CEG":{"atr20_pct":3.27,"day_atr_mult":0.425,"rel_sigma":1.292,"threshold_pct":7.521},
   "NOW":{"atr20_pct":5.65,"day_atr_mult":-0.451,"rel_sigma":1.252,"threshold_pct":12.995},
   "AVGO":{"atr20_pct":4.14,"day_atr_mult":-1.435,"rel_sigma":1.001,"threshold_pct":9.522},
   "STM":{"atr20_pct":4.17,"day_atr_mult":0.165,"rel_sigma":-1.486,"threshold_pct":9.591}
 },
 "data_quality":[
   "SKHY/DRAM 52wk_low=0 (bad data) -- pos guardrailed to 0.5, prior BREAKOUT unconfirmed this run",
   "SNDK and SKHY analyst_forecast returned empty this run",
   "ORCL tool-reported upside_per (39.1%) inconsistent with its own mean/current fields (implies 64.2%)",
   "insiderTrades/form13F plan-gated on this FMP account -- no Form-4 read for top-10 this run",
   "SD(rel_sigma)=0.77, n=34 -- mildly under-firing vs 1.0 target band, monitor not retune",
   "budget: 4 get_us_stocks_details + 2 yfinance history batches + 6 blocked insider calls = within soft cap"
 ]}
```

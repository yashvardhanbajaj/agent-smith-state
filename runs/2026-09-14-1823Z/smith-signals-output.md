# Smith Signals — 2026-09-14 (QUICK, run 1823Z) — GATE: ESCALATING

Book -5.59% weighted intraday (14:27 ET); live closes fetched post-16:00 ET show the
selloff deepened further into the close for Optics/Semis specifically (see Data Quality).

## STRONG DOWNTREND / MOMENTUM+VOLUME — confirmed vs unconfirmed
- **GLW** -12.64% close (2.2x its 5.6% ATR) — CONFIRMED: $2B dilutive equity offering
  announced today, 14 Sep 2026, negative [INDmoney news]. Largest drop in book. 1.31% wt.
  Target $194.31/10 analysts, 33.7% upside. pos 0.356 — still +168% YoY even after today,
  a pullback not a washout.
- **GEV** -8.63% close (day_atr_mult -1.79) — CONFIRMED: GLJ Research initiated Sell
  rating today (14 Sep) same day GEV raised FY26 cash-flow/revenue guidance — negative
  rating action against positive fundamentals. 6.59% wt (material). Also PEER LAGGARD,
  rel_sigma -1.06 vs XLU. Target $1236.43/21, 41.1% upside. journal_new (new today).
- **ASML** -6.16%, **STM** -6.78%, **APH** -5.78%, **TER** -12.13% — MOMENTUM+VOLUME?
  leg fired, NOT promoted: no negative catalyst in today's news for any of the four
  (ASML actually raised FY26 revenue guidance today, 14 Sep — good news, red tape).
  Moves track the broad SMH -4.07% semicap unwind, not idiosyncratic events.

## OVERSOLD BOUNCE — confirmed with caveat
- **AVGO** pos 0.275 — only book name at a genuine 52wk-range low. Upside 34.9% to
  $531.85/30 analysts. CAVEAT: -4.39% close is a real guidance-driven story, not a
  misread headline — Q3 beat (AI rev +221% YoY) but Q4 revenue guide $34.8B missed
  consensus, 14 Sep 2026 [INDmoney]. 2.08% wt, small. Distinguish: results beat, forward
  guide light — a real negative leg, so treat as lower-conviction bounce than the bucket
  alone implies.

## PEER LEADER — the counter-narrative (book is not capitulating broadly)
- **NOW** +7.41% today vs sector selloff — PEER LEADER, STRONG UPTREND, rel_sigma 1.38
  vs XLK. Catalyst: multiple analyst price-target upgrades on AI product growth, 14 Sep
  2026 [INDmoney]. 1.71% wt.
- **MSFT** +2.38% — PEER LEADER, rel_sigma 1.00 vs XLK. Strong fiscal results +
  responsible-AI framing offsetting AI-capex jitters, 14 Sep 2026. 1.52% wt.
- **QCOM** -0.4% vs SMH -4.07% — PEER LEADER, rel_sigma 2.07 (largest in book). No
  single-day catalyst; AWS AI-datacenter partnership (8-12 Sep) still supporting. 2.72% wt.
- **AMD** -3.75%, better than SMH — PEER LEADER, STRONG UPTREND, rel_sigma 1.14. 2.99% wt.
- **TSM** -2.5%, notably resilient vs KLAC/AMAT/ASML/TER (-6% to -12%) — rel_sigma 0.94,
  just short of leader threshold. Record Aug revenue +53.3% YoY (11 Sep) still supports.
  5.07% wt.

## PEER LAGGARD
- AVGO, CIEN (rel_sigma -1.13; pos 0.384, TARGET GAP 54.7% upside — Sept earnings beat +
  guide raise but analyst target cuts since, mixed not negative), AMAT (rel_sigma -1.22;
  today's headline explicitly attributes the decline to "broader semiconductor weakness,"
  14 Sep — sector, not company), KLAC (rel_sigma -1.09, no fresh news, stale positive
  from Jul 31).

## TARGET GAP — broad, not differentiating today
Every semis/optics/power name shows 20-60% upside on trailing targets. Largest: COHR
34.6%, MU 38.6% (Strong Buy 97% of 30 analysts), AVGO 34.9%, GEV 29.3%, ALAB 32.9%, TER
25.3%, VRT 29.3%. Unchanged repeats: MRVL, NBIS, GOOG, AMZN, WDC, MSFT, TSM — same
bucket, no new catalyst since last check.

## Cluster read — answering the core question
AI Networking/Optics (COHR/LITE/CIEN/GLW/CLS/APH) and Semis/Fabs (ASML/KLAC/AMAT/TER/STM)
are down 6-13% today, but pos readings (0.35-0.75) show pullbacks from 2026's huge
rallies, not washouts at 52-week lows — only AVGO sits at pos≤0.3, and even that carries
a real guidance-miss catalyst, not a panic markdown. Meanwhile NOW/MSFT/QCOM/AMD/TSM
(software, mega-cap cloud, resilient semis) are flat-to-up, showing a concentrated
de-rating of the highest-beta hardware/optics/semicap-equipment sub-segment, not
portfolio-wide capitulation. Read: continuing downtrend / valuation reset in the most
extended names (GLW's dilutive raise, TER's stale downgrade overhang), with AVGO the one
plausible tactical bounce candidate — sized small (2.08%), any add should stay small
given the guidance overhang.

## Still pending
- AMD semiconductor tariff-policy risk (30 Aug, unresolved).
- Broadcom hedge-fund exits (Druckenmiller/Loeb/D.E. Shaw, 22-23 Aug) — stale, not
  today's driver.
- TER Baird downgrade to Neutral, "no catalysts until 2028" (21 Aug) — still the
  operative overhang, not refreshed today.

## Data quality
- Live prices fetched post-16:00 ET close show a materially deeper selloff (GLW -12.6%,
  TER -12.1%, ALAB -10.2%, COHR -11.0%) than the 18:23Z compute_buckets snapshot implied
  — qualitative reads above use the fresher close data; bucket flags themselves are taken
  as-computed by compute_buckets.json.
- ASML analyst consensus is thin (6 analysts) — treat its $2157.62/$2157.62 target with
  more caution than KLAC/AMAT's 20+ analyst base.
- No FMP insiderTrades/form13F pulled — quick mode, deep-mode-only per spec.
- Earnings-proximity: no confirmed report dates surfaced for >5%-weight holdings within
  7 days in fetched news; not checked against a calendar this run.
- peer_map: all 27 current holdings already mapped in shared/peer_map — no updates.

```json
{"signal_history":{"changed":{"GLW":["MOMENTUM+VOLUME","STRONG DOWNTREND","TARGET GAP"],"GEV":["MOMENTUM+VOLUME","PEER LAGGARD","STRONG DOWNTREND","TARGET GAP"],"ASML":["MOMENTUM+VOLUME?","STRONG DOWNTREND","TARGET GAP"],"STM":["MOMENTUM+VOLUME?","STRONG DOWNTREND","TARGET GAP"],"TER":["MOMENTUM+VOLUME?","STRONG DOWNTREND","TARGET GAP"],"APH":["MOMENTUM+VOLUME?","STRONG DOWNTREND","TARGET GAP"],"AVGO":["OVERSOLD BOUNCE","PEER LAGGARD","TARGET GAP"],"CIEN":["PEER LAGGARD","TARGET GAP"],"AMAT":["PEER LAGGARD","TARGET GAP"],"KLAC":["PEER LAGGARD","TARGET GAP"],"NOW":["MOMENTUM+VOLUME","PEER LEADER","STRONG UPTREND"],"MSFT":["PEER LEADER"],"QCOM":["PEER LEADER"],"AMD":["PEER LEADER","STRONG UPTREND","TARGET GAP"],"TSM":["TARGET GAP"]},"unchanged_count":12},
 "news_watermark":"2026-09-14","resolved_flags":[],"new_flags":[],
 "journal_new":[{"date":"2026-09-14","ticker":"GEV","bucket":"MOMENTUM+VOLUME","price_at_flag":874.68,"analyst_target":1236.43,"day_atr_mult":-1.79,"rel_sigma":-1.06,"normalized":true}],
 "peer_map_updates":{},
 "analyst_targets_updates":{
   "VRT":{"mean_target_usd":338.15,"n_analysts":17,"as_of":"2026-09-14"},
   "ASML":{"mean_target_usd":2157.62,"n_analysts":6,"as_of":"2026-09-14"},
   "GEV":{"mean_target_usd":1236.43,"n_analysts":21,"as_of":"2026-09-14"},
   "KLAC":{"mean_target_usd":233.77,"n_analysts":21,"as_of":"2026-09-14"},
   "TSM":{"mean_target_usd":551.26,"n_analysts":8,"as_of":"2026-09-14"},
   "TER":{"mean_target_usd":446.47,"n_analysts":12,"as_of":"2026-09-14"},
   "COHR":{"mean_target_usd":415.36,"n_analysts":17,"as_of":"2026-09-14"},
   "AMAT":{"mean_target_usd":640.89,"n_analysts":28,"as_of":"2026-09-14"},
   "CLS":{"mean_target_usd":477.22,"n_analysts":13,"as_of":"2026-09-14"},
   "LITE":{"mean_target_usd":1149.38,"n_analysts":17,"as_of":"2026-09-14"},
   "APH":{"mean_target_usd":99.26,"n_analysts":11,"as_of":"2026-09-14"},
   "AMD":{"mean_target_usd":615.07,"n_analysts":35,"as_of":"2026-09-14"},
   "MU":{"mean_target_usd":1513.11,"n_analysts":30,"as_of":"2026-09-14"},
   "QCOM":{"mean_target_usd":193.90,"n_analysts":26,"as_of":"2026-09-14"},
   "STM":{"mean_target_usd":75.04,"n_analysts":9,"as_of":"2026-09-14"},
   "AVGO":{"mean_target_usd":531.85,"n_analysts":30,"as_of":"2026-09-14"},
   "NOW":{"mean_target_usd":142.97,"n_analysts":30,"as_of":"2026-09-14"},
   "MSFT":{"mean_target_usd":572.92,"n_analysts":34,"as_of":"2026-09-14"},
   "GLW":{"mean_target_usd":194.31,"n_analysts":10,"as_of":"2026-09-14"},
   "CIEN":{"mean_target_usd":504.13,"n_analysts":16,"as_of":"2026-09-14"},
   "ALAB":{"mean_target_usd":389.95,"n_analysts":17,"as_of":"2026-09-14"}
 },
 "vol_normalization":{
   "ASML":{"atr20_pct":3.27,"day_atr_mult":-1.88,"rel_sigma":-0.84,"threshold_pct":4.91},
   "GEV":{"atr20_pct":4.7,"day_atr_mult":-1.79,"rel_sigma":-1.06,"threshold_pct":7.05},
   "KLAC":{"atr20_pct":4.62,"day_atr_mult":-1.32,"rel_sigma":-1.09,"threshold_pct":6.93},
   "TER":{"atr20_pct":6.47,"day_atr_mult":-1.85,"rel_sigma":-0.75,"threshold_pct":9.71},
   "AMAT":{"atr20_pct":4.46,"day_atr_mult":-1.41,"rel_sigma":-1.22,"threshold_pct":6.69},
   "STM":{"atr20_pct":3.65,"day_atr_mult":-1.86,"rel_sigma":-0.42,"threshold_pct":5.47},
   "AVGO":{"atr20_pct":3.25,"day_atr_mult":-1.32,"rel_sigma":-1.29,"threshold_pct":4.88},
   "GLW":{"atr20_pct":5.61,"day_atr_mult":-2.21,"rel_sigma":-0.05,"threshold_pct":8.42},
   "CIEN":{"atr20_pct":7.31,"day_atr_mult":-0.93,"rel_sigma":-1.13,"threshold_pct":10.96},
   "AMD":{"atr20_pct":4.03,"day_atr_mult":-0.87,"rel_sigma":1.14,"threshold_pct":6.04},
   "QCOM":{"atr20_pct":3.63,"day_atr_mult":-0.15,"rel_sigma":2.07,"threshold_pct":5.45},
   "NOW":{"atr20_pct":4.63,"day_atr_mult":1.61,"rel_sigma":1.38,"threshold_pct":6.95},
   "MSFT":{"atr20_pct":1.99,"day_atr_mult":1.22,"rel_sigma":1.00,"threshold_pct":2.98},
   "APH":{"atr20_pct":3.63,"day_atr_mult":-1.6,"rel_sigma":0.34,"threshold_pct":5.45}
 },
 "data_quality":["Live post-close prices show deeper selloff than 18:23Z compute snapshot for GLW/TER/ALAB/COHR — qualitative reads use fresher data, bucket flags taken as-computed","ASML analyst consensus thin at n=6, treat target with extra caution vs KLAC/AMAT n=21-28","No FMP insiderTrades/form13F pulled (quick mode, deep-mode-only)","Earnings-proximity not checked against a calendar this run for >5% holdings","peer_map fully covers current 27 holdings, no updates needed"]}
```

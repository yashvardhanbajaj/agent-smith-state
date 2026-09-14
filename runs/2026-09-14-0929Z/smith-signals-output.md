# Smith Signals — Deep Run 2026-09-14 (pre-open, GATE ESCALATING)

## PRE-MARKET CONTEXT (read this before any bucket line below)
compute_buckets.json's pos/day_atr_mult/rel_sigma are all struck off the 2026-09-11 close — the
last completed session. Since then, EVERY held name shows an extended-hours drop of -3% to -8%
(ext_hr_day_change_percentage), consistent with the semis-specific pre-market selloff / optics
cluster -6.25% the orchestrator flagged. This is a **broad, sector-wide gate move, not idiosyncratic
company news** — across all 28 names the news flow itself skews positive-to-neutral this week
(AI-capex beats, partnerships, capacity expansions). Treat every STRONG DOWNTREND / MOMENTUM+VOLUME?
line below as "yesterday's session, about to be compounded by today's gate," not as a verdict on
the businesses. Worst pre-market gaps: GLW -8.05%, CLS -6.37%, ASML -5.29%, MRVL -7.67%, QCOM -4.82%,
LITE -6.62%, AMAT -5.74%, STM -5.84%, SMCI -5.84%. NVDA is absent from current holdings (was in
signal_history) — book composition changed since last run; flagged in data_quality.

## MOMENTUM+VOLUME? — promoted (broad-gate catalyst, not idiosyncratic)
- ASML — 6.36% wt — STRONG DOWNTREND leg fired (-1.85x its 4.23% ATR on 09-11 session), but news
  09-08→09-10 is unambiguously positive (EUV capacity expansion, TSMC/Samsung/Intel High-NA
  commitments — 3 distinct events). Catalyst = sector-wide selloff, not company deterioration.
  Target $2165.70, +34.5% upside. Grade n/a (no journal history yet).
- STM — 2.3% wt — STRONG DOWNTREND (-1.88x its 4.72% ATR). No negative company news found; last
  event was a completed buyback (positive, 08-31). TARGET GAP grade F (n=1, 0% hit rate) — this
  bucket has failed on STM before, treat the +54.8% upside/$75.04 target skeptically.
- GLW — 1.46% wt — STRONG DOWNTREND (-1.71x its 6.81% ATR), but MOMENTUM+VOLUME grade here is A
  (n=1, 100%, low-confidence) and news is a genuine positive catalyst (Verizon multi-billion fiber
  deal, 09-08). Target $191.40, +24.7% upside.

## OVERSOLD BOUNCE? — promoted
- AVGO — 2.22% wt — pos 0.295 (≤0.3), upside 52.2% (>15% threshold) satisfies the pos leg. News
  mixed-to-negative in the window: Q4 guide came in light (09-02, "Reports Strong Q3 but
  Disappoints on Guidance"), Druckenmiller/Loeb fully exited (08-23), D.E. Shaw cut 58% (08-22) —
  set against strong AI-revenue beats (09-09/09-11, $230B AI-revenue-by-2028 guide). This is a
  SanDisk-shaped setup: the guide, not the print, is what's soft — cite it as guidance-related, not
  a demand miss. Target $533.41, +32.1% upside.

## PEER LEADER / LAGGARD
- QCOM — 2.74% wt — PEER LEADER, rel_sigma +1.84 (was PEER LAGGARD last run — sign flip). But
  in-window news skews negative (revenue-impact-from-new-collaboration 09-12, valuation concerns
  09-10) — 2 distinct negative events → also fires NEW HEADWINDS. Price strength and news tone are
  diverging; worth a closer look before treating the peer-leader read as bullish confirmation.
- AMAT — 4.08% wt — PEER LAGGARD, rel_sigma -1.45 (widest laggard read in book). TARGET GAP grade F
  (n=1, 0%). Target $640.89, +49.3% upside — treat cautiously given the grade.
- CIEN — 0.01% wt (dust position, same as TER's residue — negligible P&L impact) — PEER LAGGARD
  rel_sigma -1.05. TARGET GAP grade F.
- KLAC — 5.38% wt — PEER LAGGARD rel_sigma -1.08. Target $233.77, +37.5% upside.
- AMD — 3.08% wt — PEER LEADER rel_sigma +1.09 (was STRONG UPTREND last run — pos slipped to 0.775,
  below the 0.80 breakout line). Target $613.84, +26.0% upside.
- BE — 1.61% wt — PEER LEADER rel_sigma +1.40 vs XLU (+19.58pp) — driven mostly by the S&P 500
  inclusion story (09-04/09-09, same underlying event, dedup'd to one). Upside only 8.3% —
  target basically caught up to price; treat as fully priced, not a fresh setup.

## NEW TAILWINDS (≥2 distinct positive events, 09-08→09-14 window)
- MRVL — 6.22% wt — Google $120B custom-silicon deal (09-10), new CFO + raised outlook (09-10),
  AI infra summit coverage (09-09), Piper Sandler bullish note (09-11). TARGET GAP grade A (n=1,
  100%, low-confidence). Target $285, +30.5% upside.
- TSM — 5.3% wt — record August revenue +53% YoY (09-11), ASML High-NA EUV partnership (09-09/10),
  insider ESPP purchases (09-09). Target $552.38, +31.9% upside.
- MSFT — 1.56% wt — Azure/AI capacity tripling to 38GW (09-10), Q4 revenue beat (09-11), quantum/AI
  growth note (09-12). Target $572.92, +16.5% upside (smallest gap in book — mature setup).
- NOW — 1.72% wt — revenue-target raise + Needham PT hike (09-11), Goldman conference AI showcase
  (09-10), treasury-ops enhancement note (09-09). No other bucket fired (day_atr_mult only 0.6x).
- NBIS — 1.32% wt — Palantir sovereign-AI-infra partnership (09-08), Lone Pine investment (09-04) —
  net positive despite PEER LAGGARD-adjacent read (rel_sigma -0.77, didn't cross -1.0 threshold).

## Still pending (persisting from before watermark, one clause each)
- ASML: Chinese DUV competitor threat (08-24) — no resolution seen yet.
- AVGO: EU VMware-licensing scrutiny (09-11) — unresolved, watch for follow-through.
- NBIS: dilution overhang from the $4.5-5.75B convertible-note raises (08-19/08-27) — still the
  overhang narrative even as partnership news improves.

## Unchanged repeats
None — day-move-based buckets (STRONG DOWNTREND/UPTREND, PEER LEADER/LAGGARD, MOMENTUM+VOLUME?)
shifted for nearly every name this run because they're keyed to the 09-11 session close, which
itself was a volatile session. Treating this as a full refresh rather than suppressing.

## Data quality
1. **news_watermark ambiguity**: watermark = "2026-09-14" (today) — literal "after watermark" would
   exclude all available news since nothing is dated tomorrow. Interpreted as "last ~5 sessions
   (09-08→09-14)" for TAILWINDS/HEADWINDS counting instead; flag for orchestrator to confirm intent.
2. **NVDA** is in `signal_history` but absent from current `holdings_trim` — position appears to
   have been exited since the last run captured it (2026-09-10). Not investigated further here
   (out of scope for signals); orchestrator/ledger should confirm.
3. **rel_sigma_sd = 0.828** — just under the 0.8 "under-firing" floor from the self-calibration
   rule. Borderline; not a hard alarm but trending toward under-firing on PEER LEADER/LAGGARD.
4. Insider activity for top-10 holdings by weight (VRT/ASML/GOOG/MRVL/GEV/TER/KLAC/TSM/COHR/ALAB)
   relied on news-embedded mentions only — `insiderTrades` (real Form-4) was not called this run to
   stay inside the tool-call budget with the pre-market context read already consuming several calls.
5. EARNINGS PROXIMITY: no >5%-weight holding found reporting within 7 days in the news scanned;
   section omitted rather than guessed.
6. GOOG has no `news` segment returned by the batched fetch (empty array) — analyst data only.

```json
{"signal_history":{"changed":{
  "VRT":["TARGET GAP"],
  "ASML":["MOMENTUM+VOLUME?","STRONG DOWNTREND","TARGET GAP","NEW TAILWINDS"],
  "GOOG":["TARGET GAP"],
  "MRVL":["TARGET GAP","NEW TAILWINDS"],
  "GEV":["TARGET GAP"],
  "TER":["TARGET GAP"],
  "KLAC":["PEER LAGGARD","TARGET GAP"],
  "TSM":["TARGET GAP","NEW TAILWINDS"],
  "COHR":["TARGET GAP"],
  "ALAB":["TARGET GAP"],
  "CLS":["TARGET GAP"],
  "LITE":["TARGET GAP"],
  "AMAT":["PEER LAGGARD","TARGET GAP"],
  "APH":["TARGET GAP"],
  "AMD":["PEER LEADER","TARGET GAP"],
  "MU":["TARGET GAP"],
  "QCOM":["PEER LEADER","NEW HEADWINDS"],
  "WDC":["TARGET GAP"],
  "AMZN":["TARGET GAP"],
  "STM":["MOMENTUM+VOLUME?","STRONG DOWNTREND","TARGET GAP"],
  "AVGO":["OVERSOLD BOUNCE?","PEER LAGGARD","TARGET GAP"],
  "NOW":["NEW TAILWINDS"],
  "BE":["PEER LEADER"],
  "MSFT":["TARGET GAP","NEW TAILWINDS"],
  "GLW":["MOMENTUM+VOLUME?","STRONG DOWNTREND","TARGET GAP"],
  "NBIS":["TARGET GAP","NEW TAILWINDS"],
  "SMCI":[],
  "CIEN":["PEER LAGGARD","TARGET GAP"]
},"unchanged_count":0},
 "news_watermark":"2026-09-14","resolved_flags":[],"new_flags":[],
 "journal_new":[
   {"date":"2026-09-14","ticker":"AVGO","bucket":"OVERSOLD BOUNCE","price_at_flag":361.99,"analyst_target":533.41,"day_atr_mult":-0.97,"rel_sigma":-1.36,"normalized":true},
   {"date":"2026-09-14","ticker":"ASML","bucket":"MOMENTUM+VOLUME","price_at_flag":1698.3,"analyst_target":2165.7,"day_atr_mult":-1.85,"rel_sigma":-0.52,"normalized":true},
   {"date":"2026-09-14","ticker":"STM","bucket":"MOMENTUM+VOLUME","price_at_flag":51.51,"analyst_target":75.04,"day_atr_mult":-1.88,"rel_sigma":-0.3,"normalized":true},
   {"date":"2026-09-14","ticker":"GLW","bucket":"MOMENTUM+VOLUME","price_at_flag":166.4,"analyst_target":191.4,"day_atr_mult":-1.71,"rel_sigma":0.21,"normalized":true}
 ],
 "peer_map_updates":{},
 "analyst_targets_updates":{
   "VRT":{"mean_target_usd":338.15,"n_analysts":17,"as_of":"2026-09-14"},
   "ASML":{"mean_target_usd":2167.96,"n_analysts":6,"as_of":"2026-09-14"},
   "GOOG":{"mean_target_usd":422.34,"n_analysts":12,"as_of":"2026-09-14"},
   "MRVL":{"mean_target_usd":285.0,"n_analysts":27,"as_of":"2026-09-14"},
   "GEV":{"mean_target_usd":1236.43,"n_analysts":21,"as_of":"2026-09-14"},
   "TER":{"mean_target_usd":446.47,"n_analysts":12,"as_of":"2026-09-14"},
   "KLAC":{"mean_target_usd":233.77,"n_analysts":21,"as_of":"2026-09-14"},
   "TSM":{"mean_target_usd":552.38,"n_analysts":8,"as_of":"2026-09-14"},
   "COHR":{"mean_target_usd":415.36,"n_analysts":17,"as_of":"2026-09-14"},
   "ALAB":{"mean_target_usd":389.95,"n_analysts":16,"as_of":"2026-09-14"},
   "AMAT":{"mean_target_usd":640.89,"n_analysts":28,"as_of":"2026-09-14"},
   "AVGO":{"mean_target_usd":533.41,"n_analysts":28,"as_of":"2026-09-14"},
   "BE":{"mean_target_usd":276.05,"n_analysts":17,"as_of":"2026-09-14"},
   "CIEN":{"mean_target_usd":504.13,"n_analysts":14,"as_of":"2026-09-14"},
   "GLW":{"mean_target_usd":191.4,"n_analysts":10,"as_of":"2026-09-14"},
   "MSFT":{"mean_target_usd":572.92,"n_analysts":34,"as_of":"2026-09-14"},
   "NOW":{"mean_target_usd":142.28,"n_analysts":30,"as_of":"2026-09-14"},
   "SMCI":{"mean_target_usd":42.38,"n_analysts":16,"as_of":"2026-09-14"}
 },
 "vol_normalization":{
   "ASML":{"atr20_pct":2.82,"day_atr_mult":-1.85,"rel_sigma":-0.52,"threshold_pct":4.23},
   "STM":{"atr20_pct":3.15,"day_atr_mult":-1.88,"rel_sigma":-0.3,"threshold_pct":4.72},
   "GLW":{"atr20_pct":4.54,"day_atr_mult":-1.71,"rel_sigma":0.21,"threshold_pct":6.81},
   "AVGO":{"atr20_pct":3.27,"day_atr_mult":-0.97,"rel_sigma":-1.36,"threshold_pct":4.91},
   "AMAT":{"atr20_pct":4.19,"day_atr_mult":-1.42,"rel_sigma":-1.45,"threshold_pct":6.29},
   "KLAC":{"atr20_pct":4.21,"day_atr_mult":-1.4,"rel_sigma":-1.08,"threshold_pct":6.31},
   "CIEN":{"atr20_pct":6.78,"day_atr_mult":-0.87,"rel_sigma":-1.05,"threshold_pct":10.17},
   "QCOM":{"atr20_pct":3.4,"day_atr_mult":-1.45,"rel_sigma":1.84,"threshold_pct":5.1},
   "AMD":{"atr20_pct":3.85,"day_atr_mult":-1.47,"rel_sigma":1.09,"threshold_pct":5.78},
   "BE":{"atr20_pct":6.06,"day_atr_mult":-1.3,"rel_sigma":1.4,"threshold_pct":9.09}
 },
 "data_quality":[
   "news_watermark equals today's date; interpreted as after-09-08 for tailwind/headwind counting rather than literal 'after 09-14' (which would exclude everything) -- confirm intent",
   "NVDA present in signal_history but absent from current holdings -- likely exited since 09-10, not investigated (out of scope)",
   "rel_sigma_sd 0.828, just under the 0.8 under-firing floor -- borderline, watch trend",
   "insiderTrades (Form-4) not called this run for top-10 holdings -- stayed within tool-call budget, relied on news-embedded insider mentions only",
   "no >5%-weight holding found reporting within 7 days in news scanned -- EARNINGS PROXIMITY section omitted",
   "GOOG batched fetch returned no news segment (empty array), analyst data only"
 ]}
```

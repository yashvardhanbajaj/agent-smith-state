# Signals — 2026-09-22-0926Z (quick, pre-open, gate AMBIGUOUS)

Session: pre-open (05:28 ET) — price/day-move reads below use `compute_buckets.json`'s
script-computed fields (EOD-based), not the live pre-market quotes pulled for news/targets,
which carry stale `prev_close`/day-change reads at this hour (see data_quality #4).
News watermark 2026-09-21 → today's scan found exactly one item dated after it (AMZN, minor,
below). This is functionally a delta run: 23 of 28 holdings are unchanged repeats.

## Changed / newsworthy (full lines)

- **AMD** — BREAKOUT + STRONG UPTREND + PEER LEADER (pos 0.983, PEER rel_sigma +2.93 vs SMH) — 1sh/1.61%.
  MOMENTUM+VOLUME rolled off (today's script-measured move sits inside the 5.61%-ATR threshold).
  New "OVERBOUGHT PULLBACK?" leg (pos≥0.85) judged **not confirmed**: upside to mean target
  $616.51 is only 1.3%, and no fresh negative news exists after the 09-21 watermark — GPU
  price-hike/$1T-cap coverage is all dated ≤09-21. Thesis stays WATCH (memory bf1897ca0c0b);
  today's price action is not new evidence.
- **MU** — TARGET GAP only; STRONG UPTREND rolled off (pos 0.797, just under the 0.80 floor,
  day_atr_mult -0.28 vs 6.38% threshold) — 5.44% position, largest memory stake. Mean target
  $1,513.11 (n=30), upside 46.7%. FQ4 due ~2026-10-01, 9 trading days out — outside this run's
  7-day EARNINGS PROXIMITY window.
- **MSFT** — TARGET GAP dropped this run (upside narrowed to 13.8%, below the 15% floor) — no
  buckets fire. 3.99% position, mean target $572.92.
- **SKHY** — STRONG UPTREND + TARGET GAP; PEER LEADER dropped (rel_sigma 0.94, just under the
  +1.0 floor, vs a firing read on 09-21) — position now 3sh/1.47% after +2sh @$188.26 yesterday
  (tripled). Mean target $249.70, upside 34.1%. INDmoney's live quote still misreports
  52wk_low=$0 for SKHY (the known artifact, memory cc6ae1d6c6f5); script's `wk52` cache holds
  the valid range so pos=0.818 is trustworthy — no action needed.
- **LLY** (new position) — PEER LAGGARD fired on a **mismatched benchmark**: no peer_map entry
  existed for this brand-new pharma name, so compute_buckets fell back to SMH (semis).
  rel_sigma -2.27 / rel_strength -12.3pp vs SMH says GLP-1 pharma didn't rally with AI semis
  this month — it says nothing about LLY itself. Correcting peer_map to XLV (pharma) this run;
  the bucket should re-score against the right peer next run. Position 0.5sh/1.54% @$1,164.04
  entry. Mean target $1,325.39 (n=21, pulled fresh — not yet in the targets cache), upside
  12.1% — below the 15% TARGET GAP floor.

## Yesterday's buys — size context

- **GEV** — TARGET GAP unchanged (target $1,237.34, +31.6%). Position 2.005sh/4.97% after +1sh
  @$955.32 (~doubled). GLJ Research Sell ($470 PT) and the Amodei essay threat both stay
  WEAKENED per catalyst; no new development in today's scan.
- **STM** — TARGET GAP unchanged (target $75.04, +44.8%). Position 20sh/2.74% after +5sh
  @$51.37 (+33%).
- **BE** — PEER LEADER unchanged, rel_sigma +2.86 vs XLU (large). S&P 500 inclusion (effective
  09-21, catalyst:511c7b86ce) now fully in the price — mean target $280.24, upside only 2.5%.
  Position doubled to 4sh/2.89% after +2sh @$275.27; the leadership read is priced-in, not a
  fresh entry signal.
- **MRVL** — no bucket fired (unchanged from 09-21, upside 13.8% under the TARGET GAP floor).
  Position 6sh/4.02% after +1sh @$253.63.

## Unchanged repeats (identical buckets vs 09-21, no size change, no news since watermark)

- TARGET GAP only: TSM (8.12%, $552.26, +25.7%) · GOOG (5.60%, $422.34, +19.3%) ·
  TER (4.99%, $446.47, +18.1%) · APH (4.22%, $99.26, +24.1%) · NBIS (3.65%, $288.33, +24.9%) ·
  CLS (3.55%, $471.20, +40.2%) · WDC (3.49%, $664.92, +50.8%) · VRT (3.95%, $338.15, +35.6%) ·
  ALAB (2.65%, $389.95, +16.4%) · COHR (1.66%, $415.36, +31.7%) · GLW (1.25%, $192.44, +21.8%) ·
  KLAC (4.81%, $233.77, +28.3%) · CIEN (0.01% — dust position, thesis flagged for a user
  re-establish/zero decision; target $507.62/+39.3% is technically fired but immaterial at
  this size).
- PEER LAGGARD + TARGET GAP: ASML (7.85%, $2,137.63, +25.8%) · AMAT (4.85%, $640.89, +39.9%) ·
  AMZN (3.43%, $328.22, +26.1%).
- STRONG UPTREND + TARGET GAP: LITE (2.48%, $1,149.38, +22.2%).
- PEER LEADER only: QCOM (2.55%, rel_sigma +1.54 vs SMH).
- No bucket: NOW (2.22%).

## Still pending (persisting, unresolved, no new development this window)

- GLW $2bn ATM: usage still undisclosed (catalyst:9744ffb8fe); next data point is the Q3 10-Q
  (~10-27). Optics-peer contagion into COHR/LITE remains sentiment, not confirmed.
- Amodei "Pace the Frontier" essay: still WEAKENED — no hyperscaler capex cut found in today's
  AMD/MRVL/GLW/COHR/LITE news sweep.
- GEV: GLJ Research Sell ($470 PT) — no new development.
- Trump-Xi summit Thu 09-24 (tariff truce, chips export controls, AI dialogue): still ambiguous,
  touches TSM/ASML/AMAT/KLAC/MU/SKHY/QCOM.
- CIEN's $319-materiality-floor decision (re-establish or zero): unresolved, thesis's call.
- AMZN: one new item today (22 Sep) — EC2 operational issues alongside backup-power demand
  expansion; neutral tone, single event, doesn't cross the 2-item NEW HEADWINDS threshold.

## data_quality

1. SKHY: INDmoney's live quote misreports 52wk_low=$0 (repeat of a known artifact); the
   script's wk52 cache holds valid bounds, so this run's pos/buckets for SKHY are unaffected.
2. LLY: no peer_map entry existed pre-run; compute_buckets defaulted PEER LEADER/LAGGARD to
   SMH, which is economically meaningless for a pharma name — corrected to XLV this run.
3. LLY: no analyst_targets cache entry yet; pulled fresh ($1,325.39 mean, n=21) and returned in
   analyst_targets_updates.
4. Pre-open session: get_us_stocks_details' live day-change/prev_close fields read stale for
   several names (e.g. AMD showed +9.95% vs a $559.82 prev_close that predates the 09-21
   breakout) — all price-position and day-move reads in this output use compute_buckets.json's
   script-derived fields instead, per the SCRIPT-OWNED indicator rule.
5. CIEN position is $2.98/0.01% weight ("dust") — its TARGET GAP bucket is technically fired
   but immaterial at this size; flagged so it isn't read as actionable.

```json
{"signal_history":{"changed":{"MU":["TARGET GAP"],"MSFT":[],"AMD":["BREAKOUT","STRONG UPTREND","PEER LEADER"],"SKHY":["STRONG UPTREND","TARGET GAP"],"LLY":["PEER LAGGARD"]},"unchanged_count":23},
 "news_watermark":"2026-09-22","resolved_flags":[],"new_flags":[],
 "journal_new":[],
 "peer_map_updates":{"LLY":{"peer_etf":"XLV","label":"pharma/GLP-1 (non-AI-capex; no peer_map entry existed pre-run, corrected from SMH default)"}},
 "analyst_targets_updates":{"LLY":{"mean_target_usd":1325.39,"n_analysts":21,"as_of":"2026-09-22"}},
 "vol_normalization":{
   "TSM":{"atr20_pct":2.26,"day_atr_mult":-0.56,"rel_sigma":0.21,"threshold_pct":3.39},
   "AMD":{"atr20_pct":3.74,"day_atr_mult":-0.3,"rel_sigma":2.93,"threshold_pct":5.61},
   "LITE":{"atr20_pct":6.44,"day_atr_mult":-0.23,"rel_sigma":0.18,"threshold_pct":9.66},
   "SKHY":{"atr20_pct":4.59,"day_atr_mult":-0.31,"rel_sigma":0.94,"threshold_pct":6.88},
   "ASML":{"atr20_pct":2.89,"day_atr_mult":-0.24,"rel_sigma":-1.23,"threshold_pct":4.33},
   "AMAT":{"atr20_pct":3.79,"day_atr_mult":-0.34,"rel_sigma":-1.42,"threshold_pct":5.69},
   "AMZN":{"atr20_pct":2.19,"day_atr_mult":0.33,"rel_sigma":-1.4,"threshold_pct":3.29},
   "BE":{"atr20_pct":6.36,"day_atr_mult":0.04,"rel_sigma":2.86,"threshold_pct":9.54},
   "QCOM":{"atr20_pct":4.21,"day_atr_mult":-0.16,"rel_sigma":1.54,"threshold_pct":6.31},
   "LLY":{"atr20_pct":2.36,"day_atr_mult":-0.05,"rel_sigma":-2.27,"threshold_pct":3.54}
 },
 "data_quality":[
   "SKHY live quote misreports 52wk_low=$0 (known artifact); script wk52 cache is valid, no impact this run",
   "LLY had no peer_map entry pre-run; PEER LAGGARD fired against a mismatched SMH default -- corrected to XLV",
   "LLY has no analyst_targets cache entry; pulled fresh this run (mean $1,325.39, n=21) via analyst_targets_updates",
   "Pre-open live day-change/prev_close fields from get_us_stocks_details read stale for several names (e.g. AMD); all price-position/day-move reads here use compute_buckets.json's script fields instead",
   "CIEN is a $2.98/0.01%-weight dust position; its fired TARGET GAP bucket is immaterial at this size"
 ],
 "findings_reaffirmed":["catalyst:9744ffb8fe","catalyst:b0c7d54add","catalyst:afbd345ec2","catalyst:ce8fa6cd04","catalyst:90ef472ced","catalyst:511c7b86ce"],
 "findings_revised":[],
 "comms":{"answers":[],"asks":[],"tells":[]},
 "memory_used":["acce172e73b3","bf1897ca0c0b","5a821537709e","18691a4ebc2f","d4672062d3dd","221f86bb2854","6da74338181b","cc6ae1d6c6f5","6ddf8e3ec2b4","477940e1be08"],
 "memory_refuted":[],
 "learned":[
   {"entities":["LLY"],"kind":"lesson","text":"LLY (added 2026-09-21 as a new position, 0.5sh) had no peer_map entry, so compute_buckets defaulted its PEER LEADER/LAGGARD read to SMH -- a semis ETF -- producing a -2.27 rel_sigma that measures LLY-vs-semis, not LLY-vs-its-own-sector. Mapped to XLV this run. Any brand-new non-AI-capex position needs a peer_map entry seeded the same run it's added, or its first peer-relative read is noise.","source":"compute_buckets.json 2026-09-22 + peer_map.eb396c76.json (no LLY key)","confidence":"primary"},
   {"entities":["AMD"],"kind":"event","text":"2026-09-22 pre-open: AMD's script-measured day move fell inside its 5.61%-ATR threshold (day_atr_mult -0.3), rolling off MOMENTUM+VOLUME from the 09-21 breakout day; a new OVERBOUGHT PULLBACK? leg (pos 0.983) was judged not confirmed -- upside to target is only 1.3% and no negative news exists after the 09-21 watermark.","source":"compute_buckets.json + get_us_stocks_details news sweep","confidence":"secondary"},
   {"entities":["MU","MSFT","SKHY"],"kind":"event","text":"2026-09-22: three names crossed bucket thresholds in the quiet direction on marginal moves -- MU's pos (0.797) slipped just under the 0.80 STRONG UPTREND floor, MSFT's upside (13.8%) slipped just under the 15% TARGET GAP floor, and SKHY's rel_sigma (0.94) slipped just under the +1.0 PEER LEADER floor. None reflect new negative information; all are threshold-proximity noise worth watching if it persists into the next run.","source":"compute_buckets.json vs signal_history (2026-09-21 baseline)","confidence":"secondary"}
 ]
}
```

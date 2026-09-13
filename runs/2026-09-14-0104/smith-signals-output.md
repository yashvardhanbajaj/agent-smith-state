# smith-signals — 2026-09-14 quick sweep (intraday, gate=STABILIZING)

Macro backdrop: SPX +0.86%, NDX +0.96%, SMH +1.47%, VIX -11.21% to 15.84 — broad risk-on session,
consistent with the "big single-session rally" flagged by the orchestrator. Book is 28 names post
the 09-10 stop cascade (INTC/NVDA/SKHY/LRCX/META exited; AMD/STM/GEV/NBIS/BE/MU trimmed; VRT/KLAC/
LITE added-to; AMZN/NOW new 09-11). All bucket arithmetic (pos/day-move/rel_sigma/TARGET GAP) is
pre-computed in compute_buckets.json and reported as-is, not recomputed. ATR20/RSI14/rel_strength_1m
caches are 8 days stale (past 7d TTL, inside 10d suppress floor) — used as-is per quick-mode rule,
no refresh performed.

## TARGET GAP + trend/peer buckets, by weight

- **VRT** 6.94% — TARGET GAP, +31.5% to $338.15. rel_sigma +0.22 (mild), day_atr_mult 0.82. Unchanged repeat. No news since watermark (UtilityInnovation deal/dividend was pre-09-10).
- **ASML** 6.37% — TARGET GAP, +27.5% to $2165.70. Unchanged; NEW TAILWINDS dropped (no post-watermark story; last item 09-10 was on the watermark, excluded).
- **MRVL** 6.37% — PEER LEADER (rel_sigma +2.53 vs SMH, +34.12pp) + TARGET GAP +20.7% to $285.00. Unchanged repeat; INSIDER ACTIVITY dropped (no fresh Form-4 news this run). 1 fresh item — "Marvell Technology Thrives Amid AI Demand Surge" — 2026-09-11 — INDmoney feed — insufficient alone for a new TAILWINDS flag.
- **GOOG** 6.04% — PEER LAGGARD (rel_sigma -1.53 vs XLK, -7.63pp) + TARGET GAP +25.9% to $422.34. Unchanged repeat.
- **GEV** 5.76% — TARGET GAP +29.2% to $1236.43. Unchanged; rel_sigma -0.62 vs XLU, mild laggard but not crossing -1.0. No fresh news.
- **TER** 5.70% — TARGET GAP +17.6% to $446.47. Unchanged, modest day_atr_mult 0.41.
- **KLAC** 5.42% — TARGET GAP +29.4% to $233.77. Unchanged. Open journal MOMENTUM+VOLUME entry from 09-06 still unscored at 7d.
- **TSM** 5.20% — STRONG UPTREND + TARGET GAP +27.5% to $552.38. Unchanged repeat; NEW TAILWINDS dropped (only 1 fresh item — "TSM Reports Record Revenue Amid Strong Demand" — 2026-09-11 — INDmoney feed).
- **COHR** 4.58% — TARGET GAP +36.0% to $415.36. Unchanged; rel_sigma +0.89 vs SMH — just under the +1.0 PEER LEADER bar, worth watching. No fresh news.
- **ALAB** 4.37% — TARGET GAP +33.9% to $389.95. Unchanged; rel_sigma -0.14, in-line with sector.
- **LITE** 4.17% — PEER LEADER (rel_sigma +2.37, +45.09pp vs SMH) + STRONG UPTREND (pos 0.831) + TARGET GAP +23.9% to $1148.43. Unchanged repeat; day_atr_mult -0.11 — flat/slightly down today despite the book-wide rally, pausing after a huge outperformance run.
- **CLS** 4.16% — PEER LAGGARD (rel_sigma -1.33, -17.0pp vs SMH) + TARGET GAP +37.7% to $477.22. Unchanged. 1 fresh item — "Celestica Restructures Leadership Amid Growth" — 2026-09-11 — INDmoney feed — positive but alone, notable given the name is still a peer laggard despite today's rally.
- **AMAT** 4.12% — TARGET GAP +40.4% to $640.89. Unchanged; rel_sigma -0.27. 1 fresh item ("Positive Earnings Outlook…", 2026-09-11, INDmoney feed) — insufficient alone for TAILWINDS.
- **APH** 3.78% — STRONG UPTREND **(NEW)** — pos 0.843, day_atr_mult 1.43 — + TARGET GAP +18.1% to $99.15. rel_sigma -0.46 (in-line with SMH) — this looks idiosyncratic/name-specific, not sector beta. 3.78% weight, mid-size position.
- **AMD** 3.10% — STRONG UPTREND + TARGET GAP +18.9% to $613.84. Unchanged; NEW TAILWINDS dropped — the two post-watermark headlines (09-11, 09-12) both read as continuation of the same broad AI/semis rally rather than distinct catalysts, deduped to 1 event per G58.
- **MU** 2.93% — PEER LEADER (rel_sigma +1.02, +12.93pp vs SMH) + TARGET GAP +55.1% to $1513.11 (widest gap in book). Unchanged; NEW TAILWINDS dropped — only fresh item is neutral-toned ("labor pressure amid record bonuses", 09-11).
- **QCOM** 2.73% — PEER LAGGARD (rel_sigma -1.17, -7.8pp vs SMH). No TARGET GAP (upside only 6.6%, below floor). NEW TAILWINDS dropped from history. Fresh news skews negative: "Qualcomm Faces Revenue Impact Amid New Collaborations" — negative — 2026-09-12 — INDmoney feed; "Faces Delays but Shows Positive Momentum" — neutral — 2026-09-11 — INDmoney feed. Only 1 clearly negative event, short of the ≥2 HEADWINDS bar — flagging as a watch item, not a bucket.
- **WDC** 2.68% — TARGET GAP +48.7% to $664.92 (2nd-widest gap). Unchanged; rel_sigma -0.85, mild laggard, not crossing -1.0. No fresh news (last item exactly on watermark, excluded).
- **STM** 2.32% — TARGET GAP +45.7% to $75.04. Unchanged. The open_flags PEER LAGGARD note from 08-13 is now resolved: rel_sigma -0.9, no longer crosses -1.0.
- **AMZN** 2.31% — brand-new position, no prior history. TARGET GAP +27.3% to ~$327-328 + NEW TAILWINDS **(NEW)**: 2 distinct positive events post-watermark — "Amazon Sees Strong Growth and Strategic Investments" (AWS revenue, bond raise, Qualcomm AI partnership) — 2026-09-11 — INDmoney feed; "Amazon Reports Growth Amid Strategic Expansions" (AWS, autonomous-mobility investment) — 2026-09-13 — INDmoney feed. Peer-relative corrected (task 9 override, AMZN named in stale_peer_fallback_tickers): true peer is XLK, not SMH — 1mo return -3.93% vs XLK -0.63% = -3.30pp, rel_sigma -0.66 — inside its own noise band, no PEER LAGGARD. 52wk range not yet cached (new position); wk52_updates supplied below (source: INDmoney snapshot dated 2026-09-12, 2 days stale — flagged in data_quality).
- **AVGO** 2.17% — PEER LAGGARD (rel_sigma -1.62, -13.31pp vs SMH) + TARGET GAP +47.4% to $533.41 (3rd-widest gap). POLICY IMPACT: "Broadcom Reports Strong AI Growth Amid EU Scrutiny" (VMware licensing antitrust concern) — 2026-09-11 — INDmoney feed — developing, unresolved either direction. Unchanged core buckets; small 2.17% position.
- **BE** 1.65% — no bucket fires. At consensus target (upside -0.2%, target $276.05) after its S&P-500-inclusion-driven run; rel_sigma only +0.5 vs XLU despite +9.24pp raw peer gap — correctly damped by its wide (7.97%) ATR. Worth a strategist look for profit-taking; not a signals-agent call.
- **NOW** 1.59% — brand-new position, no prior history. Compute script's PEER LEADER flag (rel_sigma +1.55, using the stale SMH fallback) does **not** survive correction. True peer is XLK per peer_map (enterprise software) — 1mo return +6.07% vs XLK -0.63% = +6.70pp, rel_sigma +0.515 — below the +1.0 leader bar once benchmarked correctly. **No bucket fires this run.** pos ≈0.45 (price $132.53 vs 52wk $81.24-$194.73, fresh fetch). 1 fresh positive item — "ServiceNow Boosts Revenue Target Amid Positive Sentiment" — 2026-09-11 — INDmoney feed — alone, insufficient for TAILWINDS.
- **GLW** 1.50% — TARGET GAP **(NEW)** — no prior history, +15.0% to $191.40 (right at the threshold floor). rel_sigma +0.73 vs SMH, in-line. Small satellite position.
- **MSFT** 1.49% — TARGET GAP (unchanged, +15.6% to $572.92) + NEW TAILWINDS **(NEW)**: 2 distinct positive events post-watermark — "Microsoft Reports Strong Revenue and Expands AI Initiatives" (Q4 revenue $90.01B, datacenter tripling) — 2026-09-11 — INDmoney feed; "Microsoft's Strong AI and Quantum Growth Highlights" (quantum research, bullish price-target raise) — 2026-09-12 — INDmoney feed.
- **NBIS** 1.35% — TARGET GAP +24.7% to $280.00. Unchanged; rel_sigma +0.12 vs XLK, in-line. No fresh news.
- **SMCI** 1.20% — PEER LEADER (rel_sigma +1.87, +29.84pp vs XLK). Unchanged. Consensus target ($42.38) implies only +5.7% upside despite the peer-leading move — priced closer to fair value than the momentum alone suggests.
- **CIEN** 0.01% — TARGET GAP +44.2% to $504.13. Unchanged; this is a dust position (0.01% weight, likely a fractional-share remnant from a prior trim/exit, not an active bet).

## Unchanged repeats (bucket + name identical to 09-10, no material change)
VRT, GOOG, GEV, TER, KLAC, COHR, ALAB, LITE, CLS, AMAT, WDC, AVGO, BE, NBIS, SMCI, CIEN (16 names).

## Still pending (carried from open_flags, unresolved)
- STM/TXN "Analog/Industrial Semis" cluster still has no policy band — user decision pending (opened 2026-08-12).
- BE at-target / possible profit-take is a strategist-level call, not resolved here.

## Resolved this run
- STM PEER LAGGARD (open_flags, opened 2026-08-13) — rel_sigma now -0.9, no longer crosses -1.0.

## Data quality
- ATR20/RSI14/rel_strength_1m caches are 8 days stale (as_of 2026-09-06/09-09) — past 7d TTL, inside 10d suppress floor; used as-is per quick-mode default, no refresh run.
- get_us_stocks_details snapshot returned last_updated 2026-09-12 08:46 for most symbols (2 days behind today's 09-14 intraday session) — used only for news dates/headlines and to backfill AMZN/NOW's missing wk52/analyst-target cache, never to recompute pos/day-move (compute_buckets.json's today-dated figures were used for all trend/peer math).
- AMZN pos not independently computed this run (would mix a stale 09-12 price with today's cache); wk52 low/high supplied below so next run can compute it cleanly.
- 2 tickers (AMZN, NOW) required a peer-benchmark override per task 9 (stale_peer_fallback_tickers) — done via one batched yfinance 1mo call (AMZN, NOW, XLK); NOW's PEER LEADER flag from the SMH-fallback read did not survive correction.

```json
{"signal_history":{"changed":{
  "ASML":["TARGET GAP"],
  "MRVL":["PEER LEADER","TARGET GAP"],
  "MU":["PEER LEADER","TARGET GAP"],
  "TSM":["STRONG UPTREND","TARGET GAP"],
  "AMD":["STRONG UPTREND","TARGET GAP"],
  "QCOM":["PEER LAGGARD"],
  "STM":["TARGET GAP"],
  "APH":["STRONG UPTREND","TARGET GAP"],
  "MSFT":["TARGET GAP","NEW TAILWINDS"],
  "GLW":["TARGET GAP"],
  "NOW":[],
  "AMZN":["TARGET GAP","NEW TAILWINDS"]
 },"unchanged_count":16},
 "news_watermark":"2026-09-14",
 "resolved_flags":["STM PEER LAGGARD (opened 2026-08-13) -- rel_sigma now -0.9, no longer crosses -1.0 threshold"],
 "new_flags":["APH STRONG UPTREND (new)","MSFT NEW TAILWINDS (new)","GLW TARGET GAP (new, first history)","AMZN TARGET GAP + NEW TAILWINDS (new position)","NOW PEER LEADER overridden false vs XLK (was SMH-fallback false positive)"],
 "journal_new":[],
 "wk52_updates":{"AMZN":{"low":196.0,"high":287.2},"NOW":{"low":81.24,"high":194.726}},
 "peer_map_updates":{},
 "analyst_targets_updates":{
   "AMZN":{"mean_target_usd":328.17,"n_analysts":40,"as_of":"2026-09-12"},
   "NOW":{"mean_target_usd":142.28,"n_analysts":30,"as_of":"2026-09-12"}
 },
 "ret_5d_updates":{},
 "vol_normalization":{
   "TSM":{"atr20_pct":2.42,"day_atr_mult":0.5,"rel_sigma":0.07,"threshold_pct":3.63},
   "AMD":{"atr20_pct":4.02,"day_atr_mult":0.62,"rel_sigma":-0.29,"threshold_pct":6.03},
   "LITE":{"atr20_pct":8.28,"day_atr_mult":-0.11,"rel_sigma":2.37,"threshold_pct":12.0},
   "APH":{"atr20_pct":3.2,"day_atr_mult":1.43,"rel_sigma":-0.46,"threshold_pct":4.8},
   "MRVL":{"atr20_pct":5.86,"day_atr_mult":0.69,"rel_sigma":2.53,"threshold_pct":8.79},
   "MU":{"atr20_pct":5.5,"day_atr_mult":-0.04,"rel_sigma":1.02,"threshold_pct":8.25},
   "SMCI":{"atr20_pct":6.93,"day_atr_mult":1.05,"rel_sigma":1.87,"threshold_pct":10.39},
   "GOOG":{"atr20_pct":1.75,"day_atr_mult":0.88,"rel_sigma":-1.53,"threshold_pct":2.62},
   "CLS":{"atr20_pct":5.57,"day_atr_mult":1.18,"rel_sigma":-1.33,"threshold_pct":8.36},
   "AVGO":{"atr20_pct":3.57,"day_atr_mult":0.09,"rel_sigma":-1.62,"threshold_pct":5.35},
   "QCOM":{"atr20_pct":2.91,"day_atr_mult":0.99,"rel_sigma":-1.17,"threshold_pct":4.37},
   "AMZN":{"atr20_pct":2.13,"day_atr_mult":0.91,"rel_sigma":-0.66,"threshold_pct":3.19},
   "NOW":{"atr20_pct":5.65,"day_atr_mult":0.18,"rel_sigma":0.515,"threshold_pct":8.48}
 },
 "atr20_updates":{},
 "rsi14_updates":{},
 "rel_strength_1m_updates":{},
 "rel_strength_1m_peer_updates":{
   "AMZN":{"rel_pp":-3.30,"peer_etf":"XLK"},
   "NOW":{"rel_pp":6.70,"peer_etf":"XLK"}
 },
 "data_quality":[
   "ATR20/RSI14/rel_strength_1m caches 8 days stale (as_of 2026-09-06/09-09); used as-is per quick-mode default, no refresh run this pass.",
   "get_us_stocks_details snapshot last_updated 2026-09-12 08:46 for most symbols, 2 days behind today's session -- used only for news dating/headlines and AMZN/NOW cache backfill, never for pos/day-move recompute.",
   "AMZN pos not computed this run (stale price vs fresh wk52); wk52_updates supplied for a clean compute next run.",
   "AMZN/NOW peer-benchmark override required one extra batched yfinance call (task 9, stale_peer_fallback_tickers) -- NOW's PEER LEADER flag from the SMH fallback did not survive correction against its true XLK peer.",
   "AMD's 2 post-watermark headlines (09-11, 09-12) deduped to 1 underlying event (same broad AI/semis rally, not 2 distinct catalysts) per G58 -- kept NEW TAILWINDS from firing.",
   "QCOM has 1 negative post-watermark item, short of the >=2-negative HEADWINDS bar -- flagged as a watch item in prose only."
 ]
}
```

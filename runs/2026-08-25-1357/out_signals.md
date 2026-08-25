# smith-signals — 2026-08-25 (deep, pre-open)

## Trend
- FLTW — STRONG UPTREND, pos 0.80 ($99.08, 52wk $52.92–$110.32) — 2.62% weight. Day move -0.96% (-0.51x its 1.89% ATR) is noise, not a downtrend confirmation — conflicted-move flag from signal_history resolved in favor of the pos-based read.
- META — STRONG DOWNTREND, pos 0.14 ($559.02, 52wk $520.26–$790.80) — 2.97% weight. Continuing from signal_history; mean target $754.14 (+25.9% upside).
- SKHY — STRONG DOWNTREND [unnormalized], day -4.92% ($155.37) — 2.11% weight. No ATR20 cache entry, absolute ±4% fallback used. **Data quality: 52wk range is broken (low=$0, high=live price) — likely a bad data return, not a real breakout ceiling; do not trust pos off this name.**

## Peer-Relative (SMH -0.32%, XLK +3.30%, XLU -5.39%, XLF +2.36% — 1mo)
- MSFT — PEER LEADER, +3.06σ. +25.24% 1m vs XLK +3.30% (+21.9pp) — 3.86% weight. Continuing.
- NOW — PEER LEADER, +1.39σ. +21.31% 1m vs XLK +3.30% (+18.0pp) — 2.36% weight. Continuing.
- AMZN — PEER LEADER, +1.40σ (NEW). +13.26% 1m vs XLK +3.30% (+9.96pp) — 4.17% weight.
- SKHY — PEER LEADER [unnormalized], +8.95pp vs SMH (no ATR cache) — 2.11% weight, same bad-52wk-data name as above; directional only.
- KLAC — PEER LAGGARD [unnormalized], -10.4pp vs SMH (no ATR cache) — 1.96% weight.
- Near-miss, not flagged: MRVL +0.95σ (was PEER LEADER, cooling); TXN -0.91σ; META -0.84σ (was PEER LAGGARD, now inside its own noise on a -9.2pp raw gap — thesis/derisk own the raw number, not a flag here).

## Target Gap (≥15% upside, mean-target cited)
New this run: KLAC $231.78 (+21.7%), INTC $114.88 (+24.0%), ASML $2,176.09 (+20.0%), TER $449.80 (+18.9%), LRCX $368.94 (+15.9%), CLS $473.24 (+37.8%).
Unchanged repeats (already flagged, no material pos/news shift ≥0.05): TSM, MU, CIEN, AMD, STM, NVDA, AVGO, GEV, QCOM, BABA, CEG, AMZN, VRT, AMAT, BE, TXN, META, GOOG, WDC, GLW.
MSFT drops out of TARGET GAP (upside now 14.4%, below 15% threshold).

## New Headwinds (dedup'd distinct events, dated ≤2026-08-24)
- AVGO — 3 distinct negative events: revenue/debt-concern report (24 Aug, Investing.com), Druckenmiller & Loeb Broadcom exit (23 Aug, Barrons), D.E. Shaw stake cut (22 Aug, MarketWatch) — 3.82% weight. Continuing from signal_history.
- BABA — 3 distinct negative events: $10.2B capital raise/dilution concern (23 Aug), mixed earnings vs AI investment surge (20 Aug), lawsuit/class-action overhang (17 Aug) — 0.62% weight, small position. Continuing.
- META — 2 distinct negative events: ongoing antitrust/ad-lawsuit litigation (recurring 22/21/16/13/11 Aug, one event) + AI-spend-scrutiny narrative (21 Aug) — 2.97% weight. Continuing.

## Insider Activity (news-derived — FMP Form-4 blocked, see data_quality)
- TSM — insider purchase reported 22 Aug (Barchart) — reads as confidence signal. 6.56% weight, book's largest position.
- AMD — insider sale + board changes, 22 Aug. Continuing from signal_history.
- MRVL — insider selling flagged twice (19, 18 Aug) alongside the Google-partnership rally. Continuing.

## Still Pending
- G81 (proximate cause of 8/18 semis rout) — unresolved; MU's Netlist patent overhang cited in today's dispatch as the driver of Monday's -5.83% has no independent confirming headline in this fetch.
- STOP-CASCADE-08-10/11 (open_flags) — GOOGL breakdown still the one genuine leg of that cascade; not in current holdings so not scored here.
- STM/TXN cluster still provisional — thesis has not yet written first theses per open_flags note.

## Journal
No new actionable swing/reversal/earnings-proximity flags this run — TARGET GAP and trend buckets above are structural continuations already scored in compute_journal.json (TARGET GAP hit rate 36.8% n=19, 30d; MOMENTUM+VOLUME 0% n=11 — weak bucket, no new momentum flags fired anyway). NVDA earnings Wed 8/27 not formally flagged: weight is 2.79%, below the >5% EARNINGS PROXIMITY gate, despite being the book's headline catalyst this week.

## Data Quality
- FMP `insiderTrades` returns ACCESS DENIED (plan tier below Starter) — deep-mode Form-4 pull for top-8 weighted holdings (TSM, GEV, VRT, BE, MRVL, AMZN, STM, MSFT) fell back to news-derived insider mentions only; GEV/VRT/BE/STM had no insider news this fetch.
- SKHY 52wk range unreliable (low=$0) — treat its STRONG DOWNTREND / PEER LEADER flags as directional, not confirmed breakout/breakdown geometry.
- KLAC has no ATR20 cache entry — its PEER LAGGARD flag used the legacy ±8pp absolute fallback, tagged [unnormalized].
- News watermark treated as inclusive of 2026-08-24-dated items (last run's signal_history_as_of also reads 2026-08-24, consistent with same-day early dispatch); new watermark set to 2026-08-25.
- Budget: insider-trade fetch capped at top 8 by weight (not the full top-10) to stay inside the ~15-tool-call soft cap after the FMP denial burned 8 calls with no data.

```json
{"signal_history":{"changed":{"KLAC":["TARGET GAP","PEER LAGGARD"],"INTC":["TARGET GAP"],"ASML":["TARGET GAP"],"TER":["TARGET GAP"],"LRCX":["TARGET GAP"],"CLS":["TARGET GAP"],"MSFT":["PEER LEADER"],"AMZN":["TARGET GAP","PEER LEADER"],"FLTW":["STRONG UPTREND"],"SKHY":["STRONG DOWNTREND","PEER LEADER"],"MRVL":["INSIDER ACTIVITY"],"TSM":["TARGET GAP","INSIDER ACTIVITY"]},"unchanged_count":23},
 "news_watermark":"2026-08-25","resolved_flags":[],"new_flags":[],
 "journal_new":[],
 "peer_map_updates":{},
 "vol_normalization":{"FLTW":{"atr20_pct":1.89,"day_atr_mult":-0.508,"rel_sigma":null,"threshold_pct":2.835},"META":{"atr20_pct":4.74,"day_atr_mult":0.350,"rel_sigma":-0.841,"threshold_pct":7.11},"SKHY":{"atr20_pct":null,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":4.0},"KLAC":{"atr20_pct":null,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":null},"MSFT":{"atr20_pct":3.12,"day_atr_mult":0.269,"rel_sigma":3.057,"threshold_pct":4.68},"NOW":{"atr20_pct":5.65,"day_atr_mult":-0.058,"rel_sigma":1.386,"threshold_pct":8.475},"AMZN":{"atr20_pct":3.09,"day_atr_mult":0.430,"rel_sigma":1.401,"threshold_pct":4.635},"MRVL":{"atr20_pct":9.88,"day_atr_mult":-0.331,"rel_sigma":0.947,"threshold_pct":12.0}},
 "data_quality":["FMP insiderTrades ACCESS DENIED (plan tier) -- deep insider pull for top-8 weighted holdings fell back to news-derived only","SKHY 52wk range broken (low=$0) -- STRONG DOWNTREND/PEER LEADER flags directional only, no ATR20 cache entry either","KLAC has no ATR20 cache entry -- PEER LAGGARD used legacy unnormalized ±8pp fallback","News watermark treated inclusive of 2026-08-24-dated items given same-day prior run; new watermark = 2026-08-25","Insider fetch capped at top 8 by weight (not top 10) after FMP denial burned budget","MSFT dropped out of TARGET GAP this run (upside now 14.4%, below 15% threshold)"]}
```

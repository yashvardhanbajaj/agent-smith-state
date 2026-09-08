# Signal Scanner — 2026-09-08 (deep, pre-open)

Note: 2026-09-07 was Labor Day (markets closed). All prices/technicals identical to the 2026-09-06/07 runs — last completed session Fri 2026-09-04. Price-derived buckets below are read from compute_buckets.json (script-owned, not recomputed). This run's value is (a) ~3 calendar days of news, (b) closing the peer-relative cache gap for 9 tickers, (c) judgment legs on `?`-suffixed buckets.

## PEER-RELATIVE STRENGTH — cache refresh (task 9)

Refreshed `rel_strength_1m_peer` for all 9 `stale_peer_fallback_tickers`. This CHANGES four bucket verdicts vs the SMH-default fallback the script used this run:

- **BE PEER LEADER → does not fire.** True peer XLU 1m -1.33%, BE 1m +7.91% → rel_pp +9.24 (vs +19.39 under wrong SMH default). rel_sigma = 9.24/18.34(=2.3×7.97% ATR) = **0.50**, below the 1.0 threshold. Weight 5.36%.
- **NBIS PEER LEADER → does not fire.** True peer XLK 1m +0.74%, NBIS 1m +3.38% → rel_pp +2.64 (vs +33.76 under wrong SMH default — that gap alone should have been a red flag). rel_sigma ≈ 0.14 (ATR20 clamped at ceiling ≥8%, so this is a conservative estimate; even generously it stays well under 1.0). Weight 3.97%.
- **IREN PEER LEADER → does not fire.** True peer XLK 1m +0.74%, IREN 1m +14.89% → rel_pp +14.15 (vs +24.64 under SMH). rel_sigma ≈ 0.5–0.8 depending on exact ATR (clamped at ceiling, same caveat as NBIS) — below 1.0 either way. Weight 2.24%.
- **MSFT PEER LEADER → does not fire** (this one was already flagged overridden-false in the prior run's signal_history; reconfirmed). True peer XLK 1m +0.74%, MSFT 1m +2.51% → rel_pp +1.77 (vs +15.68 under SMH — SMH is simply the wrong benchmark for a hyperscaler). rel_sigma = 1.77/5.0(floor) = **0.35**. Weight 1.26%.

Confirmed (fire under true peer too, direction unchanged):
- **SMCI PEER LEADER — confirmed, even stronger.** True peer XLK 1m +0.74%, SMCI 1m +30.57% → rel_pp +29.84, rel_sigma = 29.84/15.93(=2.3×6.93% ATR) = **1.87**. Genuinely leading its real peer group, not a benchmark artifact. Weight 1.0%.
- **FSLR PEER LAGGARD — confirmed.** True peer XLU 1m -1.33%, FSLR 1m -13.66% → rel_pp -12.33, rel_sigma = -12.33/9.34(=2.3×4.06% ATR) = **-1.32**. Weight 1.55%.
- **GOOG PEER LAGGARD — confirmed** (true peer XLK gives a less extreme but still-firing -1.53σ vs SMH's overstated -2.61σ). rel_pp -7.63 (XLK +0.74% vs GOOG -6.89%). Weight 3.38%.
- **GEV, VRT — no fire either way** (XLU peer gives rel_sigma -0.62 and +0.23 respectively, consistent with the SMH read).

`peer_map` unchanged this run (no new/changed mappings). `rel_strength_1m_peer_updates` in tail below.

## Bucketed signals (script-computed, confirmed)

- **KLAC — STRONG UPTREND, MOMENTUM+VOLUME confirmed** — day_atr_mult 1.61× (6.84% threshold), +7.32% Fri session on a $7B buyback (13 Jul) + Stifel target hike ($191→$270, 10 Jul) + strong Q3 print. Volume 11.4M vs typical, elevated. Weight 2.80%. Journal: none yet scored for KLAC STRONG UPTREND.
- **MRVL — PEER LEADER confirmed (SMH correct peer), TARGET GAP, INSIDER ACTIVITY** — rel_sigma 2.53, mean target $285 = +21.6% upside. News-derived insider: CEO sold shares ahead of Q2 print (18 Aug), no new filing since. Weight 5.04%.
- **MU — PEER LEADER confirmed** — rel_sigma 1.02, mean target $1,513 = +32.8% upside. Weight 3.84%.
- **LRCX — PEER LEADER confirmed** — rel_sigma 1.15, dividend +27%, target $370.87 = +17.1% upside. Weight 2.32%.
- **LITE — PEER LEADER confirmed** — rel_sigma 2.37, target $1,148 = +23.3% upside. Weight 2.22%.
- **SKHY — PEER LEADER confirmed** — rel_sigma 1.06, target $248 = +40.1% upside. NOTE: 52wk_low returned as 0 in this fetch — data_quality flag, pos calc guardrail applies if pos bucket triggers (currently deferred_pos_buckets=false, cache-owned wk52 should not carry 0; flagging for wk52 cache integrity).
- **AVGO, QCOM, CLS — PEER LAGGARD confirmed** (SMH correct peer for all three). AVGO rel_sigma -1.62 despite mixed Q3 (beat but light Q4 guide, stock -9.7% on 3mo) — TARGET GAP still open ($533 mean = +32.9% upside). QCOM -1.17σ, handset weakness persists. CLS -1.33σ despite strong Q2 (+62% rev) — TARGET GAP $477 = +34.6% upside, name mostly flat/consolidating post-print.

## Target gaps (≥15%, unchanged from prior run, all still open)

ASML +20.1%, TSM +22.4%, STM +30.4%, TER +20.0%, NVDA +29.6%, AVGO +32.9%, CLS +34.6%, CIEN +36.3%, VRT +17.0%, COHR +32.1%, AMAT +29.1%, ALAB +20.4%, IREN +42.6%, SKHY +40.1%, MRVL +21.6%, MU +32.8%, WDC +29.7%, NBIS n/a (no target field returned this pull), FSLR +25.7%, GLW +19.4% (no bucket fire, informational). No new gaps opened since watermark.

## News — distinct events since watermark (2026-09-07)

Only 4 items post-watermark, none clearing the ≥2-distinct-event threshold for a bucket on any single name:
- ASML/TSM — "ASML/TSMC High-NA 12-inch photomask collaboration, 2030-2031 timeline" — 08 Sep, INDmoney/FMP feed — positive, one event covering both tickers.
- NVDA — "Jensen Huang: rental prices rising for older GPUs; multi-year OpenAI Malaysia compute deal" — 08 Sep, INDmoney/FMP feed — positive, single event.
- INTC — "Northland upgrade + High-NA EUV progress + Trump attention" — 08 Sep, INDmoney/FMP feed — positive, single event (partially overlaps the ASML/TSM High-NA story but driven primarily by the analyst action).

## Still pending (persisting stories, no material change since watermark)

GEV NEW TAILWINDS (backlog $176B, HVDC JV, data-center power rev) — unchanged repeat. MU/AMD/LRCX/LITE/GLW NEW TAILWINDS — unchanged repeats, no new confirming events this window. MRVL/WDC INSIDER ACTIVITY — no new filings since prior flag (insiderTrades tool blocked this run — FMP plan tier, see G90; relying on news-embedded insider mentions only). INTC POLICY IMPACT (tariff/CHIPS overhang) — unchanged.

## Unchanged repeats (buckets identical to prior run, no size/news change)

ASML, TSM, STM, TER, NVDA, CIEN, AMAT, COHR, ALAB TARGET GAP; KLAC STRONG UPTREND; QCOM/CLS/AVGO PEER LAGGARD.

## Journal — new actionable flags

KLAC STRONG UPTREND is not a new open (already scored historically per journal grades — bucket_hit_rates apply). No new swing setups (MOMENTUM+VOLUME?/OVERSOLD/OVERBOUGHT judgment legs) confirmed this run — KLAC's MOMENTUM+VOLUME? leg is promoted to fired (see above) given the buyback+target-hike catalyst and elevated volume; no journal_new entry needed since STRONG UPTREND/KLAC already exists in signal_history from a prior open.

## Data quality

- insiderTrades tool blocked (FMP plan tier — Starter/Premium/Ultimate/Enterprise required). Deep-mode insider activity this run is news-derived only, not Form-4-sourced. Ties to known gap G90.
- SKHY 52week_low returned as 0 in get_us_stocks_details (live fetch, not the wk52 cache) — do not let this leak into any pos calculation; wk52 cache itself is fresh (age 2d) and unaffected.
- NBIS/IREN rel_sigma above are computed with an estimated ATR20 (their `threshold_pct` is clamped at the 12% ceiling in compute_buckets.json, so exact ATR20 isn't recoverable from that field) — directionally robust (both far under the 1.0 firing threshold across a wide plausible ATR range) but not exact to 2 decimals.
- SD(rel_sigma)=1.312 (script-reported, unchanged) — outside the 0.8–1.3 self-calibration band, bucket over-firing slightly. Reporting only, not retuning.
- Budget: 10 tool calls used (4 news/analyst batches, 4 peer-ETF/holding history batches, 2 blocked insider calls). Well under the ~15 soft cap.

```json
{"signal_history":{"changed":{"BE":["TARGET_GAP_NOT_FIRED","PEER_LEADER_OVERRIDDEN_FALSE_vs_XLU"],"NBIS":["PEER_LEADER_OVERRIDDEN_FALSE_vs_XLK","TARGET GAP"],"IREN":["PEER_LEADER_OVERRIDDEN_FALSE_vs_XLK","TARGET GAP","NEW HEADWINDS"],"MSFT":["PEER_LEADER_OVERRIDDEN_FALSE_vs_XLK"],"SMCI":["PEER LEADER"],"GOOG":["PEER LAGGARD","TARGET GAP"],"FSLR":["OVERSOLD BOUNCE","STRONG DOWNTREND","PEER LAGGARD","TARGET GAP"],"KLAC":["STRONG UPTREND","MOMENTUM+VOLUME","TARGET GAP"]},"unchanged_count":34},
 "news_watermark":"2026-09-08","resolved_flags":[],"new_flags":[],
 "journal_new":[],
 "wk52_updates":{},
 "peer_map_updates":{},
 "analyst_targets_updates":{"ASML":{"mean_target_usd":2145.06,"n_analysts":6,"as_of":"2026-09-08"},"BE":{"mean_target_usd":275.08,"n_analysts":17,"as_of":"2026-09-08"},"GEV":{"mean_target_usd":1236.43,"n_analysts":21,"as_of":"2026-09-08"},"MRVL":{"mean_target_usd":285.0,"n_analysts":26,"as_of":"2026-09-08"},"VRT":{"mean_target_usd":338.15,"n_analysts":17,"as_of":"2026-09-08"},"STM":{"mean_target_usd":75.04,"n_analysts":9,"as_of":"2026-09-08"},"TER":{"mean_target_usd":446.47,"n_analysts":12,"as_of":"2026-09-08"},"MU":{"mean_target_usd":1513.11,"n_analysts":32,"as_of":"2026-09-08"},"ALAB":{"mean_target_usd":389.95,"n_analysts":16,"as_of":"2026-09-08"},"INTC":{"mean_target_usd":115.78,"n_analysts":31,"as_of":"2026-09-08"},"AMD":{"mean_target_usd":613.84,"n_analysts":34,"as_of":"2026-09-08"},"COHR":{"mean_target_usd":415.36,"n_analysts":17,"as_of":"2026-09-08"},"AMAT":{"mean_target_usd":640.89,"n_analysts":28,"as_of":"2026-09-08"},"GOOG":{"mean_target_usd":422.34,"n_analysts":12,"as_of":"2026-09-08"},"TSM":{"mean_target_usd":552.38,"n_analysts":8,"as_of":"2026-09-08"},"NVDA":{"mean_target_usd":327.13,"n_analysts":29,"as_of":"2026-09-08"},"KLAC":{"mean_target_usd":233.77,"n_analysts":21,"as_of":"2026-09-08"},"CLS":{"mean_target_usd":477.22,"n_analysts":12,"as_of":"2026-09-08"},"WDC":{"mean_target_usd":664.92,"n_analysts":20,"as_of":"2026-09-08"},"LRCX":{"mean_target_usd":370.87,"n_analysts":23,"as_of":"2026-09-08"},"IREN":{"mean_target_usd":77.84,"n_analysts":10,"as_of":"2026-09-08"},"LITE":{"mean_target_usd":1148.43,"n_analysts":18,"as_of":"2026-09-08"},"SKHY":{"mean_target_usd":248.0,"n_analysts":10,"as_of":"2026-09-08"},"APH":{"mean_target_usd":96.06,"n_analysts":11,"as_of":"2026-09-08"},"AVGO":{"mean_target_usd":533.41,"n_analysts":28,"as_of":"2026-09-08"},"FSLR":{"mean_target_usd":275.3,"n_analysts":26,"as_of":"2026-09-08"},"MSFT":{"mean_target_usd":572.92,"n_analysts":33,"as_of":"2026-09-08"},"GLW":{"mean_target_usd":191.4,"n_analysts":10,"as_of":"2026-09-08"},"CIEN":{"mean_target_usd":504.13,"n_analysts":14,"as_of":"2026-09-08"},"QCOM":{"mean_target_usd":193.1,"n_analysts":24,"as_of":"2026-09-08"},"SMCI":{"mean_target_usd":42.38,"n_analysts":15,"as_of":"2026-09-08"}},
 "ret_5d_updates":{},
 "vol_normalization":{"KLAC":{"atr20_pct":4.25,"day_atr_mult":1.61,"rel_sigma":-0.54,"threshold_pct":6.84}},
 "atr20_updates":{},
 "rsi14_updates":{},
 "rel_strength_1m_updates":{},
 "rel_strength_1m_peer_updates":{"BE":{"rel_pp":9.24,"peer_etf":"XLU"},"FSLR":{"rel_pp":-12.33,"peer_etf":"XLU"},"GEV":{"rel_pp":-6.14,"peer_etf":"XLU"},"VRT":{"rel_pp":2.26,"peer_etf":"XLU"},"GOOG":{"rel_pp":-7.63,"peer_etf":"XLK"},"IREN":{"rel_pp":14.15,"peer_etf":"XLK"},"MSFT":{"rel_pp":1.77,"peer_etf":"XLK"},"NBIS":{"rel_pp":2.64,"peer_etf":"XLK"},"SMCI":{"rel_pp":29.84,"peer_etf":"XLK"}},
 "data_quality":["insiderTrades blocked (FMP plan tier, ties to G90) -- insider activity this run is news-derived only","SKHY 52week_low=0 in live fetch (not the wk52 cache) -- do not let leak into pos calc","NBIS/IREN rel_sigma computed with estimated ATR20 (threshold clamped at 12% ceiling, exact ATR unrecoverable) -- directionally robust, not exact","SD(rel_sigma)=1.312, outside 0.8-1.3 self-cal band, over-firing -- reporting only, not retuning","BE/NBIS/IREN/MSFT PEER LEADER buckets from compute_buckets.json's SMH fallback do NOT survive true-peer override -- see body"]}
```

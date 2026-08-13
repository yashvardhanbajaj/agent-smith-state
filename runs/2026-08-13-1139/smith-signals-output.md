# Signal Scan — 2026-08-13 pre-open (prices = Wed 08-12 close)

Note: 31 holdings scanned (META excluded — fully exited 08-12, cleared from signal_history). ATR-scaled per name; pos-based cutoffs stay absolute (self-normalizing by design).

## STRONG UPTREND
- TSM +1.68% — pos 0.805 crosses the 0.80 gate (NEW). Target $547.09, upside +21.6%. 6.6% of book.
- NBIS +34.14%, day_atr_mult 2.66x (34.1% vs 12.8% ATR, threshold clamped to 12.0) — pos 0.829, both triggers fire. Also MOMENTUM+VOLUME, volume 58.8M elevated. 4.0% of book, 1.85x over ATR cap, scale-out rung already tripped (see NBIS note below).
- ASML, FLTW — unchanged repeats (pos still ≥0.80, no new news/target move).
- DROPPED: AMZN — pos fell to 0.782 (was ≥0.80); no longer STRONG UPTREND, TARGET GAP/PEER LEADER still hold (below).

## BREAKOUT
- DRAM +7.68%, SKHY +9.01% — both closed exactly at 52wk high, pos=1.0. `[data-quality]` both show 52wk_low=0 (short trading history, not a real low), so pos arithmetic is unreliable, but live=52wk_high is a hard fact independent of that — BREAKOUT read stands. No analyst target for either (skip TARGET GAP).

## TARGET GAP (≥15% upside, mean target cited)
New: QCOM +16.3% ($194.77) · STM +24.2% ($71.52) · AMD +21.3% ($613.33, 54 analysts Strong Buy)
Unchanged repeats: NVDA +26.0% ($302.83, 8.6% of book) · ASML +16.7% ($2173.76) · TSM +21.6% ($547.09) · MU +39.3% ($1501.98) · MRVL +15.5% ($256.91, barely) · CIEN +23.6% ($565.71) · AVGO +21.2% ($527.88) · GEV +16.0% ($1238.25) · AMZN +17.7% ($324.94) · BABA +34.1% ($189.89) · CEG +20.4% ($349.96) · ORCL +38.0% ($247.17, still near 52wk lows)
Resolved (price ran up, gap closed below 15%): COHR +9.9% (was flagged) · TER +10.5% · AMAT +12.9% · LRCX +11.4% · INTC +11.5%. TXN +14.75% — just misses, watch.

## STRONG DOWNTREND
- ORCL — pos 0.168 (≤0.22), unchanged repeat. G58: 08-12 headline is layoffs/cash-burn commentary + "analysts say undervalued," not a results miss — don't read as thesis deterioration.

## OVERSOLD BOUNCE
- QCOM — pos 0.298 (≤0.3), upside 16.3% >15%, unchanged repeat.

## PEER-RELATIVE (rel_sigma vs peer ETF)
LEADER (σ≥+1.0): MSFT +24.0pp vs XLK, +3.35σ on 3.12% ATR — unchanged, dominant despite today's -2.26% (-0.72x ATR) pullback. · AMZN +8.28pp vs XLK, +1.17σ — unchanged. · BX +15.81pp vs XLF, +1.98σ — unchanged, strong. · NOW +20.18pp vs XLK, +1.55σ — NEW, leading peers even through today's -2.04% pullback.
Dropped below 1.0σ (were flagged, now inside noise): NVDA +7.4pp/0.83σ · BABA +5.23pp/0.69σ · CEG +6.98pp/0.93σ (borderline, fading not gone).
LAGGARD (σ≤-1.0): STM -15.48pp vs SMH, -1.61σ on 4.17% ATR — NEW. Ties to the provisional Analog/Industrial cluster (G62) and RSI 39.8; genuine underperformance, not noise.
Reversed: COHR was PEER LAGGARD, now +9.58pp/+0.39σ — no longer a laggard at all.

## NEW TAILWINDS
- NBIS — 2 distinct events: (1) Q2 beat, rev $582.3M +454% YoY, adj EBITDA +$236.2M (12-Aug); (2) >$1bn Reflection AI deal (per book context, not independently sourced from fetched news this run).
- NBIS specific ask: nothing in the news flow argues against booking the tripped rung — coverage is uniformly positive (no fresh negative catalyst, no analyst downgrade). The case for trimming here is mechanical (1.85x ATR cap, rung already tripped), not a thesis red flag — fundamentals genuinely improved, so a staged/partial trim reads better than an urgent full de-risk.
- Resolved: AVGO NEW TAILWINDS — no news dated after the 08-12 watermark, dropped.

## INSIDER ACTIVITY (news-derived, quick mode)
- BX — CLO John G. Finley reported a 45,000-share sale, 12-Aug, alongside a report Blackstone may scrap its $3bn "Project Eclipse." Single item, below the 2-item headwind threshold — watch only. BX NEW TAILWINDS from last run is dropped as a result.

## EARNINGS PROXIMITY
- None. No holding >5% weight reports within 7 trading days (MRVL reports 08-27 but is 3.9% weight, below the size gate).

## Specific asks
- CIEN +11.49% (G61): no dated news catalyst found (last items are stale — 15-Jul insider sale, 07-Jul AI PoC). day_atr_mult 1.43x (11.49% vs 8.05% ATR) — large but just under the vol-scaled 12.0% ceiling, so it misses the formal MOMENTUM+VOLUME cutoff. Most likely explanation: riding the same optical/datacenter rally as COHR (+8.24%) and the broader memory complex (SNDK +5.76%, MU +4.92%), not an idiosyncratic event. Cause still unresolved — flagging for next run.
- AVGO closed flat (-0.01%) after being up +1.45% intraday: no distinct new catalyst found. Last dated news is 11-Aug (AI revenue growth, positive). Reads as ordinary profit-taking into the close on a name still up sharply YTD, not news-driven.

## Unchanged repeats (suppressed, no material change)
ASML (STRONG UPTREND, TARGET GAP) · MU (TARGET GAP) · MRVL (TARGET GAP) · GEV (TARGET GAP) · FLTW (STRONG UPTREND) · AVGO, CIEN, BABA, CEG, AMZN, ORCL (TARGET GAP only, buckets unchanged even where other signals on the same ticker moved — see above).

## Still pending (stale, carried since before watermark)
- CEG: leverage-concern thesis WATCH, revisit pending (open_flag, unresolved).
- IREN standing re-entry interest (open_flag) — no new catalyst since 08-12, still a pullback/confirmed-catalyst trigger, not today's candle.
- 16-trade UNCAPTURED backlog (G55/G60) — unresolved, awaiting user rationale at next interactive run.

## Data quality
- DRAM/SKHY: 52wk_low=0 (short listing history, not a real low) inflates pos to exactly 1.0 — BREAKOUT call still valid since live=52wk_high is independent of that arithmetic.
- NBIS, SNDK: analyst_forecast empty this run — no target/upside computable, TARGET GAP skipped for both.
- CIEN cause (G61) still unresolved after this run — see specific-asks section.
- News watermark advanced to 2026-08-13.

```json
{"signal_history":{"changed":{"META":[],"TSM":["STRONG UPTREND","TARGET GAP"],"NBIS":["STRONG UPTREND","MOMENTUM+VOLUME","NEW TAILWINDS"],"AMZN":["TARGET GAP","PEER LEADER"],"QCOM":["OVERSOLD BOUNCE","TARGET GAP"],"STM":["TARGET GAP","PEER LAGGARD"],"AMD":["TARGET GAP"],"NOW":["PEER LEADER"],"COHR":[],"TER":[],"AMAT":[],"LRCX":[],"INTC":[],"NVDA":["TARGET GAP"],"BABA":["TARGET GAP"],"CEG":["TARGET GAP","REVERSAL - BUY WATCH"],"BX":["PEER LEADER"],"DRAM":["BREAKOUT"],"SKHY":["BREAKOUT"]},"unchanged_count":9},
 "news_watermark":"2026-08-13","resolved_flags":["META NEW HEADWINDS (fully exited 08-12)"],"new_flags":["STM PEER LAGGARD -1.61σ (G62 cluster)","CIEN +11.49% cause still unresolved (G61)"],
 "journal_new":[{"date":"2026-08-13","ticker":"NBIS","bucket":"MOMENTUM+VOLUME","price_at_flag":259.20,"analyst_target":null,"day_atr_mult":2.66,"rel_sigma":null,"normalized":true}],
 "peer_map_updates":{},
 "vol_normalization":{"NBIS":{"atr20_pct":12.82,"day_atr_mult":2.66,"rel_sigma":null,"threshold_pct":12.0},"CIEN":{"atr20_pct":8.05,"day_atr_mult":1.43,"rel_sigma":0.18,"threshold_pct":12.0},"MSFT":{"atr20_pct":3.12,"day_atr_mult":-0.72,"rel_sigma":3.35,"threshold_pct":4.68},"AMZN":{"atr20_pct":3.09,"day_atr_mult":-0.59,"rel_sigma":1.17,"threshold_pct":4.64},"NOW":{"atr20_pct":5.65,"day_atr_mult":-0.36,"rel_sigma":1.55,"threshold_pct":8.48},"BX":{"atr20_pct":3.47,"day_atr_mult":-0.15,"rel_sigma":1.98,"threshold_pct":5.21},"STM":{"atr20_pct":4.17,"day_atr_mult":-0.37,"rel_sigma":-1.61,"threshold_pct":6.26},"CEG":{"atr20_pct":3.27,"day_atr_mult":0.03,"rel_sigma":0.93,"threshold_pct":4.91},"NVDA":{"atr20_pct":3.88,"day_atr_mult":0.78,"rel_sigma":0.83,"threshold_pct":5.82},"TSM":{"atr20_pct":4.48,"day_atr_mult":0.38,"rel_sigma":0.07,"threshold_pct":6.72}},
 "data_quality":["DRAM/SKHY 52wk_low=0 (data gap, not real) -- pos pinned at 1.0 but live=52wk_high independently confirms BREAKOUT","NBIS/SNDK analyst_forecast empty -- no TARGET GAP computable this run","G61 CIEN +11.49% cause still unresolved -- no dated news catalyst found","AVGO flat close after +1.45% intraday -- no distinct catalyst, reads as profit-taking"]}
```

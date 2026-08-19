# smith-signals — 2026-08-19 pre-open (quick, ESCALATING)

Book: 28 names (35→28; ARM/SNDK/DRAM/IONQ/NBIS/ORCL/SKHY exited, not scanned). Tape: Tue 08-18 semis-specific
rout, SMH -4.09% vs SPX -0.69%/NDX -1.33%; Asian session extended it overnight (KOSPI -5.48%, Nikkei -3.22%,
TAIEX -1.58%); VIX only 15.84 (+4.28%) — an equity-specific unwind, not a vol-panic.

## THE HEADLINE: which moves actually broke their own volatility, not just the tape's
Of 28 names, only **3 cleared their own ATR20-scaled threshold** — everything else is the index falling, not
the name breaking:
- **FLTW -3.50%** = **-1.85x** its quiet 1.89% ATR (thresh 2.83%) — largest ATR-multiple move in the book. A
  Taiwan-broad ETF, no idiosyncratic catalyst; tracking TAIEX -1.58% overnight, not a stock-specific break.
- **STM -6.31%** = **-1.51x** its 4.17% ATR (thresh 6.25%, cleared by 0.06pp — marginal). No fresh (post-08-17)
  STM news; move is sector beta.
- **COHR -12.75%** = **-1.20x** its 10.67% ATR (thresh capped at 12.00%, cleared by 0.75pp). SanDisk-trap check:
  Q4 FY26 revenue **beat** ($2.0B+), but the stock fell on broader-semis profit-taking/rout, not a demand miss
  — "Coherent Reports Strong Earnings Amid Market Decline," 18 Aug 2026, INDmoney news feed.
25 of 28 names had double-digit-looking declines that are, in their own name's terms, an ordinary day — e.g.
MU -7.02% is only -0.75x its 9.38% ATR; CIEN -8.90% is -1.11x its 8.05% ATR (thresh capped 12%, not cleared).

## Core position/trend buckets
- **CEG STRONG DOWNTREND** — pos 0.208 (≤0.22 threshold, fires on position alone; day -4.09% = -1.25x its tight
  3.27% ATR but under the 4.91% threshold). 2.67% weight. Reversal of fortune: was REVERSAL-BUY WATCH + PEER
  LEADER as of 08-17; Q2 beat EPS but missed revenue with rising Calpine-acquisition debt concerns (06 Aug,
  stale but the last substantive news). Mean target $348.45 = 30.6% upside, but no fresh catalyst to lean on.
- **FLTW conflicted: STRONG UPTREND (pos 0.818) vs STRONG DOWNTREND (move, -1.85x ATR)** — 3.33% weight.
  Structurally still high in its 52-wk range but today's move is the sharpest ATR-multiple in the book. Not a
  stock break (it's a Taiwan index tracker); flag the conflict rather than force one label.
- **ASML STRONG UPTREND** — pos 0.847, unchanged bucket vs 08-17 but material move since: day -4.26% (-0.83x
  its 5.11% ATR, ordinary). 6.02% weight. Mean target $2176 = 17.2% upside.

## TARGET GAP — mechanical, book-wide, not a fresh buy signal
Analyst targets haven't caught down to Tuesday's rout: **25 of 28 holdings now show ≥15% upside**, only LRCX
(11.1%), NOW (14.8%), TER (10.1%, dust) fall short. This is stale numerators, not fresh conviction — treat as
one structural feature of a crashed book, not 25 individual signals. Repeats (already flagged 08-17, gap
mechanically widened by the price fall): TSM 24.4%, MU 37.4%, CIEN 28.3%, AMD 21.0%, STM 26.9%, NVDA 27.4%,
AVGO 28.0%, QCOM 17.8%, CLS 34.4%, BABA 32.4%, CEG 23.4%, AMZN 20.7%, NOW n/a, MSFT 15.4%, AMAT 19.4%, BE
24.0%, IREN 48.6%. **New crossings** (first time ≥15%, weight ≥2%): ASML 17.2% (6.0% wt), GEV 19.0% (6.7% wt),
MRVL 16.1% (2.9% wt), VRT 19.4% (2.7% wt), COHR 25.4% (3.1% wt), TXN 16.1% (2.7% wt).

## MOMENTUM+VOLUME
- **COHR** -12.75%, -1.20x ATR, catalyst = Q4 earnings reaction (beat, but semis-rout overshadowed it), volume
  8.77M elevated. 3.07% weight. Journal-worthy new flag.

## INSIDER ACTIVITY (news-derived, quick mode)
- **MRVL** — CEO share sale disclosed ahead of Q2 print (18 Aug 2026, INDmoney news). 2.88% weight, pos 0.576.
- **INTC** — CEO share purchase reported alongside the turnaround narrative (18 Aug 2026, INDmoney news).
  1.61% weight.

## EARNINGS PROXIMITY
- **NVDA** reports 2026-08-26 (5 trading days out), 11.01% weight — the book's largest position. pos 0.768,
  NOT run up into the print: today's -2.34% is the smallest ATR-multiple decline in the whole down-day cohort
  (-0.60x its 3.88% ATR), so NVDA is lagging the rout, not extending ahead of earnings. Mean target $302.83 =
  27.4% upside. Repeat of the 08-17 EARNINGS PROXIMITY flag — no material change, not re-journaled.

## NEW TAILWINDS / NEW HEADWINDS
None fired. Every ticker has at most one distinct post-08-17-dated news item (a Tue-08-18 session recap), none
reach the ≥2-distinct-event threshold. The rout itself is captured in the ATR-move analysis above, not as a
news-driven bucket.

## PEER-RELATIVE STRENGTH — SKIPPED
No `rel_strength_1m` or `rsi14` cache was present in this run's shared files (only atr20 was supplied), and
the orchestrator's cache policy for this quick run says read-as-is/refresh-nothing rather than live-compute.
PEER LEADER/LAGGARD omitted this run rather than violate that instruction; see data_quality.

## Unchanged repeats (bucket unchanged, no material trigger)
NVDA EARNINGS PROXIMITY; STM prior PEER LAGGARD flag from open_flags carried forward, uncomputable this run
(see data_quality).

## Still pending (from open_flags, unresolved)
- **IREN** — standing re-entry interest stays open; no new catalyst since 08-12, next trigger is a pullback
  or confirmed news, not today's index-wide candle (IREN itself only -0.58x its own ATR today).
- **BABA** — earnings-date conflict (08-20 FMP vs 08-28 web) still unresolved, 0.86% weight; needs a web check.
- **IONQ cluster decision** — now moot, IONQ was fully exited this run.
- **BX exit** — non-AI-capex diversifier cluster remains empty; AVGO alone still carries the XPV financing risk.

## data_quality
- rel_strength_1m / rsi14 caches absent from this run's provided files — PEER-RELATIVE bucket and the RSI
  overbought-staleness note (both instructed) could not be produced; flagging for the orchestrator to supply
  or refresh next run rather than fabricating values.
- day_chg_pct for CEG differs by 0.15pp between holdings.json (-3.94%) and the live get_us_stocks_details call
  (-4.09%); used the latter since it's paired with the 52wk-range data driving pos. Immaterial to bucket calls.
- TER is a 0.00273sh dust position (weight 0.00%) — excluded from all bucket output per orchestrator instruction.
- ATR20 cache is 7 days stale (as_of 2026-08-12) per policy; used as-is, thresholds computed on it are the
  best available, not re-derived.

```json
{"signal_history":{"changed":{"CEG":["STRONG DOWNTREND","TARGET GAP"],"FLTW":["STRONG UPTREND","STRONG DOWNTREND (move, conflicted)"],"ASML":["STRONG UPTREND","TARGET GAP"],"STM":["STRONG DOWNTREND"],"COHR":["STRONG DOWNTREND","MOMENTUM+VOLUME","TARGET GAP"],"GEV":["TARGET GAP"],"MRVL":["TARGET GAP","INSIDER ACTIVITY"],"VRT":["TARGET GAP"],"TXN":["TARGET GAP"],"INTC":["INSIDER ACTIVITY"],"NVDA":["TARGET GAP","EARNINGS PROXIMITY"]},"unchanged_count":17},
 "news_watermark":"2026-08-19","resolved_flags":["IONQ cluster decision (name exited)"],"new_flags":[],
 "journal_new":[
  {"date":"2026-08-19","ticker":"COHR","bucket":"MOMENTUM+VOLUME","price_at_flag":306.43,"analyst_target":410.76,"day_atr_mult":-1.195,"rel_sigma":null,"normalized":true},
  {"date":"2026-08-19","ticker":"ASML","bucket":"TARGET GAP","price_at_flag":1802.98,"analyst_target":2176.09,"day_atr_mult":-0.834,"rel_sigma":null,"normalized":true},
  {"date":"2026-08-19","ticker":"GEV","bucket":"TARGET GAP","price_at_flag":1004.53,"analyst_target":1239.46,"day_atr_mult":-1.010,"rel_sigma":null,"normalized":true},
  {"date":"2026-08-19","ticker":"MRVL","bucket":"TARGET GAP","price_at_flag":216.00,"analyst_target":257.29,"day_atr_mult":-0.792,"rel_sigma":null,"normalized":true},
  {"date":"2026-08-19","ticker":"VRT","bucket":"TARGET GAP","price_at_flag":272.54,"analyst_target":338.15,"day_atr_mult":-0.754,"rel_sigma":null,"normalized":true},
  {"date":"2026-08-19","ticker":"TXN","bucket":"TARGET GAP","price_at_flag":272.24,"analyst_target":324.45,"day_atr_mult":-1.125,"rel_sigma":null,"normalized":true},
  {"date":"2026-08-19","ticker":"COHR","bucket":"TARGET GAP","price_at_flag":306.43,"analyst_target":410.76,"day_atr_mult":-1.195,"rel_sigma":null,"normalized":true}
 ],
 "peer_map_updates":{},
 "vol_normalization":{
  "FLTW":{"atr20_pct":1.89,"day_atr_mult":-1.852,"rel_sigma":null,"threshold_pct":2.835},
  "STM":{"atr20_pct":4.17,"day_atr_mult":-1.513,"rel_sigma":null,"threshold_pct":6.255},
  "COHR":{"atr20_pct":10.67,"day_atr_mult":-1.195,"rel_sigma":null,"threshold_pct":12.0}
 },
 "data_quality":[
  "rel_strength_1m/rsi14 caches absent from provided shared files this run — PEER-RELATIVE bucket and RSI-staleness note omitted rather than fabricated",
  "CEG day_chg_pct: holdings.json -3.94% vs live get_us_stocks_details -4.09%, used latter (paired w/ 52wk data); immaterial to bucket calls",
  "TER is a 0.00273sh dust position, weight 0.00% — excluded from all bucket output",
  "ATR20 cache 7 days stale (as_of 2026-08-12) per orchestrator policy, used as-is"
 ]}
```

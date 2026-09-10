# smith-signals — 2026-09-10 QUICK sweep (post-close)

Book: 31 US holdings. VST (5sh, stop-loss 09-09 @$149.53) and FSLR (3sh, stop-loss 09-09 @$209.85)
correctly absent. KLAC (+2sh @$181.98) and QCOM (+2sh @$175.44) grew via buy 09-09.
Mechanical buckets (pos/day-move/peer-sigma/target-gap) are compute_buckets.json's, consumed not
recomputed. News window treated as "since watermark" = dated 2026-09-07 through 2026-09-09 (no
2026-09-10-dated articles existed in this post-close US-session pull — see data_quality #1).

## Standout of the run

**META — 4 buckets resolved in one session.** STRONG DOWNTREND / PEER LAGGARD / NEW HEADWINDS /
OVERSOLD BOUNCE all cleared as of today's **+6.55%** pop ($653.69) on the Muse AI-agent launch +
a favorable lawsuit settlement (09-09, 1 event — INDmoney news feed). Only TARGET GAP persists
(target $754.77, +13.4% upside). 1.55% position. This is the reversal the open OVERSOLD BOUNCE
journal entries (08-03, 08-06, 08-20 — mixed grades, bucket-wide 66.7% hit rate n=3/30d, n=6/7d)
were waiting on.

## BREAKOUT / STRONG UPTREND

- **SKHY** — BREAKOUT (pos 1.028, above cached 52wk high) + STRONG UPTREND + PEER LEADER (+1.06σ,
  +13.82pp vs SMH) + **NEW TAILWINDS** (2 distinct events: "SK Hynix Gains Momentum Amid Positive
  Analyst Ratings" — 2026-09-09 — INDmoney feed; "SK Hynix Gains Analyst Confidence Amid Tight
  Market" (BofA bullish on tight HBM supply/pricing power) — 2026-09-08 — INDmoney feed). +7.05%
  today ($198.63), day_atr_mult 1.25× its 5.66% ATR — the move is real but the STRONG UPTREND tag
  fired off the pos leg (breakout), not the magnitude leg. 2.34% position, target $248, upside
  24.9% — still room despite the extension. OVERBOUGHT PULLBACK? judged **not confirmed**: no
  negatives found, upside still healthy. [Live API 52week_low still returns 0 for SKHY — same
  artifact flagged 2026-09-06; compute_buckets' cached wk52 clearly holds the real number since
  pos>1 is a genuine breakout, not the div-by-zero fake. See data_quality #3.]
- **TSM** — newly STRONG UPTREND (pos 0.813) + **NEW TAILWINDS** (3 distinct events: "TSMC
  Advances EUV Technology and Insider Purchases" — 09-09; "Taiwan Semiconductor Advances Amid AI
  Demand and New Initiatives" — 09-08; "TSMC Maintains Market Share Amid Soaring Chip Demand" —
  09-07, all INDmoney feed, all positive) + TARGET GAP unchanged. 4.14% position, target $552.38,
  upside 27.1%. Day move only -0.83% (0.34× its 2.42% ATR) — the uptrend tag is a pos-leg call,
  not today's candle. Insider-purchase mention (09-09) also feeds INSIDER ACTIVITY, unchanged from
  the open 08-24 journal entry.
- **NVDA** — unchanged repeat: STRONG UPTREND + TARGET GAP (pos 0.82, target $327.13, upside
  46.3%). 2.66% position. Journal grade **A** on TARGET GAP (100%, n=1, low-confidence). No fresh
  news past 09-09 (1 item only, not enough for a tailwind bucket).
- **AMD** — newly STRONG UPTREND (pos 0.852, wasn't flagged 09-09) + TARGET GAP + NEW TAILWINDS
  unchanged (no items past 09-08). 3.72% position, target $613.84, upside 17.9%. OVERBOUGHT
  PULLBACK? judged **not confirmed** — no negatives, upside not compressed.
- **LITE** — PEER LEADER (+2.37σ, +45.09pp vs SMH — genuinely leading, not riding the sector) +
  newly STRONG UPTREND (pos 0.893) + newly TARGET GAP (target $1148.43, upside 13.9–16.6%). NEW
  TAILWINDS from 09-09 **resolved** (no fresh coverage since 09-01). 2.35% position. OVERBOUGHT
  PULLBACK? judged **not confirmed**. Journal grade A on TARGET GAP (n=1, 100%).

## PEER LEADER (unchanged repeats unless noted)

- **MRVL** +2.53σ (+34.12pp vs SMH). 5.04% position, target $285, upside 21.2% (grade A n=1).
  NEW TAILWINDS story (analyst coverage 09-09, AI/partnerships 09-08) is a **continuation** of the
  multi-week Marvell rally, not a fresh catalyst — not re-flagged. INSIDER ACTIVITY unchanged
  (Google-partnership-era insider selling, last dated 08-19, no new filings this run).
- **MU** +1.02σ (+12.93pp vs SMH). 4.89% position, target $1513.11, upside 47.5% (largest in
  book). NEW TAILWINDS unchanged (surge story 09-08/09-09, already flagged 09-09). Journal grade
  **F** on TARGET GAP and MOMENTUM+VOLUME (0% hit, n=1–2, low-confidence/early).
- **LRCX** +1.15σ (+12.6pp vs SMH). 2.26% position, target $370.87, upside 17.4%. Newly shows
  TARGET GAP this run; NEW TAILWINDS (dividend hike/R&D story) suppressed — stale since 09-08.
  Journal PEER LEADER entry (08-31) worked at 7d (+4.6%).
- **SMCI** +1.87σ (+29.84pp vs XLK). 0.92% position, target $42.38, upside only 9.2% — most
  compressed target gap in the book after its run. No fresh news (1 item, 09-08, not enough).
- (LITE, SKHY — see above.)

## PEER LAGGARD (unchanged unless noted)

- **AVGO** -1.62σ (-13.31pp vs SMH) — **widest laggard reading in the book**, despite today's
  bullish "$230B AI revenue by 2028" headline (09-09, positive) — classic headline/price
  divergence, not a tailwind bucket (only 1 clear positive event in window). 1.73% position,
  target $533.41, upside 46.6% (largest gap in book). Journal grade F on TARGET GAP (0%, n=1).
- **GOOG** -1.53σ (-7.63pp vs XLK). 4.70% position, target $422.34, upside 28.5%. No fresh news.
- **CLS** -1.33σ (-17.0pp vs SMH). 3.17% position, target $477.22, upside 43.3%. Worst-graded name
  in the book on these buckets: journal grade F on both TARGET GAP and MOMENTUM+VOLUME (0%, n=1-2).
- **QCOM** -1.17σ (-7.8pp vs SMH) unchanged, but **NEW TAILWINDS fires fresh**: "Qualcomm Expands
  AI Chip Partnerships, Price Target Raised" (RBC) — 09-09 — INDmoney feed; "Qualcomm Partners
  with AWS for AI Chip Development" ($5B revenue-by-FY27 target) — 09-08 — INDmoney feed. Catalyst
  news hasn't moved the peer-relative reading yet. 2.10% position — **just bought +2sh @$175.44 on
  09-09**, now $176.40 (~flat). Target $193.9, upside 9%.

## TARGET GAP only (unchanged unless noted)

- **GEV** — 9.07% position (largest), target $1236.43, upside 30%. NEW TAILWINDS **resolved** (no
  fresh coverage since 09-03) — GE Vernova backlog/JV story still pending, not new.
- **ASML** — target $2165.70 (live)/$2145.06 (cached), upside ~20-24%. 5.15% position. **NEW
  TAILWINDS newly fires**: "ASML Advances Semiconductor Tech Amid Market Challenges" (TSMC/Intel
  collabs, notes upcoming earnings) — 09-09 — INDmoney feed; "ASML Secures Major Deals and Expands
  Capacity" — 09-08 — INDmoney feed.
- **TER** — target $446.47, upside 14.1%. 4.56% position. No fresh news. Journal grade F on
  MOMENTUM+VOLUME (0%, n=1).
- **VRT** — target $338.15, upside 22.3%. 4.38% position. **See urgent flag below.**
- **STM** — target $75.04, upside 31.3%. 4.27% position. PEER LAGGARD from 08-13 has resolved
  (rel_sigma now -0.9, above the -1.0 threshold). No fresh news.
- **COHR** — target $415.36, upside 26.9-37.2%. 3.60% position. No fresh news. Journal grade F
  (0%, n=1) — history of failing to hold this bucket.
- **ALAB** — target $389.95, upside 22.9-30.2%. 3.56% position. No fresh news (last item 08-05).
- **KLAC** — target $233.77, upside 21.8-28.1%. 3.48% position (grew +2sh @$181.98 on 09-09, now
  $182.91 — essentially flat). **STRONG UPTREND and MOMENTUM+VOLUME both resolved** since 09-09
  (day -3.21% today, pos down to 0.424) — pulled back the day after the add. No fresh news.
- **AMAT** — target $640.89, upside 26.8-36.7%. 3.36% position. **NEW TAILWINDS newly fires**: 2
  distinct positive events — "Applied Materials Strengthens Semiconductor Portfolio Amid AI
  Demand" — 09-09 — INDmoney feed; "Analyst Upgrades AMAT with Strong Buy Rating" — 09-07 —
  INDmoney feed.
- **APH** — target $99.15/$96.06, upside 17.9-18.4%. 2.90% position. STRONG UPTREND from 09-09 has
  **resolved** (pos now 0.761); TARGET GAP newly appears in its place. No fresh news.
- **NBIS** — target $280.00 (cached; live fetch returned null this run — data_quality #4), upside
  18.3%. 2.82% position. No fresh news past 08-31.
- **WDC** — target $664.92, upside 27.5-38.0%. 2.29% position. INSIDER ACTIVITY unchanged (director
  sold 5,600sh + CEO trust transfer 112,500sh, dated 09-02 — no new filings this run). One 09-09
  item flags valuation scrutiny (neutral) — not enough for a headwind bucket.
- **MSFT** — newly shows TARGET GAP (target $572.92, upside 14.2-16.3%). 1.17% position. AI
  training-data lawsuits (Seattle Times, Newsday — 09-08, negative) are a watch item, not yet a
  2-event headwind.
- **CIEN** — target $504.13, upside 33-49%. 0.01% position — effectively a dust holding, signal is
  moot at this size.

## Urgent — flag, not a fired bucket

**VRT -9.61% today** ($262.89 live), day_atr_mult **-2.2×** its 4.37% ATR — a genuinely large move
that compute_buckets.json (as_of 2026-09-10) does **not** reflect: it shows only TARGET GAP, pos
0.547, no STRONG DOWNTREND. No catalyst news found in this run's feed (freshest VRT item is 09-08,
positive — "Vertiv Holdings Targets Growth Amid AI Demand"). This reads like a live-price/cache
timing mismatch rather than a resolved non-event. 4.38% position — worth a direct price check
before the next action on this name. See data_quality #2.

## Unchanged repeats (no material change vs signal_history)

MRVL (PEER LEADER, TARGET GAP, INSIDER ACTIVITY), MU (PEER LEADER, TARGET GAP, NEW TAILWINDS),
GOOG (PEER LAGGARD, TARGET GAP), TER (TARGET GAP), VRT (TARGET GAP), STM (TARGET GAP), COHR
(TARGET GAP), ALAB (TARGET GAP), CLS (PEER LAGGARD, TARGET GAP), NVDA (STRONG UPTREND, TARGET
GAP), WDC (TARGET GAP, INSIDER ACTIVITY), AVGO (PEER LAGGARD, TARGET GAP), SMCI (PEER LEADER),
CIEN (TARGET GAP), BE (nothing fired, unchanged).

## Still pending (persisting older stories, one clause each)

- GEV: backlog/JV growth narrative (09-03) — no fresh developments.
- LRCX: dividend hike/R&D-expansion story (09-08) — continuing, not new.
- GLW: Verizon optical-fiber supply deal (09-08) — already flagged, still developing; GLW's own
  NEW TAILWINDS has resolved (no bucket fires for GLW this run).
- WDC: insider sales filing (09-02) — no new filings.
- COHR: mixed Q4 earnings reaction (mid-Aug) — still working through the pullback.
- MSFT: AI-training-data lawsuits (09-08) — watch item.

## data_quality

1. News-freshness convention: news_watermark=2026-09-09 with no 2026-09-10-dated articles in this
   post-close pull; treated 2026-09-07 through 2026-09-09 as "since last run" for TAILWINDS/
   HEADWINDS counting.
2. VRT: live price feed shows -9.61% today vs compute_buckets.json showing no STRONG DOWNTREND —
   likely a cache/live timing mismatch, not a resolved event. 4.38% position, verify before acting.
3. SKHY: live get_us_stocks_details still returns 52week_low=0 (same artifact as 2026-09-06);
   compute_buckets' cached wk52 is evidently correct (pos=1.028 is a genuine breakout).
4. NBIS: analyst_forecast.target_price came back null in this run's live fetch; used
   compute_buckets.json's cached figure (280.00, 18.3% upside) instead.
5. No confirmed earnings date within 7 days found for the three >5%-weight holdings (GEV 9.07%,
   ASML 5.15%, MRVL 5.04%); ASML coverage references "upcoming earnings" without a date.
6. stale_peer_fallback_tickers and unnormalized_tickers both empty this run; ATR/RSI/rel-strength
   caches within TTL — no refresh or peer-ETF refetch performed. 7 tool calls used, well under
   budget.

## JSON tail

```json
{"signal_history":{"changed":{
  "GEV":["TARGET GAP"],
  "ASML":["NEW TAILWINDS","TARGET GAP"],
  "TSM":["STRONG UPTREND","NEW TAILWINDS","TARGET GAP"],
  "AMD":["STRONG UPTREND","NEW TAILWINDS","TARGET GAP"],
  "KLAC":["TARGET GAP"],
  "AMAT":["NEW TAILWINDS","TARGET GAP"],
  "APH":["TARGET GAP"],
  "NBIS":["TARGET GAP"],
  "INTC":["NEW TAILWINDS"],
  "LITE":["PEER LEADER","STRONG UPTREND","TARGET GAP"],
  "SKHY":["BREAKOUT","STRONG UPTREND","PEER LEADER","NEW TAILWINDS","TARGET GAP"],
  "LRCX":["PEER LEADER","TARGET GAP"],
  "QCOM":["PEER LAGGARD","NEW TAILWINDS"],
  "META":["TARGET GAP"],
  "GLW":[],
  "MSFT":["TARGET GAP"]
 },"unchanged_count":15},
 "news_watermark":"2026-09-10",
 "resolved_flags":["STM PEER LAGGARD (rel_sigma now -0.9, above -1.0 threshold)","KLAC STRONG UPTREND + MOMENTUM+VOLUME (pulled back to pos 0.424 day after the 09-09 add)","APH STRONG UPTREND (pos now 0.761)","META STRONG DOWNTREND + PEER LAGGARD + NEW HEADWINDS + OVERSOLD BOUNCE (all cleared on today's +6.55% Muse-launch/settlement pop)","GLW NEW TAILWINDS (Verizon deal now stale, no fresh coverage)","GEV NEW TAILWINDS (backlog/JV story stale since 09-03)","LRCX NEW TAILWINDS (dividend/R&D story stale since 09-08)"],
 "new_flags":["ASML NEW TAILWINDS","TSM STRONG UPTREND + NEW TAILWINDS","AMD STRONG UPTREND","AMAT NEW TAILWINDS","INTC NEW TAILWINDS (replaces resolved MOMENTUM+VOLUME/POLICY IMPACT)","SKHY BREAKOUT + NEW TAILWINDS","QCOM NEW TAILWINDS","LITE STRONG UPTREND + TARGET GAP","NBIS TARGET GAP","MSFT TARGET GAP","APH TARGET GAP","LRCX TARGET GAP"],
 "journal_new":[],
 "wk52_updates":{},
 "peer_map_updates":{},
 "analyst_targets_updates":{
   "ASML":{"mean_target_usd":2165.70,"n_analysts":6,"as_of":"2026-09-10"},
   "BE":{"mean_target_usd":275.08,"n_analysts":17,"as_of":"2026-09-10"},
   "GEV":{"mean_target_usd":1236.43,"n_analysts":21,"as_of":"2026-09-10"},
   "GOOG":{"mean_target_usd":422.34,"n_analysts":12,"as_of":"2026-09-10"},
   "MRVL":{"mean_target_usd":285.00,"n_analysts":26,"as_of":"2026-09-10"},
   "MU":{"mean_target_usd":1513.11,"n_analysts":32,"as_of":"2026-09-10"},
   "STM":{"mean_target_usd":75.04,"n_analysts":9,"as_of":"2026-09-10"},
   "TER":{"mean_target_usd":446.47,"n_analysts":12,"as_of":"2026-09-10"},
   "TSM":{"mean_target_usd":552.38,"n_analysts":8,"as_of":"2026-09-10"},
   "VRT":{"mean_target_usd":338.15,"n_analysts":17,"as_of":"2026-09-10"},
   "ALAB":{"mean_target_usd":389.95,"n_analysts":16,"as_of":"2026-09-10"},
   "AMAT":{"mean_target_usd":640.89,"n_analysts":28,"as_of":"2026-09-10"},
   "AMD":{"mean_target_usd":613.84,"n_analysts":34,"as_of":"2026-09-10"},
   "APH":{"mean_target_usd":99.15,"n_analysts":11,"as_of":"2026-09-10"},
   "CLS":{"mean_target_usd":477.22,"n_analysts":13,"as_of":"2026-09-10"},
   "COHR":{"mean_target_usd":415.36,"n_analysts":17,"as_of":"2026-09-10"},
   "INTC":{"mean_target_usd":115.88,"n_analysts":31,"as_of":"2026-09-10"},
   "KLAC":{"mean_target_usd":233.77,"n_analysts":21,"as_of":"2026-09-10"},
   "NVDA":{"mean_target_usd":327.13,"n_analysts":29,"as_of":"2026-09-10"},
   "LITE":{"mean_target_usd":1148.43,"n_analysts":18,"as_of":"2026-09-10"},
   "LRCX":{"mean_target_usd":370.87,"n_analysts":24,"as_of":"2026-09-10"},
   "QCOM":{"mean_target_usd":193.90,"n_analysts":24,"as_of":"2026-09-10"},
   "WDC":{"mean_target_usd":664.92,"n_analysts":19,"as_of":"2026-09-10"},
   "AVGO":{"mean_target_usd":533.41,"n_analysts":28,"as_of":"2026-09-10"},
   "GLW":{"mean_target_usd":191.40,"n_analysts":10,"as_of":"2026-09-10"},
   "META":{"mean_target_usd":754.77,"n_analysts":42,"as_of":"2026-09-10"},
   "MSFT":{"mean_target_usd":572.92,"n_analysts":34,"as_of":"2026-09-10"},
   "SMCI":{"mean_target_usd":42.38,"n_analysts":16,"as_of":"2026-09-10"},
   "CIEN":{"mean_target_usd":504.13,"n_analysts":14,"as_of":"2026-09-10"},
   "SKHY":{"mean_target_usd":248.00,"n_analysts":10,"as_of":"2026-09-10"}
 },
 "ret_5d_updates":{},
 "vol_normalization":{
   "TSM":{"atr20_pct":2.42,"day_atr_mult":-0.34,"rel_sigma":0.07,"threshold_pct":3.63},
   "NVDA":{"atr20_pct":4.36,"day_atr_mult":-0.21,"rel_sigma":0.63,"threshold_pct":6.54},
   "AMD":{"atr20_pct":4.02,"day_atr_mult":0.76,"rel_sigma":-0.29,"threshold_pct":6.03},
   "LITE":{"atr20_pct":8.28,"day_atr_mult":0.13,"rel_sigma":2.37,"threshold_pct":12.0},
   "SKHY":{"atr20_pct":5.66,"day_atr_mult":1.25,"rel_sigma":1.06,"threshold_pct":8.49},
   "MRVL":{"atr20_pct":5.86,"day_atr_mult":0.73,"rel_sigma":2.53,"threshold_pct":8.79},
   "MU":{"atr20_pct":5.5,"day_atr_mult":0.50,"rel_sigma":1.02,"threshold_pct":8.25},
   "LRCX":{"atr20_pct":4.77,"day_atr_mult":-0.30,"rel_sigma":1.15,"threshold_pct":7.16},
   "SMCI":{"atr20_pct":6.93,"day_atr_mult":-0.48,"rel_sigma":1.87,"threshold_pct":10.4},
   "GOOG":{"atr20_pct":3.34,"day_atr_mult":-0.63,"rel_sigma":-1.53,"threshold_pct":5.01},
   "AVGO":{"atr20_pct":3.57,"day_atr_mult":-0.32,"rel_sigma":-1.62,"threshold_pct":5.36},
   "CLS":{"atr20_pct":5.57,"day_atr_mult":0.20,"rel_sigma":-1.33,"threshold_pct":8.36},
   "QCOM":{"atr20_pct":2.91,"day_atr_mult":0.46,"rel_sigma":-1.17,"threshold_pct":4.37},
   "VRT":{"atr20_pct":4.37,"day_atr_mult":-2.20,"rel_sigma":0.22,"threshold_pct":6.56}
 },
 "atr20_updates":{},
 "rsi14_updates":{},
 "rel_strength_1m_updates":{},
 "rel_strength_1m_peer_updates":{},
 "data_quality":[
   "News-freshness convention: news_watermark=2026-09-09 with no 2026-09-10-dated articles in this post-close pull; treated 2026-09-07 through 2026-09-09 as since-last-run for TAILWINDS/HEADWINDS counting.",
   "VRT: live price feed shows -9.61% today vs compute_buckets.json (as_of 09-10) showing no STRONG DOWNTREND and pos=0.547 -- likely a cache/live timing mismatch, not a resolved event. 4.38% position, verify live price before acting.",
   "SKHY: live get_us_stocks_details still returns 52week_low=0 (same artifact flagged 2026-09-06); compute_buckets' cached wk52 is evidently correct (pos=1.028 is a genuine breakout, not the div-by-zero artifact).",
   "NBIS: analyst_forecast.target_price came back null in this run's live fetch; used compute_buckets.json's cached figure (280.00, 18.3% upside) instead.",
   "No confirmed earnings date within 7 days found for the three >5%-weight holdings (GEV 9.07%, ASML 5.15%, MRVL 5.04%); ASML coverage references upcoming earnings without a date.",
   "stale_peer_fallback_tickers and unnormalized_tickers both empty this run; ATR/RSI/rel-strength caches within TTL -- no refresh or peer-ETF refetch performed. 7 tool calls used, well under the 15-call budget."
 ]}
```

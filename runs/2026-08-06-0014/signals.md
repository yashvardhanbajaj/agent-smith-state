# Signal Scan — 2026-08-06 (quick mode, intraday) | watermark: 2026-08-03

## STRONG DOWNTREND (pos-based)
- ORCL — pos 0.13 (52w $114.50–$345.72), recently added (4→6sh) — 2.19% of book — target $248.15, +41.9% upside. No post-watermark news.
- MP — pos 0.16 (52w $37.81–$100.25) — NEW position, 1.21% of book — target $77.78, +38.7% upside. China export-control overhang still pending (pre-watermark).
- CEG — pos 0.20 (52w $228.63–$412.70) — 2.01% of book — target $352.86, +24.8% upside. Journal already has REVERSAL–BUY WATCH open since 07-31 (unscored). Also PEER LEADER below.

## STRONG UPTREND (pos-based)
- AMZN — pos 0.83 (52w $196–$287.20), day -2.25% (pullback off highs) — 1.37% of book — target $321.95, +15.7% upside. Extended despite red print; also PEER LEADER.

## NEW TAILWINDS (≥2 positive items post-watermark)
- NVDA — SpaceX AI-chip partnership (08-04, 08-05) — 8.39% of book, largest holding — target $302.83, +26.8% upside. Day +4.64% = 1.2× its 3.88% ATR. Also PEER LEADER.
- MU — AI-demand/strong-performance items (08-04, 08-05) — 6.95% of book — target $1522.26, +39.7% upside.
- AVGO — China-risk-resilient growth + Google partnership (08-04, 08-05) — 5.31% of book — target $527.88, +20.2% upside. Also PEER LEADER.
- TSM — production expansion + earnings-beat/insider-confidence items (08-04, 08-05) — 5.25% of book — target $540.20, +22.9% upside.

## INSIDER ACTIVITY (news-derived, quick mode)
- TSM — "Insider Activity" cited in the 08-04 earnings-beat headline (positive framing) — 5.25% of book.
- Still pending: CIEN execs "plan significant stock sales" (07-15, pre-watermark, unresolved) — 1.06% position.

## EARNINGS PROXIMITY
- QBTS — earnings on/around 2026-08-06 per orchestrator flag; get_earnings_calendar returned no data for the window, so date is UNCONFIRMED independently. Binary event on a 1.35% position, pos 0.25 (52w $12.75–$46.75), target $37.05, +42.4% upside — high optionality, high risk.
- SNDK — 08-04 news reads "ahead of Strong Q4 Earnings," date unconfirmed — 7.12% of book (largest earnings-proximity exposure). NOT run up into the print (1m return -19.6%, day -1.54%), pos 0.59. No analyst target available (data gap).

## PEER-RELATIVE STRENGTH
- NVDA +13.3% 1m vs SMH -4.7% (+2.03σ on 3.88% ATR) — genuinely leading, not riding the sector.
- AVGO +12.7% 1m vs SMH -4.7% (+1.83σ) — leading.
- CEG +7.8% 1m vs XLU -3.8% (+1.55σ) — leading despite the STRONG DOWNTREND price position; power-infra pairing, correlation solid.
- AMZN +11.1% 1m vs XLK +2.2% (+1.26σ) — leading.
- MP -10.1% 1m vs XLP +1.4% (-11.5pp, [unnormalized] — no ATR cache) — PEER LAGGARD by legacy ±8pp threshold. Peer correlation assumption weak for this mapping (rare-earth miner vs consumer-staples ETF).

## TARGET GAP (≥15%, mean target cited)
Book-wide target-gap expansion following the semis pullback (SMH -4.7% 1m) — read this as a sector-level signal, not 20 individual buy calls.
- Extreme (>25%): ORCL +41.9%, QBTS +42.4%, MP +38.7%, MU +39.7%, BABA +32.4%, NVDA +26.8%, CIEN +26.4%, CEG +24.8%.
- Moderate (15–25%): AVGO +20.2%, TSM +22.9%, ASML +20.7%, CLS +21.7%, MKSI +23.1%, GLW +18.0%, VRT +17.4%, MRVL +16.8%, NOW +16.6%, QCOM +19.6%, AMZN +15.7%, AMD +15.7%, GEV +15.8%, GOOGL +15.1%, LRCX +15.2%.
- No target data (excluded): SNDK, EWY, NBIS, DRAM.

## OVERSOLD BOUNCE (pos≤0.3 + positive news/upgrade/upside>15%)
- QCOM — pos 0.26, upside 19.6% — mechanical trigger only; underlying news net negative (mixed Q3, revenue-challenge headlines, all pre-watermark) — value-trap risk, not a clean bounce. 1.99% of book.
- META — pos 0.23, upside 24.1% — mechanical trigger; news mixed (AI-spend concerns), no post-watermark catalyst. 1.47% of book.
- ORCL — pos 0.13, upside 41.9% — extreme gap on a recent add (4→6sh); no post-watermark catalyst either. 2.19% of book.

## Still pending (no post-watermark news, prior framing carries forward)
- MP: China export-control overhang (06-22/06-23) unresolved.
- QCOM: mixed Q3/revenue-challenge narrative (07-26–07-30) persists.
- TER, COHR, VRT, AMAT, LRCX, ASML, GEV, CLS, BE, NBIS, CIEN: no news dated after watermark.
- MKSI: news feed returned only stale Feb-2026 items despite an active position — likely a feed gap.

## AMD / GOOGL context (explicit check)
- GOOGL -4.08% today despite 08-04 "Strong Earnings, Raises Capex Guidance" headline; 08-05 headline reads "Faces Challenges Amid AI Restructuring" — raised capex guidance is the named cause (margin-fear reaction), not a results miss.
- AMD -5.86% today despite 08-04 "Reports Strong Q2 Earnings" headline — classic sell-the-news pattern; no explicit negative headline captured in-feed — likely guidance/outlook-driven, flagged as a data gap. Journal has AMD EARNINGS PROXIMITY open since 07-31, unscored.

## Journal — new actionable flags today
QBTS EARNINGS PROXIMITY, ORCL OVERSOLD BOUNCE, META OVERSOLD BOUNCE, QCOM OVERSOLD BOUNCE (see JSON tail for prices/targets).

```json
{"signal_history":{"changed":{
  "ORCL":["STRONG DOWNTREND","TARGET GAP","OVERSOLD BOUNCE"],
  "MP":["STRONG DOWNTREND","TARGET GAP","PEER LAGGARD"],
  "CEG":["STRONG DOWNTREND","TARGET GAP","PEER LEADER"],
  "AMZN":["STRONG UPTREND","TARGET GAP","PEER LEADER"],
  "NVDA":["NEW TAILWINDS","TARGET GAP","PEER LEADER"],
  "MU":["NEW TAILWINDS","TARGET GAP"],
  "AVGO":["NEW TAILWINDS","TARGET GAP","PEER LEADER"],
  "TSM":["NEW TAILWINDS","TARGET GAP","INSIDER ACTIVITY"],
  "QBTS":["EARNINGS PROXIMITY","TARGET GAP"],
  "SNDK":["EARNINGS PROXIMITY"],
  "QCOM":["OVERSOLD BOUNCE","TARGET GAP"],
  "META":["OVERSOLD BOUNCE","TARGET GAP"],
  "AMD":["TARGET GAP"],"GOOGL":["TARGET GAP"],"LRCX":["TARGET GAP"],"MRVL":["TARGET GAP"],
  "VRT":["TARGET GAP"],"ASML":["TARGET GAP"],"BABA":["TARGET GAP"],"CLS":["TARGET GAP"],
  "GEV":["TARGET GAP"],"GLW":["TARGET GAP"],"NOW":["TARGET GAP"],"MKSI":["TARGET GAP"],"CIEN":["TARGET GAP"]
 },"unchanged_count":0},
 "news_watermark":"2026-08-06","resolved_flags":[],"new_flags":[],
 "journal_new":[
  {"date":"2026-08-06","ticker":"QBTS","bucket":"EARNINGS PROXIMITY","price_at_flag":21.33,"analyst_target":37.05,"day_atr_mult":-0.286,"rel_sigma":null,"normalized":true},
  {"date":"2026-08-06","ticker":"ORCL","bucket":"OVERSOLD BOUNCE","price_at_flag":144.22,"analyst_target":248.15,"day_atr_mult":-0.166,"rel_sigma":-0.146,"normalized":true},
  {"date":"2026-08-06","ticker":"META","bucket":"OVERSOLD BOUNCE","price_at_flag":583.34,"analyst_target":768.58,"day_atr_mult":-0.165,"rel_sigma":-0.456,"normalized":true},
  {"date":"2026-08-06","ticker":"QCOM","bucket":"OVERSOLD BOUNCE","price_at_flag":157.90,"analyst_target":196.27,"day_atr_mult":-0.545,"rel_sigma":-0.855,"normalized":true}
 ],
 "peer_map_updates":{"LRCX":{"peer_etf":"SMH"},"MP":{"peer_etf":"XLP"},"NOW":{"peer_etf":"XLK"}},
 "vol_normalization":{
  "NVDA":{"atr20_pct":3.88,"day_atr_mult":1.196,"rel_sigma":2.028,"threshold_pct":5.82},
  "AVGO":{"atr20_pct":4.14,"day_atr_mult":0.167,"rel_sigma":1.827,"threshold_pct":6.21},
  "CEG":{"atr20_pct":3.27,"day_atr_mult":-0.190,"rel_sigma":1.549,"threshold_pct":4.905},
  "AMZN":{"atr20_pct":3.09,"day_atr_mult":-0.728,"rel_sigma":1.260,"threshold_pct":4.635},
  "MP":{"atr20_pct":null,"day_atr_mult":null,"rel_sigma":null,"threshold_pct":8.0}
 },
 "data_quality":[
  "DRAM 52wk_low returned 0 (bad data) -> pos guardrail set to 0.5, not divided by zero",
  "MP & NOW lack ATR20 cache entries; MP's PEER LAGGARD flag used legacy absolute +/-8pp threshold [unnormalized]; both peer_etf mappings (MP->XLP, NOW->XLK) are proxy fits, weak correlation for MP specifically",
  "QBTS earnings date unconfirmed -- get_earnings_calendar returned empty for the Aug4-13 window; relying on orchestrator's flag (on/around 08-06), not independently verified",
  "SNDK/EWY/NBIS/DRAM have no analyst target_price data -- TARGET GAP/upside checks skipped for these four",
  "MKSI news feed returned only stale Feb-2026 items despite an active position -- likely a feed gap, not 'no news'",
  "signal_history map was not included in this run's input slice -- repeat-suppression skipped, all current flags reported in full"
 ]}
```

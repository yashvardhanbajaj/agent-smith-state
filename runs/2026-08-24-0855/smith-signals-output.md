# smith-signals — 2026-08-24 QUICK (pre-open, gate=AMBIGUOUS)

## STRONG DOWNTREND / MOMENTUM+VOLUME
- BABA -8.57% day (2.61x its 3.28% ATR) — post-earnings reaction: "Alibaba Reports Mixed Earnings Amid AI Investment Surge" 2026-08-20 (negative). Resolves the open_flags earnings-date conflict: FMP's 08-20 date was correct, the 08-28 web-verified date was wrong. Tiny 0.61% position. Target $189.61, +37.06% upside.
- HOOD +13.7% day (2.44x its 5.62% ATR) — "Robinhood Stock Surges Amid Bitcoin Rally and Regulation Hopes" 2026-08-21 (positive), volume elevated. TARGET GAP resolved by the surge (upside now only 9.9%). Small 1.23% position. Target $120.01.
- META pos=0.11 (near 52wk low, $549.90 vs range $520.26-$790.80) — STRONG DOWNTREND by price-position, not day-move. 2.82% position. Target $754.14, +27.08% upside (OVERSOLD BOUNCE criterion still technically met, but see NEW HEADWINDS/PEER LAGGARD below — bounce thesis increasingly stressed).

## NEW HEADWINDS (>=2 distinct negative events, dedup'd)
- AVGO — (1) "Druckenmiller and Loeb Exit Broadcom for AI Investments" 2026-08-23 (negative); (2) "D.E. Shaw Cuts Stake Amid Strong Broadcom Performance" 2026-08-22 (negative). Both are hedge-fund position trims, not fundamentals — fundamentals stayed positive (AI-financing/Google-partnership stories continue). 3.77% position. Target $527.88, +30.2% upside. [outlet/URL not returned by this feed — see data_quality]
- META — (1) "Meta Faces Lawsuit Amid Strong Advertising Growth" 2026-08-22 (negative); (2) "Meta Faces Trials and AI Spending Challenges" 2026-08-21 (negative). Compounds with STRONG DOWNTREND above.

## PEER-RELATIVE
- NOW PEER LEADER: +34.6% 1m vs XLK +1.69% (+32.9pp, +2.53 sigma on its 5.65% ATR) — genuinely leading, not sector beta. 2.30% position. OVERSOLD BOUNCE grade: 100% hit at 30d (n=1), 66.7% interim at 7d (n=3) per journal.
- BX PEER LEADER: +16.7% 1m vs XLF +2.55% (+14.2pp, +1.78 sigma on its 3.47% ATR). New re-entry (0->10sh, 3.67% weight). Still Unclassified in sector_map — flagging for smith-thesis, not fixing here.
- STM PEER LAGGARD: -23.1% 1m vs SMH -4.51% (-18.6pp, -1.94 sigma on its 4.17% ATR) — deepened from the -1.61 sigma noted 2026-08-13. STRONG DOWNTREND (price-based) has resolved (pos now 0.49, day +1.28%); this is now the live signal instead.
- META PEER LAGGARD: -12.3% 1m vs XLK +1.69% (-14.0pp, -1.29 sigma on its 4.74% ATR).
- MSFT PEER LEADER: unchanged repeat (+22.1pp vs XLK, +3.08 sigma) — already tracked since before 08-20.

## TARGET GAP (>=15% upside/downside)
- New: STM +29.31% upside (target $71.52); INTC +21.60% upside (target $114.88, +3sh added this run, 3.46% weight).
- Unchanged repeats (no material change, upside still >=15%, pos moved <0.05): MU, CIEN, GEV, QCOM, CEG, AMZN, VRT, AMAT, BE, TXN, WDC, GOOG, GLW, MSFT, NVDA, TSM, AMD, BABA.
- Resolved this run: HOOD (surge closed the gap, see above); MRVL upside fell to 7.87%, under threshold.

## INSIDER ACTIVITY
- TSM (new): "Insider Purchase Signals Confidence in TSMC" 2026-08-22 (positive) — a buy, not a sale.
- Unchanged repeats (no new post-watermark filings, headline-only, no Form-4 detail — quick mode is news-derived): MRVL, INTC.

## RESOLVED (Core trend buckets that no longer hold)
- AMD STRONG UPTREND: pos 0.744 (<0.80), day +0.81% — no longer extended.
- TSM STRONG UPTREND: pos 0.765 (<0.80), day +0.71% — no longer extended.
- STM STRONG DOWNTREND: pos 0.488, day +1.28% — recovered off lows (superseded by PEER LAGGARD above).

## EARNINGS PROXIMITY
- NVDA (8.25% weight, largest holding): journal entry from 2026-08-20 stays open (4 days old, no 7d score yet). Headlines are internally contradictory this run — some say "reports strong earnings" (08-20), others "prepares for earnings" (08-22/08-23) — no new date asserted; see data_quality.

## COHR / IREN / CLS exit investigation (per orchestrator request)
No idiosyncratic negative news found for any of the three after the 08-20 watermark:
- COHR: last stories (08-10 to 08-18) already show the real story — a post-Q4-earnings "expectations reset" (op-cash-flow miss despite a revenue beat) that predates and likely compounded through the 08-18 semis rout. Nothing new since.
- IREN: last two stories (08-13, 08-18) are both positive — first AI data-center delivery to Microsoft, Nvidia Exemplar Cloud status. Exit is not news-explained.
- CLS: last three stories (07-24 to 08-19) are all positive — Q2 beat, raised outlook, AI-demand upgrade. Also not news-explained.
- Working read: all three (plus TER's near-total sell) look like mechanical stop-loss exits from the 08-18 semis rout, consistent with the book's tight large-quantum SL policy — not idiosyncratic deterioration. TER does have one real headwind though: Baird downgraded to Neutral, "no catalysts until 2028" (2026-08-21).
- smith-ledger should confirm exact fill timestamps/prices to close this out.

## Data quality
- NBIS and SKHY: analyst target/upside fields returned empty this run — TARGET GAP check skipped for both. SKHY also returned 52wk_low=0 (implausible/discarded) — guardrail pos=0.5 fallback applied.
- FMP `news`/`insiderTrades`/`form13F` tools returned ACCESS DENIED (plan-tier gate) — could not pull dedicated COHR/IREN news or real Form-4 filings; used INDmoney's embedded news segment instead, which returns headline+date+sentiment only, no outlet/URL — bucket citations above carry date+headline but not a source link.
- NVDA earnings date internally contradictory across headlines this run (see EARNINGS PROXIMITY) — no new date asserted.
- CLS/TER/ASML are at dust quantities (~0 shares/weight) — no bucket analysis performed, treated as effectively exited pending smith-ledger confirmation.

```json
{"signal_history":{"changed":{
  "BABA":["TARGET GAP","STRONG DOWNTREND","MOMENTUM+VOLUME"],
  "STM":["TARGET GAP","PEER LAGGARD"],
  "INTC":["INSIDER ACTIVITY","TARGET GAP"],
  "TSM":["TARGET GAP","INSIDER ACTIVITY"],
  "AMD":["TARGET GAP"],
  "AVGO":["TARGET GAP","NEW HEADWINDS"],
  "META":["OVERSOLD BOUNCE","TARGET GAP","STRONG DOWNTREND","PEER LAGGARD","NEW HEADWINDS"],
  "NOW":["PEER LEADER"],
  "BX":["PEER LEADER"],
  "HOOD":["MOMENTUM+VOLUME"],
  "COHR":[],"IREN":[],"CLS":[],"TER":[],"ASML":[]
 },"unchanged_count":20},
 "news_watermark":"2026-08-24",
 "resolved_flags":[
   "AMD STRONG UPTREND resolved: pos 0.744, day +0.81% — no longer extended",
   "TSM STRONG UPTREND resolved: pos 0.765, day +0.71% — no longer extended",
   "STM STRONG DOWNTREND resolved: pos 0.488, day +1.28% — recovered off lows",
   "BABA earnings-date conflict resolved: FMP's 2026-08-20 date confirmed correct by post-print news; the 08-28 web-verified date was wrong"
 ],
 "new_flags":[
   "BX (new re-entry, 3.67% weight, +1.78 sigma PEER LEADER vs XLF) still Unclassified in sector_map — needs smith-thesis cluster assignment",
   "COHR/IREN/CLS/TER exit investigation: no post-08-20 negative news for COHR/IREN/CLS; all four look like mechanical stop-loss exits from the 08-18 semis rout, not idiosyncratic deterioration; TER alone has a real headwind (Baird downgrade 08-21, no catalysts until 2028); smith-ledger should confirm exact fills"
 ],
 "journal_new":[
   {"date":"2026-08-24","ticker":"BABA","bucket":"MOMENTUM+VOLUME","price_at_flag":119.34,"analyst_target":189.61,"day_atr_mult":-2.613,"rel_sigma":null,"normalized":true},
   {"date":"2026-08-24","ticker":"HOOD","bucket":"MOMENTUM+VOLUME","price_at_flag":108.13,"analyst_target":120.01,"day_atr_mult":2.438,"rel_sigma":null,"normalized":true},
   {"date":"2026-08-24","ticker":"BX","bucket":"PEER LEADER","price_at_flag":143.38,"analyst_target":142.38,"day_atr_mult":null,"rel_sigma":1.778,"normalized":true},
   {"date":"2026-08-24","ticker":"NOW","bucket":"PEER LEADER","price_at_flag":128.48,"analyst_target":140.25,"day_atr_mult":null,"rel_sigma":2.531,"normalized":true},
   {"date":"2026-08-24","ticker":"STM","bucket":"PEER LAGGARD","price_at_flag":50.56,"analyst_target":71.52,"day_atr_mult":null,"rel_sigma":-1.943,"normalized":true},
   {"date":"2026-08-24","ticker":"META","bucket":"PEER LAGGARD","price_at_flag":549.90,"analyst_target":754.14,"day_atr_mult":null,"rel_sigma":-1.285,"normalized":true},
   {"date":"2026-08-24","ticker":"TSM","bucket":"INSIDER ACTIVITY","price_at_flag":418.95,"analyst_target":547.09,"day_atr_mult":null,"rel_sigma":null,"normalized":true},
   {"date":"2026-08-24","ticker":"STM","bucket":"TARGET GAP","price_at_flag":50.56,"analyst_target":71.52,"day_atr_mult":null,"rel_sigma":null,"normalized":true},
   {"date":"2026-08-24","ticker":"INTC","bucket":"TARGET GAP","price_at_flag":90.07,"analyst_target":114.88,"day_atr_mult":null,"rel_sigma":null,"normalized":true}
 ],
 "peer_map_updates":{},
 "vol_normalization":{
   "BABA":{"atr20_pct":3.28,"day_atr_mult":-2.613,"rel_sigma":null,"threshold_pct":4.92},
   "HOOD":{"atr20_pct":5.62,"day_atr_mult":2.438,"rel_sigma":null,"threshold_pct":8.43},
   "STM":{"atr20_pct":4.17,"day_atr_mult":0.307,"rel_sigma":-1.943,"threshold_pct":6.255},
   "BX":{"atr20_pct":3.47,"day_atr_mult":0.415,"rel_sigma":1.778,"threshold_pct":5.205},
   "NOW":{"atr20_pct":5.65,"day_atr_mult":-0.173,"rel_sigma":2.531,"threshold_pct":8.475},
   "META":{"atr20_pct":4.74,"day_atr_mult":0.158,"rel_sigma":-1.285,"threshold_pct":7.11}
 },
 "data_quality":[
   "NBIS/SKHY analyst target fields empty this run — TARGET GAP skipped for both",
   "SKHY 52wk_low returned as 0 (implausible) — discarded, pos=0.5 fallback used",
   "FMP news/insiderTrades/form13F ACCESS DENIED (plan tier) — used INDmoney embedded news (headline+date+sentiment, no outlet/URL) instead",
   "NVDA earnings date internally contradictory across headlines this run — no new EARNINGS PROXIMITY date asserted",
   "CLS/TER/ASML at dust quantities (~0 weight) — no bucket analysis performed"
 ]}
```

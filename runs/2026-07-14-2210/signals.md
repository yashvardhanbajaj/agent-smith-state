# Signal Scan — 2026-07-14 22:10 (quick, intraday, gate=STABILIZING)

## Earnings proximity (>5% weight, within 7 days)
- **TSM** — confirmed **Jul 16 (2 days out)**. Weight 9.04%, pos 0.77, day -0.29% — flat into
  print, no run-up. Target $490.34, +14.3% upside. Implied-move data not accessible, skipped.
- LRCX — unconfirmed date, carried from prior run. Weight 6.09%, pos 0.73, ran up +4.73%
  today into the (unconfirmed) print — watch for pullback risk.
- RESOLVED: QCOM (confirmed Jul 29, <5% weight anyway) and GLW (confirmed Jul 28, >7d out,
  weight 3.98% <5%) — closing both EARNINGS PROXIMITY watches.
- ASML reported Jul 13 (positive sentiment) — resolves prior EARNINGS PROXIMITY flag.

## Policy impact
- NVDA — still open: chip-smuggling/export-control headline (13-Jul) alongside bullish
  analyst commentary (14-Jul) — net less negative than prior run's "tightened white list"
  framing. Weight 6.99%. Target $301.62, +30.3% upside.

## Peer-relative strength (peer_map seeded this run, all readings new)
LEADER (≥+8% vs peer ETF):
- AMAT +10.9% (own -0.1%1m vs SOXX -9.2% semicap) — weight 2.05%
- AVGO +9.1% (own -0.1%1m vs SOXX -9.2%) — weight 1.38%

LAGGARD (≤-8% vs peer ETF):
- NBIS -19.4% (own -23.5%1m vs XLK -4.1%) — weight 4.47%, position size increased today
- MRVL -18.6% (own -27.8%1m vs SOXX -9.2%) — new position, weight 3.35%
- CLS -10.6% (own -14.7%1m vs XLK -4.1%) — weight 1.23%
- TER -8.5% (own -17.7%1m vs SOXX -9.2%) — weight 3.76%
- QCOM -9.9% (own -19.1%1m vs SOXX -9.2%) — weight 3.95%
- CRDO -0.5% (own -7.6%1m vs SMH -7.1%) — in-line with sector, not underperforming despite
  the large headline drop; noted, not a laggard flag.

## Strong uptrend (pos≥0.80 or day≥+4%)
MU (pos 0.77, day +5.76%), LRCX (pos 0.73, day +4.73%), TER (pos 0.67, day +4.34%),
EWY (pos 0.71, day +5.65% — bounce after two KOSPI crash days), ASML (pos 0.83),
STM (pos 0.82). DRAM day +7.56%, pos calc =1.0 but 52wk_low=0 is bad data (see data_quality)
— treat as strong move, not confirmed breakout.

## Strong downtrend
- NBIS — day -5.52%, pos 0.60. Position size was increased (4→6sh) right through this drop —
  same pattern flagged on EWY last run.
- NOW — pos 0.20 (≤0.22 threshold), day -3.52%. Also OVERSOLD BOUNCE below.

## Swing setups
- MOMENTUM+VOLUME (|day|≥4%): MU +5.76%, LRCX +4.73%, TER +4.34%, EWY +5.65%, NBIS -5.52%,
  DRAM +7.56% (data-quality caveat). SNDK's 07-14 MOMENTUM+VOLUME flag stays open in journal
  (grade/hit-rate still empty — too early).
- OVERSOLD BOUNCE (unchanged, open since 07-12): NOW — pos 0.20, upside 23.9%, weight 3.00%.
  Prior run's unexplained -7.95% pre-market move is still unresolved (no news explains it).
- TARGET GAP ≥15% (mostly unchanged repeats, targets flat vs prior run): NVDA +30.3%, MU
  +33.3%, AVGO +24.9%, CLS +22.7%, CIEN +19.6% (target unchanged, still pending soft-guidance
  thesis question), VRT +19.8% (re-entered position, weight 3.35%), TER +15.9%.

## SNDK — whipsaw-then-exit (weight now 0.05%, effective full exit)
Grew to 7.4% intraday on the +251% revenue beat, whipsawed -12.6% same day, and is now back
down to dust (0.008sh) — position was apparently exited again intraday after re-entering.
No analyst consensus target available (data gap, unchanged from last run).

## Still pending (no material news change since watermark)
CIEN — soft FY guidance vs. intact optical-demand thesis (last news 07-07, before watermark).
NOW — pre-market -7.95% move (07-12) still unexplained by the news feed.

## Unchanged repeats
CQQQ, GEV, STM, GLW: no bucket-relevant delta beyond what's covered above.

## Insider activity (quick mode, news-derived only) — no new filings since watermark

## Hit-rate / grade readout
bucket_hit_rates and name_bucket_grades are still empty in compute_journal.json — too early
in the journal's life (all entries `verdict: open`, no 7d/30d outcomes scored yet).

```json
{"signal_history":{"changed":{"TSM":["EARNINGS PROXIMITY"],"LRCX":["EARNINGS PROXIMITY","STRONG UPTREND","MOMENTUM+VOLUME"],"ASML":["STRONG UPTREND"],"NVDA":["POLICY IMPACT","TARGET GAP"],"MU":["TARGET GAP","STRONG UPTREND","MOMENTUM+VOLUME"],"AVGO":["TARGET GAP","PEER LEADER"],"AMAT":["PEER LEADER"],"NBIS":["STRONG DOWNTREND","MOMENTUM+VOLUME","PEER LAGGARD"],"MRVL":["PEER LAGGARD"],"CLS":["TARGET GAP","PEER LAGGARD"],"TER":["TARGET GAP","STRONG UPTREND","MOMENTUM+VOLUME","PEER LAGGARD"],"QCOM":["PEER LAGGARD"],"EWY":["STRONG UPTREND","MOMENTUM+VOLUME"],"STM":["STRONG UPTREND"],"DRAM":["MOMENTUM+VOLUME"],"NOW":["OVERSOLD BOUNCE","TARGET GAP","STRONG DOWNTREND"],"CIEN":["TARGET GAP"],"VRT":["TARGET GAP"],"SNDK":["MOMENTUM+VOLUME"],"GEV":[],"CRDO":[],"GLW":[],"CQQQ":[]},"unchanged_count":0},
 "news_watermark":"2026-07-14","resolved_flags":["QCOM EARNINGS PROXIMITY (confirmed Jul 29, <5% weight)","GLW EARNINGS PROXIMITY (confirmed Jul 28, >7d out, <5% weight)","ASML EARNINGS PROXIMITY (reported Jul 13)"],
 "new_flags":["NBIS position increased (4->6sh) through a -5.52% day and -19.4% peer-relative laggard read — same pattern as prior EWY flag","SNDK whipsawed to dust again intraday after this morning's re-entry — flagging the pattern, not a corporate action (G6)","MRVL new position already -18.6% peer-relative laggard vs SOXX on day one","TER now crosses -8% peer-laggard threshold vs SOXX despite today's +4.34% bounce"],
 "journal_new":[{"date":"2026-07-14","ticker":"MU","bucket":"MOMENTUM+VOLUME","price_at_flag":991.01,"analyst_target":1486},{"date":"2026-07-14","ticker":"TER","bucket":"MOMENTUM+VOLUME","price_at_flag":355.92,"analyst_target":423.41},{"date":"2026-07-14","ticker":"NBIS","bucket":"MOMENTUM+VOLUME","price_at_flag":198.88,"analyst_target":0},{"date":"2026-07-14","ticker":"EWY","bucket":"MOMENTUM+VOLUME","price_at_flag":177.5,"analyst_target":0}],
 "peer_map_updates":{"TSM":{"peer_etf":"SOXX","label":"Semis foundry"},"MU":{"peer_etf":"SMH","label":"Memory"},"SNDK":{"peer_etf":"SMH","label":"Memory"},"LRCX":{"peer_etf":"SOXX","label":"Semicap"},"NOW":{"peer_etf":"XLK","label":"Software/Cloud"},"QCOM":{"peer_etf":"SOXX","label":"Semis"},"AVGO":{"peer_etf":"SOXX","label":"Semis/Networking"},"MRVL":{"peer_etf":"SOXX","label":"Semis/Networking"},"CIEN":{"peer_etf":"SMH","label":"Optical interconnect"},"VRT":{"peer_etf":"XLU","label":"Power infra"},"ASML":{"peer_etf":"SOXX","label":"Semicap"},"CLS":{"peer_etf":"XLK","label":"Hyperscaler/compute EMS"},"GEV":{"peer_etf":"XLU","label":"Power infra"},"AMAT":{"peer_etf":"SOXX","label":"Semicap"},"STM":{"peer_etf":"SOXX","label":"Semis"},"NBIS":{"peer_etf":"XLK","label":"Hyperscaler/compute"},"CRDO":{"peer_etf":"SMH","label":"Optical interconnect"},"NVDA":{"peer_etf":"SMH","label":"AI compute/semis"},"GLW":{"peer_etf":"SMH","label":"Optical interconnect"},"TER":{"peer_etf":"SOXX","label":"Semicap"},"DRAM":{"peer_etf":"SMH","label":"Memory ETF (self, no external proxy needed)"},"CQQQ":{"peer_etf":"","label":"China tech ETF (self, no proxy)"},"EWY":{"peer_etf":"","label":"Korea ETF (self, no proxy)"}},
 "data_quality":["DRAM 52wk_low=0 (bad/placeholder data) — pos formula gives 1.0, treat as unconfirmed breakout not hard BREAKOUT","SNDK and NBIS analyst_forecast still empty from data source — no consensus target/upside","CQQQ and DRAM analyst_forecast also empty (ETFs, expected)","QCOM earnings date still unconfirmed despite journal flag open since 07-12 — no firm date found in tool window","LRCX earnings date still unconfirmed — running up (+4.73% today) into an undated print, weight 6.09%"]}
```

# Watchlist & Market Context — 2026-08-16 (DEEP)

## 1. Watchlist setups
**Setups unchanged since 2026-08-15 — market has been closed since Friday's close, same prices, no session has occurred.** Carrying forward from the prior run (not re-derived):
1. SNPS — OVERSOLD BOUNCE + TARGET GAP: pos 0.21, mean target $564.43, upside 25.32%
2. MKSI — TARGET GAP: pos 0.61, mean target $413.62, upside 24.88%
3. WDC — TARGET GAP: pos 0.60, mean target $662.12, upside 23.16%

**Fresh rotation slice scanned this run (index 60-74 of the deduped, non-held watchlist; ETFs SOXX/BKCH/EWT/INDA/CNXT/TINY/VDE skipped, no fundamentals):**
4. **META** (watchlist) — OVERSOLD BOUNCE + TARGET GAP: pos 0.25 (52wk $520.26-$796.25, now $589.85), mean target $754.14, upside **21.79%**, 88.4% BUY. Note: recent news flow is dominated by litigation/fine headlines and an EPS-miss reaction, not a clean bounce catalyst — flag conviction accordingly.
5. **OLED** (watchlist) — OVERSOLD BOUNCE + TARGET GAP: pos 0.16 (52wk $76.42-$153.38, now $88.92), mean target $115.37, upside **22.93%**, 76.5% BUY. Most recent cached news item is stale (Nov 2025 Q3 miss) — no fresh catalyst confirmed, upside/positioning driven only.

No setups in this slice: BAM (pos 0.59, upside 5.0%), PLTR (pos 0.67, upside 9.2%, HOLD-leaning), SMCI (pos 0.52, upside -5.4%, price above target), TSLA (pos 0.22 oversold but upside 13.7% — below 15% bar), PENG (pos 0.65, no analyst_forecast data returned — upside unconfirmable).

Book has no dry powder — these remain rotation/funding candidates, not cash buys.

## 2. Earnings calendar (holdings, next 14 days: 2026-08-16 → 2026-08-30)
- **NVDA (7.72%, largest position)** — 2026-08-26, CONFIRMED (already established, cache unchanged).
- **MRVL (3.55%)** — 2026-08-27, CONFIRMED (already established, cache unchanged).
- **BABA (0.56%)** — 2026-08-28, CONFIRMED (cache, web-verified 08-07, no change).
- **AVGO (3.59%)** — cache had this UNCONFIRMED on a "cadence" guess (2026-09-02). Resolved this run via INDmoney news (03-Aug item, company-sourced): "will announce its Q3 FY26 financial results on September 2, 2026." Now CONFIRMED. Date falls just outside the 14-day window (17 days out) but is now locked in given AVGO's book weight.
- GEV (4.81%) reports 2026-10-21 (cached, confirmed) — outside window, no action.
- No other holding in the 35-name book has a confirmed or plausible report date inside the 08-16→08-30 window. Checked news feeds for ORCL, CIEN, IREN, DRAM (ETF, no earnings) — none show an imminent date; ORCL's fiscal Q1 print is expected mid-September (outside window, not cached), CIEN's news references a recent report already behind it. TSM, MU, MSFT, STM, INTC, TXN, ARM, SKHY, NOW, BX, BE all reported in Jul/early-Aug per the standard quarterly cadence and next report in Oct/Nov — not re-verified individually this run, no evidence of a 14-day-window print.

## 3. Data quality
- ORCL's next earnings date (~mid-September, fiscal Q1 FY27) is not yet cached and is outside this run's 14-day window — flag for next run when it enters range.
- PENG (watchlist, index 60 slice) returned no analyst_forecast data from INDmoney — upside/target unconfirmable, excluded from setups.
- TSLA borderline: pos 0.22 (oversold territory) but upside only 13.7%, just under the 15% TARGET GAP / bounce threshold — excluded, not a setup.
- Watchlist cursor: this run's slice (index 60-74) was computed against a freshly deduped, non-held list built from the three live INDmoney watchlists (135 raw entries, 104 non-held after excluding the 35 current book holdings) — index alignment will drift slightly run-to-run as holdings change what's excluded; treat cursor as approximate rotation, not exact resumption.
- Budget: 4 tool calls used this run (well under the ~12 soft cap), all in service of earnings-date verification per orchestrator's steer.

```json
{"watchlist_setups":[{"ticker":"SNPS","type":"oversold_bounce+target_gap","upside_pct":25.32,"pos":0.21},{"ticker":"MKSI","type":"target_gap","upside_pct":24.88,"pos":0.61},{"ticker":"WDC","type":"target_gap","upside_pct":23.16,"pos":0.60},{"ticker":"META","type":"oversold_bounce+target_gap","upside_pct":21.79,"pos":0.25},{"ticker":"OLED","type":"oversold_bounce+target_gap","upside_pct":22.93,"pos":0.16}],
 "earnings_calendar_updates":{"NVDA":{"date":"2026-08-26","confirmed":true,"source":"web (stockanalysis.com)"},"MRVL":{"date":"2026-08-27","confirmed":true,"source":"indmoney-news"},"AVGO":{"date":"2026-09-02","confirmed":true,"source":"indmoney-news"}},
 "watchlist_scan_cursor":75,
 "data_quality":["ORCL next earnings (~mid-Sept, fiscal Q1 FY27) uncached and outside 14-day window","PENG watchlist name: no analyst_forecast data returned, upside unconfirmable","TSLA borderline: pos 0.22 oversold but upside only 13.7% (<15% threshold), excluded","cursor/index alignment approximate -- non-held watchlist set shrinks as holdings change"]}
```

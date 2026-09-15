# smith-watchlist — 2026-09-15 deep run

## 1. Watchlist setups (rotating slice: index 105-116 + wrap to 3, cursor advanced to 4)

Pre-FOMC context (decision 2026-09-16): SMH -4.75% Mon close, VIX 17.43. Setups below are
support-level watch levels for AFTER the FOMC print settles, not chase entries — per house style.

**OVERSOLD BOUNCE**
- VST (Vistra) — watchlist. pos 0.09 (near 52w low $132.66, live $140.73). Mean target $217.42/16 analysts, upside 35.3%. Positive: new long-term power PPAs with Meta and AWS (2026-09-10); Q2 earnings miss on revenue but Strong Buy consensus held (2026-08-24). Down -5.16% today with the broader power/AI-infra complex.
- SPGI (S&P Global) — watchlist. pos 0.22 (52w range $381.61-$552.25, live $418.54). Mean target $520.30/19 analysts, upside 19.6%. Up +1.91% today on Kaiko digital-assets investment (2026-09-14); guidance raised 2026-09-04 eased earlier growth-concern selloff.

**TARGET GAP ≥15%** (all inside today's semis-wide drawdown — SMH -4.75% — treat as watchlist, not entries, until post-FOMC)
- AAOI (Applied Optoelectronics) — watchlist. pos 0.36, upside 41.4% (target $163.40/5 analysts). Q2 revenue +86.4% YoY (2026-09-01); down -9.11% today.
- STM (STMicroelectronics) — watchlist. pos 0.44, upside 36.3% (target $75.04/9 analysts). New automotive sensor launch + SiC growth forecast (2026-09-14); down -7.24% today.
- WDC (Western Digital) — watchlist. pos 0.47, upside 35.8% (target $664.92/19 analysts). FQ4 revenue +44% YoY on cloud demand (2026-09-10); down -4.53% today.
- VRT (Vertiv) — watchlist. pos 0.42, upside 29.8% (target $338.15/17 analysts). $26bn 2030 revenue target reaffirmed, UtilityInnovation acquisition (2026-09-08/09-02); down -7.65% today — largest single-day drop among book-adjacent names.
- STX (Seagate) — watchlist. pos 0.64, upside 28.4% (target $1,125/19 analysts). Record FY26 FCF $3.1bn, data-center revenue +57% YoY (2026-09-08); down -2.97% today.
- TSM (TSMC) — watchlist [also a current holding, 5.05% wt]. pos 0.72, upside 24.2% (target $551.26/8 analysts, cache as_of 2026-09-14). Record August revenue +53.3% YoY (2026-09-11); down -3.52% today.
- TER (Teradyne) — watchlist [also a current holding, 5.02% wt]. pos 0.58, upside 26.3% (target $446.47/12 analysts, cache as_of 2026-09-14). Baird downgraded to Neutral 2026-08-21 (valuation, no catalyst until 2028) vs $1bn credit line for AI capacity (2026-08-18); down -13.3% today, the sharpest mover in this slice.

No setup: TSLA (pos 0.31, upside only 8.0%), UHS (pos 0.31, upside 10.5%), ADBE (upside 5.1%), AAPL (pos 0.90 but upside is negative -2.7%, no breakout catalyst). TINY (ETF) and ZEO (micro-cap, no analyst coverage) excluded — not scorable against setup criteria.

## 2. Earnings calendar

No current holding reports within the 14-day deep-mode window (2026-09-15 to 2026-09-29). Nearest is
MU at 2026-10-01 (confirmed, yfinance), 16 days out — outside window, no action needed.
earnings_calendar cache is unchanged since the previous run (per slice note); no updates to write back.

## 3. Data quality
- No prior JSON tail was supplied in this slice, so this run could not re-scan tickers that had an
  active setup in a previous run per the standing coverage rule — only the fresh rotating slice
  (index 105 -> wrap to 3) plus today's news-watermark delta was covered.
- TER/VRT/WDC/STM/STX/TSM/AAOI target-gap upside% is inflated by today's broad semis selloff (SMH
  -4.75%); these are pre-FOMC (2026-09-16) snapshots, not standing entry signals.
- ZEO (micro-cap) returned no analyst_forecast data; TINY is an ETF, not scorable against pos/target
  setup criteria — both excluded from output.
- AAPL sits just under the NEARING BREAKOUT threshold (pos 0.895 vs required 0.90) with negative
  analyst upside (-2.7%) — noted but not flagged as a setup.

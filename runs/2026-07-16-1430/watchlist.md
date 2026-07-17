# Watchlist & Market Context — 2026-07-16 (Quick, pre-open)

## 1. Watchlist Setups (rotating slice idx 45-59: MKSI,SNPS,LRCX,CLS,ROBO,WDC,IBM,COHR,LITE,RMBS,GLW,UMC,TSM,MCHP,SNDK; plus ad hoc CRDO/GEV re-entry check)

- **SNPS** — watchlist — OVERSOLD BOUNCE. pos 0.16 (52w $376.18–$651.73, now $419.80). Mean target $563.74, upside 25.5%. Piper Sandler upgraded to Overweight ($550 PT, 23 Jun); Strong Buy maintained despite recent pullback; NVIDIA design-tool partnership (17 Jun).
- **IBM** — watchlist — OVERSOLD BOUNCE (caution). pos 0.00 (at 52w low $205.33). Mean target $296.07, upside 30.65%. CAUTION: this is earnings-miss driven — stock plunged ~25% on 14 Jul after Q2 revenue/EPS miss (hardware spending shift), not a clean technical dip. JPMorgan upgrade (24 Jun, pre-miss) and BofA PT raise are now stale.
- **RMBS** — watchlist — TARGET GAP. pos 0.33 (borderline). Mean target $144.57, upside 31.5%. Only news on file is a Q1 print (28 Apr, mixed margins); no recent catalyst — gap is stale/analyst-driven, not news-driven.
- **WDC** — watchlist — TARGET GAP. pos 0.57. Mean target $618.62, upside 21.5%. Wells Fargo PT raised to $730 (13 Jul) on AI storage demand; but stock down 5-9% over the past week on Chinese-NAND competition concerns — mixed signal.
- **MCHP** — watchlist — TARGET GAP. pos 0.62. Mean target $113.38, upside 25.75%. AI datacenter product cycle (PCIe Gen6 switch) driving estimate revisions; note one source flags 26% DCF overvaluation vs current price.
- **MKSI** — watchlist — TARGET GAP. pos 0.70. Mean target $406.92, upside 16.2%. Zacks Rank #1 into Q4 print; thin on recent (last news 11 Feb) — dated coverage.
- No setup: CLS, COHR, LITE, TSM, GLW (all now current holdings this run — excluded from shopping-list per scope); ROBO (ETF, no target); SNDK (no analyst_forecast data); UMC (target below price, -40.7% "upside").

### Re-entry candidates (orchestrator-requested check on this run's exits)
- **CRDO** — full exit this run (real sale). Mechanical/clean pattern: all 6 recent headlines positive (Zacks #1, Evercore Outperform $325 PT, 206% rev growth), no bearish news found. Mean target $269.81, upside 19.1% from current $218.30. Down -3.7% today alongside broad semis selloff (not idiosyncratic). Same pattern as prior ETN/ANET/DLR re-entry flags.
- **GEV** — cut to dust remainder (real ~2-sh sale). No idiosyncratic bearish news — one negative headline (07 Jul) attributes the drop to a broad AI-infra sell-off, not GEV-specific; backlog/capex headlines are positive. Mean target $1,215.32, upside 14.45% (just under the 15% target-gap bar). Flagged per orchestrator instruction, not on independent criteria strength.

## 2. Earnings Calendar (holdings, quick-mode 7-day window + cache maintenance)
- **TSM** — 2026-07-16 (TODAY) — confirmed, cached. Reported record Q2 rev/profit this morning; stock down ~1.8% pre-open on "sell the news" despite beat and $100B Arizona expansion plan.
- **GLW** — 2026-07-28 — confirmed, cached (outside 7-day window, listed for cache continuity).
- **QCOM** — 2026-07-29 — confirmed, cached (outside 7-day window, listed for cache continuity).
- **LRCX** — unconfirmed. Re-attempted via yfinance get_earnings_calendar (2026-07-16 to 2026-08-15 window) — returned no data. News hints "fiscal Q4 earnings soon" (07 Jul) but no hard date found. Gap remains open since 07-12; now a 4.89%-weight holding, worth another attempt next run.

## Attribution caveat (pass-through, not recomputed)
Per orchestrator: compute_attribution.json's flow_usd ($2,646.14) and residual_market_move_usd ($3,593.47) are understated/unreliable — script gaps G6 (false-positive corporate-action flags on AMAT/AVGO/CLS/GEV real trades) and G9 (6 new tickers LITE/IREN/COHR/ARM/GOOG/META silently skipped, ~$4,144 combined). Orchestrator's corrected est_net_flows_usd ≈ $5,345 implies residual_market_move_usd ≈ $894, not $3,593. Not recomputed here — flagging only.

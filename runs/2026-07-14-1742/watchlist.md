# Watchlist & Market Context — 2026-07-14 quick sweep

## Watchlist setups (rotation slice: LEU→GLNG, cursor 15→30; plus exited-name re-entry check)

- CEG (watchlist) — OVERSOLD BOUNCE: pos 0.16, mean target $357.81, upside 28.0%. Down 24% over past year on Calpine-deal leverage concerns, but Walmart nuclear PPA + Morgan Stanley target raise this week; Citi cut target to $297 (still above spot).
- VST (watchlist) — OVERSOLD BOUNCE: pos 0.29, mean target $222.89, upside 29.1%. Meta/AWS power-purchase visibility, low forward P/E vs S&P 500, positive news flow.
- LEU (watchlist) — OVERSOLD BOUNCE/TARGET GAP: pos 0.04, mean target $268.29, upside 41.8%. CAUTION: recent news is negative (weak margins, HALEU deliveries slipped to 2029); only 7 analysts cover it — treat upside as low-confidence, not a clean bounce signal.
- BWXT (watchlist) — TARGET GAP: pos 0.39, mean target $238.79, upside 25.8%. Positive isotope-production expansion news.
- GLNG (watchlist) — TARGET GAP: pos 0.71, mean target $60.28, upside 15.3%. Thin coverage (15 analysts), no fresh news returned — low-confidence flag.
- VRT (exited, re-entry read) — TARGET GAP: pos 0.72, mean target $377.40, upside 18.9%. News is uniformly positive since the exit (top data-center-stock mentions, Malaysia plant, Nvidia collab, 77% Buy ratings) — legible case that the exit was premature or macro-driven rather than thesis-driven; worth a re-entry look.
- DLR (exited, re-entry read) — TARGET GAP: pos 0.51, mean target $219.43, upside 18.9%. Mixed: $3.5B Blackstone data-center acquisition is thesis-positive, but a dilutive $2.28B equity offering to fund it knocked shares -5.3% premarket on 06-30 — re-entry watch, not a clean setup yet.

No setup / no re-entry trigger: ANET (exited) — pos 0.90, upside only 4.7%, richly valued near highs despite strong AI-networking news; no legible re-entry edge at current price. ETN (exited) — pos 0.73, upside 11.6%, steady but no bounce/breakout/gap trigger — exit looks thesis-neutral, no reason to chase back in.

Not re-scanned this run (outside rotation slice, no prior setup flagged): ARM, EFNL, EVER, ALAB, BP, CMI, KLAC — checked, none met setup thresholds (ARM upside -0.05%, EFNL is an ETF with no analyst coverage, EVER upside 2.75%, ALAB upside -32.9% (overvalued vs target), BP upside 13.9%, CMI upside 11.8% HOLD-rated, KLAC upside 2.78%).

## Earnings calendar (quick mode, 7-day window)

- TSM — confirmed 2026-07-16 (2 days out), source: cached. Fresh pre-earnings news is uniformly positive: 36% YoY quarterly sales growth, AA- S&P credit upgrade, Citi/BofA target raises, capacity expansion — no negative pre-print surprises found.
- GLW (07-28) and QCOM (07-29) — outside the 7-day quick-mode window; cached dates unchanged, no re-check needed this run.

## Data quality
- LEU's 41.8% upside is analyst-dispersion-driven (only 7 analysts) and conflicts with negative near-term news — do not treat as a high-confidence bounce.
- GLNG target-gap flag has no news corroboration this run (news segment returned empty) — thin coverage, lower confidence.
- Several names showed unusually large day-change swings in a pre-open session snapshot (ALAB -12.3%, ARM -7.6%, KLAC -4.0%) — worth confirming against regular-session data before acting.
- VRT/DLR re-entry reads are directional judgment, not confirmed theses — orchestrator/strategist should size any re-entry cautiously.
- Rotation slice this run covered indices 15-29 (LEU through GLNG) of the deduplicated ~104-name watchlist; cursor advances to 30 for next run.

```json
{"watchlist_setups":[
 {"ticker":"CEG","type":"oversold_bounce","upside_pct":28.0,"pos":0.16},
 {"ticker":"VST","type":"oversold_bounce","upside_pct":29.1,"pos":0.29},
 {"ticker":"LEU","type":"oversold_bounce","upside_pct":41.8,"pos":0.04},
 {"ticker":"BWXT","type":"target_gap","upside_pct":25.8,"pos":0.39},
 {"ticker":"GLNG","type":"target_gap","upside_pct":15.3,"pos":0.71},
 {"ticker":"VRT","type":"target_gap_reentry","upside_pct":18.9,"pos":0.72},
 {"ticker":"DLR","type":"target_gap_reentry","upside_pct":18.9,"pos":0.51}
],
 "earnings_calendar_updates":{"TSM":{"date":"2026-07-16","confirmed":true,"source":"indmoney_cached_reconfirmed"}},
 "watchlist_scan_cursor":30,
 "data_quality":["LEU upside driven by thin 7-analyst coverage, conflicts with negative near-term news","GLNG target-gap has no corroborating news this run","ALAB/ARM/KLAC showed outsized pre-open swings vs typical session moves - verify vs regular session","VRT/DLR re-entry reads are directional judgment, not confirmed theses","ANET near-breakout (pos 0.90) but only 4.7% upside - no edge, excluded from setups","ETN exit reads thesis-neutral - no bounce/breakout/gap trigger found"]}
```

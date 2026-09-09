# smith-signals — quick sweep, 2026-09-09 pre-open

TOP LINE: 25+ of 33 holdings are up 2-11% pre-open with no post-09-08-watermark
company-specific news found to explain the move (all sourced items are dated
09-08 or earlier). Reads as a broad AI-capex/semis sector-beta rally,
INFERRED not confirmed — same pattern flagged for IREN on 08-12. Treat
today's price-based buckets below as real; treat the absence of fresh
NEW TAILWINDS/HEADWINDS fires as intentional (nothing crossed the watermark).

## PEER LEADER (from compute_buckets.json, unchanged methodology)
- MRVL (4.76% wt) — PEER LEADER +2.53σ, +34.12pp vs SMH. Grade A (TARGET GAP, n=1). Target $285, +20.91% upside (repeat).
- MU (4.72% wt) — PEER LEADER +1.02σ, +12.93pp vs SMH. NEW TARGET GAP: target $1513.11, +33.89% upside. Name grades F on TARGET GAP/MOMENTUM+VOLUME historically (n=1-2, 0%) despite bullish AI-memory news flow — track record lags the story.
- LITE (2.3% wt) — NEW: PEER LEADER +2.37σ, +45.09pp vs SMH. Day +11.04% — 0.92x its 12%-capped threshold, just under MOMENTUM+VOLUME. Target $1148.43, only +14.79% upside (TARGET GAP not met, was never flagged here).
- LRCX (2.28% wt) — NEW: PEER LEADER +1.15σ, +12.6pp vs SMH. Grade A prior (worked 08-31). Target $370.87, +13.6% (no gap).
- SKHY (2.18% wt) — PEER LEADER +1.06σ, +13.82pp (repeat). Target $248, +33.65% upside (repeat TARGET GAP).
- SMCI (0.95% wt) — PEER LEADER +1.87σ, +29.84pp vs XLK (repeat, graded worked x2). Target $42.38, only +5% upside — price has largely caught the target.

## PEER LAGGARD
- GOOG (3.95% wt) — PEER LAGGARD -1.53σ, -7.63pp vs XLK (repeat). Target $422.34, +20.59% (repeat TARGET GAP).
- CLS (3.11% wt) — PEER LAGGARD -1.33σ, -17.0pp vs SMH (repeat). Target $477.22, +30.86% (repeat). Grades F on TARGET GAP/MOMENTUM+VOLUME (0% hit) despite +62% rev growth headline — flagged disconnect.
- AVGO (1.73% wt) — PEER LAGGARD -1.62σ, -13.31pp vs SMH (repeat). Target $533.41, +30.9% (repeat). Stale (pre-watermark) negative flow still weighing: Q4 guide miss (02-Sep), Druckenmiller/Loeb full exits (23-Aug), D.E. Shaw -58% stake cut (22-Aug) — still pending, not re-counted today.
- FSLR (1.51% wt) — PEER LAGGARD -1.32σ, -12.33pp vs XLU (weak-fit proxy, per peer_map caveat). Target $275.30, +22.54% (repeat). Reversing: +4.3% today after STRONG DOWNTREND — pos ~0.22, still OVERSOLD-BOUNCE territory, no fresh catalyst confirms it (still pending).
- QCOM (1.23% wt) — PEER LAGGARD -1.17σ, -7.8pp vs SMH (repeat). Target $193.10, only +9.84% — TARGET GAP RESOLVED (was ≥15% before today's +3.17% move). New (at-watermark) catalyst still pending: AWS AI-datacenter partnership, targeting $15B revenue by FY29 — single item, doesn't meet 2-event tailwind bar yet.

## TARGET GAP (recomputed live — not in this run's compute_buckets.json; script had no live analyst-target cache)
NEW fires: GEV (9.16% wt, book's largest position) — target $1236.43, +21.44% upside. AMD (3.58% wt) — target $613.84, +21.38%. VST (1.79% wt, new to tracking) — target $217.42, +30.22%, unnormalized ATR (missing atr20).
RESOLVED (rallied through the 15% line today): VRT (was +19.4%, now +13.99%), INTC (now +9.77%, big price-hike rally closed it), NBIS (now +14.81%, just under, Palantir-partnership rally).
Unchanged repeats (still ≥15%, no material change): ASML +17.72%, TSM +20.53%, CIEN +32.3%, STM +30.74%, NVDA +31.0%, COHR +27.32%, AMAT +26.23%, TER +16.67% (thin margin), META +18.72%, WDC +28.22%, KLAC +19.16%, ALAB +25.93%.
Not fired (unchanged): BE -0.78% (at target, per TARGET_GAP_NOT_FIRED).

## MOMENTUM+VOLUME
- INTC (2.7% wt) — CONFIRMED: day +9.05%, 1.76x its 5.15% ATR20 (threshold 7.73%). Catalyst: reported 10% CPU price hike + analyst upgrade (continuing from 08-Sep story, not brand-new, but real and dated). journal_new opened.

## Not fired but notable
- ALAB (3.41% wt) — down -6.94% against a broadly rallying book (day_atr_mult 0.68x its 9.88% threshold, rel_sigma only -0.14 vs SMH — not a peer-relative outlier). Below both thresholds, no bucket fires, but the divergence from the rest of the book is worth a thesis check.

## Still pending (pre-watermark, unresolved)
- STM/TXN cluster: still unbanded (G-open per orchestrator flags), smith-thesis theses still owed.
- BX: fully exited 08-17; AI-capex diversifier slot still empty.
- IREN: no longer in current holdings — was carried in signal_history/open_flags; recommend dropping from tracking (see data_quality).
- AVGO: Q4 guide miss and hedge-fund exits (Druckenmiller/Loeb/D.E.Shaw) — all pre-watermark, no new confirmation today.
- FSLR: reversal off lows lacks a fresh catalyst — still inferred, not confirmed.

## Data quality
- Book-wide pre-open rally (25+/33 holdings, +2% to +11%) has no post-09-08 company news attached to it in this fetch — treated as sector/macro beta, INFERRED (same pattern as IREN 08-12).
- compute_buckets.json's day-move legs read ~0 across nearly the whole book (day_atr_mult ≈ -0.0/0.0), consistent with it snapshotting before this run's live pre-open quotes. TARGET GAP, MOMENTUM+VOLUME magnitude, and FSLR's STRONG DOWNTREND→OVERSOLD reversal were recomputed here off live data instead.
- IREN is absent from current holdings.json but still carried in signal_history/open_flags — likely already exited; orchestrator should retire the entry rather than carry it stale.
- get_earnings_calendar returned empty for 09-09→09-16 (checked GEV/ASML specifically, the only >5%-weight holdings) — no EARNINGS PROXIMITY fires, but calendar coverage for these names is unverified, not confirmed-empty.
- META's rel_strength_1m_peer refreshed vs its true peer XLK: +2.29pp (was falling back to a stale SMH read of -9.55pp). Doesn't flip any bucket (rel_sigma trivial either way) but corrects the stored number.
- Tool budget: 6 calls used (4x get_us_stocks_details batched ≤10, 1x get_earnings_calendar, 1x get_stock_history for META/XLK) — well under the 15-call soft cap.

# Watchlist & Market Context — 2026-07-17 (quick, pre-open, gate ESCALATING)

## 1. Watchlist Setups (US only, entry candidates)
Scan slice: cursor 60-74 (TER, PATH, APLD, GEV, AMZN, CRWV, INTC, GOOG, MU, CORZ, AAPL, AEM, NEM, ASML, ADBE) + targeted checks on AMD/ORCL (new positions, ex-watchlist names) and GOOG (today's exit). Broad-selloff caveat: most target-gap readings below reflect today's index-wide drawdown (VIX +7.5%, Asia -4 to -6.5%), not idiosyncratic dislocation — treat upside% as noisy today.

- **ORCL** — watchlist — OVERSOLD BOUNCE: pos ~0.00 (at 52-wk low $123.66, live $124.21), mean target $251.85, upside **+50.7%**. 16-Jul: "analysts maintain Buy ratings... strong growth in cloud infrastructure" despite debt/leadership overhang. Note: also a brand-new 4sh position bought today — this is a re-entry-strength read, not a fresh-money call.
- **AEM** — watchlist — OVERSOLD BOUNCE: pos 0.15 (52wk $116.83–$255.24, live $137.29), mean target $223.48, upside **+38.6%**. TD Cowen upgrade 14-Jul; gold-sector selloff today (-3.5%) is sector-wide, not stock-specific.
- **AAPL** — watchlist — NEARING BREAKOUT: pos 0.99 (fresh 52-wk high $334.68, live $333.26). Catalyst: 15-Jul China AI-platform regulatory approval + record FCF outlook. Analyst target $315.79 is now below price (-5.5%) — breakout is price-action driven, not target-gap driven.
- **APLD** — watchlist — TARGET GAP: mean target $76.70 vs $26.44, upside **+65.5%**. 16-Jul: ND AI campus expansion, but "widening losses" flagged — high-risk name.
- **MU** — watchlist — TARGET GAP: mean target $1,489.57 vs $853.20, upside **+42.7%**. Today -5.65% on Buffett-related sentiment/China competition headlines, not a downgrade.
- **CORZ** — watchlist — TARGET GAP: mean target $33.36 vs $21.02, upside **+37.0%**. No fresh news this cycle; move is macro-driven (-7.5% today).
- **NEM** — watchlist — TARGET GAP: mean target $135.81 vs $90.83, upside **+33.1%**. TD Cowen upgrade 14-Jul; Jefferies cut target to $146 same week — mixed.
- **TER** — watchlist — TARGET GAP: mean target $423.41 vs $322.30, upside **+23.9%**. Goldman raised target to $465 (6-Jul) on AI-test-equipment demand.
- **AMZN** — watchlist — TARGET GAP: mean target $314.35 vs $249.89, upside **+20.5%**. 15-Jul: bullish analyst notes, rally into earnings.
- **GOOG** — watchlist — TARGET GAP + RE-ENTRY CANDIDATE: mean target $427.77 vs $353.81, upside **+17.3%**. Fully exited today (real sale, per orchestrator). No bearish headline found in this fetch (news segment returned empty for GOOG) — consistent with a clean technical/mechanical exit, same pattern as CRDO/GEV/ETN/ANET/DLR. Flagging for re-entry watch, not a signal to re-buy immediately.

No setup: CRWV (analyst_forecast empty — no target/upside data to score; news mixed on Meta competition), INTC (upside only 7.1%), ASML (upside 6.1%), ADBE (pos 0.24 oversold-range but upside only 13.6%, below threshold), AMD (pos 0.81, upside 6.7% — no setup; already a watchlist name and now also a brand-new 2sh holding, no action beyond noting overlap), GEV (upside 14.7%, just under threshold), PATH (pos 0.27 but upside only 9.2%, catalyst news is stale from May).

## 2. Earnings Calendar
- **GLW** — 2026-07-28 — confirmed (cached, unchanged, outside quick-mode 7-day window).
- **QCOM** — 2026-07-29 — confirmed (cached, unchanged, outside quick-mode 7-day window).
- **LRCX** — still unconfirmed. Checked yfinance quarterly history: last reported 1Q2026 (~late Apr 2026); no explicit next-report date field available from that source. Given LRCX is now 4.39% of book, worth a direct-source check (LRCX IR page) before next sweep — flagging as a durable gap rather than guessing.
- AMD/ORCL/NOW (new/trimmed holdings): no confirmed report date surfaced in this pass; last-quarter reportedDate epochs suggest none fall inside the quick-mode 7-day window (07-17 to 07-24), so not urgent this cycle — will re-check as dates approach.

## Data Quality
- CRWV: get_us_stocks_details returned an empty analyst_forecast block — no target price/upside available this cycle.
- GOOG: no news items returned by this fetch — read as "no bearish news found," not confirmed absence of any news (API may simply not have indexed anything new).
- LRCX: earnings date remains unconfirmed after checking both INDmoney cache and yfinance; recommend a direct IR-page check next run given its 4.39% book weight.
- CORZ: no news items returned this cycle; target-gap read is price-only.
- Today's target-gap readings are inflated market-wide by the ESCALATING selloff (VIX +7.5%, Asia -4 to -6.5%) — treat upside% as a snapshot of a stressed tape, not a clean entry signal.
- Watchlist coverage remains partial: cursor covered indices 60-74 of ~126 unique names; full-list coverage continues over subsequent runs.

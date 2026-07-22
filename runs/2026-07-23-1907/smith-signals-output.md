# Smith Signals — Quick Sweep — 2026-07-23 intraday

DATA QUALITY FLAG (new): INDmoney's networth_holdings price feed returned internally-consistent
but fabricated prices this run (implied +10-20% intraday "gains" on GLW/SNDK/MRVL/CIEN/ARM/ORCL/
DRAM/LRCX/QCOM/EWY vs a flat/-0.3% tape). Confirmed wrong against yfinance; discarded entirely.
All reads below use yfinance direct quotes. This is a new G3 variant — actively wrong, not merely
stale — separate from prior staleness entries.

## Core
- ORCL — BREAKDOWN, pos 0.02 (52wk 120.03–345.72, live 124.86) — 1.19% of book — mean target $249.24, upside +49.9%. Confirmed persistent; fresh credit downgrade + breakdown thesis both still active (open_flag). Exit ~$530 proposal stands.
- ASML — STRONG UPTREND, pos 0.85 — 4.30% of book — mean target $2,121.55, upside +15.1%.
- AMD — STRONG UPTREND, pos 0.93 — 2.65% of book — mean target $541.66 (price already ~2.5% above mean).

## GEV — flagged catalyst check (position just increased +0.394sh to 1.395sh, ~$394 spent)
- GEV — MOMENTUM+VOLUME (downside), day -7.1% to -7.4%, pos 0.71, 3.33% of book — mean target $1,221.48, upside +17.9%. Catalyst: "GE Vernova Reports Mixed Q2 Results, Raises Guidance" (dated 22 Jul, borderline vs watermark but the direct explanation for today's drop) — guidance raised but Q2 print itself read mixed, market selling the beat. Also newly qualifies for TARGET GAP (+17.9%) and PEER LAGGARD vs XLU (-13.7pp) — lost STRONG UPTREND status it held yesterday. Worth noting the buy-up landed the day of the selloff.

## Peer-relative strength (SMH -11.9%, XLK -6.1%, XLI -1.5%, XLU +2.6%, KWEB +5.7% over 1mo)
- PEER LEADER: NVDA +14.3pp vs SMH, AVGO +13.2pp vs SMH, AMD +12.5pp vs SMH, META +17.1pp vs XLK — all unchanged from yesterday.
- PEER LAGGARD (new/expanded — broad rollover from yesterday's rally): MU -8.4pp, LRCX -9.8pp, GLW -13.5pp (unchanged), SNDK -18.0pp (unchanged), MRVL -19.0pp (unchanged), QCOM -8.8pp, COHR -14.0pp, ARM -18.2pp, ORCL -22.6pp vs XLK (unchanged), IREN -21.0pp vs XLK, NBIS -15.2pp vs XLK, VRT -14.0pp vs XLI, GEV -13.7pp vs XLU.
- FADED OUT of PEER LEADER (relative strength compressed toward peer, now neutral): ASML (+5.3pp), TSM (+2.1pp), GOOG (+5.3pp), BABA (+5.2pp, was leader yesterday). None crossed into laggard.

## Target gap (≥15% upside, unchanged repeats: GLW, MU, CIEN, CLS, LITE, ASML, TSM, AVGO, GOOG, QCOM, VRT, COHR, IREN, ORCL, NVDA, META, MRVL, BABA)
- New this run: GEV (+17.9%, see above).
- Headline names: NVDA $302.31 (+29.3%), META $822.69 (+23.9%), AVGO $524.51 (+24.3%), BABA $190.62 (+38.9%).
- Not qualifying: SNDK and NBIS have no analyst consensus in this feed despite 11.4%/3.2% weight — data gap, see below.

## Swing setups
- OVERSOLD BOUNCE: BABA — pos 0.24, 1.39% of book — mean target $190.62, upside +38.9% (open, journal 2026-07-22, no score yet). Peer-leader status faded (was leader yesterday, now neutral) — bounce thesis intact but momentum cooling.
- MOMENTUM+VOLUME fading/reversing (drop from yesterday, day moves now <4%, real tape flat-to-mixed): SNDK (+0.19%), MU (-0.55%), CIEN (-1.37%), TER (-0.80%), CLS (-1.16%), LITE (-1.24%), DRAM (-1.75%), AMAT (-0.78%) — all unchanged repeats now closed out of this bucket.
- No OVERBOUGHT PULLBACK or new BREAKOUT/STRONG DOWNTREND today (AMD/ASML near-highs but not >10% above target; nothing at pos≤0.22 or day≤-4% besides GEV, which reads as momentum not a downtrend structurally).

## Earnings proximity
- QCOM — 5.885% of book, reports 2026-07-29 (6 days out, per company news) — pos 0.39, not run up into the print (down ~1% over last 2wk). Mean target $222.73, upside +21%. Already an open journal entry from 2026-07-12 (outcome -6.9% at 7d) — not re-opening, just flagging proximity.
- STM reports today (2026-07-23) but weight 1.57% is below the >5% threshold — informational only, not bucketed.

## Insider activity
- No new Form-4/filing-level items surfaced (quick mode, news-derived only). CIEN's confirmed insider-sell open_flag persists unchanged (dated 15 Jul, predates watermark).

## Still pending (persisting stories, no new development this run)
- ASML export-control risk story (14 Jul) — no fresh policy news; POLICY IMPACT tag dropped to still-pending.
- AVGO patent-infringement scrutiny (21 Jul) — no fresh item; POLICY IMPACT tag dropped to still-pending.
- CIEN insider sale (already trimmed 59%, WATCH) — unresolved.
- ORCL credit downgrade + breakdown — unresolved, exit proposal stands.
- SNDK largest position (11.44%) — WATCH/trim proposal from last run persists; still no analyst target data this run.
- GOOG re-entry flip-flop (07-17/18) — still unresolved, user's call.

## Data quality
- G3-new: INDmoney price feed fabricated ~10-20% "gains" on 10 tickers this run — discarded, yfinance used throughout (see top note).
- DRAM: 52wk_low returned as 0 (implausible) — pos calc discarded, treated as data gap rather than forced to 0.5 (guardrail variant; true low almost certainly >0).
- SNDK and NBIS: no analyst consensus/target in get_us_stocks_details despite 11.4%/3.2% weight — TARGET GAP unassessable for both.
- yfinance 1mo returnPct figures for this book run -20% to -31% on several names (MU, LRCX, ARM, MRVL, ORCL, GLW, SNDK, QCOM) despite <2% daily moves shown — consistent with the book's extreme realized volatility (annualized vol 70-155% per stats) and a real mid-month correction after the disclosed rally/crash pattern; not flagged as implausible.
- Budget: 5 tool calls used (3x get_us_stocks_details batched, 2x yfinance history batched) — well under the ~15 cap, no truncation.

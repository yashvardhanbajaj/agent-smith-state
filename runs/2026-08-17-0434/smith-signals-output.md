# Signal Scanner — 2026-08-17 (Sun 19:04 ET post-futures-reopen)

## Data condition
US cash market closed since Fri 2026-08-14 close. All 36 INDmoney holdings prices/pos/day% are
byte-identical to the 2026-08-16 run (last_updated stamps still read 2026-08-15 08:4x UTC = Fri close).
Every price-derived bucket below is therefore a **carry-forward, not a recompute** — pos, day_atr_mult,
and relative_strength_1m are unchanged by construction. peer_map required no updates (no new tickers).

Futures: ES +0.074% / NQ +0.221% vs Friday settle, ~1h into the reopen (gate STABILIZING). No named
catalyst found — FMP `general-news` is plan-gated on this account (confirmed again, not re-probed further
per standing note) and no other accessible tool surfaces overnight macro causality. Read the move as
routine Sunday-reopen drift, not a signal on anything in this book.

## News scan vs 2026-08-16 watermark
Checked all 36 holdings via batched get_us_stocks_details (news+analyst segments). **Zero items dated
strictly after 2026-08-16.** Latest dated items across the book cluster on 2026-08-16 itself (NVDA
"Strategic Investments and Positive Analyst Outlook", MU "Stock Upgraded Amid Strong Market Growth",
INTC "Explores Memory Market and Attracts Investment", AVGO "Reports Strong Revenue Growth Driven by
AI") — these sit ON the watermark boundary, not after it, so per the "after news_watermark" rule they
do not count as new and are not double-counted into today's buckets. TSM's 2026-08-15 July-revenue
+45% YoY item (flagged yesterday) is unchanged and not re-reported.

## Buckets — all carried forward unchanged (no repricing, no qualifying new news)
- STRONG DOWNTREND: ORCL (5.85%→2.06% wt — TARGET GAP name, unchanged)
- TARGET GAP (≥15%): ORCL 39.1%↑, TSM 22.07%↑, MU 35.31%↑, AVGO 25.55%↑, CLS 29.2%↑, CIEN 24.21%↑,
  AMD 16.13%↑, STM 24.09%↑, NVDA 25.65%↑, CEG 19.28%↑, AMZN 19.23%↑, COHR 17.43%↑, AMAT 19.92%↑,
  BE 15.93%↑, IREN 46.09%↑, ASML 15.05%↑, BABA 34.7%↑ — targets/upside re-confirmed from this run's
  fetch, all still ≥15%, no change in ranking
- STRONG UPTREND: ASML, AMD, GEV, NBIS, FLTW, TER
- PEER LEADER: ORCL, AVGO, CEG, NOW, MSFT, BX
- PEER LAGGARD: STM (−1.61σ, provisional Analog/Industrial Semis cluster — peer-correlation-vs-SMH
  caveat stands per prior run)
- BREAKOUT: DRAM, SKHY
- REVERSAL - TRIM WATCH: NBIS
- REVERSAL - BUY WATCH: CEG

**Unchanged repeats (31 tickers, all buckets): ORCL, ASML, SNDK, TSM, MU, MRVL, CIEN, AMD, STM, ARM,
DRAM, NVDA, AVGO, GEV, QCOM, CLS, BABA, NBIS, CEG, AMZN, NOW, SKHY, MSFT, FLTW, BX, TER, VRT, COHR,
AMAT, BE, IREN** — no ticker crossed a pos threshold (<0.05 pos delta, impossible with frozen prices),
no ticker had a qualifying post-watermark news event, no analyst action posted.

## Still pending (persisting, not re-flagged in full)
- SNDK: 2026-08-06 guidance-miss headline is a known G58 trap (beat quarter, light forward guide only —
  do not read as demand miss); still no news since 08-13 Investor Day.
- STM/TXN: cluster assignment remains provisional (orchestrator-assigned, smith-thesis confirmation
  still owed); no band set.
- IREN: standing re-entry interest open per 08-12 smith-watchlist call; still no confirmed new catalyst,
  chase-not-entry read stands.
- 5 UNCAPTURED trades (SNDK/TER/ARM/NBIS/INTC, 08-07) and STOP-CASCADE-08-10/11 flags: unchanged,
  belong to book/ledger, not signals.

## Deep-mode insider/13F
Skipped this run. Zero SEC Form-4/13F filings post between Fri 08-14 close and Sun 08-17 — EDGAR does
not process weekend filings — so a fresh pull would return the same data already covered in the
2026-08-16 deep pass. Re-fetching would burn tool budget for a guaranteed null result; noted here
instead of re-probed.

## Journal
No new actionable flags today (journal_new empty) — no repricing, no new news, nothing to score at
flag time. compute_journal.json's existing 26 open entries and 3 graded bucket hit-rates (MOMENTUM+VOLUME
100% n=3, OVERSOLD BOUNCE 100% n=1, TARGET GAP 68.8% n=16) stand unchanged; consumed as-is, not recomputed.

## Data quality
- SKHY: no analyst_forecast returned (foreign ADR, thin US coverage) — target/upside omitted, not
  estimated.
- FMP `general-news` and `insiderTrades`: plan-gated on this account (confirmed, not re-probed).
- Futures-reopen catalyst: no accessible source found; reported as unattributed drift, not silence.

# Signal Scan — 2026-08-16 (DEEP) — WEEKEND, market closed since Fri 08-14 close

## Data condition
No trading session since the 2026-08-15 deep run. Every price field returned this run is byte-identical to that run's Friday close. Per orchestrator instruction: all PRICE-derived buckets (pos, STRONG UPTREND/DOWNTREND, TARGET GAP, PEER-RELATIVE, vol-normalized triggers) are unchanged by construction — not re-derived, not re-reported as new. See prior run's full bucket list at /Users/yb/Claude/AgentSmith/runs/2026-08-15-1809/smith-signals-output.md; carry forward verbatim. This run's only job was a weekend news sweep.

## Weekend news sweep (Fri close → today, all 35 holdings, batched news pulls)
**Result: essentially nothing.** Across all 35 tickers, only ONE item carries a date on or after the prior watermark (2026-08-15):
- TSM — "TSMC Reports Strong Revenue Growth and AI Demand" — 2026-08-15 — INDmoney/aggregated wire. July revenue +45% YoY, 7-month YTD +37%, 73% foundry share, a 25% AI-chip price hike planned for next year. Positive, but it is ONE distinct event — below the 2-event NEW TAILWINDS threshold on its own. No bucket fires.

Every other name's most recent item is dated 08-14 or earlier — already inside the prior run's window, not new. No policy/tariff/export-control items, no insider-activity headlines, no rating actions dated in-window.

## Buckets (none fire fresh this run)
No NEW TAILWINDS, NEW HEADWINDS, POLICY IMPACT, INSIDER ACTIVITY, MOMENTUM+VOLUME, OVERSOLD BOUNCE, OVERBOUGHT PULLBACK, REVERSAL, or CAPITAL ROTATION signals this run — there is no fresh price or news input to generate one. A weekend with no news is a valid finding, not a gap.

## Carried forward unchanged from 2026-08-15 (do not re-score; see prior file for size context/targets)
STRONG UPTREND: AMD, NBIS, GEV, TER, ASML, FLTW (TSM faded off this bucket last run, pos 0.794).
STRONG DOWNTREND: ORCL.
NEW TAILWINDS (as of 08-15, not re-fired today): MU.
TARGET GAP ≥15%: NVDA, CLS, BABA, STM, COHR, AMAT, BE, IREN, CIEN, CEG, TSM, AMZN, ASML (all unchanged).
PEER-RELATIVE: MSFT +2.80σ, BX +1.72σ, CEG +1.29σ, NOW +1.25σ, ORCL +1.02σ, AVGO +1.00σ (line), STM −1.49σ PEER LAGGARD.
REVERSAL — TRIM WATCH: NBIS. REVERSAL — BUY WATCH: CEG.

## Earnings proximity
Still none within 7 trading days for any >5% weight holding. NVDA/MRVL report 08-26 (8 trading days out), AVGO 09-02 — both outside the window, unchanged from last run.

## Journal
No new actionable flags this run (no new price move, no new dated news event to score). `journal_new` is empty. The five 08-15 flags (COHR, AMAT, BE, IREN, NBIS) remain open at 1 day old, per compute_journal.json — nothing to add.

## Still pending (unresolved, pre-watermark)
- ASML: China DUV structural risk, unresolved.
- MU/SNDK: CXMT reconciliation + memory-cluster concentration, unresolved.
- BX: Project Eclipse review + 08-12 insider sale, unresolved.
- COHR: 08-12/13 cash-generation concern, no follow-up yet.
- ORCL: tool-reported upside_per internally inconsistent (mean $247.17 vs current $150.52 implies +64.2%, tool shows +39.1%) — still uncorrected, still open.

## Data quality
- Confirmed CRITICAL DATA CONDITION: all `last_updated` timestamps across all 35 batched news pulls read "2026-08-15 08:45-46" — single stale snapshot, consistent with no new session.
- insiderTrades (FMP) still plan-gated on this account ("requires Starter/Premium/Ultimate/Enterprise plan") — same as 2026-08-15, not retried beyond one confirmation call. No Form-4 read possible this run either.
- FMP `news` tool (search-stock-news) is ALSO plan-gated on this account — new finding this run (not previously tested as a fallback). Falls back entirely to INDmoney's embedded news segment, which is what the bucket counts above are built from.
- atr20 cache last refreshed 2026-08-12 (TTL 7 days, refresh_after 2026-08-19) — still valid, not re-pulled this run since no new price bars exist to compute against.
- Budget: 4 get_us_stocks_details (news-only) + 1 FMP news (denied) + 1 insiderTrades (denied) = 6 calls, well under soft cap.

```json
{"signal_history":{"changed":{},"unchanged_count":34},
 "news_watermark":"2026-08-16","resolved_flags":[],"new_flags":[],
 "journal_new":[],
 "peer_map_updates":{},
 "vol_normalization":{},
 "data_quality":[
   "Market closed since 2026-08-14 -- all price-derived buckets carried forward unchanged from 2026-08-15 run, not recomputed",
   "Weekend news sweep across all 35 holdings found exactly one in-window item (TSM, 2026-08-15, TSMC July revenue +45% YoY) -- one distinct event, below 2-event NEW TAILWINDS threshold, no bucket fires",
   "insiderTrades (FMP) plan-gated, confirmed again this run -- no Form-4 read for top-10",
   "FMP news (search-stock-news) also plan-gated -- new finding, fell back to INDmoney embedded news entirely",
   "ORCL tool-reported upside_per (39.1%) still inconsistent with its own mean/current fields (implies 64.2%) -- unresolved carryover, not re-verified this run since price unchanged"
 ]}
```

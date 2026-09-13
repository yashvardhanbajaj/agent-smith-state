# smith-watchlist — 2026-09-14 (quick, intraday, gate=STABILIZING)

## 1. Watchlist setups

Context: book stopped out of INTC/NVDA/SKHY/LRCX/META on 2026-09-10 and added AMZN/NOW (holdings) 2026-09-11. Of the exited names, NVDA, LRCX and META are still on the US watchlist (SKHY is not watchlisted — dropped from tracking). All three were force-included in this scan regardless of cursor position. Quote data below is last_updated 2026-09-12 (Friday close) — today's rally (SMH +1.47%, VIX -11.2%) is not yet reflected in these ticks; treat upside/pos as pre-rally.

- **NVDA** (exited 09-10, watchlist) — watchlist / TARGET GAP: mean target $327.65 (30 analysts, 100% buy) vs live $218.29 → **+33.4% upside**, pos 0.75 (mid-upper range, not a breakout read). Re-entry candidate now that it's off the book; upside likely to compress once today's rally prints.
- **LRCX** (exited 09-10, watchlist) — watchlist / TARGET GAP: mean target $370.87 (24 analysts, cached) vs live $298.22 → **+19.6% upside**, pos 0.58. News flow since the stop-out has been uniformly positive (dividend hike, FQ1 FY27 guide raise, AI/HBM demand commentary).
- **META** — watchlist / no setup: upside 14.07% (just under the 15% target-gap bar), pos 0.47. Note only, not a setup.
- **INTC** (exited 09-10, watchlist) — watchlist / no setup: upside only 11.17% at live $102.94 (mean target $115.88, cached), pos 0.67, consensus HOLD (74% hold). Back on the shopping list post-exit but doesn't clear the bar yet.
- **CORZ** — watchlist / OVERSOLD BOUNCE: pos 0.27 (≤0.3), mean target $37.12 (11 analysts, 100% buy, no hold/sell — thin/one-sided coverage) vs live $17.94 → **+51.7% upside**. Today's tape already +3.28%.
- **APLD** — watchlist / TARGET GAP: mean target $74.23 (only 6 analysts — thin coverage, discount confidence) vs live $26.42 → **+64.4% upside**, pos 0.31 (borderline oversold too).
- **CRWV** — watchlist / TARGET GAP: mean target $138.81 (23 analysts) vs live $88.99 → **+56.0% upside**, pos 0.31 (borderline oversold). Recent flow mixed: Goldman raised PT / Hudson River Trading deal (positive), but large insider-selling disclosure ($688.5M) and post-earnings profit-taking (negative) — net still a live target gap.
- **PATH** — watchlist / TARGET GAP: mean target $16.85 (16 analysts, 81% hold — soft conviction) vs live $13.75 → **+18.4% upside**, pos 0.43.
- **SNDK** — watchlist / TARGET GAP: mean target $2,145 (16 analysts, 87.5% buy) vs live $1,633.35 → **+31.3% upside**. Caveat: 52-week range ($72.03–$2,354.39) spans the WDC spinoff, so the pos metric (0.68) is not meaningful for this name — upside read is unaffected.

No setups on AAPL (pos 0.90, but upside -2.6% — overvalued vs target, foldable-launch news already priced in) or AEM/NEM (gold miners, upside <7%, no qualifying setup).

## 2. Earnings calendar (holdings, quick-mode 7-day window: 2026-09-14 → 2026-09-21)

No current holding has a confirmed earnings date inside this window. yfinance's market-wide earnings calendar for 2026-09-14→2026-09-21 returned zero rows.

- **MU** (2.93% weight, no cache entry): last reported ~2026-06-25 (FQ3 FY26). Cadence estimate (+~91d) points to **~2026-09-24 — unconfirmed**, likely just outside this quick-mode window. Below the 3% weight threshold that would trigger a web-source escalation; flag for the next run or deep review.
- 13 other holdings (TSM, ASML, KLAC, ALAB, LITE, APH, WDC, STM, BE, NOW, MSFT, GLW, SMCI) have no earnings_calendar cache entry at all and none plausibly report in the next 7 days on standard quarterly cadence — full verification deferred to a deep run.
- GEV, GOOG both cached confirmed for 2026-10-21 — outside window, no action needed.

## Data quality
- Fetched-name quotes (AAPL, AEM, APLD, CORZ, CRWV, INTC, NEM, NVDA, PATH, SNDK, LRCX, META) are last_updated 2026-09-12 — today's rally isn't priced in yet.
- SNDK's 52-week range is spinoff-distorted; pos metric unreliable for that name only.
- yfinance get_earnings_calendar returned no rows for the quick-mode window — absence of data, not confirmation of no earnings.
- APLD (6 analysts) and CORZ (11 analysts, all-buy) have thin/one-sided coverage — discount confidence on their large upside_pct figures.
- 14 holdings have zero earnings_calendar cache coverage; MU is the only plausible near-term reporter and remains unconfirmed.
- NVDA live target_prc ($327.65) vs cached analyst_targets ($327.13, as_of 09-10) differ trivially — used the live figure.

```json
{"watchlist_setups":[
  {"ticker":"NVDA","type":"target_gap","upside_pct":33.4,"pos":0.75},
  {"ticker":"LRCX","type":"target_gap","upside_pct":19.6,"pos":0.58},
  {"ticker":"CORZ","type":"oversold_bounce","upside_pct":51.7,"pos":0.27},
  {"ticker":"APLD","type":"target_gap","upside_pct":64.4,"pos":0.31},
  {"ticker":"CRWV","type":"target_gap","upside_pct":56.0,"pos":0.31},
  {"ticker":"PATH","type":"target_gap","upside_pct":18.4,"pos":0.43},
  {"ticker":"SNDK","type":"target_gap","upside_pct":31.3,"pos":0.68}
],
 "earnings_calendar_updates":{"MU":{"date":"2026-09-24","confirmed":false,"source":"estimate = last-reported (2026-06-25) + ~91d cadence"}},
 "watchlist_scan_cursor":90,
 "data_quality":["Fetched quotes last_updated 2026-09-12 (pre-rally)","SNDK 52w range spinoff-distorted, pos unreliable for SNDK only","yfinance market earnings calendar returned zero rows for the window","APLD/CORZ have thin or one-sided analyst coverage","14 holdings have zero earnings_calendar cache coverage","NVDA live vs cached target trivial mismatch, used live"]}
```

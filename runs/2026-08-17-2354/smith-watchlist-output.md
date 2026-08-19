# Watchlist & Market Context — 2026-08-18 (quick, intraday, second run of day)

## 1. Watchlist setups — funding reality: cash $499.06 = 1.12% of book, deployable_cash = $0.00
No cash-funded entries possible. Every row below is WATCH-ONLY; "funding" states what a real trade would require. None clears the bar to justify a trim today — see verdict at bottom.

Re-scanned prior-setup names (index 74-89) + rotation slice index 90-104 (cursor 90→105):

- **CORZ** — TARGET GAP: mean target $37.12 vs $20.39, upside 45.07%, pos 0.42 (52w $13.14-$30.46, 12 analysts, thin coverage). Not held. Funding: would be a new position — no candidate identified worth selling to fund; small-cap/thin-coverage target reduces conviction.
- **MU** — TARGET GAP: mean target $1501.98 vs $1019.33, upside 32.13%, pos 0.79. HELD 5.79% wt. Funding: add-on would require trimming elsewhere; already a top-5 position — not recommended to concentrate further.
- **NVDA** — TARGET GAP: mean target $302.83 vs $225.54, upside 25.52%, pos 0.85. HELD 7.68% wt (largest position), earnings 2026-08-26 (8 trading days out). Funding: explicitly NOT recommended — adding into the book's largest concentration right before its print, with zero cash, is the wrong trade even if a seller could be found.
- **AVGO** — TARGET GAP: mean target $527.88 vs $394.38, upside 25.29%, pos 0.53. HELD 3.58% wt. News positive (upgrade, 17 Aug). Earnings 2026-09-02. Funding: no cash; book already net-sold this session (-$532 flow) — no trim identified as low-conviction enough to fund an add here.
- **META** — TARGET GAP: mean target $754.14 vs $567.17, upside 24.79%, pos 0.17 (oversold range) but news is dominated by an active youth-safety trial with potential $1.4T exposure (17 Aug) — NOT an oversold-bounce (no positive catalyst, litigation tail risk). Not held. Funding: not compelling enough to justify a sell elsewhere.
- **OLED** — TARGET GAP: mean target $115.37 vs $86.95, upside 24.63%, pos 0.14. Only news on file is a stale Nov-2025 earnings miss; 6 analysts (thin). Not held. Funding: no path, low conviction.
- **AMZN** — TARGET GAP: mean target $327 vs $259.64, upside 20.6%, pos 0.70. HELD 3.54% wt. Funding: no identified trim.
- **GOOG** — TARGET GAP: mean target $421.79 vs $341.39, upside 19.06%, pos 0.70. Not held. Funding: no identified trim.
- **AMD** — TARGET GAP: mean target $612.84 vs $509.02, upside 16.94%, pos 0.83 (near highs, post-earnings AI-debt-raise news). HELD 2.31% wt. Funding: no trim identified.
- **QCOM** — TARGET GAP: mean target $194.77 vs $161.83, upside 16.91%, pos 0.29 (oversold range) but recent news is negative (margin pressure, mixed Q3) — NOT an oversold bounce, target-gap only. HELD 3.67% wt. Funding: no trim identified.
- **MSFT** — TARGET GAP: mean target $569.56 vs $479.55, upside 15.8%, pos 0.64. HELD 3.27% wt. Funding: no trim identified.

Dropped from setups this run: **ASML** — upside compressed to 13.15% (was 15.26% last run) as price ran toward target; pos 0.91 but no confirmed breakout catalyst. No longer qualifies.
No setups (below 15% threshold or ETF/no target): SMCI (10.52%), BAM (7.66%), SOXX/BKCH/EWT/INDA/CNXT/TINY/FRNW (ETFs, no analyst target).

**Verdict: nothing here justifies a funding trade today.** The two highest-upside names are either already the book's largest concentrated position going into earnings (NVDA) or thin-coverage/low-conviction (CORZ, OLED). Watch, don't fund.

## 2. IREN re-read (standing interest, HELD 20sh, 2.07% wt)
Now $45.99 (day +4.38%), continuing the run past the 2026-08-12 CHASE-NOT-ENTRY call ($42.33-43.37) — up ~7-8% further since. pos 0.48 (52w $17.22-$76.87), mean target $81.73/+43.73% (10 analysts). News since: Microsoft AI-cloud delivery + Nvidia "Exemplar Cloud" status (13 Aug, positive), $2.8B contract backlog (20 Jul). Honest re-read: the original call's logic (don't chase after a big run) has not been invalidated by a pullback — it simply hasn't happened yet; the stock kept extending on genuine catalyst news rather than reversing. That means the original caution avoided a worse entry price, not a missed one, but also that the "already extended" read is now more true, not less. At $0 deployable cash this is moot for action; watch for a pullback toward the 52w mid-range before treating it as a fresh entry.

## 3. Earnings calendar
Confirmed, cached, in/near window:
- **NVDA** — 2026-08-26, confirmed (source: web/stockanalysis.com, cross-checked against FMP earnings-calendar range query which independently returned the same 2026-08-26 date). 8 trading days out; largest position (7.68% wt) into ~zero cash.
- **MRVL** — 2026-08-27, confirmed (cached, indmoney-news). Not independently re-confirmed this run (FMP range query did not surface it — see data_quality).
- **BABA** — cached confirmed 2026-08-28 (web-verified) but FMP's earnings-calendar range query returned **2026-08-20** for BABA — an 8-day conflict. Low stakes (0.56% wt) but flagging given this name has a prior history of date errors (G-note: FMP heuristic previously wrong by 16 days). Not overwriting cache without a tie-breaking source; left as-is.
- **AVGO** — 2026-09-02, confirmed, cached, outside window.
IREN — still unconfirmed (below 3%-weight mandatory-check threshold); one FMP symbol-filtered query attempted, returned an unrelated historical dump (endpoint doesn't filter by symbol as expected) — no signal obtained, not worth a second call this run.

```json
{"watchlist_setups":[
  {"ticker":"CORZ","type":"target_gap","upside_pct":45.07,"pos":0.42},
  {"ticker":"MU","type":"target_gap","upside_pct":32.13,"pos":0.79},
  {"ticker":"NVDA","type":"target_gap","upside_pct":25.52,"pos":0.85},
  {"ticker":"AVGO","type":"target_gap","upside_pct":25.29,"pos":0.53},
  {"ticker":"META","type":"target_gap","upside_pct":24.79,"pos":0.17},
  {"ticker":"OLED","type":"target_gap","upside_pct":24.63,"pos":0.14},
  {"ticker":"AMZN","type":"target_gap","upside_pct":20.6,"pos":0.70},
  {"ticker":"GOOG","type":"target_gap","upside_pct":19.06,"pos":0.70},
  {"ticker":"AMD","type":"target_gap","upside_pct":16.94,"pos":0.83},
  {"ticker":"QCOM","type":"target_gap","upside_pct":16.91,"pos":0.29},
  {"ticker":"MSFT","type":"target_gap","upside_pct":15.8,"pos":0.64}
],
 "earnings_calendar_updates":{"NVDA":{"date":"2026-08-26","confirmed":true,"source":"web+fmp-cross-checked","checked":"2026-08-18"}},
 "watchlist_scan_cursor":105,
 "data_quality":["ASML dropped from setups: upside compressed to 13.15% (was 15.26%) as price approached target — not a data error, just price movement","FMP earnings-calendar range query (08-17 to 09-15) returned only ~10 rows and omitted MRVL/AVGO/IREN entirely — likely capped/incomplete, not proof those dates are wrong; existing cache used as-is","BABA date conflict: cache confirmed 2026-08-28 (web-verified) vs FMP earnings-calendar showing 2026-08-20 — unresolved, flagging for next run's web check given this name's prior 16-day-error history","IREN earnings date remains unconfirmed; FMP symbol-filtered query did not filter as expected and returned an unrelated historical dump instead of a next-date signal","QCOM sits at pos 0.29 (oversold range) but carries negative news (margin pressure) — explicitly NOT classified as oversold-bounce, target-gap only","get_us_stocks_details rejected a 22-symbol batch (10-symbol cap undocumented in schema) — split into 3 batches of ≤8, no data lost, minor budget cost"]}
```

# Watchlist & Market Context — 2026-08-15 (DEEP)

## 1. Watchlist setups (rotation slice: index 45-59, next cursor 60)
Book has NO dry powder (wallet $12, 0.028% vs [5,15]% band) and 35 positions — nothing here is buyable from cash. These are rotation/funding candidates only, ranked by conviction if a sale frees capital:

1. **SNPS** (watchlist) — OVERSOLD BOUNCE + TARGET GAP: pos 0.21 (52wk $366-$626, now $421.50), mean target $564.43, upside **25.32%**, analyst mix 95.65% BUY. Strongest setup in this slice — deep pullback, near-unanimous buy consensus, semicap/EDA exposure adjacent to book's AI-capex thesis.
2. **MKSI** (watchlist) — TARGET GAP: pos 0.61 (52wk $97-$448, now $310.73), mean target $413.62, upside **24.88%**, 76.9% BUY. Semicap (litho/optics adjacent). Worth funding only if conviction exceeds an existing holding's.
3. **WDC** (watchlist) — TARGET GAP: pos 0.60 (52wk $73-$800, now $508.80, +4.41% today), mean target $662.12, upside **23.16%**, 75.9% BUY. Momentum already ran hard today — chasing into strength, lowest-priority of the three.

No setups: GLNG (pos 0.77, upside 12.9%, below thresholds), ITA (ETF, pos 0.95 but no catalyst data), APA (pos 0.80, upside 3.7%), LLY (pos 0.88, upside 9.2%), NET (pos 0.90 but -4.55% today, mixed 44/44/11 analyst split, no catalyst confirmed), ROBO (ETF, no analyst data). UHS/ODD/FIG had oversold positioning but failed the upside/data-quality bar — see data_quality.

CLS, LRCX, CIEN appear in this slice but are already held — excluded (holdings review is Book & Risk's job, not this scan's).

## 2. Earnings calendar (holdings, next 14 days, through 2026-08-29)
- **NVDA (7.74% of book, largest position)** — **2026-08-26, CONFIRMED.** Cache had this unconfirmed on a cadence estimate; both INDmoney news and yfinance left it unconfirmed, so per escalation rule I WebFetched stockanalysis.com/stocks/nvda — "Earnings Date Aug 26, 2026," corroborated by multiple referenced news articles ("will report its fiscal second-quarter results on August 26"). Book is carrying ~$12 cash — this print is the dominant scheduled risk over the next two weeks.
- **MRVL (3.56% of book)** — **2026-08-27, CONFIRMED**, corrected from the cached 2026-08-26 cadence estimate. INDmoney news (12-Aug item): "set to report its Q2 earnings on August 27." One day later than previously cached.
- **BABA (0.56% of book)** — 2026-08-28, already confirmed in cache (web-verified 08-07), no change needed.
- GEV (4.82%) and AVGO (3.83%) both report outside the 14-day window (10-21 and 09-02) — no action.
- Uncached holdings (TSM, MU, ASML, SKHY, DRAM, MSFT, ORCL, NOW, ARM, TXN, BX, GLW, INTC) were not individually re-verified this run — see data_quality.

## 3. Data quality
- yfinance `get_earnings_calendar` returned empty (both json/text) for the 2026-08-15→08-29 window — couldn't batch-verify uncached holdings' earnings dates; none of them are >3% weight with a cache-flagged imminent date, so no override of the escalation rule was triggered, but their true dates remain unconfirmed.
- IREN, VRT, BE, GLW, COHR are still present in the raw INDmoney watchlist export but are now held positions (re-entered since 08-10) — excluded from this scan per instruction. They were not in this run's rotation slice (45-59) so no live re-check occurred; flagging for the orchestrator to prune from the source watchlist.
- ODD: pos 0.07 (deep oversold) but analyst mean target is BELOW current price (upside -18.43%) — deterioration signal, not a bounce setup; excluded.
- FIG: pos 0.13 (oversold) but INDmoney returned no analyst_forecast data — upside unconfirmable; excluded pending data.
- UHS: pos 0.28 (borderline oversold) but upside only 12.33% (<15% threshold) and consensus sentiment is HOLD — excluded.
- Tool-call budget: ~12 calls used this run; scan did not extend beyond the assigned 45-59 slice.

```json
{"watchlist_setups":[{"ticker":"SNPS","type":"oversold_bounce+target_gap","upside_pct":25.32,"pos":0.21},{"ticker":"MKSI","type":"target_gap","upside_pct":24.88,"pos":0.61},{"ticker":"WDC","type":"target_gap","upside_pct":23.16,"pos":0.60}],
 "earnings_calendar_updates":{"NVDA":{"date":"2026-08-26","confirmed":true,"source":"web (stockanalysis.com)"},"MRVL":{"date":"2026-08-27","confirmed":true,"source":"indmoney-news"}},
 "watchlist_scan_cursor":60,
 "data_quality":["yfinance get_earnings_calendar returned empty for 2026-08-15..08-29 window (json+text) -- uncached holdings not batch-verified","IREN/VRT/BE/GLW/COHR still in raw watchlist export but now held (re-entered since 08-10) -- not in this run's slice, flagged for pruning","ODD pos 0.07 oversold but upside -18.43% (target below price) -- deterioration flag not a setup, excluded","FIG pos 0.13 oversold but no analyst_forecast data returned -- upside unconfirmable, excluded","UHS pos 0.28 borderline oversold but upside only 12.33% (<15%) and sentiment HOLD -- excluded","budget ~12 calls used this run"]}
```

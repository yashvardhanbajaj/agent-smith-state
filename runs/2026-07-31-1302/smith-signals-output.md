# Signal Scan — 2026-07-31 (deep, pre-open)

## Macro backdrop for the melt-up
SMH +6.88% today on top of Tue's +6.91% relief rally, after Mon/Tue's CXMT-driven crash (SMH -3-5%, KOSPI -10.84%). Overnight: KOSPI +17.9%, TAIEX +7.98%, Nikkei +4.03% — a violent Asia-session reversal. No distinct 07-31-dated catalyst headline surfaced in the US-stock feeds (they lag Asian-session moves) explaining a specific retraction of the CXMT price-war fear; the move reads as technical/short-covering (VIX 16.86, calm) rather than confirmed fundamental resolution. Treat with caution until Asian names' own local news confirms a driver.

## BREAKDOWN / OVERSOLD BOUNCE
- **ORCL** — pos 0.057 (still near 52wk low $114.50 despite +8.3% today) — BREAKDOWN + OVERSOLD BOUNCE persist (unchanged bucket vs history). Google Cloud AI partnership news (30 Jul, positive) vs valuation-concern pushback (29 Jul, negative). Weight 1.33%, mean target $248.15 (+48.6% upside — largest in book).

## STRONG DOWNTREND
- **QCOM** — pos 0.21, day -2.6%, the only red name in the book today. Weak FQ4 guidance + declining Apple modem revenue (29-30 Jul misses) offset by non-handset/automotive strength. Unchanged bucket vs history. Weight 1.97%, target $220.57 (+31.3%).
- **CEG** — pos 0.19, **brand-new 3-share add today** ("Power/DC diversification proposal") landing immediately near its 52wk low ($228.63). Mixed news: positive EPS-growth outlook (21 Jul) vs acquisition/investment-cost concerns (08-16 Jul). First-ever signal_history entry for this ticker — flagging as a reversal-buy-watch candidate given the fresh entry, not a stale drawdown. Weight 2.06%, target $352.91 (+25.3%).

## STRONG UPTREND (mechanical, day≥+4% — unchanged repeats, suppressed to one line)
Unchanged repeats: ASML, MU, SNDK, DRAM, AMD, AVGO, GEV, CLS, GLW, AMAT, CIEN, TSM, TER, MKSI, IREN, BE, NBIS, MRVL, COHR, ARM, EWY (all STRONG UPTREND by the day≥+4% rule; already flagged historically, no new news since watermark).

## PEER-RELATIVE STRENGTH — the durable-vs-mechanical answer
1-month peer ETF returns: SMH -17.84%, XLK -7.76%, XLI -3.69%, XLU -1.50%.
- **PEER LEADER**: NVDA -2.5% 1m vs SMH -17.8% (rel +15.3pp) — genuinely holding up, not just riding the bounce. AVGO +2.7% vs SMH -17.8% (rel +20.5pp) — leading the whole complex.
- **PEER LAGGARD** (rel ≤ -8pp, i.e. still well underwater vs sector despite today's spike): GLW -47.1% vs XLK -7.8% (rel -39.3pp, worst), BE -31.6% vs XLU -1.5% (rel -30.1pp), NBIS -31.8% vs XLK -7.8% (rel -24.0pp), SNDK -43.7% vs SMH -17.8% (rel -25.9pp), MRVL -38.5% vs SMH (rel -20.6pp), COHR -36.9% vs SMH (rel -19.0pp), ARM -31.9% vs SMH (rel -14.0pp), GEV -16.4% vs XLU -1.5% (rel -14.9pp), MKSI -34.1% vs SMH (rel -16.2pp), AMAT -30.6% vs SMH (rel -12.8pp), DRAM -29.1% vs SMH (rel -11.3pp), IREN -16.3% vs XLK (rel -8.6pp).
- Near-neutral (borderline, not flagged): MU rel -6.4%, TER rel -6.6%, CIEN rel -6.3%, EWY rel -2.3% (Korea's own index led the melt-up, so its ADR proxy tracked rather than lagged).
- **Read for the CXMT-crash names**: SNDK, MRVL, COHR, MKSI, AMAT, DRAM are all still deep peer laggards a full month out despite the last two sessions' violent bounce — today's +6.9%/+16.7%/+26% moves have recovered only a fraction of the underperformance vs SMH. MU and EWY are closer to sector-neutral. This is consistent with **mechanical short-covering, not yet a durable re-rating** — the memory-cluster thesis (SNDK, DRAM, EWY doubled into the crash) remains unproven; CXMT pricing data point (still 2.2% above Samsung/SK Hynix) is unchanged since last run.

## TARGET GAP (≥15% upside, selected — full book has wide gaps post-crash)
IREN +53.2%, ORCL +48.6%, MU +42.0%, VRT +39.5%, GLW +37.2%, COHR +36.4%, NVDA +35.6%, CIEN +34.2%, AMD/BE ~27.6%, TSM +25.3%, CEG +25.3%.

## EARNINGS PROXIMITY
- **AMD** reports 2026-08-04 (4 trading days out, confirmed). Already up +13% today into the print, ran up on "strong growth prospects" news (29 Jul); weight 3.85%. Implied move not fetched this run (budget) — see data_quality.

## INSIDER ACTIVITY
- FMP `insiderTrades`/`form13F` blocked this run (plan-tier restriction — see data_quality). News-derived only: **CIEN** — "Executives Plan Significant Stock Sales" (15 Jul, still pending, neutral-framed) — no fresh confirmation since watermark.

## Still pending (pre-watermark, unresolved)
- RISK-CAPS: five names over 2xATR20 as of 07-28 — not re-verified this run (fresh compute_risk.json not supplied).
- GOOGL ticker swap (GOOG→GOOGL, 07-28) — still awaiting explicit confirmation it was intentional.
- MEMORY-CLUSTER: CXMT DDR5 still priced 2.2% above Samsung/SK Hynix; no new data point this run.

## data_quality
- insiderTrades/form13F returned ACCESS DENIED (FMP plan tier too low) for SNDK/MU/NVDA/ASML — not retried per guardrail; insider bucket is news-derived only this run.
- No 07-31-dated headline found explaining the Asia melt-up's specific catalyst; described via price action only.
- RISK-CAPS open_flag not re-verified — compute_risk.json/ATR20 refresh not in this run's input slice.
- yfinance 1mo history payloads displayed only the last 2 rows (token truncation) but `stats.returnPct` reflects the full 22-row/1-month window — used as-is.
- EWY/DRAM are ETFs with no analyst target — TARGET GAP bucket not applicable to them.
- AMD earnings implied-move (options data) not fetched this run — budget management.

```json
{"signal_history":{"changed":{"CEG":["STRONG DOWNTREND"]},"unchanged_count":26},
 "news_watermark":"2026-07-31","resolved_flags":[],
 "new_flags":[{"ticker":"CEG","flag":"New 3sh position entered 07-31 lands immediately near 52wk low (pos 0.19) — reversal-buy-watch, not yet thesis-tested."}],
 "journal_new":[
   {"date":"2026-07-31","ticker":"AMD","bucket":"EARNINGS PROXIMITY","price_at_flag":485.39,"analyst_target":575.49},
   {"date":"2026-07-31","ticker":"CEG","bucket":"REVERSAL - BUY WATCH","price_at_flag":263.56,"analyst_target":352.91}
 ],
 "peer_map_updates":{},
 "data_quality":["insiderTrades/form13F ACCESS DENIED (FMP plan tier) — insider bucket news-derived only","no 07-31-dated catalyst headline for Asia melt-up found","RISK-CAPS open_flag not re-verified (compute_risk.json not supplied this run)","yfinance 1mo stats computed on full window despite 2-row display truncation","EWY/DRAM ETFs have no analyst target, TARGET GAP n/a","AMD earnings implied-move not fetched (budget)"]}
```

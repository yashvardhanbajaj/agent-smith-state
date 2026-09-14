# Scout — Session, Sentiment & US Macro (2026-09-14, deep/full)

## Session Read
ES -0.80% / NQ -1.84% imply a lower, Nasdaq-led open; futures alone put Fri's SPX +0.86%/NDX +0.96% cash close at risk of a reversal gap-down at the open. Asia: KOSPI -3.26% (>1% threshold) — memory/HBM-adjacent complex (SK hynix/Samsung proxies) carries gap risk into the US open. Nikkei -0.81% and TAIEX -0.70% are both under the 1% flag threshold — noted, not flagged. STOXX50 -1.11% adds to a broadly risk-off overnight tape.

Headline-level gap-risk scan (post-watermark, book-level only — smith-signals owns per-holding depth): the optics cluster is down -6.25% per the pre-market gate classification (ESCALATING) — this is the single largest overnight mover touching the book and should be treated as live gap risk at the open. VIX +13.8% confirms a broad de-risking move, not an isolated name event.

## Sentiment Narrative
The composite sentiment gauge reads 70.6 ("greed"), essentially unchanged from the prior band, built from VIX-range (74.1), 125-DMA distance (71.7), RSI14 (50.7, neutral), % off 52-week high (91.8, close to highs), and yield-trend (64.7). No `action_hint` fired, so there's no explicit sizing signal from this gauge this run. But the gauge is a daily-bar composite and does not yet reflect this morning's VIX +13.8% / NQ -1.84% move — it's showing where the tape closed Friday, not where futures are pointing pre-open. Treat "greed" as a lagging read into an escalating pre-market tape: it argues against reading today's setup as a fear-driven buying opportunity, but it should not be read as "all clear" either given the gate classification.

## Fed Funds & Stance
Cached — no FOMC meeting since last check. Fed funds target: 3.63% (cached), stance: hawkish (cached). Cache `next_check_date` is 2026-09-17, and today (2026-09-14) is before that date, so per protocol the cache is reused verbatim. Note: the FOMC's next decision lands 2026-09-15/16 — inside this window — so the cached hawkish stance is the pre-decision read; it will need refreshing the run after 09-17 once the statement is out.

## Options Positioning
Options positioning unavailable pre-market — SPY and QQQ both show zero open interest across every strike for the 2026-09-21 and 2026-09-22 expiries (Yahoo's known pre-market OI gap), so `max_pain`/`pcr_oi`/`pcr_vol` are all null for both tickers. No positioning read possible this run.

## Calendar + Regime Read
- Next FOMC: 2026-09-16 (decision) — **inside 5 trading days, effectively tomorrow/day-after**.
- Next CPI (Sept data): 2026-10-14 — outside 5-day window.
- Next NFP (Sept data): 2026-10-02 — outside 5-day window.
- Mega-cap earnings window: closed (next season starts mid-October).

Regime call: **risk-off**. VIX +13.8% on the day, NQ futures -1.84% (double ES's -0.80%), KOSPI -3.26%, and a -6.25% single-day move in the optics cluster all point to a de-risking tape landing directly ahead of a hawkish-stance FOMC decision. US10Y is only +3bps today (`us10y_change_pts` +0.031) but is up 29.3bps over the trailing month — the sentiment gauge's yield-trend subscore (64.7) is already pricing that drift, and a hawkish hold/statement Tuesday would extend it.

- **AI-capex chain**: pressured first and hardest — NQ futures leading ES to the downside, KOSPI's memory-adjacent weakness, and the optics cluster's outsized -6.25% overnight move all sit inside this factor. A hawkish FOMC read this week presses the long-duration multiple on this cluster before anything else in the book.
- **Rate-sensitive long-duration growth**: the 29bps one-month climb in US10Y with a hawkish FOMC stance into Tuesday's decision is the mechanism — today's 3bp move is small, but the setup (VIX up sharply, yields drifting higher into a hawkish Fed) is the classic pre-FOMC squeeze on long-duration names.
- **Defensives/diversifiers**: holding up better — UNH, DUK, SO, PG, LLY are all down modestly-to-flat versus the broader risk-off tape (see bench below); classic rotation-into-quality behavior on a VIX-up day, though DUK/SO (regulated utilities) aren't fully rate-immune given the yield backdrop.

## Diversifier Bench (8 names, refreshed)
Prices refreshed this run (single batched yfinance call). Targets/thesis are 8 days old (>7-day threshold) — carried forward unchanged this run for budget reasons; flagged in data_quality for next full run's re-fetch.

| Ticker | Price | Target | Upside | Clean? | Status | Thesis |
|---|---|---|---|---|---|---|
| VST | 148.38 | 223.17 | 50.4% | No (AI-load adjacent) | active | Merchant power gen, beta 1.41 |
| UNH | 379.09 | 471.65 | 24.4% | Yes | active | Managed care rebound, beta 0.62 |
| SO | 87.17 | 101.45 | 16.4% | Yes | active | Regulated SE utility, beta 0.32 |
| DUK | 119.42 | 138.61 | 16.1% | Yes | active | Regulated utility, beta 0.36 |
| LLY | 1115.70 | 1270.37 | 13.9% | Yes | active | Pharma/GLP-1, beta 0.50 |
| PG | 145.27 | 163.35 | 12.4% | Yes | active | Staples ballast, beta 0.38 |
| NEM | 126.81 | 133.00 | 4.9% | Yes | active | Gold miner, beta 0.54 |
| JNJ | 265.58 | 269.95 | 1.6% | Yes | active | Diversified pharma/medtech, beta 0.24 — back within reach of target after today's pullback |

Ranked by upside × cleanliness: UNH, SO, DUK, LLY, PG, NEM, JNJ lead the clean bench; VST offers the largest raw upside but stays excluded from "clean" sizing given AI-load adjacency.

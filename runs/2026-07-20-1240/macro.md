# US Macro Desk — 2026-07-20 (run 2026-07-20-1240)

## 1. Fed Funds & Stance
- Effective Fed funds target: **3.63%** (cached — no new FOMC meeting since last check, next_check_date 2026-07-29)
- Stance: **HAWKISH** (cached verbatim from fomc_cache; not re-searched this cycle per caching rule)

## 2. Options Sentiment — Market Level
Source: Barchart put/call-ratios page (worked as expected; no chain-math needed for PCR).

- **SPY**: put/call OI ratio **1.86**, put/call volume ratio **1.52**, total OI 15,348,820
- **QQQ**: put/call OI ratio **1.38**, put/call volume ratio **1.38**, total OI 9,363,371

Both ratios sit above 1.0, i.e. put positioning outweighs calls on both open interest and volume — a defensive/hedging skew rather than complacency. SPY's skew (1.86 OI) is notably heavier than QQQ's (1.38), suggesting broad-market hedging demand is running ahead of tech-specific hedging — consistent with investors buying downside protection on the index while staying comparatively more constructive on the mega-cap/AI-growth complex. Context: VIX 18.77, mid-range of its 52-week band (13.38–35.30) and not signaling panic — so this reads as tactical hedging into known catalysts (FOMC, earnings) rather than acute fear.

**Max pain: unavailable.** The single-nearest-expiry option chain pull (2026-07-20) for both SPY and QQQ returned `openInterest` as 0 or null across effectively every strike and every expiry in the payload (not just the front one) — a yfinance data-availability gap, not a real reading of zero OI on a liquid ETF. Computing max pain off all-zero OI would produce a meaningless number, so it was not calculated or reported. Flagged in data_quality.

## 3. Calendar
- **Next FOMC decision**: September 16, 2026 (meeting Sept 15–16, includes SEP)
- **Next CPI print**: August 12, 2026 (July 2026 CPI data)
- **Next NFP (jobs report)**: August 7, 2026 (July 2026 employment data)
- **Mega-cap earnings-season window**: **ACTIVE** — today (Jul 20) falls inside the mid-Jul-through-end-of-month window.
  - **GOOGL/Alphabet Q2 2026 earnings confirmed July 22, 2026** — inside the next 5 trading days (Jul 20–24). Flagged as a near-term volatility catalyst.
  - NVDA/META/AMD/AVGO/MU dates not individually confirmed this run (budget-capped); META/MSFT typically follow within the same week-plus in prior cycles, NVDA/AVGO/MU typically report late Aug–Sept. Treat as approximate; not verified.
- None of FOMC/CPI/NFP themselves fall inside the next 5 trading days — the near-term calendar risk this week is earnings-driven (GOOGL), not macro-print-driven.

## 4. Regime Read
Fed funds at 3.63% with a HAWKISH stance, 10-yr yield holding at 4.541% (+7.8bps over the past month), and SPX down 1.01% on Friday off a 52-week high (7620.90 vs. 7457.69 spot) point to a **risk-off-leaning, cautious** tape rather than outright risk-on — VIX at 18.77 (mid-range) and elevated put/call skew in both SPY and QQQ corroborate active hedging rather than complacency. The combination of a hawkish Fed and yields grinding higher keeps discount rates elevated, which pressures long-duration/rate-sensitive growth names first and hardest — and because the book's AI-capex chain exposure is running near-total (~99.2% per compute_drift.json), that cluster is effectively this book's single point of macro sensitivity right now. GOOGL's July 22 print (inside the next 5 trading days) is the nearest concrete catalyst that can move this cluster sharply in either direction; defensives/diversifiers are the one relative pressure valve in this regime given the modest safe-haven bid implied by the options skew.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"HAWKISH","next_check_date":"2026-07-29"},
 "spy_pcr":1.86,"spy_max_pain":null,"qqq_pcr":1.38,"qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-09-16","next_cpi":"2026-08-12","next_nfp":"2026-08-07","earnings_season_window":true,"near_term_catalyst":"GOOGL earnings 2026-07-22 (within 5 trading days)"},
 "regime":"risk_off","regime_note":"Hawkish Fed + 10yr holding above 4.5% and rising, SPX -1.01% off 52w high, elevated put/call skew (SPY 1.86 OI, QQQ 1.38 OI) vs mid-range VIX (18.77) signal defensive positioning/hedging rather than panic or complacency.",
 "cluster_impact":{"ai_capex_chain":"pressured — hawkish Fed and 10yr >4.5% compress forward multiples on capex-linked growth names; GOOGL earnings Jul 22 is an immediate volatility catalyst given book's ~99.2% AI-capex concentration","rate_sensitive":"pressured — 10yr +7.8bps over 1mo with hawkish FOMC stance keeps discount rates elevated, hitting long-duration names first","defensives":"relatively favored — modest safe-haven bid implied by SPX pullback off highs and elevated options hedging skew"},
 "data_quality":["SPY/QQQ get_options single-expiry pull returned openInterest=0/null across nearly all strikes and expirations for both symbols — max pain not computable this run, marked unavailable rather than guessed","NVDA/META/AMD/AVGO/MU individual earnings dates not confirmed this run (tool-budget managed); only GOOGL confirmed (Jul 22, 2026)"]}
```

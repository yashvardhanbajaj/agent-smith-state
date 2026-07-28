# US Macro Desk — Deep Run, 2026-07-28 13:35 ET

## 1. Fed Funds & FOMC Stance
- Current target range: 3.50%-3.75% (midpoint 3.63%, matches cache). Cache was due to expire 2026-07-29 — refreshed per instructions.
- FOMC decision tomorrow Wed 2026-07-29, 14:00 ET; Powell presser 14:30 ET. NO SEP/dot-plot this meeting — reaction trades purely off statement language + presser tone.
- Priced: fed-funds futures ~64% hold at 3.50-3.75%, ~36% hike to 3.75-4.00% (per FactSet/market consensus). This would be the 5th straight hold if realized. Standing stance carried into this meeting is HAWKISH — June SEP showed the median dot moving rates higher for year-end 2026 against CPI running 4.2%.
- Surprise map given hawkish standing stance + 10yr +19.4bps over the month (easing -4.5bps today to 4.596%):
  - HAWKISH surprise = actual hike (the priced 36% tail) or a hold with statement language hardening on inflation persistence/fewer cuts. Pushes 10yr back up through the month's highs, compounds discount-rate pressure onto the book's longest-duration multiples.
  - DOVISH surprise = hold + statement softening (acknowledging labor cooling, opening a cut path). Would let the 10yr's intraday relief (-4.5bps) extend, easing the discount-rate drag on AI-capex forward multiples.
  - Base case (hold, stance essentially unchanged) is close to a non-event for rates but keeps the "higher for longer" overhang on the book intact into August data.
- Transmission channel to the book: this is a 100%-AI-capex-on-equity, beta 1.070-vs-SMH book carrying long-duration growth multiples (memory, optics, semis capex names priced heavily on out-year earnings). A hawkish hold/hike keeps the discount rate elevated, compressing forward multiples fastest in the names furthest out on the duration curve (Memory 19.4%, Optics 20.1% of equity) — these clusters feel a hawkish surprise before value-tilted defensives do.

## 2. Options Sentiment — Market Level (Barchart, live)
- SPY: put/call OI ratio 1.99, put/call volume ratio 1.16, total OI ~17.65M. Elevated OI put-skew — consistent with pre-FOMC protective hedging rather than pure directional bearishness.
- QQQ: put/call OI ratio 1.32, put/call volume ratio 1.03, total OI ~10.91M. Closer to neutral, modest put lean.
- Read: options market is pricing hedged caution into the FOMC print, not complacency — the SPY put-skew is the more pronounced tell. This sits alongside VIX 17.95 (-3.85% today, off an intraday high of 19.52) — spot vol easing even as hedging positioning stays put-heavy, a pattern consistent with "buy dip in the index, hedge the event risk" rather than outright fear.
- Max pain: not computed. Known G18 data-quality gap — yfinance `get_options` returns near-zero open interest across nearly all strikes for SPY/QQQ, making max-pain math unreliable; per standing instruction, not chasing it with extra calls. Reported unavailable.

## 3. Calendar (next 5 trading days flagged)
- **Wed Jul 29 (T+1): FOMC decision + presser; QCOM, LRCX earnings** — flagged, dense.
- **Thu Jul 30 (T+2): AAPL, AMZN, VRT earnings** — flagged.
- **Fri Jul 31 (T+3): month-end** — flagged.
- Mon Aug 3 (T+4): no scheduled catalyst.
- **Tue Aug 4 (T+5): AMD earnings** — flagged.
- Just outside the 5-day window: COHR Aug 5, NFP Aug 7, CEG ~Aug 10, CPI Aug 12.
- Earnings-season window: YES — today (Jul 28) sits inside the mid-Jul-through-end-of-month mega-cap window; the book is heading into its single densest 8-day catalyst stretch of the quarter (FOMC + QCOM/LRCX + AAPL/AMZN/VRT + month-end + AMD), directly overlapping the AI-capex chain names.

## 4. Regime Read
- Broad-market tape is NOT confirming the overnight Asia rout: SPX +0.43%, NDX -0.04%, VIX falling intraday — the US session is shrugging off KOSPI's circuit-breaker (-10.84%), TAIEX -4.65%, Nikkei -3.95%. But SMH -3.08% shows the semis/AI-capex factor specifically is not shrugging it off — this is a factor-specific unwind layered under an index-level "buy the dip," not a broad risk-off regime (yet).
- Versus a week ago: the combination of a hawkish standing Fed stance, a 10yr that ran up 19bps over the month, and now an Asia-led semis-specific rout is a incremental negative shift for the AI-capex chain specifically, even though the index tape looks calm. The book's -14.46% drawdown sitting just above the -15% warn rung means this factor-specific weakness has direct, immediate relevance — SMH's -3.08% today is exactly the transmission path into the book's Semis (30.6%) and Memory (19.4%) clusters.
- Cluster read: AI-capex chain (semis/memory/optics/hyperscaler) — pressured, both by the Asia-led sector-specific selloff and by tomorrow's event risk into a hawkish-leaning Fed; rate-sensitive/long-duration growth — pressured, 10yr still up materially over the month despite today's dip, and a hawkish or hike surprise tomorrow extends this; defensives/diversifiers — relatively favored on a relative basis (index resilience, VIX easing) but the book holds none in equity (100% AI-capex on invested equity) — the 47.7% cash position is the only ballast currently in play.
- Net regime call: risk-off tilted specifically for the book's factor (AI-capex chain), neutral-to-mildly-risk-on for the broad index. FOMC tomorrow is the swing event — a hold-with-softening would be the best case for arresting the factor-specific slide; a hawkish hold or hike compounds it directly into a drawdown already close to the warn rung.

## Data Quality
- Max pain unavailable (yfinance near-zero OI, known gap G18) — not chased further, budget preserved.
- All other figures sourced live this run (Barchart PCR, FOMC probability/rate search, CPI/NFP calendar search) or reused from market_inputs.json per instruction.

```json
{"fed_funds_pct":3.63,"fomc_stance":"hawkish",
 "fomc_cache_update":{"rate_pct":3.63,"stance":"hawkish","next_check_date":"2026-07-30"},
 "spy_pcr":1.99,"spy_max_pain":null,"qqq_pcr":1.32,"qqq_max_pain":null,
 "calendar":{"next_fomc":"2026-07-29","next_cpi":"2026-08-12","next_nfp":"2026-08-07","earnings_season_window":true},
 "regime":"neutral","regime_note":"broad index resilient (SPX+, VIX easing intraday) despite Asia-led semis rout; AI-capex chain factor specifically risk-off (SMH -3.08%) ahead of hawkish-leaning FOMC tomorrow — factor-specific stress, not broad risk-off",
 "cluster_impact":{"ai_capex_chain":"pressured — Asia contagion (KOSPI circuit breaker, TAIEX -4.65%) plus hawkish FOMC overhang hits Semis/Memory/Optics clusters first","rate_sensitive":"pressured — 10yr +19.4bps over the month despite today's -4.5bps dip; hawkish hold or hike tomorrow extends discount-rate drag on long-duration multiples","defensives":"relatively favored on index-level resilience but book carries none in equity; 47.7% cash is the only ballast"},
 "data_quality":["max_pain unavailable — yfinance near-zero OI known gap (G18), not chased further to preserve budget"]}
```

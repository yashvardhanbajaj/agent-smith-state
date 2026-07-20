# Book & Risk — US Portfolio (Deep) — 2026-07-20

Scope: US holdings only (INDmoney), 29 names, value $38,879.56 (per compute_book.json, live-corrected — see holdings.json G3/G14 note).

## 1. Income

- Portfolio trailing dividend yield (weight-weighted, dividendYield × weight_pct across all 29 names, non-payers = 0): **~0.32%** (0.3208 computed). Dominated by QCOM (2.14% yield, 2.65% weight), ORCL (1.58%, 1.30%), TSM (0.95%, 6.15%), GLW (0.72%, 7.56%). This is a growth/semicap-heavy book — income is incidental, not a portfolio objective.
- Ex-dividend dates within 30 days of 2026-07-20 (window through 2026-08-19): only **ASML — ex-div 2026-07-28, 8 days out** (dividendRate $9.09, yield 0.52%).
- Checked and excluded as outside window: AMAT (ex 2026-08-20, 31 days out — just misses), GLW (2026-08-31), TSM/QCOM/STM (Sep), MU/LRCX/VRT/MRVL/META/GOOG/AVGO/TER/ORCL/GEV (all already past ex-date this cycle, next date not yet posted or >30d out). SNDK, DRAM, EWY, CLS, CIEN, NBIS, AMD, IREN, COHR, LITE, ARM, NOW pay no dividend (payoutRatio 0 / no dividendRate).

## 2. LTCG Narrative

- compute_book.json `ltcg_flags` = [] this run.
- **Gap G1 stands**: lots.json is empty (confirmed read this run) — no per-lot purchase dates, so LTCG boundary proximity (24-month Indian foreign-equity rule) cannot be assessed for any of the 29 names, including the largest/oldest-looking positions (SNDK, GLW, DRAM). No holding-period estimation attempted by any other method, per instruction. Seed lots.json from INDmoney contract notes to unlock this.

## 3. Beta Cache Refresh

- data_cache.betas was empty — all 29 names needed refresh (prior 1.477 portfolio beta figure is unrecoverable/stale, cache was lost).
- Batch-fetched via yfinance (get_key_stats): valid betas returned for 24/29 names — see JSON tail `refreshed_betas`.
- **SNDK, DRAM**: yfinance returned no beta. Checked stockanalysis.com/statistics and /etf pages — both report beta as "n/a" (SNDK is the thin-history spinoff case, G5; DRAM is a niche single-theme ETF with insufficient regression history). No fallback value available — genuine gap, not a discard.
- **EWY**: yfinance returned no beta. stockanalysis.com/etf/EWY/ reports **1.46** — in-band, ingested with `"source":"stockanalysis"`.
- **ARM (3.77) and IREN (4.28/4.279)**: both yfinance and stockanalysis.com independently agree on these values, but both exceed the 0–3.5 plausibility band for equity beta. Per standing guardrail, discarded — NOT ingested into refreshed_betas or state. Flagged below; a human should sanity-check whether the 3.5 band is too tight for genuinely high-beta small-caps (IREN is a bitcoin-adjacent miner, ARM is a richly-valued chip-IP name), but I will not override the band unilaterally.
- Net: 25 of 29 names now have a fresh, band-valid beta ready for the orchestrator to cache with today's date; 2 remain a hard gap (no data exists); 2 were computed but held back on plausibility grounds.

## 4. Risk Narrative

Concentration is real and top-heavy: SNDK alone is 10.48% of book (the only >10% single-name), and the top-3 (SNDK/GLW/DRAM) — two of which are actually pooled-vehicle wrappers (DRAM = memory-theme ETF) rather than single operating names — carry 24.8% combined; top5 is 37.2%, top10 58.2%. compute_book.json's portfolio beta is still showing the 1.0 no-cache default, which understates true risk-weighted concentration: several of the largest and most volatile names by raw beta (AMD 2.47, NVDA 2.21, MRVL 2.20, COHR 2.04, VRT 2.03, IREN ~4.3 discarded, ARM ~3.8 discarded) sit inside the top10, so once the orchestrator folds the refreshed betas back in, expect the recomputed portfolio beta to land meaningfully above 1.0 — plausibly back near the prior 1.477 reading. Drawdown is 0.0% (book sits at its own peak_value_usd) but this is a pre-open/no-tick artifact (G3/G14: Friday's close carried forward, US cash session hasn't opened) rather than a genuine all-time-high signal — treat as neutral, not bullish, until Monday's live session confirms.

## Data Quality
- G1: lots.json empty — LTCG flags unavailable (standing).
- G5: SNDK beta unavailable from any source (thin-history spinoff) — extended this run to also cover DRAM (niche ETF, also n/a on stockanalysis).
- Beta plausibility: ARM (3.77) and IREN (4.28) computed by two independent sources but discarded for exceeding the 0–3.5 band — excluded from refreshed_betas, not cached.
- Portfolio beta in compute_book.json (1.0) is the no-cache default, not yet reflecting this run's refresh — will update on next script pass once refreshed_betas is folded in.
- Tool-call budget: 8 calls used (2 yfinance batch, 1 yfinance batch top-up, 5 WebFetch) — within soft cap, no truncation needed.

# Book & Risk — Deep Review, 2026-07-18

## Income
- Trailing portfolio dividend yield (weight-weighted, current 29 US holdings): **~0.30%** (0.3032%).
  Largest contributors: QCOM (2.16% yield x 2.534% wt), ORCL (1.61% x 1.275%), TSM (0.92% x 5.793%),
  GLW (0.71% x 8.077%), AVGO (0.69% x 1.773%). Most of the book (SNDK, DRAM, EWY, CLS, CIEN, NBIS,
  AMD, IREN, COHR, LITE, ARM, NOW) pays no dividend — this is a growth/semi-capex book, income is
  incidental, not a portfolio objective.
- Ex-dividend dates within 30 days of 2026-07-18: **ASML — 2026-07-28 (10 days out)**.
  No other holding has an ex-div date inside the window (nearest others: AMAT 2026-08-20 [33d, just
  outside], GLW 2026-08-31 [44d]).

## LTCG Narrative
- lots.json is empty this run (standing gap **known_gaps G1**) — no per-lot purchase dates available,
  so no LTCG boundary flags can be computed. compute_book.json correctly returns `ltcg_flags: []`.
  Do not infer holding periods from qty-change history or any other proxy; this remains a hard gap
  until lots.json is populated.

## Beta Cache Refresh (urgent this run)
Fetched fresh betas via yfinance (batched, ≤10 symbols/call) for all 29 current holdings.

**Refreshed successfully (23 tickers) — write to data_cache.betas with today's date (2026-07-18):**
META 1.246, AMD 2.469, COHR 2.037, LITE 1.482, ORCL 1.712, GOOG 1.247, GLW 1.086, CLS 1.515,
QCOM 1.638, TER 1.742, MU 2.142, GEV 0.935, NVDA 2.211, LRCX 1.805, TSM 1.246, MRVL 2.197,
AMAT 1.567, CIEN 1.274, NBIS 1.402, AVGO 1.462, STM 1.563, VRT 2.029, NOW 0.959.
(MU, NVDA, MRVL refreshed values match the existing 2026-07-13 cache almost exactly — cache was
still reliable, refresh was for completeness per orchestrator instruction.)

**EWY — no beta from yfinance; WebFetch stockanalysis.com/etf/ewy/ returned 1.46**, tagged
`"source":"stockanalysis"`. Confirms the orchestrator's note (verified 2026-07-18) that EWY's true
beta (1.46) is meaningfully above the 1.0 default it had been carrying.

**Still unresolved — no plausible beta available (do not let 1.0 default stand unflagged):**
- SNDK: yfinance key_stats returned no beta field; stockanalysis.com/stocks/sndk/statistics/ also
  shows "n/a" (Beta 5Y). Thin post-spinoff trading history — known_gaps G5. Return null, not 1.0.
- DRAM: yfinance returned no beta; stockanalysis.com/etf/dram/ also shows "n/a". ETF, known_gaps G5.
  Return null, not 1.0.
- ASML: this refresh attempt's yfinance call returned no beta field (unusual for a mega-cap; likely
  a transient data gap). Existing 2026-07-13 cache entry is not overwritten — retain it as-is.

**Fetched but discarded — outside the 0–3.5 beta plausibility band (guardrail):**
- IREN: yfinance 4.279, stockanalysis 4.28 — two independent sources agree, but both exceed the
  hard 3.5 ceiling. Discarded, not ingested. Flagging for manual review rather than auto-accepting;
  IREN is a bitcoin-miner/datacenter name whose realized beta may genuinely run this hot, but the
  band is a hard guardrail here.
- ARM: yfinance 3.77, stockanalysis 3.77 — same situation, discarded.
Both remain on the 1.0 default in data_cache.betas pending a policy decision on whether to widen
the band for these two names specifically.

## Risk Narrative
Portfolio beta is 1.372 (script's placeholder blend of stale + newly fetched betas — the orchestrator
should recompute portfolio beta and risk_concentration once refreshed_betas below are folded into
data_cache.betas; not redone here). The risk_concentration table shows NVDA (5.377% weight, beta
2.211, 8.66% of risk), MU (4.383% weight, beta 2.142, 6.84% of risk) and MRVL (3.763% weight, beta
2.197, 6.02% of risk) each contributing meaningfully more portfolio risk than their weight alone
implies — all three carry betas above 2x market. GLW, the #2 position by weight (8.077%), is the
opposite case: below-market beta (1.086) means its risk contribution (6.39%) is roughly proportionate
to its weight, not amplified. SNDK, the single largest position (12.352%) and the only one over the
10% concentration threshold, is still riding the 1.0 default beta (no genuine beta available per
above) — its true risk contribution is almost certainly understated given it moved with the
semiconductor complex through Friday's VIX spike. Combined, the top-5 risk names are ~37% of
estimated risk vs. ~34% of weight — a real but not extreme amplification. Drawdown sits at 0% (a
fresh peak as of Friday's close) even as the gate classification is ESCALATING (VIX +12.2%, ES/NQ
both down hard) — no drawdown-policy breach yet, but note the book is entering this stress episode
with essentially zero cash buffer (wallet 0.052%), so there is no dry powder to average down or
absorb a Monday gap-down if Friday's stress carries through.

## Data Quality
- lots.json empty — LTCG flags unavailable (known_gaps G1, standing).
- SNDK, DRAM betas unavailable from both yfinance and stockanalysis fallback (known_gaps G5,
  standing) — returned as null, not defaulted to 1.0.
- ASML beta refresh attempt returned no data this run — existing 2026-07-13 cache entry untouched.
- IREN (4.28) and ARM (3.77) betas discarded per the 0–3.5 plausibility guardrail despite two-source
  agreement — flagged for manual review, not written to cache.
- Dividend yield figures taken at face value from yfinance trailing dividendYield; no dividend data
  available/inferred for non-paying names (treated as 0%, not estimated).
- Tool-call budget: 11 calls used this run (6 yfinance batched + 5 WebFetch fallbacks) — within
  tolerance given explicit "urgent" beta-refresh instruction; not truncated.

```json
{"div_yield_pct": 0.303, "ex_dates": [{"ticker": "ASML", "ex_dividend_date": "2026-07-28", "days_out": 10}],
 "ltcg_narrative": [], 
 "refreshed_betas": {"META": 1.246, "AMD": 2.469, "COHR": 2.037, "LITE": 1.482, "ORCL": 1.712, "GOOG": 1.247, "GLW": 1.086, "CLS": 1.515, "QCOM": 1.638, "TER": 1.742, "MU": 2.142, "GEV": 0.935, "NVDA": 2.211, "LRCX": 1.805, "TSM": 1.246, "MRVL": 2.197, "AMAT": 1.567, "CIEN": 1.274, "NBIS": 1.402, "AVGO": 1.462, "STM": 1.563, "VRT": 2.029, "NOW": 0.959, "EWY": {"value": 1.46, "source": "stockanalysis"}},
 "risk_narrative": "Portfolio beta 1.372 is a blend placeholder pending this run's refreshed_betas being folded in. NVDA/MU/MRVL (all beta >2.1) contribute disproportionate risk vs weight (8.66%/6.84%/6.02% risk vs 5.377%/4.383%/3.763% weight); GLW's below-market beta (1.086) keeps its risk in line with its 8.077% weight. SNDK, the largest position (12.352%, over the 10% threshold) still has no genuine beta (thin post-spinoff history) so its risk share is likely understated. Drawdown is 0% (new peak) despite an ESCALATING gate (VIX +12.2%, ES/NQ down hard Friday) -- no policy breach yet, but cash is essentially zero (0.052%), leaving no buffer if the stress carries into Monday.",
 "data_quality": ["lots.json empty -- LTCG flags unavailable, known_gaps G1", "SNDK and DRAM betas unavailable from yfinance and stockanalysis fallback -- known_gaps G5, returned null not 1.0", "ASML beta refresh returned no data this run -- existing 2026-07-13 cache entry retained untouched", "IREN (4.28-4.28 two sources) and ARM (3.77 two sources) betas discarded per 0-3.5 plausibility guardrail -- flagged for manual review, not cached", "EWY dividend yield not available (ETF distribution data absent from yfinance) -- treated as 0% in trailing yield calc, not estimated"]}
```

# Market Scout — 2026-07-20 (deep, runs/2026-07-20-1240)

## 1. Session Read
**Futures (pre-open):** ES=F -0.02%, NQ=F +0.08% — essentially flat. Futures are NOT confirming Friday's cash-session decline (SPX -1.01%, NDX -1.40%); implies a calm, gap-neutral open, consistent with gate_classification=STABILIZING (VIX chg 0.0%, NQ=F +0.08%). No rebound-desk dispatch this run.

**Asia (closed):**
- Nikkei -4.03% and KOSPI -4.46% — both sharp, >1% notable moves overnight.
- EWY (US-listed Korea proxy) only -0.50% — a sharp lag vs the -4.46% local KOSPI print; the ETF is not yet pricing in the local session's damage. Watch for EWY catch-down risk.
- Taiwan (TWII) -0.52% — muted, but see TSM-specific listing below.
- No Hang Seng/China proxy in this run's data slice — not assessed.

**Europe (in session) — ADR gap-risk flags:**
- ASML Amsterdam -3.84% overnight — **flag: expect ASML to carry gap-down risk at the US open.** STOXX50E also soft (-0.84%), a broadly weak European tape.
- TSM Taiwan listing (2330.TW) +1.31% (fresh Monday print) vs US ADR TSM's stale Friday close of -2.77% — **flag: the real overnight signal for TSM is the Taiwan print (up), not the stale US read. Gap risk is to the upside**, not downside.
- STM Paris flat (0.0%) — no signal.

**Headline scan (holdings-adjacent, post-watermark, headline-level only):**
- TSM: CFO reiterated "strong, multi-year" AI-chip demand, accelerating the $100B Arizona buildout; Q2 revenue +34% YoY, 2026 guide raised to 40%+ growth (Reuters/CNBC, Jul 19-20). Bullish backdrop, aligns with the Taiwan-listing pop.
- Cross-current: Finbold (Jul 19) — "Semiconductor stocks enter bear market," SOX down >20% from its June 2026 high. Mixed tape: strong single-name fundamentals (TSM) vs. sector-wide technical damage — consistent with ASML's sharp overnight drop despite no negative ASML-specific news found.
- No ASML-specific negative headline found; the Amsterdam drop looks sector-driven (SOX de-rating) rather than idiosyncratic.

## 2. Sentiment Narrative
Score 69.6 = **greed** (not extreme; action_hint is null). VIX sits at 18.77, flat on the day and still low/calm by historical standards (component score 75.4) even after a real -1.01%/-1.40% SPX/NDX pullback Friday — that combination (index down, VIX not moving) is a classic "garden-variety dip inside a still-greedy regime" signature, not a stress event. The 52-week-high proxy (91.4) confirms the index is still hugging its highs despite the pullback, and RSI14 (52.9) is neutral — no momentum extreme either direction. Yield-trend (53.9) is unremarkable. Net read: sentiment is friendly to risk-taking but not euphoric, and nothing here forces caution on its own — the concentration risk in this book (99.2% AI-capex factor exposure per compute_drift.json) is the more binding constraint than sentiment for anything the strategist proposes this run.

## 3. Diversifier Bench (non-AI-capex candidates; seeded fresh this run, diversifier_candidates was empty)
Ranked by upside% x diversification-cleanliness (partial diversifiers discounted ~0.4x in ranking):

| Ticker | Price (USD) | Target (mean) | Upside% | Status | Flag | Thesis |
|---|---|---|---|---|---|---|
| NEM | 89.70 | 133.00 | +32.6% | new | clean | Gold miner; 26 analysts, 96% buy/hold, off 33% from 52wk high — pure macro-hedge, zero AI-capex overlap. |
| VST | 155.44 | 223.17 | +30.4% | new | **PARTIAL** | Merchant power gen — genuine upside (14 analysts, 93% buy) but a large slice of its demand story is datacenter/AI load growth. Not a clean diversifier; treat as AI-capex-adjacent. |
| DUK | 125.01 | 138.61 | +9.8% | new | clean | Regulated multi-state utility, rate-base growth; some datacenter demand tailwind exists but book is overwhelmingly regulated retail/industrial, not a dedicated AI-power play like VST/CEG. |
| UNH | 426.09 | 471.65 | +9.7% | new | clean | Managed care, post-selloff (52wk low 234.6 -> now 426); 88% buy-rated. Healthcare, no capex-cycle correlation. |
| PG | 149.98 | 163.35 | +8.2% | new | clean | Staples defensive, 2.9% yield, 74% buy-rated. Low-beta ballast. |
| LLY | 1179.11 | 1270.37 | +7.2% | new | clean | Pharma/GLP-1 franchise; idiosyncratic growth driver fully decoupled from semis/AI capex. |
| KO | 81.56 | 87.35 | +6.6% | new | clean | Staples, sold off -3.96% on the day (largest single-day move in the bench) — worth a closer look for an entry-setup flag next run. |
| JNJ | 253.04 | 269.95 | +6.3% | new | clean | Diversified pharma/medtech, 52wk high 269.43 nearly touched today. |
| SO | 95.30 | 101.45 | +6.1% | new | clean | Regulated Southeast utility, defensive/rate-driven, low beta (0.33). |

**Dropped candidate:** GOLD ticker resolved to "Gold.com Inc." (a $1.1B fintech, not Barrick Mining Corp — Barrick's ticker changed to "B" after its 2025 rename) — discarded, out-of-scope mismatch, not a plausibility-band violation but a symbol-resolution error. Logged in data_quality.

## Data Quality
- GOLD ticker mismatch: resolves to Gold.com Inc. (Financial Services, $1.1B mkt cap), not Barrick Mining — dropped from bench, do not reintroduce under this symbol.
- No Hang Seng/China proxy present in this run's market_inputs.json slice — Asia session read is Nikkei/KOSPI/EWY/TWII only.
- No dedicated per-holding headline scan beyond ASML/TSM/STM (the three ADR/home-listing names already flagged in market_inputs) — full holdings-list headline depth is smith-signals' remit.
- All diversifier betas and target upsides sanity-checked in-band (beta 0.24-1.41, upside 6-33%) — none discarded on plausibility grounds.

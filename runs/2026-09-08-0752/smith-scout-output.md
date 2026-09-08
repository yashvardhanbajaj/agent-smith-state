# Smith Scout — 2026-09-08 deep run

## 1. Session read

**Domain status: no US session has traded since Friday 2026-09-04.** Monday 2026-09-07 was Labor Day (US markets closed); this run is 03:52 ET Tuesday, ~8 min before pre-market even opens. All SPX/NDX/ES/NQ/VIX/SMH figures in market_inputs.json are Friday's closing prints carried forward — not fresh reads. `domain_moved: false` confirmed by identical yfinance closes on the diversifier bench (VST/UNH/DUK/SO/PG/LLY/NEM/JNJ all print byte-identical to the 2026-09-06 as_of).

**Futures (stale, Friday-derived):** ES=F 7696.5 vs SPX cash 7718.6 (-0.29%); NQ=F 29565.5. Not informative for today's open — treat as placeholder until a live pre-market print exists after 04:00 ET.

**The real edge this run — three sessions of Asia/Europe trading the US book hasn't priced:**
- Nikkei 225: -1.70% (largest overnight move; no direct book holding, watch general risk tone)
- KOSPI: -0.58% (SK hynix/SKHY-adjacent memory read; held 2.2%)
- TAIEX: -0.47% (TSM home-market lead; TSM held 3.2%)
- Euro Stoxx 50: -0.45% (broad European risk tone into the STM/ASML session)

**Home-listing leads for ADR holdings (live European session, checked 07:52 UTC):**
- ASML.AS: €1518.80, +1.23% vs prior close (€1500.40) — below the 2% gap-risk threshold, no explicit ADR gap flag.
- STMPA.PA: €45.28, **-2.91%** vs prior close (€46.635) — **≥2% threshold breached. Expect STM (held 4.58% weight) to gap down at the US open**, absent a Tuesday-session reversal in Paris before the US bell.
- 2330.TW (Taiwan listing, TSM proxy): NT$2470, +0.41% vs prior close — muted, consistent with the -0.47% TAIEX index-level move; no gap flag for TSM.

**ADR gap risk summary:** STM is the one name on this book with a live, actionable overnight signal (Paris -2.9%). TSM and the memory complex (SK hynix via KOSPI) show only modest overnight softness, not gap-worthy on their own.

**Overnight/weekend US headline scan:** none surfaced in this pass — headline-level scan only, smith-signals owns per-holding depth. No holiday-weekend headline flagged for book names.

## 2. Sentiment narrative

Score 72.4 / band "greed" (unchanged from prior_band, action_hint null — no extreme-greed/fear override for this run). The read: VIX component at 86.7 (VIX itself 15.69, well inside its ~6-month range of 13.8–28.0 — near the low end, consistent with genuine complacency, not yet a fear signal); SPX sits at 95% of its ~6-month high (7718.6 vs 7816.7), and 125dma component at 70.6 with SPX (7718.6) running well above its ~115-session mean (7413.82) — a market that has grinded higher and stayed there. NDX RSI14 at 53.4 is neutral, not overbought, which is the one component keeping the composite short of "extreme." **Caveat: the ma125/52w-high/vix-range inputs are ~6-month statistics (23 of 53 weekly rows, per a yfinance row-budget truncation), not true 52-week figures — directionally sound but overstate how close these levels are to genuine 52-week extremes.** With action_hint null, this reads as a garden-variety greed regime: no explicit sizing constraint for the strategist, but the setup (index near highs, VIX near the low end of its recent range, zero deployable cash) argues against chasing beta and toward the diversifier bench for any rotation legs.

## 3. Diversifier bench (ranked by upside% × cleanliness; all target/thesis reused unchanged, as_of within 7-day TTL — price refreshed live this run)

| Ticker | Price (live) | Target | Upside% | Thesis | Status | Diversifier flag |
|---|---|---|---|---|---|---|
| VST | $149.30 | $223.17 | 49.5% | Merchant power gen, beta 1.41 — AI-load adjacent | active | **partial** (not clean — capex-adjacent) |
| UNH | $397.14 | $471.65 | 18.8% | Managed care rebound, beta 0.62 | active | clean |
| DUK | $120.22 | $138.61 | 15.3% | Regulated utility, beta 0.36 | active | clean |
| SO | $88.11 | $101.45 | 15.1% | Regulated SE utility, beta 0.32 | active | clean |
| PG | $146.44 | $163.35 | 11.5% | Staples ballast, beta 0.38 | active | clean |
| LLY | $1149.36 | $1270.37 | 10.5% | Pharma/GLP-1, beta 0.50 | active | clean |
| NEM | $128.09 | $133.00 | 3.8% | Gold miner, beta 0.54 | active | clean |
| JNJ | $275.23 | $269.95 | -1.9% | Diversified pharma/medtech, beta 0.24 — trading through target | stale | clean |

Note: all 8 candidates printed prices byte-identical to the 2026-09-06 as_of — consistent with the no-new-US-session finding above, not a data error. JNJ remains stale (trading through target) — flag for possible drop next run if it stays stale a second consecutive time. Deployable cash is $0.00 above the band floor this run, so any bench entry is a rotation buy-leg (trim-to-fund), not a fresh-cash deployment — sizing owned by the strategist.

## 4. Data quality
- market_inputs futures/SPX/NDX/VIX are Friday 2026-09-04 closes carried through the Labor Day holiday — not live Tuesday pre-market prints (pre-market hadn't opened yet at run time).
- spx_125dma/spx_52w_high/vix_52w_range are ~6-month (23-week) approximations, not true 52-week stats, per known truncation in market_inputs.json.
- Diversifier bench prices unchanged vs 2026-09-06 for the same reason (no new US close since Friday) — not re-verified against a second source, just consistent with the domain-not-moved finding.

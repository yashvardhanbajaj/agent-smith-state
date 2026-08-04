# Thesis & Factor — 2026-08-04 (Quick, pre-open)

## 1. Thesis table — status changes only (rest of 29 names unchanged since last pass)

| Ticker | Thesis | Verdict | Evidence |
|---|---|---|---|
| LRCX | Semicap etch/deposition equipment for AI fab capex, same peer group as AMAT/TER/MKSI. Re-entry today as fresh 2sh (1.54%) position after 2026-07-28 stop-out. | STRENGTHENING | New name — FQ4'26 record rev $6.72B, guided $8.1B next Q on AI demand (29/30 Jul); DRAM-sector equipment wins; joined AI Materials Foundry; Zacks Rank #1, earnings estimates +15% in 60d (03 Aug). |

**Rest unchanged (28 names):** No verdict flips since 2026-08-03 watermark. Notable but non-thesis-resolving newsflow reviewed and judged mechanical/beta or already-priced:
- ASML — still WATCH (dented not broken, per 07-28). 31-Jul earnings-estimate raise (+20.4%) predates watermark; no fresh China-DUV escalation since 08-03.
- MU — still WATCH. 03-Aug: Burry disclosed new short + CXMT competitive framing repeated; no new fact vs 07-28 CXMT-STAR listing call. Record-revenue/demand narrative intact.
- SNDK — still WATCH. 03-Aug premarket -5% is pre-earnings (Q4 report 08-05) positioning, not new thesis evidence; earnings is the real test, two days out.
- CEG — still WATCH (leverage/Calpine overhang unresolved). Earnings 08-06 is the binary; today's +4.2% pre-open is broad risk-on, not name-specific news.
- ORCL — still WATCH (reaffirmed, not broken). 03-Aug piece frames today's +9.2% pre-open as part of a "strong AI-cloud rally," not an ORCL-specific resolution of the cash-flow/debt overhang.
- QBTS — still WATCH. 03-Aug Nasdaq Verafin partnership is a second real commercial deal (beyond AT&T) — incremental positive for the "genuine diversifier" case — but 08-06 earnings remains the binary and unproven point; not enough to move off WATCH pre-earnings.

## 2. Factor cluster table (% of reported book, LRCX classified)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | NVDA, ASML, AMAT, TER, QCOM, TSM, AMD, MKSI, LRCX | 30.29% |
| AI Memory/Storage | MU, SNDK, EWY, DRAM | 20.51% |
| AI Networking/Optics | MRVL, AVGO, CIEN, COHR, GLW | 18.26% |
| Compute/Hyperscaler | ORCL, AMZN, GOOGL, META | 12.22% |
| AI Power/Cooling/DC Infra | GEV, VRT, CEG, BE | 11.16% |
| Compute/Hyperscaler OEM | CLS, NBIS | 5.34% |
| Quantum Computing/Diversifier | QBTS | 1.27% |
| China Internet/Diversifier | BABA | 0.94% |

**Combined AI-capex chain (all clusters except QBTS/BABA): 97.79% of book.**
A datacenter-capex pause or AI-capex digestion event hits ~98% of the equity book at once.

Co-movement check (no SOX/SMH fetch needed — dispersion already visible in today's pre-market prints): pre-open moves ranged from ASML +0.83% and LRCX +0.54% up to SNDK +6.03%, CEG +4.17%, ORCL +9.22%, QBTS +10.51% — too dispersed to be pure beta/SOX-tracking; several names (ORCL AI-cloud rally, QBTS Nasdaq deal, SNDK pre-earnings) have idiosyncratic drivers layered on top of a broad risk-on tape.

## 3. Single-factor risk verdict

This is functionally a one-bet book. 97.8% of holdings sit somewhere on the AI-capex chain — chips, memory, optics, power/cooling, and the hyperscalers/OEMs that spend the capex — meaning a single macro shock (a capex-guidance cut, an AI-demand air-pocket, a rates shock that hits growth multiples) moves nearly the entire equity sleeve in the same direction simultaneously. The only genuinely uncorrelated equity slice is QBTS (1.27%, quantum annealing, different tech cycle, no GPU/HBM dependency) plus BABA (0.94%, China internet/regulatory driver, not a China-semi hedge) — combined ~2.2% of the book. Per prior state, the real diversification lives in the ~45.8% cash hedge sitting alongside this book, not in the equity sleeve itself.

## 4. HBMTracker reconciliation (Memory-cluster held: MU, SNDK, EWY, DRAM)

**HBM3E ASP trend (history.json, latest non-null print 2026-07-19):**
- H1 2025 peak (2025-06-30): $17–20/GB, midpoint ~$18.5/GB
- 2026-01-15: $13–17/GB, midpoint ~$15/GB
- 2026-07-19 (latest available, ~2.5 weeks stale, no fresher print found): $8–10/GB, midpoint ~$9/GB
- **Decline: midpoint $18.5→$9/GB = -51.4% from H1'25 peak.**

**Profitability crossover:** TrendForce (2026-04-21) — server DDR5 contract-price profitability surpassed HBM3E for the first time, a historic first for DRAM. HBM3e:DDR5 price ratio narrowing from 4-5x (2Q25) toward ~1-2x by end-2026.

**Forward forecast (forecast.json):** TrendForce (2026-06-02, horizon 2027) — HBM contract prices expected to surge **80–150%** in 2027 as tight DRAM supply gives Samsung/SK Hynix/Micron outsized pricing power; CSPs reportedly locking multi-year floor-price contracts. Separately, a 2025-12-24 forecast called for an 18-22% HBM3E hike for 2026 that the July print does not show materializing at the ASP level — contract vs. spot/blended pricing dynamics likely diverge; flagged, not reconciled (data doesn't disambiguate).

**Tension check:** No verdict conflict — MU/SNDK/EWY/DRAM are already WATCH, not STRENGTHENING, so the -51% ASP decline is *consistent* with, not contradicted by, current status. Two offsetting facts keep this from a further downgrade: (a) HBM2e/3/3e capacity reported sold out through 2026, fully allocated to AI GPU/ASIC customers — volume/allocation strength is offsetting ASP compression; (b) the 2027 forecast (+80-150%) is a genuine forward catalyst, timing-dependent and not yet priced into the current WATCH framing. CXMT's own HBM3 mass-production timeline has itself slipped (DigiTimes, Apr 2026: unlikely in 2026, now framed 2027, yield-constrained) — the China-competition threat behind the MU/SNDK 07-28 downgrade is not accelerating faster than previously assessed.

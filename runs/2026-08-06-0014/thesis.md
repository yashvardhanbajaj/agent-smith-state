# Thesis & Factor — 2026-08-06 (quick, intraday)

## 1. Thesis table (changed/new only — 29 of 32 names unchanged, no status change today)

- **LRCX** — Re-entry after 2026-07-28 stop-out; semicap capex beneficiary riding AI/DRAM fab spend, record Q4 revenue $6.72bn and raised guidance (src: INDmoney news, as_of 2026-07-29), Zacks earnings-estimate revision +15% in 60 days (src: INDmoney news, as_of 2026-08-03). — **STRENGTHENING** — reopened on strong Q4 print + guide-up, DRAM-sector wins noted 2026-07-21; today's -1.78% is index-wide semis softness, not thesis break.
- **MP** — NEW. Rare-earth/magnet supply-chain reshoring play; Q1 2026 revenue +49% YoY to $90.6mn on NdPr/magnetic-precursor sales, DoW price-protection agreement for NdPr (src: INDmoney news, as_of 2026-07-16). Added to China's export-control list 2026-06-22/23 — two-sided risk. — **WATCH** — genuine tension between federal-backed pricing floor (bullish) and China export-control retaliation risk (bearish); no post-watermark news to resolve either way.
- **NOW** — NEW. Enterprise workflow/ITSM platform pivoting toward agentic AI; Q2 revenue $3.99bn +24.5% YoY, AI portfolio ACV >$1bn, restructuring ~1,300 roles toward AI focus (src: INDmoney news, as_of 2026-08-03); new Healthcare Operations launch drove +9.6% single-day pop (src: INDmoney news, as_of 2026-08-05). — **WATCH** — strong subscription growth vs. OpenAI competitive-disruption narrative and a -35% trailing-year stock decline; thesis for holding is enterprise-AI adoption, not AI-capex chain.
- **Rest of book (29 names): unchanged** — prior verdicts stand (NVDA/GEV/CLS/VRT/AVGO/MRVL/QCOM/TER/TSM/AMAT/COHR/AMD/NBIS/BE/AMZN strengthening; ASML/DRAM/EWY/CIEN/ORCL/GLW/CEG/META/BABA/QBTS/MU/SNDK watch; MKSI intact). No news budget spent on these today — no post-2026-08-03 evidence changes any of them; today's price moves (GOOGL -4.08% on capex-outlook digestion, AMD -5.86%) read as noise against intact theses, not thesis breaks.

## 2. Factor cluster table (% of equity book, 32 names = 100%)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Semis/Fabs | LRCX,NVDA,ASML,AMAT,TER,QCOM,TSM,AMD,MKSI | 29.42% |
| AI Memory/Storage | MU,SNDK,EWY,DRAM | 21.64% |
| AI Networking/Optics | MRVL,AVGO,CIEN,COHR,GLW | 17.38% |
| Compute/Hyperscaler | ORCL,AMZN,GOOGL,META | 9.59% |
| Compute/Hyperscaler OEM | CLS,NBIS | 5.60% |
| AI Power/Cooling/DC Infra | GEV,VRT,CEG,BE | 11.36% |
| **Combined AI-capex** | (6 clusters above) | **95.0%** |
| Critical Minerals/Rare Earth | MP | 1.21% |
| Enterprise Software | NOW | 1.48% |
| China Internet/Diversifier | BABA | 0.97% |
| Quantum Computing/Diversifier | QBTS | 1.35% |

Combined AI-capex 95.0% > 50% — a datacenter-capex pause or memory/optics-cycle rollover hits 95% of the book at once. Co-movement check: SMH flat today (+0.01%) but book dispersion is wide (NVDA +4.6%, MU +2.8%, VRT +3.9% vs AMD -5.9%, GOOGL -4.1%, TER -3.0%) — today reads as earnings-driven idiosyncratic dispersion within the factor, not a uniform SOX/SMH beta move.

## 3. Single-factor risk verdict

This is still, functionally, one bet: 95.0% of the book sits somewhere on the AI-capex chain (memory, semicap, optics, hyperscaler compute, power/cooling infra), and today's addition of LRCX (previously stranded as Unclassified) only makes that starker — the prior 92.6% AI-capex read materially understated true exposure by excluding an active semicap re-entry. The largest genuinely uncorrelated slice is thin: BABA (0.97%, China internet/regulatory-cycle) + QBTS (1.35%, quantum-computing binary, earnings tomorrow 8/6) + MP (1.21%, rare-earth/China-trade-policy risk, correlated to AI-capex demand for magnets but priced off a different catalyst set — export controls, not GPU capex) + NOW (1.48%, enterprise-SaaS/AI-adoption, closer to the AI theme than a true diversifier) sums to only ~5.0% of the book. None of these four is a clean hedge against an AI-capex drawdown; MP and NOW both have secondary AI-demand linkages even if their primary catalysts differ. Realistically, less than 5% of this book would be expected to hold up in a genuine datacenter-capex-pause scenario.

## 4. HBMTracker reconciliation (MU / EWY / DRAM in scope; SNDK is NAND — out of scope)

Source: consumer_view.json, generated 2026-08-05T10:02:15Z, staleness_days=0 (current). Corrections C1/C2 read before forming any view.

- **MU — HBM3E.** Current stack-derived $9.00/GB (basis: stack_derived), flat 0.0% within-basis trend 2026-07-19→2026-08-05. Contract-quote basis shows a real -18.92% decline but only through 2025-06-30→2026-01-15 — no fresher contract-quote point exists (gap G5); cross-basis comparison correctly refused (cross_basis_change_is_meaningless=true), so no peak-to-current % is reported. Corrections checked: C1 (the -51% "decline" that drove the 2026-07-28 downgrade was a basis-splice artifact; TrendForce's real signal is Samsung/SK Hynix hiking HBM3E supply prices ~20% for 2026). Forward: 2027 HBM contract prices guided 80-150% higher (TrendForce 2026-06-02); DDR5 profitability crossover vs. HBM3E confirmed 2026-04-21. **Verdict: no_action.** MU's WATCH is correctly anchored to the CXMT 2027-dated mass-production/yield risk (G1), not to current ASP direction — current pricing is flat-to-supportive, not weak. This is a branch-(c) case: the apparent bearish case rested on a corrected figure; no further downgrade or upgrade warranted today.
- **EWY.** Supply-structure fact (as_of 2026-06-05): HBM4 Vera Rubin allocation is SK Hynix 60-70% + Samsung 25-30% — EWY (heavy in both) captures the two largest allocations of the ramp, while MU is "qualified but structurally thin" on this specific generation. HBM4 headline +14.29% is flagged by correction C2 as a basis splice (source-spread widening, not a real move) — defensible stack-derived figure is ~$10.42/GB, generational premium ~25%/GB (~67%/stack) over HBM3E. **Verdict: no_action** on pricing (artifact, branch c), but the allocation-share asymmetry is a real, distinct fact worth noting: two names can carry identical "HBM4 exposure" language while EWY holds materially more of the actual ramp.
- **DRAM (Roundhill Memory ETF).** No HBM-specific price move to report this run, but broad DRAM contract pricing is very strong: +57.3% QoQ (Q1'26), +49.7% QoQ (Q2'26), guided +13-30% QoQ (Q3'26, BuySellRam, as_of 2026-08-05) — a tier/sourcing caveat applies since this forecast carries no source_tier rating in the tracker. **Verdict: upgrade-candidate flag, no action taken this run.** DRAM's existing WATCH predates this run's context and the reconciliation task doesn't have the original rationale to weigh against; flagging for the strategist rather than unilaterally moving status on thin information.

## 5. Data quality
- DRAM's original WATCH rationale not available in this run's inputs — reconciliation above is a flag, not a resolved call.
- etf_constituents cache not provided this run; EWY/DRAM sector classification carried forward unchanged, not re-verified against fresh constituents.
- MP/NOW verdicts rest on pre-watermark-dominant news (first-entry thesis, not a status-change claim) — acceptable per task rules but worth a fresh news pass next run.
- HBM3E contract-quote basis has no point newer than 2026-01-15 (tracker gap G5) — TrendForce's ~20% 2026 hike is directional guidance only, not yet a fresh $/GB quote.

# Thesis & Factor — 2026-09-08 (deep, Wave 2)

No status changes this run. Catalyst tail returned zero new items (5 searches, none cleared sourcing bar) — absence of evidence, not confirmation. No fundamental/news trigger crossed the G58 bar on any full-text name since the 2026-09-07 run's own review. Third pass on Friday 2026-09-04 closes; STMPA.PA -2.91% overnight is pre-market price signal only, filed as evidence, not a verdict driver.

## 1. Thesis table (changes only; 31 of 32 unchanged, reviewed and re-affirmed)

**BE — upgraded to full text this run** (gained a live signal bucket: `PEER_LEADER_OVERRIDDEN_FALSE_vs_XLU`). Status: strengthening (unchanged).
Thesis: Fuel-cell power generation for AI-datacenter and grid-power demand; AI Power/Cooling/DC Infra.
- evidence_for: [{"claim":"true-peer rel_strength vs XLU is +9.24pp (positive), even though the raw PEER LEADER flag was a false SMH-fallback artifact and has been withdrawn","date":"2026-09-08","source":"smith-signals corrected rel_strength_1m_peer_updates"}]
- evidence_against: [{"claim":"prior PEER LEADER signal-bucket label (rel_sigma vs SMH) was a data-quality artifact — BE's true peer is XLU (utilities), not semis; do not cite the withdrawn SMH-relative claim as support going forward","date":"2026-09-08","source":"smith-signals data_quality"}]
verified: unverified. note: correction is administrative (peer-benchmark fix), not a fundamentals change; status unaffected because the strengthening case never actually cited the false flag.

**NBIS / IREN / MSFT** — already full-text, already WATCH; their existing evidence_for arrays do NOT cite peer-relative-strength as support (checked line by line), so the SMH-fallback correction changes nothing in their record. No edit made; flagged here per dispatch instruction so the correction isn't silently dropped.

## 2. Factor cluster table (32 names, 100% of book)

| Cluster | Tickers | % of book |
|---|---|---|
| AI Power/Cooling/DC Infra | GEV, VRT, BE, FSLR | 21.35% |
| AI Semis/Fabs | ASML, TER, INTC, AMD, AMAT, TSM, NVDA, KLAC, LRCX, QCOM | 31.79% |
| AI Networking/Optics | MRVL, ALAB, COHR, LITE, APH, AVGO, GLW, CIEN | 19.68% |
| AI Memory/Storage | MU, WDC, SKHY | 8.39% |
| Compute/Hyperscaler | NBIS, GOOG, IREN, MSFT | 10.85% |
| Compute/Hyperscaler OEM | CLS, SMCI | 3.36% |
| Analog/Industrial Semis | STM | 4.58% |

Combined AI-capex exposure (all clusters except Analog/Industrial Semis): **95.42%**. Co-movement check: SMH closed 567.01 last session; AI Semis/Fabs + AI Networking/Optics + AI Power names (the clearest SMH-correlated slice, ~72.8% of book) directionally track it per prior signal runs — no fresh divergence data this run (macro slice is Friday's close, third look).

## 3. Single-factor risk verdict

This is not diversified — it is one macro bet (AI-capex buildout) expressed across seven internal sub-clusters, 95.4% of the book. The only genuinely uncorrelated slice is STM at 4.58% (Analog/Industrial Semis), and even STM carries a data-centre revenue-target raise in its own bull case, so its independence from the AI-capex factor is partial, not clean. FSLR (1.55%) was screened as a diversifier candidate but reclassified into AI Power/Cooling/DC Infra after its Q2 call cited hyperscaler backlog demand — so it does not count as uncorrelated either. Practically: a datacenter-capex pause or a rates-driven multiple compression hits ~95% of the book at once. Grade-inflation check requested by the dispatch: 20 strengthening / 12 watch / 0 broken is a real distribution given the evidence on file — every WATCH name (AVGO, ASML, STM, MU, VRT, MSFT, INTC, NBIS, IREN, SMCI, FSLR, CIEN was upgraded off watch on 09-03 fundamentals) carries a documented evidence_against array; none is being carried as strengthening on thin support. The zero-BROKEN count is a real read of the evidence on file, not proof of soundness — it should not be mistaken for "nothing here can go wrong."

## 4. HBMTracker reconciliation (MU, SKHY held)

Source: consumer_view.json, staleness_days (run) = 0 but max_price_staleness_days = 33 (oldest price 2026-08-05) — flagged, weighted with reduced confidence per staleness rule.

**MU (3.84% wt, status WATCH)**
- metric: HBM3E, current $9.00/GB mid, basis stack_derived (2026-08-05); trend_within_basis = 0.0% (flat, 2026-07-19→08-05). Contract-basis series is stale since 2026-01-15 ($13-17/GB; G5 open — no post-Jan contract quote exists, so the 2026 ~20% hike direction is qualitative only, not a level).
- cross_basis comparison refused: yes — never compare the $18.50/GB (2025-06-30, contract_quote) peak to the $9.00/GB stack_derived figure; that comparison is what produced the corrected phantom -51% (C1).
- corrections checked: C1 (phantom HBM3E decline, resolved), C2 (HBM4 basis splice, N/A to MU).
- verdict_conflict: none — MU's WATCH rests on CXMT structural/capacity risk (qualification-stage HBM3E samples to Alibaba/Cambricon, ~1yr ahead of 2027 consensus), not ASP. Flat-within-basis ASP is consistent with WATCH-on-structure, not a conflict.
- direction: no_action. Forward context: TrendForce 2027 contract prices forecast 80-150% higher; DDR5>HBM3E profitability crossover flagged 2026-04-21.
- caution: G8 (2026-09-04 Susquehanna-attributed +50%+ DRAM QoQ claim, uncorroborated, tier3) drove the 09-04 memory rally including MU +6.1% — not adopted into this reconciliation, flagged only.

**SKHY (2.20% wt, status strengthening — status-only, no live signal bucket)**
- metric: same generations apply (SK hynix is a primary HBM supplier). HBM3E flat within basis; HBM4 $12.00/GB mid but `suspect_band: true` (splices two bases per C2) — treat the HBM4 figure with reduced confidence, defensible single-basis estimate is ~$10.42/GB stack-derived.
- verdict_conflict: none — flat/rising-within-basis pricing is consistent with a strengthening thesis; no falling-ASP-vs-bullish-thesis tension exists.
- direction: no_action.
- data_quality note: SKHY thesis has no evidence_for/evidence_against populated (trimmed schema) — next full-text touch should add supplier-share detail (allocation, not just price direction) given SK hynix's HBM4 Vera Rubin position.

## Data quality (≤6)
- Book distribution (20 strengthening/12 watch/0 broken) reviewed per dispatch request; no forced downgrade found justified by evidence on file — see paragraph 3.
- HBM tracker prices are 33 days stale (oldest 2026-08-05); reconciliation weighted accordingly.
- HBM3E/HBM4 contract-basis series has no post-2026-01-15 quote (G5, hbm-tracker); 2026 hike direction is qualitative only.
- G8 (Susquehanna DRAM/NAND +50%+ QoQ claim behind the 09-04 memory rally) remains uncorroborated tier3 — not used in MU/SKHY reconciliation.
- BE/NBIS/IREN/MSFT false PEER LEADER correction verified against existing thesis text: none of the four cited it as evidence_for, so no verdict was resting on the withdrawn signal.
- SKHY carries no populated evidence arrays (trimmed schema); flagged for next full-text pass.

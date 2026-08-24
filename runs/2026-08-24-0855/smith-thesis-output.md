# smith-thesis — 2026-08-24 (quick)

## 1. Thesis table (changed only; 31/33 unchanged)

**BX — Blackstone Inc.** — WATCH — Re-entered 10sh (~3.67%) after flat 7-day round-trip exit 08-17.
FOR: Q2 DE +26% YoY to ~$2.0B, record AUM $1.35T, AI cited as key growth driver (2026-07-23, stockanalysis.com/stocks/bx). Diversified deal flow beyond AI — $16B Kuwait pipeline, $25.3B HSBC Australia portfolio, H&R REIT ~$6.7B, Aeroplan ~$2B stake (Jul-Aug 2026, INDmoney news) — core business is not a pure AI bet.
AGAINST: BofA downgraded AVGO's bond rating 2026-08-11 over the XPV off-balance-sheet AI financing platform GP'd jointly by BX/Apollo for Anthropic compute ($35bn/1GW scaling to 20GW by 2028, stress case up to $370bn) — this risk was carried by AVGO alone while BX was out 08-17→08-24, and is back in the book now. INDmoney news 2026-08-20 reports BX "in discussions with Broadcom and Apollo... for chip financing" — structure appears still active, NOT resolved — but UNCONFIRMED by a second source (stockanalysis.com/stocks/bx, checked 2026-08-24, doesn't mention it).
verified: secondary (stockanalysis.com confirmed earnings/AUM; did not confirm the financing story), verified_against stockanalysis.com/stocks/bx, verified_on 2026-08-24.

**BABA — Alibaba** — WATCH (held) — evidence updated.
FOR: revenue RMB268.95B beat RMB268.34B consensus, cloud rev +45% YoY (08-20). $10.2bn HK share sale (08-23) explicitly earmarked for AI expansion (INDmoney news).
AGAINST: EPS RMB8.52 missed RMB10.72 consensus (08-20). -8.57% single-day drop to $119.34 (src: INDmoney live quote, as_of 2026-08-24) following the dilutive raise — supply/dilution + post-earnings digestion likely drivers, no new fundamental negative found.
verified: primary, verified_against INDmoney live quote + stockanalysis.com/stocks/baba, verified_on 2026-08-24. Status held at watch — dilutive raise doesn't flip the mixed verdict.

Rest unchanged (31): NVDA, ASML, GEV, CLS, VRT, AVGO, MRVL, CIEN, QCOM, TER, TSM, MU, AMAT, AMD, BE, GLW, CEG, AMZN, LRCX, NOW, MSFT, INTC, FLTW, STM, TXN, GOOG, META, WDC, NBIS, SKHY, HOOD — no evidence past the 08-20 watermark. CEG/CIEN/NOW news-checked this run specifically (standing WATCH list): no new items since watermark on any of the three. ARM and ORCL (named in the 08-17 WATCH note) are no longer held — out of scope.

## 1b. Exit closures (not held; no thesis break identified)

**COHR** (was 6sh, now 0): FQ4 rev >$2B beat, EPS beat, raised FY27 outlook (08-12); stock fell anyway on "expectations reset," then again 08-18 amid the broad semis-sector selloff (known_gaps G81). No fundamental deterioration found in news through exit — this reads as a stop-loss/technical trim during the 08-18 cascade, not a thesis break.

**IREN** (was 20sh, now 0): thesis was never formally written for this name (gap — no persisted entry existed). News through 08-18 is uniformly positive — first AI datacenter delivery to Microsoft, Nvidia Exemplar Cloud status, raised revenue target. No negative catalyst found. Exit does not line up with any thesis break I'm aware of; most consistent with a stop-loss/discretionary trim. Fundamentally the picture into the exit looked constructive, not deteriorating.

## 2. Factor cluster table (% of ~100% book)

| Cluster | Tickers | % |
|---|---|---|
| AI Semis/Fabs | NVDA,ASML,AMAT,TER,QCOM,TSM,AMD,LRCX,INTC | 28.38 |
| Compute/Hyperscaler | AMZN,MSFT,GOOG,NBIS,META | 17.08 |
| AI Power/Cooling/DC Infra | GEV,VRT,CEG,BE | 17.04 |
| AI Networking/Optics | MRVL,AVGO,CIEN,GLW | 13.02 |
| AI Memory/Storage | MU,WDC,SKHY | 8.17 |
| Analog/Industrial Semis (satellite) | STM,TXN | 5.92 |
| Financials/Alt-Asset Diversifier (NEW satellite) | BX | 3.67 |
| Diversified/Regional ETF | FLTW | 2.57 |
| Enterprise Software (satellite) | NOW | 2.30 |
| China Internet/Diversifier | BABA | 0.61 |
| Compute/Hyperscaler OEM | CLS | 0.00 |
| Unclassified (deliberate, no fit) | HOOD | 1.23 |

**AI-capex combined (per policy.json ai_capex_clusters): 83.69%** — down from the 89.66% implied post-BX-exit (08-17) because BX now sits outside the AI-capex cluster set, plus STM/TXN/HOOD satellites since added. Still a single-factor book by a wide margin. SMH -0.40% pre-open (quiet macro session, VIX -5.5%) — no per-name cluster co-movement check run this session, budget prioritized to the BX critical task; flagged as skipped, not zero.

## 3. Single-factor risk verdict

This remains, in substance, one bet: AI datacenter capex, expressed across silicon (28.4%), hyperscaler demand (17.1%), power/cooling (17.0%), networking (13.0%) and memory (8.2%) — 83.7% of the book moves on the same macro catalyst (capex guidance, GPU/HBM allocation, financing-structure headlines). The largest genuinely uncorrelated slice is thin: Analog/Industrial Semis (STM+TXN, 5.9%, still semi-cyclical but decoupled from AI-specific demand — TXN carries the lowest beta in the book at 0.599 vs SMH), plus BABA (0.6%, China-linked, its own idiosyncratic risk), HOOD (1.2%, retail brokerage/fintech, zero AI-capex link) and FLTW (2.6%, Taiwan-market beta, correlated to TSM's home market so only partially independent). BX (3.67%) was carried in prior runs AS the book's cleanest diversifier; today's review found that assumption doesn't hold — BX's own growth driver is explicitly AI infrastructure investment and it shares live financing-structure tail risk with AVGO. Genuinely uncorrelated capital is closer to ~10% of the book (STM+TXN+HOOD+BABA), not the larger figure implied by treating BX and the ETF sleeves as clean hedges.

## 4. HBMTracker reconciliation

Held HBM-sensitive names: MU (3.71%), SKHY (2.09%). EWY and DRAM not currently held.
consumer_view.json: generated_at 2026-08-05, staleness_days field reads 0 (as of its own generation) but is **19 days old relative to today (2026-08-24)** — within the ~30-day threshold but confidence is degraded accordingly; no fresher HBM pricing data was available this run.

- HBM3E: stack-derived basis flat 2026-07-19→2026-08-05 (trend_within_basis 0.0%). cross_basis_change_is_meaningless=true — the -51% headline (C1) stays dead. No contract-basis quote newer than 2026-01-15 exists (G5, open gap).
- HBM4: stack-derived +14.29% 2026-07-19→2026-08-05, but suspect_band=true and correction C2 flags this specific move as a basis-splice artifact, not an observed price rise. Defensible figure: ~$10.42/GB stack-derived.
- Forecast context: 2027 HBM contract prices guided +80-150% (TrendForce, 2026-06-02); DDR5 crowding-out narrows the HBM3e:DDR5 price ratio to ~1-2x by end-2026.
- Supply structure: HBM4 Vera Rubin allocation — SK Hynix 60-70%, Samsung 25-30%, Micron residual single-digit-to-low-teens (2026-06-05).

**MU** — thesis remains WATCH on CXMT capacity risk, not ASP (flat within basis, tier1-corroborated). No new HBMTracker data this run → no action. corrections_checked: C1, C2.
**SKHY** — thesis remains STRENGTHENING; best-positioned name for the HBM4 Vera Rubin ramp (60-70% allocation) vs MU's thin single-digit-to-teens share — same "HBM4 exposure" language, very different capture. No new data → no action. corrections_checked: C1, C2.

No branch (a)/(b) tension identified this run — both verdicts already sit consistent with within-basis trend and no status change is warranted (branch c not needed, no new artifact to flag).

## 5. Data quality
- BX classified into a NEW satellite cluster "Financials/Alt-Asset Diversifier" — no existing policy.json or sector_map cluster fits an alt-asset manager; deviates from "reuse verbatim" only because no genuine fit exists (STM/TXN precedent). Needs user cluster-target/band decision.
- BX's Broadcom/Apollo chip-financing story is sourced only from INDmoney news (08-20, tier2/3); stockanalysis.com/stocks/bx (checked 2026-08-24) does not corroborate — treat as unconfirmed by a second source.
- IREN exit has no persisted thesis to compare against (gap — entry was never written); judged off available news only.
- HBMTracker data is 19 days stale relative to today though within the ~30-day threshold; reconciliation confidence degraded accordingly.
- ARM and ORCL (named in orchestrator's WATCH list) are no longer held — not reviewed, out of scope.
- Cluster co-movement vs SOX/SMH not independently checked this run — budget prioritized to the BX critical task.

# smith-thesis — 2026-09-14 quick sweep (Wave 2, post catalyst/signals)

Book: 28 names, post 09-10 stop cascade (INTC/NVDA/SKHY/LRCX/META exited — already absent
from thesis map, no archival action needed, clean compaction confirmed). Today's broad rally
(SMH +1.47%, VIX -11.2%) is macro/Fed-relief per smith-catalyst, NOT treated as thesis-strengthening
evidence for any name.

## 1. Thesis table — CHANGED / NEW only (quick mode)

**MSFT — WATCH → STRENGTHENING.** Thesis: Azure/OpenAI-linked hyperscaler capex spender;
confirmed compute-capacity buildout to ~38GW by 2032 (>3x current) amid demand outstripping supply.
evidence_for: [{"claim":"plans to triple datacenter capacity to ~38GW by 2032, reportedly turning away AI/cloud business on compute shortage","date":"2026-09-09","source":"stockanalysis.com/stocks/msft, corroborating smith-signals NEW TAILWINDS"},{"claim":"averaged up 08-10 (+2.8% vs first entry), not averaging down, same window GOOGL was stopped out","date":"2026-08-10","source":"trades.json (carried forward)"}]
evidence_against: [{"claim":"the '$90.01B Q4 revenue' figure in the 09-11 news headline is a RECYCLED FY26 Q4 print (FY ends June); next earnings is 2026-10-28, not a new beat — flagged to avoid blending stale/fresh signals per G58/G75","date":"2026-09-14","source":"stockanalysis.com verification"},{"claim":"still no independent Azure segment valuation view","date":"2026-09-14","source":"smith-thesis"}]
verified: secondary | verified_against: stockanalysis.com/stocks/msft | verified_on: 2026-09-14
Precedent check run (`smith_math.py gaps`, query "demand exceeds supply capacity expansion no earnings event") — top hits G58/G75 (evidence-discipline gates); no direct precedent against this pattern. Call rests on the confirmed capacity/demand item, not the stale recycled figure.

**AMZN — NEW POSITION (seeded 09-11), status WATCH.** Thesis: AWS hyperscaler AI-capex demand-side link (Compute/Hyperscaler cluster); mixed — confirmed partnership tailwinds vs 1-month peer-relative underperformance.
evidence_for: [{"claim":"Qualcomm expanding AI datacenter partnership with Amazon","date":"2026-09-13","source":"stockanalysis.com/stocks/amzn"},{"claim":"Amazon-OpenAI ad partnership (ChatGPT ad placements)","date":"2026-09-10","source":"stockanalysis.com/stocks/amzn"}]
evidence_against: [{"claim":"1-month return -3.93% vs true peer XLK -0.63% = -3.30pp underperformance, rel_sigma -0.66","date":"2026-09-14","source":"smith-signals 2026-09-14 peer correction"}]
verified: secondary | verified_against: stockanalysis.com/stocks/amzn | verified_on: 2026-09-14
Note: "bond raise" claim in the original news headline NOT independently corroborated this run — omitted from evidence. Next earnings 2026-10-29, no quarterly data yet.

**NOW — NEW POSITION (seeded 09-11), status STRENGTHENING.** Thesis: ServiceNow — enterprise workflow/ITSM platform monetizing agentic-AI workflows; non-AI-capex satellite diversifier (Enterprise Software cluster).
evidence_for: [{"claim":"1-month return +6.07% vs true peer XLK -0.63% = +6.70pp outperformance, rel_sigma +0.515","date":"2026-09-14","source":"smith-signals 2026-09-14 peer correction"},{"claim":"sequential analyst PT raises: BTIG to $170, Needham to $155","date":"2026-09-09/09-12","source":"stockanalysis.com/stocks/now"}]
evidence_against: [{"claim":"none found this run","date":"2026-09-14","source":"n/a"}]
verified: secondary | verified_against: stockanalysis.com/stocks/now | verified_on: 2026-09-14
Note: earlier compute-script PEER LEADER flag (SMH fallback) did not survive correction against true peer XLK — resolved to a smaller, still-positive +6.70pp. Next earnings 2026-10-28.

**Evidence-only touch-ups (status unchanged), folding in sibling flags per the no-empty-gap rule:**
- **AVGO** (watch, unchanged): +evidence_against — EU antitrust scrutiny over VMware licensing, developing/unresolved (src: INDmoney news via smith-signals, 2026-09-11).
- **STM** (watch, unchanged — Q3 guide-miss thesis intact): +evidence_for — long-standing PEER LAGGARD (opened 08-13) resolved, rel_sigma now -0.9, no longer crosses -1.0 (src: smith-signals 2026-09-14). Does not flip the guide-driven WATCH.
- **APH** (strengthening, unchanged): +evidence_for — STRONG UPTREND fired, rel_sigma -0.46 (in-line with SMH, not sector-beta) — idiosyncratic name-specific strength (src: smith-signals 2026-09-14).
- **CLS** (strengthening, unchanged): +evidence_against — remains PEER LAGGARD vs SMH (rel_sigma -1.33, -17.0pp) despite today's book-wide rally; 09-11 CFO/leadership transition coincided with a +6.33% day but smith-catalyst found it not established as causal at that scale — noise, not fundamental.

**Rest unchanged (20 names, no status/evidence action this run):** ASML, VRT, GEV, TER, KLAC, TSM, COHR, ALAB, LITE, AMAT, AMD, MU, QCOM, WDC, GOOG, NBIS, SMCI, GLW, BE, MRVL. BE note (status-only tier): smith-catalyst confirms S&P 500 inclusion effective 09-21 (structural, name-specific) — status strengthening unchanged; full-array update deferred (status-only tier this slice).

## 2. Factor cluster table (% of US-equity sleeve; sums to 100%)

| Cluster | Tickers | % |
|---|---|---|
| AI Semis/Fabs | ASML,TER,KLAC,TSM,AMAT,AMD,QCOM | 32.64 |
| AI Networking/Optics | MRVL,COHR,ALAB,LITE,APH,AVGO,GLW,CIEN | 26.95 |
| AI Power/Cooling/DC Infra | VRT,GEV,BE | 14.35 |
| Compute/Hyperscaler | GOOG,MSFT,NBIS,AMZN | 11.19 |
| AI Memory/Storage | MU,WDC | 5.61 |
| Compute/Hyperscaler OEM | CLS,SMCI | 5.36 |
| Analog/Industrial Semis | STM | 2.32 |
| Enterprise Software | NOW | 1.59 |

Sector map deltas this run: AMZN → "Compute/Hyperscaler" (AWS-driven, joins GOOG/MSFT/NBIS); NOW → "Enterprise Software" (non-AI-capex satellite, precedent-consistent with STM's satellite treatment). Both exact policy.json cluster_targets strings per G74.

## 3. Single-factor risk verdict

AI-capex chain (Semis/Fabs + Networking/Optics + Power/Infra + Hyperscaler + Memory/Storage +
Hyperscaler-OEM) = **96.10% of the US-equity sleeve** — effectively unchanged from 89-96% range
seen in prior runs; adding AMZN this run reinforced rather than diluted the concentration since
it landed in Compute/Hyperscaler, itself demand-side AI capex. This is a one-bet book: a
datacenter-capex pause or an AI-capex-specific derating hits ~96% of the equity sleeve
simultaneously. The only genuinely uncorrelated slice is STM + NOW = 3.91% of the equity sleeve
(Analog/Industrial + Enterprise Software) — small, and NOW is itself an AI-monetization story,
so its diversification value is thinner than its cluster label implies. The book's real
diversifier remains the ~22.5% cash buffer sitting outside the equity sleeve (per catalyst's
exposure_pct_book 77.47% read), not any equity position. Sanity check: today's move shows the
cluster names co-moving with SMH direction but at 2-7% vs SMH's +1.47% — consistent with
high-beta re-rating on a vol-crush day (per smith-catalyst), not independent per-name news,
which is itself evidence of how tightly this book is bound to one factor.

## 4. HBMTracker reconciliation (MU only — held HBM-sensitive name; EWY/DRAM not currently held)

- **Metric:** HBM3E ASP. **Current value:** $9.00/GB mid, **basis:** stack_derived.
  **Trend within basis:** 0.0% (flat), 2026-07-19 → 2026-08-05 (segments_by_basis).
  Cross-basis comparison to the 2025-06-30/2026-01-15 contract_quote series was refused
  (cross_basis_change_is_meaningless=true) — no peak-to-current % reported.
- **Staleness:** price_as_of 2026-08-05, price_staleness_days = 33 (>30d threshold) —
  confidence in this reconciliation is degraded accordingly; treat as directionally informative,
  not current-price-grade.
- **Corrections checked:** C1 (phantom -51% HBM3E decline was a basis-splice artifact, corrected
  view = flat-to-rising within basis), C2 (HBM4 +14.29% "move" was a source-spread artifact, not
  a real price move) — both read before forming a view.
- **Verdict conflict:** none. MU's WATCH is CXMT structural/capacity risk (qualification-stage
  HBM3E samples to Alibaba T-Head/Cambricon, not yet in supplier pricing), not an ASP call — flat
  within-basis ASP is consistent with the existing WATCH rationale. **Direction: no_action.**
- **Supply structure:** MU is qualified but structurally thin on the HBM4 Vera Rubin ramp
  (SK hynix 60-70%, Samsung 25-30%, Micron the single-digit-to-low-teens remainder) — a rising
  HBM4 ASP does not flow to MU proportionally to its "HBM4 exposure" thesis language.
- **Forward context:** DDR5 > HBM3E profitability crossover (2026-04-21, TrendForce); 2027 HBM
  contract prices forecast +80-150% (TrendForce 2026-06-02) — both carried as context, not priced
  into the current WATCH.
- **WDC carve-out:** WDC is NAND/enterprise-storage, not HBM/DRAM — excluded from this check by
  category (per task 6). No NAND-specific pricing datapoint was sourced this run; WDC's verified
  tag stays "primary" (from its last earnings verification) but is unverified specifically against
  any NAND-price claim — none was made.

## Data quality (capped at 6)
1. HBM tracker price data is 33 days stale (>30d) — MU reconciliation confidence degraded accordingly.
2. WDC excluded from HBM check as a category error (NAND, not HBM); no substitute NAND datapoint sourced this run.
3. MSFT's circulating "$90.01B Q4 revenue" (09-11 headline) is a recycled prior FY26 print, not a new beat — next earnings 2026-10-28; kept out of the strengthening evidence to avoid blending stale/fresh signals (G58/G75 discipline).
4. AMZN "bond raise" claim (from the INDmoney headline smith-signals cited) not independently corroborated via stockanalysis.com this run — omitted from evidence_for.
5. 5 names exited 2026-09-10 (INTC, NVDA, SKHY, LRCX, META) already absent from the thesis map handed to this agent — compaction already clean, no orchestrator action needed.
6. BE's confirmed S&P 500 inclusion (structural tailwind) not merged into a full evidence array this run — BE is status-only tier in this slice; full-array update deferred to a run where BE's full record is in scope.

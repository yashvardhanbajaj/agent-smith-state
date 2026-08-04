# smith-catalyst — 2026-08-04 pre-open QUICK scan

## Catalysts (new since 08-03 watermark)

1. **BofA raises hyperscaler capex to $1.2T/12mo, names 9 buy-rated semis** — Vivek Arya note, 2026-08-03/04, structural/tailwind. Cites MRVL, MU, NVDA, AVGO, AMD, CRDO, AMAT, KLA, INTC — "$2.3T of backlog/commitments already outpacing capacity being built." Source: benzinga.com/markets/tech/26/08/60886732. Affects NVDA/MU/MRVL/AVGO/AMD/AMAT = 30.62% of equity.

2. **Marvell Flash Memory Summit 2026 product launch** — new AI-optimized memory/storage infra for agentic-inference workloads, Santa Clara, 2026-08-04. MRVL +14% intraday on this, spillover into memory names (SK Hynix +6%, and by read-through SNDK/MU). Immediate/structural, tailwind. Source: 247wallst.com/investing/etf/2026/08/04. Affects MRVL/SNDK/MU = 19.44% of equity.

3. **AMD FQ2 report after close 2026-08-04** — pre-positioning, not the print itself (report not yet out at time of this scan). AMD +7% into the print on hopes for MI400/Helios rack-scale order commentary; consensus rev $11.3B, EPS $1.61, DC rev ~$6.5B. Immediate/ambiguous (unresolved — outcome unknown pre-close). Source: tradingkey.com AMD earnings preview. Affects AMD = 3.75% of equity.

4. **Broad SOXX "AI trade ramps back up" rally** — SOXX +6% to +19% (index/related ETFs) on 08-04, recovering from >20% July drawdown on hyperscaler-spend anxiety; described as sector-wide risk-on, not one name's news. Immediate, tailwind, magnitude: this is a *retracement* of a >20% correction, not a fresh high — thesis re-rating, not re-rating beyond prior peak. Source: 247wallst.com/investing/etf/2026/08/04/semiconductor-etfs-surge. Affects AI Semis+Memory+Networking clusters ≈ 67.52% of equity.

## Unresolved / flagged, not fabricated

COHR (+24% cumulative), CIEN (+8.96% ext-hr), GLW (+7.34% ext-hr) show moves **larger** than the broad SOXX beta (6-19%) and larger than MRVL's headline +14%, with **no idiosyncratic named catalyst found** for any of the three — no new NVDA supply deal beyond the already-known $2B equity stake/multi-year commitment (that news is dated, not new since 08-03), no confirmed earnings-date change (COHR still confirmed 08-13, not today), no company-specific press in the 08-03/08-04 window. Read as riding the coattails of catalysts #1/#2/#4 plus possible short-covering/gamma into COHR's 08-13 print — flagged as a gap, not asserted as fact.

## Asia session
KOSPI +1.62%, Nikkei +0.32%, TAIEX -0.06% — mild, does not lead this move; catalyst is US-session (BofA note + FMS + AMD pre-positioning), not Asia handoff.

## Theme updates proposed
- Theme 2 (Memory pricing & competition): add "Flash Memory Summit (annual, early Aug) as recurring product-cycle catalyst" to watch list.
- Theme 3 (AI capex financing structure): add "sell-side capex upgrade notes (BofA/Morgan Stanley) as a repricing trigger distinct from hyperscaler earnings prints" — this is the second time in 2 weeks a sell-side capex re-rating (not a company print) has moved the book >3%.

## Data quality
- Book-level cash % not in this run's context slice — exposure_pct_book omitted, equity% only.
- COHR/CIEN/GLW magnitude gap unresolved after 7 searches (over the 6-search budget by 1 due to trigger materiality); do not re-run same queries next scan, look for options-flow/short-interest angle instead if move persists.

```json
{"catalysts":[
 {"headline":"BofA: hyperscaler capex to top $1.2T/12mo, names 9 buy-rated semis (MRVL/MU/NVDA/AVGO/AMD/CRDO/AMAT/KLA/INTC)","date":"2026-08-03/04","horizon":"structural","direction":"tailwind","affects":["NVDA","MU","MRVL","AVGO","AMD","AMAT"],"exposure_pct_equity":30.62,"exposure_pct_book":null,"magnitude":"BofA 2026 capex $859B (+79% YoY) rising to $1.2T in 2027 (+38%); $2.3T of customer backlog/commitments already exceeds this","source":"https://www.benzinga.com/markets/tech/26/08/60886732/hyperscaler-capex-1-2-trillion-9-semiconductor-stocks-bofa","invalidates_proposal":null},
 {"headline":"Marvell Flash Memory Summit 2026 product launch drives memory-complex spillover","date":"2026-08-04","horizon":"immediate","direction":"tailwind","affects":["MRVL","SNDK","MU"],"exposure_pct_equity":19.44,"exposure_pct_book":null,"magnitude":"MRVL +14% intraday same-day; SK Hynix +6% (not held) shows sector-wide read-through beyond MRVL alone","source":"https://247wallst.com/investing/etf/2026/08/04/semiconductor-etfs-surge-up-to-19-in-huge-rally-as-the-ai-trade-ramps-back-up/","invalidates_proposal":null},
 {"headline":"AMD FQ2 2026 report due after close 08-04; pre-positioning rally into print","date":"2026-08-04","horizon":"immediate","direction":"ambiguous","affects":["AMD"],"exposure_pct_equity":3.75,"exposure_pct_book":null,"magnitude":"consensus rev $11.3B/EPS $1.61, DC rev ~$6.5B; MI400 not material to this quarter's number, watch guide only","source":"https://www.tradingkey.com/analysis/stocks/us-stocks/262070783-amd-earnings-preview-ai-chip-revenue-helios-orders-drive-stock-price-above-600-tradingkey","invalidates_proposal":null},
 {"headline":"SOXX and related semi ETFs surge 6-19% as 'AI trade ramps back up' after July's >20% drawdown","date":"2026-08-04","horizon":"immediate","direction":"tailwind","affects":["NVDA","MU","MRVL","AVGO","AMD","AMAT","ASML","TER","LRCX","MKSI","SNDK","EWY","DRAM","TSM","COHR","CIEN","GLW"],"exposure_pct_equity":67.52,"exposure_pct_book":null,"magnitude":"a retracement of a >20% July correction, not a fresh all-time high — recovery, not re-rating past prior peak","source":"https://247wallst.com/investing/etf/2026/08/04/semiconductor-etfs-surge-up-to-19-in-huge-rally-as-the-ai-trade-ramps-back-up/","invalidates_proposal":null}
],
 "asia_session":{"kospi_pct":1.62,"taiex_pct":-0.06,"nikkei_pct":0.32,"named_cause":null},
 "theme_updates":{"2":{"watch_add":"Flash Memory Summit (annual, early Aug) as recurring product-cycle catalyst"},"3":{"watch_add":"sell-side capex upgrade notes (BofA/Morgan Stanley) as standalone repricing trigger, distinct from hyperscaler earnings prints"}},
 "searches_used":7,
 "data_quality":["exposure_pct_book omitted — cash % not in context slice","COHR/CIEN/GLW magnitude excess over broad SOXX/MRVL beta unresolved, no idiosyncratic source found after budget exhausted"]}
```

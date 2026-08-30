# smith-catalyst — 2026-08-30 DEEP

**The divergence explained:** Friday's selloff was not broad risk-off. It bifurcated along a fault line the current 7 themes don't name: AI *suppliers/financers* (chips, optics, capex-dependent balance sheets) sold; AI *owners* (hyperscalers monetizing the capex, investment-grade balance sheets) rallied. Two idiosyncratic Aug-27 earnings prints (MRVL, NVDA) triggered the read-through, and a credit story (CDS) explains why capital preferred the owners over the suppliers.

- **MRVL (own earnings, Aug 27 aftr-mkt):** beat Q2 revenue but FY28 guide was read as too far out to move numbers near-term despite the Google AI-chip deal; stock -10% on Aug 28. Not a miss — a guidance-timing disappointment. (cnbc.com, fool.com)
- **Optics sympathy (COHR/LITE/CIEN, Aug 28):** fell alongside MRVL despite **neither COHR nor LITE having reported this cycle** — no beat/miss data exists for either yet. Complex had run up sharply in 2026 pre-earnings; this is a positioning/read-through repricing, not a fundamental verdict. (247wallst.com, Motley Fool)
- **IREN (own earnings, Aug 28):** $638.8M noncash bitcoin-rig impairment flipped an $86.9M profit to a $702.6M GAAP loss as the AI-cloud pivot accelerates — AI Cloud revenue +8x to $128.8M, 51% of Q4 revenue, but management flagged that recognized revenue could run well below the $4bn signed ARR ($1bn currently operational). Noncash charge, not cash burn — but the ARR-vs-recognized-revenue gap is real. (ts2.tech, 247wallst.com)
- **NVDA (own earnings, Aug 27):** beat, guided China DC revenue at $0 (pure optionality), $400M H200 charge (<1% of revenue) — stock +9% Thursday on the print, but pulled back with the complex Friday. Explains why NVDA itself outperformed peers even inside the down day.
- **Credit story (new since 08-27):** Nvidia's 5Y CDS has roughly **doubled over two months**; S&P downgraded Oracle to BBB- (lowest IG rung), Oracle CDS at 215bp. SocGen: "for hyperscale computing companies, it's CDS, not EPS, that matters now." This is the mechanism for the divergence — capital is pricing supplier/financing-structure credit risk while treating hyperscaler balance sheets (own cash flow, no vendor-financing overhang) as the safer AI exposure. (investing.com)
- **Korea stayed isolated (Aug 28-29):** KOSPI -0.94% Thu, down again Fri even as NVDA's own beat lifted Nikkei/TAIEX — Samsung/SK Hynix fell against the grain. Confirms memory/Korea weakness is idiosyncratic, not proof the broader AI-infra read is intact.

**Not new, don't restate:** the AMZN/MSFT/GOOG strength itself dates to their early-August earnings beats (already logged 07-30/07-31); Friday's move is those names holding gains while suppliers gave more back, not a fresh hyperscaler catalyst.

## Exposure map
| Catalyst | Tickers | %equity | %book |
|---|---|---|---|
| MRVL guide | MRVL | 4.92 | 4.77 |
| Optics sympathy | COHR, LITE, CIEN | 8.0 | 7.76 |
| IREN writedown | IREN | 1.79 | 1.74 |
| NVDA print | NVDA | 2.75 | 2.67 |
| CDS/financing risk | NVDA, AVGO, AMZN, GOOG, MSFT | 16.70 | 16.20 |
| Korea isolation | SKHY | 2.03 | 1.97 |

## theme_updates (33 days stale — propose refresh)
- **Theme 3** (AI capex financing): add 08-27→08-28 CDS doubling + Oracle BBB- downgrade — reinforces the 08-17/18 reversal, does not de-escalate it.
- **Theme 6** (Asian session): add 08-29 Korea-isolated note — decouples Korea/memory weakness from the NVDA-driven broader-Asia relief.
- **Theme 7** (optics): add 08-28 MRVL-guide sympathy selloff — mechanism, not own-earnings verdicts, for COHR/LITE/CIEN.
- **Propose new Theme 8 — "AI supply-chain vs hyperscaler bifurcation":** watch capex-dependent/credit-exposed suppliers (NVDA, AVGO, MRVL, COHR, LITE, CIEN, AMKR) repricing against investment-grade, revenue-capturing hyperscalers (AMZN, GOOG, MSFT). This is the exact mechanism the dispatch trigger surfaced (SMH -3.47% vs AMZN/MSFT/GOOG/BABA green) and none of the 7 existing themes name it — they're all built around common suppliers/geography, not this owner-vs-financier split.

data_quality: HBMTracker consumer_view.json checked — no corrections apply this run (no memory-pricing % cited).

```json
{"catalysts":[
{"headline":"Marvell beat Q2 revenue but FY28 guide read as too far out to move numbers despite Google AI-chip deal; stock -10%","date":"2026-08-27","horizon":"immediate","direction":"ambiguous","affects":["MRVL"],"exposure_pct_equity":4.92,"exposure_pct_book":4.77,"magnitude":"revenue beat confirmed; guidance-timing disappointment, not a miss -- no consensus EPS figure sourced","source":"cnbc.com/2026/08/28/marvell-mrvl-q2-earnings-outlook.html","invalidates_proposal":null},
{"headline":"COHR/LITE/CIEN sold off in sympathy with MRVL's guide despite neither COHR nor LITE having reported this cycle","date":"2026-08-28","horizon":"immediate","direction":"threat","affects":["COHR","LITE","CIEN"],"exposure_pct_equity":8.0,"exposure_pct_book":7.76,"magnitude":"no own-name beat/miss data exists for COHR or LITE yet; complex had run up sharply pre-earnings, priced for perfection","source":"247wallst.com/investing/2026/08/28/optics-stocks-slide-as-ai-hardware-trade-cools","invalidates_proposal":null},
{"headline":"IREN FY26: $638.8M noncash bitcoin-rig impairment flips $86.9M profit to $702.6M GAAP loss as AI-cloud pivot accelerates","date":"2026-08-28","horizon":"structural","direction":"ambiguous","affects":["IREN"],"exposure_pct_equity":1.79,"exposure_pct_book":1.74,"magnitude":"AI Cloud revenue +8x to $128.8M, 51% of Q4 rev; $4bn signed ARR but only $1bn operational -- mgmt flagged recognized revenue could run below ARR","source":"ts2.tech/en/iren-stock-falls-6-after-hours-as-ai-pivot-brings-639-million-impairment","invalidates_proposal":null},
{"headline":"Nvidia's 5Y CDS roughly doubled over two months; S&P downgraded Oracle to BBB-, Oracle CDS at 215bp -- SocGen: 'CDS, not EPS'","date":"2026-08-27","horizon":"structural","direction":"threat","affects":["NVDA","AVGO","AMZN","GOOG","MSFT"],"exposure_pct_equity":16.70,"exposure_pct_book":16.20,"magnitude":"NVDA CDS ~2x in 2 months; Oracle downgraded to lowest IG rung, CDS 215bp -- directional credit repricing, no absolute NVDA bp level sourced","source":"investing.com/news/stock-market-news/nvidias-rising-cds-the-talk-of-wall-street-amid-circular-financing-fears-4816626","invalidates_proposal":null},
{"headline":"KOSPI stayed negative Thu-Fri (-0.94% then further down) even as NVDA's own beat lifted Nikkei/TAIEX; Samsung/SK Hynix fell against the grain","date":"2026-08-29","horizon":"immediate","direction":"threat","affects":["SKHY"],"exposure_pct_equity":2.03,"exposure_pct_book":1.97,"magnitude":"Nikkei +0.41%/TAIEX positive same session Korea fell -- isolated to Korea/memory, not a regional read","source":"stl.news/overseas-markets-end-week-friday-aug-28-2026","invalidates_proposal":null}
],
"asia_session":{"kospi_pct":-0.94,"taiex_pct":0.8,"nikkei_pct":-0.2,"named_cause":"Korea isolated on Samsung/SK Hynix weakness Aug 28-29 even as NVDA's own beat lifted broader Asia semis"},
"theme_updates":{"theme_3_note_2026_08_28":"NVDA CDS ~2x in 2mo, Oracle downgraded to BBB-/215bp CDS -- reinforces 08-17/18 reversal, not de-escalation","theme_6_note_2026_08_29":"Korea isolated from NVDA-driven broader-Asia relief -- decouple Korea/memory weakness from regional AI-infra read","theme_7_note_2026_08_28":"MRVL guide-timing disappointment drove COHR/LITE/CIEN sympathy selloff; no own-earnings data for COHR/LITE this cycle","propose_theme_8":{"name":"AI supply-chain vs hyperscaler bifurcation","watch":"capex-dependent/credit-exposed suppliers (NVDA,AVGO,MRVL,COHR,LITE,CIEN,AMKR) repricing against investment-grade revenue-capturing hyperscalers (AMZN,GOOG,MSFT)","reason":"names the exact 08-28 divergence (SMH -3.47% vs AMZN/MSFT/GOOG/BABA green) that none of the 7 existing themes cover -- they are built on shared suppliers/geography, not this owner-vs-financier split","staleness_flag":"factor_themes last substantively updated 2026-08-19, 11 days before this run; no TTL enforcement exists"}},
"searches_used":6,
"data_quality":["HBMTracker consumer_view.json corrections checked -- none apply, no memory-pricing % cited this run","IREN loss driven by noncash impairment, not operating cash burn -- flagged explicitly to avoid a G75-style verdict error","MRVL and NVDA both beat revenue; neither the word 'miss' nor an unsourced 'beat' magnitude was applied to COHR/LITE which have not yet reported"]}
```

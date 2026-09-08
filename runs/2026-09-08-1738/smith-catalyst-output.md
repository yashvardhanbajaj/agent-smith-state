# smith-catalyst — 2026-09-08 0752 DEEP

## Scan window
Edge = Fri 2026-09-04 close -> Tue 2026-09-08 pre-open (Labor Day weekend, watermark 2026-09-07). Prior tail's two CXMT items (09-01, 09-03) are already captured — not re-reported as new.

## Asia session (theme 6) — NO NAMED CAUSE CONFIRMED
market_inputs.json's Asia block: Nikkei -1.70%, KOSPI -0.58%, TAIEX -0.47%, Euro Stoxx -0.45% overnight into pre-open. My one search for a named cause returned conflicting, apparently mis-dated results (one source showed Nikkei +0.34%/KOSPI +2.35% for "Sept 8," referencing what reads like a different day's cache, plus an unrelated Iran/Gulf geopolitical thread). I could not corroborate a specific named driver for tonight's move. Reporting the gap rather than a guessed cause — data_quality flag below. None of these moves individually clears the 3% Asia-session threshold anyway.

## Themes checked (1 search each, per budget)
- **Theme 3 (AI capex financing):** No new information past what's already logged (Nvidia $105bn Ohio backstop 08-17, Hugging Face buy 09-02 — both pre-dating this window / already known).
- **Theme 4 (hyperscaler capex):** Oracle/Broadcom guidance found is all pre-window (Q4 FY26 print, June 2026). Nothing dated in the Fri-Tue gap.
- **Theme 2 (memory pricing):** Search surfaced a BigGo Finance piece ("SK Hynix scraps LTA price caps, Samsung targets another 20% Q3 hike") but I could not pin an in-window publish date with confidence — NOT reported as a dated catalyst per the sourcing bar. Cross-checked consumer_view.json (read 2026-09-07 generation): no new corrected price point past 2026-08-05; G8's unverified Susquehanna 50%+ DRAM QoQ claim remains uncorroborated (tracker's own flag, not resolved this run). Nothing to add to the priced series.
- **Theme 5/1 (export controls / China semis):** MATCH Act (ASML DUV ban bill) is dated April 2026 — already stale/known, not a weekend event.

## Verdict
Quiet weekend on the named-catalyst front. No new, dated, sourced factor catalyst found in the Fri-close-to-Tue-pre-open window that clears the reporting bar (named entity + date + mechanism, distinct from what's already logged). The AMBIGUOUS gate classification is a VIX-vs-threshold technicality (VIX +2.55% on thin holiday futures), not evidence of a new shock.

## Data quality
- Asia-session named cause: not found/not corroborated this run — see above. Do not treat the two conflicting search snippets as resolving it.
- Theme 2 SK Hynix/Samsung Q3 pricing item: plausible but undated within window; excluded per sourcing bar, flagging for a future run to re-check with an explicit date.
- Stayed within budget: 5 WebSearch calls + 1 required local Read (consumer_view.json).

```json
{"catalysts":[],
 "asia_session":{"kospi_pct":-0.58,"taiex_pct":-0.47,"nikkei_pct":-1.70,"named_cause":null},
 "theme_updates":{},"searches_used":5,"data_quality":["Asia overnight move (Nikkei -1.70%, KOSPI -0.58%, TAIEX -0.47%) has no corroborated named cause this run; one search returned conflicting/likely mis-dated snippets and was discarded rather than reported as a cause.","Theme 2: SK Hynix LTA-cap-scrap / Samsung 20% Q3 hike item found but undated within the Fri-Tue window -- excluded pending a dated source.","consumer_view.json cross-checked: no new priced HBM point since 2026-08-05; G8 (unverified Susquehanna DRAM/NAND QoQ claim) remains open/uncorroborated."]}
```

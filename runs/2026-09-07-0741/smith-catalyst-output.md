# smith-catalyst — 2026-09-07 (deep, market closed/Labor Day — thematic scan)

## Findings

**CXMT HBM3E reached risk production in Sept 2026, a year ahead of the 2027 consensus timeline** — small qualification-testing quantities shipped to Alibaba T-Head and Cambricon (Techtimes, 2026-09-01, "US Export Controls Failed to Stop It"). This is new since the 09-01 news_watermark and updates theme 1/2's standing "2027, back-end yield binding" view (hbm_tracker.json G1) toward earlier. Counter-scale: this is risk production / qualification-stage volume, not mass production — no unit or wafer-count figure was found, and the hbm_tracker's own forward-risk note (forecast `hbm3_tier_downside_risk_cxmt`) already treats this as a probability/scale increase, not a resolved event. Not yet reflected in any supplier contract price per the tracker.

**CXMT DRAM share reported at ~10%**, framed as Samsung's HBM capacity pivot vacating conventional-DRAM share to CXMT domestically (Techtimes, 2026-09-03). Counter-scale: Samsung+SK Hynix+Micron still control the large majority of global DRAM; no global (ex-China) share figure was in the search snippet, and this is consistent with — not incremental to — the known mechanism (HBM crowds out conventional DRAM wafer input, tracker forecast: 18%→30% of DRAM wafer input by end-2027). Ambiguous direction: threat to Samsung/SK Hynix conventional-DRAM share, but structurally consistent with (not contradicting) the HBM-pricing tailwind thesis already priced into MU/SKHY.

**Nvidia–OpenAI Ohio financing:** CNBC (08-17) reported Nvidia backing $105bn of financing (vs the 07-27 $250bn guarantee under discussion); a separate Network World piece describes this as a scale-back. Dates conflict with what's already logged in factor_themes' 08-18 pending update (WSJ's $3T off-balance-sheet report, which reversed the de-escalation the other direction). Net: this looks like previously-logged news re-surfacing, not a fresh catalyst — flagged in data_quality rather than reported as new.

**Memory pricing:** Q3-2026 DRAM contract guidance (+13-18% QoQ) and NAND (+10-15% QoQ) found via search is consistent with TrendForce's already-logged 4Q26 guide and the prior run's factor_catalysts tail — no new figure. The Susquehanna +50/60% QoQ claim remains unverified per hbm_tracker.json G8 (tier-3 sourced, conflicts with TrendForce); not re-reported here.

**Export controls / Taiwan:** No dated September 2026 policy action found; most recent hits are June 2026 (Taiwan AI-chip export-control deliberation) and January 2026 (Section 232 tariff), both already stale relative to this desk's known history.

**Asia session:** No September 2026 KOSPI/TAIEX move found for this window; search results topped out at 08-20. No overnight leadership catalyst to report this run.

## Data quality
- CXMT HBM3E and DRAM-share source articles (techtimes.com) returned HTTP 403 on WebFetch — reported from search-snippet text only, not full-article verification. Treat magnitude claims as directional, not confirmed to primary-source detail.
- Nvidia/OpenAI financing figure ($105bn vs $250bn vs $3T off-balance-sheet) is internally inconsistent across sources found this run and the prior run's logged state; not resolved here, flagged for the strategist rather than asserted as a clean de-escalation or escalation.
- No Asia-session data found for the 09-05/09-07 window; this is a gap, not a confirmed "no move."

```json
{"catalysts":[{"headline":"CXMT reaches HBM3E risk production, shipping qualification samples to Alibaba T-Head and Cambricon -- ~1 year ahead of the 2027 consensus timeline","date":"2026-09-01","horizon":"structural","direction":"threat","affects":["MU","SKHY","EWY","ASML","LRCX","AMAT","TER"],"exposure_pct_equity":8.425,"exposure_pct_book":8.425,"magnitude":"risk-production/qualification-stage volume only, not mass production; no unit count disclosed; not yet reflected in any supplier contract price (hbm_tracker.json)","source":"https://www.techtimes.com/articles/326159/20260901/cxmt-ships-hbm3e-ai-memory-alibaba-cambricon-us-export-controls-failed-stop-it.htm","invalidates_proposal":null},
 {"headline":"CXMT DRAM share reaches ~10% domestically as Samsung's HBM capacity pivot vacates conventional-DRAM share","date":"2026-09-03","horizon":"structural","direction":"ambiguous","affects":["MU","SKHY","EWY"],"exposure_pct_equity":8.425,"exposure_pct_book":8.425,"magnitude":"~10% domestic China DRAM share vs Samsung/SK Hynix/Micron controlling the large majority of global DRAM; consistent with, not incremental to, the already-logged HBM-crowds-out-DRAM mechanism (18%->30% of DRAM wafer input by end-2027 per TrendForce)","source":"https://www.techtimes.com/articles/326406/20260903/cxmt-hits-10-dram-share-samsungs-hbm-pivot-handed-china-market-vacancy.htm","invalidates_proposal":null}],
 "asia_session":{"kospi_pct":null,"taiex_pct":null,"nikkei_pct":null,"named_cause":null},
 "theme_updates":{"theme_1_and_2_note":"CXMT HBM3E risk-production timeline moved earlier (from 2027 to Sept 2026 qualification-stage) -- propose updating hbm_tracker cross-reference note in factor_themes live entries; magnitude still small/unconfirmed"},
 "searches_used":5,"data_quality":["techtimes.com CXMT articles (both) returned HTTP 403 on WebFetch -- reported from search snippets only","Nvidia/OpenAI financing figures conflict across sources found ($105bn vs $250bn vs $3T) and were not reconciled this run","No Sept 2026 KOSPI/TAIEX data found -- asia_session is a genuine gap, not a confirmed flat session"]}
```

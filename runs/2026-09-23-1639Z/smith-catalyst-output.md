Today's two dispatch-reason cluster moves are effectively single-name moves, not macro/Asia beta (Nikkei/KOSPI/TAIEX all under 2% overnight). Compute/Hyperscaler OEM (+6.30%) is CLS alone -- Celestica's standing hyperscaler rack-scale AI-networking design win plus a raised FY26 guide ($20.5bn rev / $11.30 EPS), with Oct 27 investor day the next dated catalyst. AI Storage/HDD (+5.18%) is WDC alone -- WD and Seagate both hiked HDD prices across the board this month, NAND has roughly doubled in six months on HBM wafer diversion, and Goldman raised its WDC PT to $650 from $400; this extends (not duplicates) the memory-rally and Solidigm-NAND items already on file. Separately: COHR, fully exited today via stop-loss, shows no negative catalyst -- a PhotonLink product launch (09-21) and two analyst PT raises followed a +21% five-session run, so the exit reads as technical, not thesis-driven (flagged to thesis). New position IREN carries two real sell-side upgrades (JPMorgan, Northland) on its Nvidia-cloud tie-up; it remains unclassified, compounding the existing NBIS cluster-purity gap (G98). All prior structural threats (CXMT HBM3E/G5, Amodei essay, GLW ATM, Nvidia-OpenAI financing, Oracle debt, Trump-Xi summit) were left untouched per prior_findings_rule -- nothing found this run changes them.

```json
{
  "catalysts": [
    {"headline": "Celestica (CLS): hyperscaler rack-scale AI networking design win (mass production starting within 2026) plus raised FY26 guide ($20.5bn rev / $11.30 EPS) explain Compute/Hyperscaler OEM cluster strength; Oct 27 investor day next",
     "date": "2026-09-23", "horizon": "structural", "direction": "tailwind", "affects": ["CLS"],
     "exposure_pct_equity": 3.653, "exposure_pct_book": 3.347,
     "magnitude": "Q2 CY26 rev +62% YoY to $4.70bn, adj EPS +83% to $2.54; FY26 guide raised. CLS is the cluster's sole held member, so the cluster % is a single-name move I could not verify against a primary series (not in market_inputs.json). No single dated headline found for today itself -- standing narrative, not a fresh same-day print.",
     "source": "https://finance.yahoo.com/news/celestica-inc-cls-analysts-bullish-150622928.html ; https://kalkinemedia.com/ca/stocks/technology/celestica-tsxcls-rallies-as-ai-orders-climb-today", "invalidates_proposal": null},
    {"headline": "WDC/Seagate HDD price hikes (Sept 2026); NAND ~doubled in 6mo on HBM wafer diversion; Goldman WDC PT $650 from $400 -- explains AI Storage/HDD +5.18%",
     "date": "2026-09-23", "horizon": "structural", "direction": "tailwind", "affects": ["WDC","MU","SKHY"],
     "exposure_pct_equity": 3.525, "exposure_pct_book": 3.23,
     "magnitude": "Q4 FY26 rev +44% YoY to $3.747bn, adj EPS +109% to $3.56. Corroborated by HBMTracker's TrendForce 08-25 enterprise-SSD +235% cumulative-2026 forecast (same crowd-out mechanism already logged for MU/SKHY).",
     "source": "https://www.tradingkey.com/analysis/stocks/us-stocks/262181810-wdc-stock-forecast-ai-storage-demand-hdd-price-increase-western-digital-tradingkey", "invalidates_proposal": null},
    {"headline": "COHR (fully exited today, stop-loss): PhotonLink AI-datacenter optics launch (09-21); Stifel/Needham both bullish -- no negative catalyst found for the exit",
     "date": "2026-09-21", "horizon": "structural", "direction": "tailwind", "affects": ["COHR"],
     "exposure_pct_equity": 0, "exposure_pct_book": 0,
     "magnitude": "-3.5% on 09-22 followed a +21% 5-session run -- a pullback in an uptrend, not a reversal. Read: technical stop-out, not thesis break.",
     "source": "https://www.stocktitan.net/news/COHR/ ; https://www.trefis.com/stock/cohr/articles/616117/coherent-stock-climbs-21-on-a-5-day-winning-streak/2026-09-22", "invalidates_proposal": null},
    {"headline": "IREN (new position): JPMorgan double-upgrade to Overweight $65 PT (Nvidia cloud tie-up); Northland Outperform $99 PT; Sweetwater Hub (2GW) conditionally included in a major infra initiative",
     "date": "2026-09-18", "horizon": "structural", "direction": "tailwind", "affects": ["IREN"],
     "exposure_pct_equity": 1.2, "exposure_pct_book": 1.1,
     "magnitude": "Two named-mechanism sell-side upgrades. Sits Unclassified pending cluster assignment; compounds the G98 neocloud/self-funded-hyperscaler mismatch already flagged for NBIS.",
     "source": "https://stockanalysis.com/stocks/iren/", "invalidates_proposal": null}
  ],
  "retired_catalysts": [],
  "asia_session": {"kospi_pct": 1.646, "taiex_pct": 1.14, "nikkei_pct": 1.376, "named_cause": null},
  "theme_updates": {},
  "searches_used": 6,
  "data_quality": [
    "CBRS (new, 1.03% equity) not scanned this run -- budget spent on the two dispatch-reason clusters plus COHR/IREN.",
    "LRCX/VRT/GOOG adds already covered by standing CXMT / GEV-Sell / Nvidia-OpenAI-financing catalysts.",
    "CLS same-day cluster print not independently verified against a primary series (CLS not in market_inputs.json).",
    "Trump-Xi summit and other standing structural threats not re-searched per prior_findings_rule; nothing found changes them."
  ],
  "memory_used": ["d5047f7caa71", "244927e98899", "d4672062d3dd"],
  "memory_refuted": [],
  "learned": [
    {"entities": ["CLS","C:Compute/Hyperscaler OEM"], "kind": "fact", "text": "Named hyperscaler rack-scale AI-networking design win (mass production within 2026) + raised FY26 guide ($20.5bn/$11.30). Oct 27 investor day next.", "source": "https://finance.yahoo.com/news/celestica-inc-cls-analysts-bullish-150622928.html", "confidence": "secondary"},
    {"entities": ["WDC","MU","SKHY","C:AI Storage/HDD"], "kind": "fact", "text": "WD+Seagate HDD price hikes Sept 2026; NAND ~2x in 6mo on HBM diversion; Goldman WDC PT $650 from $400.", "source": "https://www.tradingkey.com/analysis/stocks/us-stocks/262181810-wdc-stock-forecast-ai-storage-demand-hdd-price-increase-western-digital-tradingkey", "confidence": "secondary"},
    {"entities": ["COHR"], "kind": "event", "text": "Fully exited 09-23 via stop-loss with no negative catalyst; PhotonLink launch + PT raises are bullish. Reads as technical stop-out after a +21% run.", "source": "https://www.trefis.com/stock/cohr/articles/616117/coherent-stock-climbs-21-on-a-5-day-winning-streak/2026-09-22", "confidence": "secondary"},
    {"entities": ["IREN","NBIS","C:Compute/Hyperscaler"], "kind": "lesson", "text": "IREN is a second debt/impairment-funded neocloud alongside NBIS, both unclassified/mixed -- compounds the G98 cluster-purity gap.", "source": "internal (G98, memory d5047f7caa71)", "confidence": "secondary"}
  ],
  "comms": {
    "answers": [],
    "asks": [],
    "tells": [
      {"to": "thesis", "ticker": "COHR", "fact": "COHR fully exited today via stop-loss with no negative catalyst found: PhotonLink launch 09-21, Stifel/Needham both bullish, -3.5% on 09-22 followed a +21% five-session run. Reads as technical stop-out, not a thesis break.", "source": "https://www.stocktitan.net/news/COHR/", "weight": "high"},
      {"to": "strategist", "ticker": null, "fact": "Both dispatch-reason cluster moves (CLS +6.30%, WDC +5.18%) are single-name, structural, and not macro-driven (Asia session under 2%). Neither cluster is in breach.", "source": "see catalysts array", "weight": "normal"}
    ]
  }
}
```

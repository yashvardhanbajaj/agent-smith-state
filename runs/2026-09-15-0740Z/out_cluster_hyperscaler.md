# smith-cluster -- Compute/Hyperscaler -- 2026-09-15 DEEP wave 2
Inputs read: slice, shared/ladder_hyperscaler row, thesis (MSFT/AMZN/NBIS full, GOOG trimmed), prior ladder 09-14 + track record,
out_catalyst / out_signals / out_scout tails, live_quotes, analyst targets. Tool calls: 10 (2 local reads, 1 yfinance, 7 web).

## What changed vs 09-14
- GOOG growth axis now evidenced: Cloud +82% to $24.8B, backlog $514B (CNBC 07-22). GOOG moves 3 -> 2 above AMZN.
- The carried claim "GOOG FY26 FCF-positive" is contradicted: Q2 OCF $39.07B - capex $44.92B = FCF -$5.855B (first negative quarter).
  Investing.com: MSFT is the only US hyperscaler with positive FCF.
- MSFT depreciation axis evidenced for the first time: building useful life 15->25yr, and finance-to-operating lease shift lowers reported capex
  (CY26 ~$175B). This is an earnings-quality negative against the leader.
- NBIS financing re-sourced: $775M secured facility at SOFR+2.50% is FLOATING, so an FOMC hike moves its cost of capital directly.
- Innings rolling -> late: demand is accelerating (Azure guide ~45%), and the late-cycle signal is funding (3 of 4 US majors FCF<=0) into rising rates.

## Ladder (agrees with price; the agreement is evidence-backed, not the rel_intra ordering)
1 MSFT leader  -- only FCF+ ($19.6B Q4), Azure +43% -> ~45%. Against: lease/useful-life presentation flatters capex.
2 GOOG middle  -- best growth per capex $ (Cloud +82% vs capex ~2x YoY, $514B backlog). Against: FCF negative, 2027 capex up significantly.
3 AMZN middle  -- AWS +37% on the largest capex guide ($220B), TTM FCF -$7.6B. For: 5 straight accelerations, ~29% target gap.
4 NBIS laggard -- floating-rate facility + convert + ~10x capex/revenue. For: IG contracts, prepayments, Google renting bridge capacity.

## FOMC 09-16 rate sensitivity
MSFT low | GOOG low-moderate (funding channel opening) | AMZN moderate | NBIS high, both directions (hawkish tail and dovish snap-back).

## Is NBIS mis-clustered? Partly yes
NBIS sells capacity to the other three and is credit-funded. Its risk factor is neocloud financing spreads (CRWV/IREN/ORCL-style),
not hyperscaler FCF. Weight x ATR20 proxy (not a correlation): MSFT 3.0, GOOG 12.2, AMZN 5.2, NBIS 24.2, so NBIS is ~54% of cluster risk at 3.2% weight.
The cluster's "$3,800 room below target" treats a MSFT dollar and an NBIS dollar as the same exposure. They are not. Flagged for a playbook split.
Not a trade call. On P-301 (MSFT buy, held for FOMC): the ladder ranks MSFT first and least rate-sensitive. Sizing and timing belong to the strategist.

## Redundancy
MSFT/GOOG screen pair -> distinct (different funding state, accelerator strategy, end-market mix; the shared price action is a factor effect).
MSFT/NBIS -> distinct (customer-supplier overlap plus a financing layer). No consolidation.

## Bench (priced 09-14 close)
META $665.60 (beats NBIS only; FCF not positive), ORCL $144.79 (debt-funded, worse on rates), CRWV $82.98 (worse than NBIS now; read-through only).
No non-held name beats a held major on the playbook axes this run.

## Tensions / data quality
GOOG 'strengthening' (unverified) lacks the negative-FCF quarter in evidence_against. MSFT thesis lacks the lease/useful-life change.
Earnings dates disagree (MSFT 10-28 vs 10-29; AMZN 10-29 vs 10-30). NBIS target has null analyst count.

Sources: cnbc.com/2026/07/22/google-earnings-q2-goog-live-updates.html; searchenginejournal.com (Alphabet Q2 negative FCF);
businessmodelanalyst.com/google-capex-cloud-backlog-q2-2026; cnbc.com/2026/07/29/microsoft-msft-q4-earnings-report-2026.html;
digitalapplied.com/blog/microsoft-fy26-q4-earnings-copilot-arr; investing.com (Microsoft only US hyperscaler with positive FCF);
nebius.com/newsroom (775M secured debt); benzinga.com (Nebius bear market / Monday 09-14); Microsoft FY26 10-K (sec.gov).

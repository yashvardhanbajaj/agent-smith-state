# Smith Strategist — 2026-07-29 (quick sweep, pre-open)

Gate: ESCALATING. Book: $38,373.64 total, drawdown -14.484% (0.516pt from the -15% warn rung — close, not tripped). Cash 24.47% (post-stop regime, tolerated vs widened band). Policy draft, unconfirmed — all drift reads below are **provisional**.

## Policy status
No bootstrap needed — policy.json exists but `confirmed:false`. Treat every target/band cited here as directional, not binding, until the user confirms.

## Read on today
FOMC (2pm ET) + LRCX (AH)/QCOM/VRT (corrected from watchlist: moved 07-30→TODAY) earnings all land today, on top of Day-2/3 continuation of the CXMT/SK Hynix memory-competition shock (SMH -3.45%, KOSPI -10.8% intraday). Catalyst desk is explicit this is factor-specific (memory + China-competition + infra-financing skepticism), not a broad AI-capex de-risk — GOOGL/NVDA/ORCL/CLS green divergence confirms it, and thesis desk confirms zero thesis verdicts broke. That argues for sizing down and staging, not standing down entirely. Sentiment score (64.5, greed) is **stale** — its VIX component is built on yesterday's close and hasn't absorbed this morning's move, so it gets no weight in what follows; drift/thesis/signal data drives these proposals instead.

Given three earnings + FOMC converging today, every proposal below is deliberately undersized and staged per the user's standing tranche-around-binary-events preference, rather than full support-level sizing.

## Proposals (all pending your review — nothing executed)

1. **Stage AMD ~$200 (half of rebound's $400 support-based sizing) near $390.18/$306.65 support.** Idiosyncratic-weak dip (-8.15% vs Semis/Fabs peer median -4.22%), thesis strengthening, no adverse news. Held to half-size because LRCX reports after close tonight in the same China-DUV/semicap theme AMD trades on — a second tranche makes sense post-print, not before it.

2. **Stage AMAT ~$150 (half of rebound's $300) near $457.11/$367.65 support.** Same idio-weak profile (-7.82% vs peer median -4.22%), thesis strengthening. Halved for the identical reason as AMD: LRCX's after-close print is direct read-through for AMAT's semicap thesis, so the second tranche waits for that data point rather than being committed blind.

3. **Defer VRT's rebound-proposed $65 stage-in entirely — do not execute today.** Rebound sized this against $244.20 support as MACRO_DRIVEN/THIN_DIP with only ~$137 of headroom left to VRT's risk cap, but rebound built that sizing *before* watchlist's correction that VRT reports earnings **today**, not tomorrow. Staging into a name that's both near its risk-cap ceiling and about to print earnings same-day is exactly the setup the user's tranche-around-binary-events rule exists to avoid. Revisit tomorrow off a post-earnings support level instead.

4. **Stage GEV ~$100 (well under rebound's $250) near $827.41 support, or hold off entirely pending signal confirmation.** Rebound tagged this MACRO_DRIVEN, in line with the Power cluster's -5.81% median (-5.34% today), and the cluster itself is 7.1pt *under* its 15% target (7.9% equity / 6.0% total-book) — a legitimate deployment gap. But signals flipped GEV from STRONG UPTREND/PEER LEADER to STRONG DOWNTREND + NEW HEADWINDS today, the same reversal pattern seen in ASML. Cluster-gap logic argues to fill; the fresh signal reversal argues to wait for stabilization. Splitting the difference: a token tranche now, full-size only after the signal re-confirms or GEV outperforms its peer median again.

5. **No new capital into ASML — trim-watch only, no dollar action proposed this run.** Largest position (10.9%), flipped STRONG UPTREND/PEER LEADER → STRONG DOWNTREND + NEW HEADWINDS today, sits in the group of five previously risk-cap-breached names (DRAM, MRVL, SNDK, ASML, COHR) whose excess "likely worsened" from the prior ~$4,160 aggregate figure since all five declined further today. Not proposing a sized trim because (a) its home cluster (AI Semis/Fabs, 31.1%) is still within its 25-35% band, so this isn't a cluster-forced trim, and (b) thesis desk confirms no verdict broke — this reads as factor-beta, not company-specific damage. Given LRCX (a direct sector read-through) reports after close tonight, the highest-signal action is to hold the trim decision until that data lands rather than force one on an as-yet-unconfirmed reversal.

**Standing tension, unresolved by design:** fully curing the cash breach (24.47% vs the normal 5-15% band; tolerated vs the widened post-stop 5-40% band) within current draft-policy bands would mean buying into Memory/Optics/Power — the three most volatile clusters in the book, and the ones currently getting hit hardest. Flagging for your call, not resolving unilaterally. Note also the Compute/Hyperscaler cluster is 8.0pt under target (12.0% equity/9.1% total-book) — a lower-beta redeployment channel worth considering ahead of the higher-vol clusters if/when you want to put cash to work, consistent with your preference for lower-vol mega-caps when filling gaps.

**Named but not actioned:** QCOM — narrowly missed rebound's cutoff, sold off *into* today's print (not run up), earnings today makes it a pure binary-event hold, no proposal either way until the print lands. MU — CEO insider sales fresh 29-Jul, tagged WATCH_THESIS by rebound (stay-out for adds); its qty_change (1.0004→2.0004) looks like a genuine +1-share purchase given flat day-over-day pricing, not the corporate-action the heuristic guessed — data-quality note, not an action item.

## Risk-off status
`normal` per compute_drift.json — not tripped. But drawdown sits at -14.484%, just 0.516pt from the -15% warn rung, and today carries three earnings plus FOMC on top of an escalating factor selloff. Treat this as elevated-caution, not yet defensive-mode: no proposal above is full-size, none of the five risk-cap-breached names (ASML/DRAM/MRVL/SNDK/COHR) get fresh capital, and every staged entry above is halved or smaller pending today's data (LRCX/QCOM/VRT/FOMC). If drawdown crosses -15% intraday, re-run and expect this posture to shift to lead-with-defense per the risk-off protocol.

## Stress table
Not run — deep-mode only, this is a quick sweep. No macro/scout tail available this run to anchor scenario reads; skip rather than approximate off stale/absent inputs.

## Hit-rate readout
journal.json has no populated `bucket_hit_rates` and an empty `name_bucket_grades` this run — no scored buckets available to grade. Skipping task 5 substantively rather than fabricating a read; flagged in data_quality below for the orchestrator to check why the journal scoring hasn't populated.

## Proposal-outcomes scorecard
Not run — reserved for deep-mode or monthly cadence per task scope; this is a quick sweep. No scorecard this run.

## Data quality
- compute_drift.json's AI Memory/Storage cluster line is internally inconsistent: it states both "19.4% of total-book" and "still above the 20% ceiling" — those don't square (19.4 < 20). Treated conservatively as near-ceiling-but-not-confirmed-breached on the total-book test; the equity-basis breach (25.6% vs 20% band top, +5.6pt) is real and unambiguous. Flagging the total-book line for the orchestrator to check on the next compute_drift refresh.
- journal.json bucket_hit_rates/name_bucket_grades empty this run — hit-rate readout (task 5) skipped for lack of data, not by choice.
- fomc_cache (rate_pct=3.63%, HAWKISH, next_check_date=2026-09-17) predates today's live FOMC decision — do not treat as authoritative for today's 2pm ET outcome; due for refresh on next deep run.
- MU qty_change (1.0004→2.0004) mis-flagged "likely_corporate_action" by the book script's ratio heuristic; price evidence (flat ~$820 day-over-day, no split-consistent adjustment) contradicts a split — reads as a genuine +1 share purchase. Open item, not resolved this run.
- LTCG: ltcg_flags=[] this run, lots.json gap G1 (partially seeded) applies — no LTCG-aware deferrals to propose, N/A rather than omitted.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Stage AMD (tranche 1 of 2, half-size)","size_usd":200,"price_at_proposal":null,"rationale":"Idio-weak dip -8.15% vs Semis/Fabs peer median -4.22%, thesis strengthening, support at $390.18/$306.65; halved and staged because LRCX reports after close tonight in the same semicap theme."},
   {"action":"Stage AMAT (tranche 1 of 2, half-size)","size_usd":150,"price_at_proposal":null,"rationale":"Idio-weak dip -7.82% vs peer median -4.22%, thesis strengthening, support at $457.11/$367.65; halved pending LRCX after-close print, direct read-through to AMAT's thesis."},
   {"action":"Defer VRT stage-in (rebound's $65 proposal) to post-earnings","size_usd":0,"price_at_proposal":null,"rationale":"VRT reports earnings TODAY (corrected from 07-30 by watchlist, unknown to rebound when it sized this) and only has ~$137 headroom to its risk cap; staging into a same-day binary event this close to cap violates the tranche-around-earnings rule."},
   {"action":"Stage GEV (token tranche, well under rebound's $250)","size_usd":100,"price_at_proposal":null,"rationale":"Power cluster 7.1pt under target (legitimate gap), macro-driven dip near peer median, but signal flipped STRONG UPTREND->STRONG DOWNTREND today (same pattern as ASML) -- token size only pending signal re-confirmation."},
   {"action":"ASML trim-watch, no capital action","size_usd":0,"price_at_proposal":null,"rationale":"Largest position (10.9%), signal flipped to STRONG DOWNTREND+headwinds, in the worsening risk-cap-breach group of five, but home cluster (AI Semis/Fabs) still within band and thesis unbroken -- holding the trim call until LRCX's after-close print confirms whether this is factor-beta or name-specific."}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["compute_drift.json AI Memory/Storage total-book line internally inconsistent (19.4% stated as both under and 'above the 20% ceiling') -- flagged for orchestrator, not resolved here","journal.json bucket_hit_rates/name_bucket_grades empty this run -- hit-rate readout skipped for lack of data","fomc_cache predates today's live FOMC decision, due for refresh","MU qty_change 1.0004->2.0004 mis-flagged likely_corporate_action by heuristic; price evidence points to a genuine +1 share purchase, open item","stress table and proposal-outcomes scorecard both skipped -- deep-mode/monthly scope, this is a quick sweep"]}
```

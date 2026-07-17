# Portfolio Strategist — Quick Sweep, 2026-07-16 (pre-open)

Policy present but UNCONFIRMED (`policy_confirmed: false`). Not bootstrapping (policy exists) — treat as due for revision/confirmation, not draft-from-scratch. All proposals below are review items, never instructions to execute.

## Proposals (2026-07-16)

1. **Trim MRVL ~$150** (partial walk-back of today's add, not a reversal) — peer-laggard trend kept worsening *after* this morning's buy (open_flag escalated -18.6%→-21.4% vs SOXX intraday, position now 4.71% wt, 4→7sh added today), and it sits inside the over-band AI Semis/Fabs cluster (38.12% vs 35% band top). Small size deliberately — trimming a name bought hours ago risks whipsaw, so this only caps further exposure rather than undoing today's decision. Price_at_proposal $194.71 (target $252.56, +29.7% — bullish target gap argues against a full exit, only a partial cap). LTCG check not possible: lots.json empty, cite G1.

2. **Hold, do not fund GLW ($600) / CQQQ ($300) stage-ins from rebound** — real setups (GLW sharpest AI-capex-adjacent dip -6.07%, strengthening thesis; CQQQ thin dip, ample ETF-band headroom) but cash is 0.095% vs the 3–15% band, wallet ~$34, and today's real net flow into stocks was already ~$5,345 (corrected for G6/G9 — script's raw $2,646 understates it). Deploying more the same session the cash band blew out would compound the breach. Revisit once cash is rebuilt.

3. **No new adds to today's six new positions (LITE/IREN/COHR/ARM/GOOG/META)** despite live target-gap setups (LITE +34.7%, IREN +55.6%, COHR +26.4%, META +18.6%) — theses were only seeded this run (no prior status entry), all bought same day; let a session pass before sizing up. ARM/IREN carry explicit thesis-WATCH flags (execution risk / BTC-linked volatility) — outrank the target-gap upside as an add case.

4. **No action — AI Power/Cooling/DC Infra gap** (actual 2.69% vs 15% target, -12.3pt, deepest breach on the table) — natural vehicle VRT sits on today's stay-out list (watch-thesis flag). No clean way to close this without adding a flagged name; carry to next run.

5. **No action — SNDK** (peer-laggard -18.0% vs SMH, marginally pushes Memory/Storage 0.49pt over its band top) — also bought today (+0.5sh) and already carries an open_flag for 3x whipsaw in 48h. Trading it again this session would extend the whipsaw pattern the journal is already flagging; sit still.

## Risk-off status
`risk_off_status: normal` (drawdown 0.0%, book at a fresh peak on real inflows). Standalone flag regardless: **cash is a severe, structural breach** — 0.095% vs the 3–15% floor, ~$34 of wallet left after today's ~$5,345 deployment. Not a risk-off trigger by policy math, but there is effectively zero dry powder for any further opportunistic buy, which itself is a risk worth tracking distinctly from drift.

## Macro-anchored note (quick mode — header strip only, no smith-macro dispatch)
VIX 16.01, 10y 4.545%, DXY 100.573 — broad macro is calm. Today's rout is sector-specific: SMH -2% / SOXX sharper vs S&P -0.23% just today (per smith-thesis), consistent with a correlated AI-semis/memory rotation, not a macro shock. Low VIX also underwrites the sentiment score's "greed" band (66.0) — component vix=80 — book risk here is concentration/rotation risk, not macro tail risk today.

## Hit-rate readout
`bucket_hit_rates` empty this run — nothing has aged to a 30-day scoring window yet. No readout possible; re-check once the 9 fresh TARGET GAP journal entries and today's signals have had time to mature.

## Proposal outcomes / scorecard
Skipped — quick mode, not deep or monthly cadence (task 6 gate). No scorecard computed this run.

## Policy revision notes
- New **Compute/Hyperscaler** cluster (GOOG/META/IREN split off OEM this run, actual 4.876%) has no `target_pct`/`band_pct` yet — needs one added on next policy confirmation.
- `max_ai_capex_factor_pct=90%` is worth revisiting: book is structurally at ~96.0% (stock-only 96.01%) and climbing — today's six adds are almost entirely capex-chain names. This is a decision for the user: commit to trimming back toward 90% over time, or formally raise the cap to reflect the intended concentration. Running ~6pt over an unconfirmed cap is a policy-hygiene gap, flagged not resolved here.
- G3 note: holdings-sum vs snapshot gap widened to 6.5% this run (was 0.6%→3.15% historically) — orchestrator used bottom-up holdings-sum as authoritative; worth a reconciliation check next deep review.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim MRVL ~$150 (partial, same-day add caution)","size_usd":150,"price_at_proposal":194.71,"rationale":"Escalating peer-laggard -18.6%->-21.4% vs SOXX since this morning's buy; Semis/Fabs cluster over band top (38.12% vs 35%); AI-capex exposure reduction; LTCG check unavailable, lots.json empty (G1)"},
   {"action":"Defer GLW stage-in","size_usd":0,"price_at_proposal":162.0,"rationale":"Rebound flagged $600 stage-in on sharpest AI-capex dip (-6.07%) but cash 0.095% vs 3-15% band leaves no dry powder; deferred pending cash rebuild"},
   {"action":"Defer CQQQ stage-in","size_usd":0,"price_at_proposal":null,"rationale":"Low-priority $300 ETF-band stage-in from rebound; same cash constraint as GLW, deferred"},
   {"action":"Hold - no add to today's 6 new positions","size_usd":0,"price_at_proposal":null,"rationale":"LITE/IREN/COHR/ARM/GOOG/META all bought same day, theses only seeded this run; ARM/IREN carry thesis-WATCH flags that outrank target-gap upside"},
   {"action":"No action - AI Power/Cooling/DC Infra gap","size_usd":0,"price_at_proposal":null,"rationale":"Actual 2.69% vs 15% target (-12.3pt), deepest breach on the table, but only natural vehicle VRT is on the stay-out (watch-thesis) list"},
   {"action":"No action - SNDK","size_usd":0,"price_at_proposal":null,"rationale":"Peer-laggard -18.0% vs SMH and marginal Memory/Storage over-band, but bought today (+0.5sh) with an existing 3x-whipsaw-in-48h open_flag; further trading would extend the pattern; no price data available (data gap)"}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["G1: lots.json empty, no LTCG boundary check possible on MRVL trim","G3: holdings-sum vs snapshot gap widened to 6.5% this run","G5: beta defaults to 1.0 for 10 names incl. today's new adds, weakens any beta-based sizing","G6: qty-change false-positive heuristic confirmed again on AMAT/AVGO/CLS/GEV, flow figures need manual correction","G9: script's new-ticker blind spot confirmed on all 6 adds, true net flow ~$5,345 not the raw ~$2,646","SNDK/DRAM/EWY/NBIS/CQQQ: no analyst target/price returned, TARGET GAP and price_at_proposal not computable for these names","bucket_hit_rates empty this run, no entries have aged to 30 days"]}
```

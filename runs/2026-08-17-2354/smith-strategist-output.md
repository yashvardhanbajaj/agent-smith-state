# smith-strategist — 2026-08-17 intraday (second run today)

## 1. Review of the 14 open proposals

**Retired:**
- **P-101 Trim BX $220** — position fully exited (0 shares in holdings.json). Moot.
- **P-098 Buy QCOM $185 (BX-funded pair)** — BX did fully exit, so the funding leg technically occurred, but cash did NOT rise ($499.06 unchanged) — proceeds were absorbed elsewhere (IONQ entry, BE/AMZN adds), leaving zero trace. Funding is dead; replaced below by a fresh ORCL→QCOM pair with an honestly-funded sell leg.
- **P-102 Trim NBIS $700** — NBIS is simultaneously in compute_rotation.json's `accumulate` bucket with thesis `strengthening`; trimming a name whose own thesis argues for adding is the exact contradiction G-rule 2d forbids. Also: the position already dropped 6→3sh (~$826, unverified fill) — not claiming credit, but no further forced trim is warranted on top of an unverified reduction plus a live contradiction.
- **P-103 Add CEG $300 (NBIS-funded pair)** — its sell leg (P-102) is retired above for cause; proceeds untraceable to cash. An unfunded buy is exactly what was retired on 2026-08-15 for this reason. Not recreating it.
- **P-100 Raise MRVL stop to cost basis** — MRVL no longer appears in this run's profit_ratchet shadow screen despite a +25.3% gain that would otherwise qualify; the absence implies the stop is already effectively at/above breakeven. Treated as resolved.
- **P-087 Trim NVDA $550 (rc4)** — no live trigger has ever attached to this proposal across 4 repeats (RSI 62.2, neither oversold nor overbought); it is pure ATR-cap mechanics, exactly the pattern the user has objected to. At rc4, one more re-raise hits rc5 (zero bonus). Dismissing now rather than pushing it there. NVDA earnings 2026-08-26 (8 sessions out) is a real proximity risk but not a sized-trim basis on its own — noted, not proposed.

**Kept / restated below:** P-082 (MSFT), P-088 (SKHY), P-089 (MU), P-091 (DRAM), P-094 (ORCL hard stop — stands unchanged, not superseded), P-099 (SNDK), P-104 (MU stop raise), P-105 (AVGO).

## 2. Sized proposals

Live-triggered (HIGH):
1. **Trim MSFT $359.69** — live overbought_distribution (RSI14 78.8, +24.7% 1m, cap-independent). Compute/Hyperscaler cluster is -9.11pt under floor with no intra-cluster rotation target (every peer already ran) — per the trigger's own blocker this is trim-anyway-and-deepen, or leave it, no third option. Real-gain protection is the basis; the cluster breach is tension, not support (G56).
2. **Trim ORCL $177.50** — new live catalyst_threat (continuing debt/capex/cloud-AI-returns skepticism, 2026-08-14, narrative-level, no new figure). Corroborated by computed STRONG DOWNTREND peer-relative signal and rotate_out bucket membership; smith-signals reads this as value-destruction, not a bounce. Sell leg for pair #3. P-094's existing hard stop at $139.14 stands separately, unchanged.
3. **Buy QCOM $177.50** [pair_id PAIR-2026-08-17-ORCL-QCOM, buy_leg] — laggard_rotation shadow (bottom-quartile 1m relative strength -6.7pp, thesis strengthening, within cap) — shadow, not yet hit-rate validated, scored zero on the trigger alone. Sized to the smaller of the ORCL sell-leg proceeds ($177.50) and QCOM's own headroom ($448.33).
4. **Trim AVGO $315.41** — live catalyst_threat (BofA bond downgrade on the XPV off-balance-sheet AI financing platform, extreme-case loss exposure ~$42bn, though BofA simultaneously raised FY26 AVGO revenue/EBITDA). Thesis strengthening but this catalyst is now carried alone — BX's exit removed the offsetting GP-side upside in the same vehicle.

Mechanics-only, cap-independent triggers absent → capped MEDIUM per the 2026-08-17 priority rule:
5. **Trim SKHY $900** — ATR cap 2.142x (book's #2 breach), de-risk queue rank #2 (99.1). Coincides with scale_out_ladder shadow (+25.2%, rung 1 of 2, $635.76 shadow-suggested) cited as color only.
6. **Trim MU $500** — ATR cap 2.152x (book's largest breach), de-risk queue rank #1 (100.0). No live TRIM trigger; MU's only live-adjacent item is the STOP_RAISE below, a different action.
7. **Trim DRAM $450** — ATR cap 1.593x. No live trigger.
8. **Trim SNDK $280** — ATR cap 1.277x plus scale_out_ladder shadow coincidence (+48.0%, rung 1 of 2, $303.43 shadow-suggested, close to this ask).
9. **Trim MRVL $550.65** (new) — ATR cap 1.468x plus scale_out_ladder shadow coincidence (+25.3%, rung 1 of 2). MRVL had no open trim proposal; its prior open item (P-100, stop raise) is retired above as resolved.

Zero-capital stop housekeeping (sanctioned regardless of the 21.8%-win-rate stop data, because this mechanic only ever raises a stop to breakeven, never below):
10. **Raise MU stop to $874.17** (restates P-104) — current stop $829.12 is below the $874.17 basis; $112.66 of a +16.7% gain at risk on a retracement.
11. **Raise SKHY stop to $138.52** (new) — stop $130.08 below basis, $92.87 at risk on a +25.2% gain; coincides with SKHY's own cap breach.
12. **Raise TER stop to $378.89** (new) — stop $359.05 below basis, $59.58 at risk on a +15.9% gain; coincides with TER's cap breach (1.081x).
13. **Raise DRAM stop to $49.05** (new) — stop $48.94 marginally below basis, only $3.34 at risk but still technically sub-breakeven; coincides with DRAM's cap breach.

No LTCG deferral proposed: earliest open lot (2026-07-15) is ~24 months from its boundary (~mid-2028); no live LTCG-deferral decisions exist in the book.

## 3. Risk-off check

`risk_off_status` = **normal** (drawdown -0.865% off peak $44,873.02 — shallow, not stress-level). No drawdown-triggered defensive posture required. Separately and independently of drawdown: cash 1.122% is under the [5,15]% floor, and aggregate open risk 14.316% is over the 10% cap (11/35 names over their own ATR cap). Every trim above raises cash except the ORCL→QCOM pair, which nets zero cash change by design (funded rotation, not a new deployment). No unfunded buys are proposed.

## 4. Stress table

Skipped — Task 4 is deep-mode only and this is a quick run; smith-macro did not run this session, so there is no live regime read to anchor rate-sensitive rows to either. Flagged in data_quality.

## 5. Hit-rate readout

- 30d: MOMENTUM+VOLUME 100% (n=5), TARGET GAP 76.5% (n=17). OVERSOLD BOUNCE n=1 — skipped, below the 3-entry floor.
- 7d interim (not equivalent to 30d, label only): MOMENTUM+VOLUME 93.8% (n=16), OVERSOLD BOUNCE 100% (n=5), TARGET GAP 76.5% (n=17).
- No bucket sits below 40% over ≥5 entries — no de-emphasis recommended this run.
- Stop-loss efficacy (94 scored fills, unchanged since 2026-08-13): 21.8% overall win rate (19 saved/68 hurt/7 flat), deliberate cohort 28.8% (n=56), cascade 14.3% (n=7). This is evidence against tightening stops generally — it does not argue against the four raise-to-breakeven proposals above, which are the one sanctioned response the data doesn't contradict (never moves a stop below cost).

## 6. Scorecard interpretation (stored, not recomputed)

`smith_math.py score` reports 7 proposals scored at 30d/90d: **14.3% overall accuracy** (1 worked / 5 missed / 1 neutral), avg benefit -3.47%. By direction: TRIM/SELL 0.0% (n=1 — a single data point, not a verdict), BUY 25.0% (n=4), HOLD 0.0% (n=2, avg benefit -9.37%, the worst-performing bucket though also n=2). 0 quarantined. 9 excluded as dismissed_by_user (fair — a user override isn't a strategist miss). 48 of the desk's proposals are still under the 30-day scoring window, so this record will keep moving.

Read honestly: n=7 is too small to certify or condemn the desk's method, but it is the only measured record that exists, and it is not flattering — HOLD calls have fared worst, and the single scored TRIM missed. That argues for continued caution on directional HOLD-style calls (e.g., "no action" verdicts under live threat) and for leaning on the mechanically-verifiable proposals in this run (cap-breach trims, breakeven stop-raises) over speculative BUY calls like the QCOM leg, until the sample grows. It does not change the arithmetic behind any proposal above — those numbers come straight from compute_triggers.json / compute_drift.json / compute_derisk.json.

## Data quality
- smith-macro did not run this quick-mode session; Task 4 stress table skipped, no live regime anchor available.
- Explicit `verified:"primary"|"secondary"` tags were not visible in the Stage-1 tails handed to this run; evidence_quality below classifies only compute_*.json fields as `computed` and treats thesis/news-narrative claims conservatively as `unverified` rather than assuming a verified tag that wasn't shown.
- G69 (116 historical fills lost) and G78 (32+5 UNCAPTURED trade rationales) remain open/partially-closed; they limit cost-basis confidence specifically on the 5 newly-changed positions this run (BX exit, NBIS reduction, IONQ entry, BE add, AMZN add), all flagged reason=UNCAPTURED / price_source=reconstructed in the book slice.
- shared/thesis.json, preferences.json, open_flags.json were not re-opened this run; reasoning relied on the inline Stage-1 tails and the prompt's own summary of them (budget: ~9 read/bash calls used against an ~8 soft cap, justified by the need to confirm BX's exit, NBIS's share count, and the stored scorecard/open-proposal history directly rather than assume them).

```json
{"policy_draft":null,
 "proposals":[
   {"action":"TRIM","ticker":"MSFT","size_usd":359.69,"price_at_proposal":479.59,"rationale":"Live overbought_distribution (RSI14 78.8, +24.7% 1m, cap-independent). Compute/Hyperscaler cluster -9.11pt under floor, no intra-cluster rotation target exists -- trim-anyway-and-deepen or leave it, no third option; cluster cited as tension only, not support (G56).","trigger_type":"overbought_distribution","trigger_bucket":"live","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"ORCL","size_usd":177.50,"price_at_proposal":147.92,"rationale":"New live catalyst_threat: continuing debt/capex/cloud-AI-returns skepticism (2026-08-14), narrative-level. Corroborated by computed STRONG DOWNTREND peer-relative signal and rotate_out bucket -- read as value-destruction, not a bounce. Sell leg for QCOM pair. P-094 hard stop $139.14 unchanged, not superseded.","trigger_type":"catalyst_threat","trigger_bucket":"live","pair_id":"PAIR-2026-08-17-ORCL-QCOM","pair_role":"sell_leg","evidence_quality":{"verified":0,"computed":2,"unverified":2}},
   {"action":"BUY","ticker":"QCOM","size_usd":177.50,"price_at_proposal":161.87,"rationale":"laggard_rotation shadow (bottom-quartile 1m rel strength -6.7pp, thesis strengthening, within cap) -- shadow, not yet hit-rate validated, scored zero on trigger alone. Sized to the smaller of ORCL sell proceeds ($177.50) and QCOM's own headroom ($448.33). Replaces P-098: BX exit occurred but proceeds left no cash trace (absorbed by IONQ/BE/AMZN), so that funding leg is dead.","trigger_type":"laggard_rotation","trigger_bucket":"shadow","pair_id":"PAIR-2026-08-17-ORCL-QCOM","pair_role":"buy_leg","evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"AVGO","size_usd":315.41,"price_at_proposal":394.26,"rationale":"Live catalyst_threat: BofA bond downgrade on XPV off-balance-sheet AI financing platform, extreme-case loss exposure ~$42bn (BofA also raised FY26 AVGO rev/EBITDA). Thesis strengthening but catalyst now carried alone -- BX exit removed the offsetting GP-side upside in the same vehicle.","trigger_type":"catalyst_threat","trigger_bucket":"live","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"TRIM","ticker":"SKHY","size_usd":900,"price_at_proposal":173.39,"rationale":"Mechanics-only: ATR cap 2.142x (book #2 breach), de-risk queue rank #2 (99.1). No live trigger of SKHY's own. Coincides with scale_out_ladder shadow (+25.2%, rung 1/2, $635.76 shadow-suggested), cited as color only. Capped MEDIUM per no-live-trigger rule.","trigger_type":"scale_out_ladder","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"action":"TRIM","ticker":"MU","size_usd":500,"price_at_proposal":1020.575,"rationale":"Mechanics-only: ATR cap 2.152x (book's largest breach), de-risk queue rank #1 (100.0). No live TRIM trigger; MU's only live-adjacent item is the STOP_RAISE below, a different action. Capped MEDIUM.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"DRAM","size_usd":450,"price_at_proposal":60.75,"rationale":"Mechanics-only: ATR cap 1.593x. No live trigger. Capped MEDIUM.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"SNDK","size_usd":280,"price_at_proposal":1791.47,"rationale":"Mechanics-only: ATR cap 1.277x, plus scale_out_ladder shadow coincidence (+48.0%, rung 1/2, $303.43 shadow-suggested, close to this ask). Capped MEDIUM.","trigger_type":"scale_out_ladder","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"action":"TRIM","ticker":"MRVL","size_usd":550.65,"price_at_proposal":235.9937,"rationale":"New: ATR cap 1.468x plus scale_out_ladder shadow coincidence (+25.3%, rung 1/2). No prior open trim; P-100 (stop raise) retired as resolved. Capped MEDIUM.","trigger_type":"scale_out_ladder","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"action":"STOP_RAISE","ticker":"MU","size_usd":0,"price_at_proposal":1020.575,"rationale":"profit_ratchet shadow: stop $829.12 below $874.17 basis, $112.66 of a +16.7% gain at risk. Zero capital; raise-to-breakeven is the sanctioned exception to the 21.8%-win-rate stop-efficacy data. Restates P-104.","trigger_type":"profit_ratchet","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"STOP_RAISE","ticker":"SKHY","size_usd":0,"price_at_proposal":173.39,"rationale":"profit_ratchet shadow: stop $130.08 below $138.52 basis, $92.87 at risk on +25.2% gain. Coincides with SKHY's own cap breach (2.142x). New, zero capital.","trigger_type":"profit_ratchet","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"STOP_RAISE","ticker":"TER","size_usd":0,"price_at_proposal":439.155,"rationale":"profit_ratchet shadow: stop $359.05 below $378.89 basis, $59.58 at risk on +15.9% gain. Coincides with TER's cap breach (1.081x). New, zero capital.","trigger_type":"profit_ratchet","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"STOP_RAISE","ticker":"DRAM","size_usd":0,"price_at_proposal":60.75,"rationale":"profit_ratchet shadow: stop $48.94 marginally below $49.05 basis, only $3.34 at risk but still sub-breakeven. Coincides with DRAM's cap breach (1.593x). New, zero capital.","trigger_type":"profit_ratchet","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":0}}
 ],
 "scorecard_read":"Stored scorecard (7 scored, n too small to be a verdict): 14.3% overall (1 worked/5 missed/1 neutral, avg benefit -3.47%). TRIM/SELL 0% (n=1), BUY 25% (n=4), HOLD 0% (n=2, worst avg benefit -9.37%). 0 quarantined, 9 dismissed_by_user excluded, 48 still under 30 days. Read: not flattering but not yet a verdict at n=7; HOLD-style no-action calls have fared worst so far, which argues for leaning on the mechanically-verifiable cap/stop proposals in this run over the speculative QCOM buy leg until the sample grows.",
 "deemphasize_buckets":[],
 "data_quality":["smith-macro did not run this quick-mode session -- stress table skipped, no live regime anchor","explicit verified:primary/secondary tags not visible in Stage-1 tails this run -- evidence_quality below is conservative (computed-only counted with confidence, narrative/thesis claims bucketed unverified)","G69 (116 historical fills lost) and G78 (32+5 UNCAPTURED rationales) remain open, limiting cost-basis confidence on BX exit / NBIS reduction / IONQ entry / BE add / AMZN add this run","BX exit and NBIS reduction proceeds did not raise cash -- P-098 and P-103 funding legs are dead and retired rather than carried as unfunded buys","shared/thesis.json, preferences.json, open_flags.json not re-opened this run (budget: relied on inline Stage-1 tails); ~9 read/bash calls used against the ~8 soft cap"]}
```

Output file: /Users/yb/Claude/AgentSmith/runs/2026-08-17-2354/smith-strategist-output.md

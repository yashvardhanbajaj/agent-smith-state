# Portfolio Strategist — Deep Weekly Review, 2026-08-17 (pre-open, gate AMBIGUOUS)

Policy is confirmed and valid (no bootstrap needed). Total book $43,669, cash $12.23 (0.028% — effectively zero dry powder), drawdown -2.683%, risk_off_status **normal**. Aggregate open risk 14.786% vs a 10% cap is a live, separate breach worked via the cap-cure trims below — it is not a risk-off trigger.

## Review of the 12 open proposals

All 12 were re-checked against today's compute tables. **None retire this run** — every `retires_when` condition is still unmet (the book has been quiet; Rebound independently confirmed no stop-loss activity since the last snapshot). One price-drift flag:

| ID | Ticker | Action | Status this run |
|---|---|---|---|
| P-082 | MSFT | Trim $370 | Reaffirmed. RSI 78.8, +24.7% 1m — both unchanged in direction. Price $492.43→$491.53 (-0.2%), no flag. |
| P-087 | NVDA | Trim $550 | Reaffirmed. Cap multiple 1.207x (unchanged character). Price +0.6%, no flag. |
| P-088 | SKHY | Trim $900 | Reaffirmed, **worsened**: cap multiple 2.081x→2.182x, still the worst breach in the book. Price +4.7%, no flag. |
| P-089 | MU | Trim $500 | Reaffirmed, worsened: headroom -$1,209→-$1,358. Price +6.2%, no flag. **New companion action added below (stop-raise).** |
| P-090 | NBIS | Trim $700 | Reaffirmed but **price drift +10.70%** ($255.05→$282.34) — flagged, re-quote share count before acting. Cap multiple now 1.989x, headroom -$842 (was -$813/-$677 cited across earlier revisions). |
| P-091 | DRAM | Trim $450 | Reaffirmed, worsened: headroom -$583→-$685. Price +5.9%, no flag. |
| P-093 | CEG | Add $300 (rotation buy leg, paired w/ P-090) | Reaffirmed unchanged. Price +1.8%, no flag. |
| P-094 | ORCL | Hard stop @ $139.14 | **Kept open per explicit instruction** — this is a standing risk instruction, not hold-fire advice, and must not auto-retire as a tactical HOLD again. STRONG DOWNTREND persists; oversold-bounce technical trip is correctly suppressed given the negative 5-of-8-headline skew. |
| P-097 | BX | Trim $185 | **Rationale and priority updated** — see below. |
| P-098 | QCOM | Buy $185 (rotation buy leg, shadow, paired w/ P-097) | Reaffirmed unchanged. Price +1.4%, no flag. |
| P-099 | SNDK | Trim $280 | Reaffirmed, worsened: cap multiple 1.189x→1.263x. Price +6.0%, no flag. |
| P-100 | MRVL | Raise stop to cost basis (no capital) | Reaffirmed unchanged. |

### P-097 (BX trim) — does the AVGO/BX financing-structure catalyst change anything?

Yes, on rationale and modestly on size. BofA downgraded AVGO's **bond rating** (2026-08-11) over the XPV off-balance-sheet AI-financing platform AVGO built with Blackstone and Apollo to fund Anthropic compute — stress-test exposure up to $370bn at full 2028 buildout vs a $35bn/1GW current tranche (~$42bn extreme-loss case). This hits AVGO (3.57% wt) and BX (1.62% wt) together — 5.19% of book carries this financing-structure tail risk. BofA simultaneously *raised* FY26 AVGO revenue/EBITDA estimates in the same call, so this is a financing-structure concern, not a fundamentals one.

BX now has **two independent supporting reasons** stacked: (1) overbought_distribution, RSI 71.1, +16.5% 1m — cap-independent, pure technical profit-take; (2) the financing-structure tail risk just quantified for the first time. Two independent reasons argue for taking slightly more off than the pure-technical $180.44 the trigger alone would suggest. **Sizing raised from $185 to $220** (~30% of the $721.75 position, up from ~25%) — modest, not aggressive, since the tail scenario itself is multi-year (2028 buildout) and low-probability at the extreme-loss end. Priority bumped from HIGH to HIGH+ in practice (unchanged label, stronger evidence stack).

AVGO itself is **not** touched: no overbought trigger fires (RSI 65.3), it carries $1,044 of cap headroom, and it sits in `compute_rotation.json`'s `accumulate` bucket with a strengthening thesis — trimming it would be the exact accumulate/strengthening contradiction the rotation rule (2d) exists to prevent. AVGO's Friday -5.94% despite the Q2 beat (48% rev growth, AI +143%) stays flagged as an unresolved beat-vs-reaction divergence (G58) — not treated as a fundamental negative, no action taken on it.

Separately: propose adding BX to the circular-vendor-financing theme's mapped tickers (opened 07-28) — this is a tracking/data action, not a capital one, flagged for the next catalyst-agent touch.

### New this run: MU stop-raise

`profit_ratchet` (shadow) fires on MU independently of, and consistent with, the already-open P-089 cap-breach trim: MU is up +15.4% vs a $874.17 basis, but its current stop ($819.34) sits *below* breakeven — a retracement would turn a real gain into a realised loss. Per 2c, a shadow trigger may be surfaced when it coincides with a computed breach; this one does. No capital moves — ratchet up only, consistent with standing instruction to never tighten stops down.

## Sized proposals this run (4)

1. **TRIM BX $220** @ $144.35 — updated rationale/size, see above.
2. **TRIM NBIS $700** @ $282.34 (rotation sell leg, pair `ROT-NBIS-CEG`) — reaffirmed, price-drift flagged, re-quote shares before execution.
3. **ADD CEG $300** @ $283.60 (rotation buy leg, pair `ROT-NBIS-CEG`) — reaffirmed unchanged; deliberately not sized to the full $700 sell proceeds so the remainder rebuilds the near-zero cash buffer.
4. **RAISE MU stop to $874.17 (cost basis)** — no capital moved; new this run.

No `oversold_reversion` candidates fired (list empty) — nothing to propose on that side this cycle. No LTCG deferral: as of 2026-08-16 the earliest open lot is 2026-07-15, so the 24-month boundary is mid-2028 — no lot is within 6 months of it. Not manufacturing one.

## Risk-off check

`risk_off_status`: **normal** (drawdown -2.683% vs 8% warn / 12% risk-off). No blanket restriction on new deployments; exceptional setups still fine. The separate 14.786%-vs-10%-cap aggregate open-risk breach is being worked down through the cap-cure trims above (SKHY/MU/NBIS/DRAM/NVDA/SNDK) — a volatility-budget problem, not a risk-off signal.

## Stress table (approximate, macro-anchored)

Anchored to smith-macro's live regime read: Fed 3.63% hawkish/unchanged, no FOMC/CPI/NFP within 5 sessions; SPY PCR-OI 2.58 vs QQQ PCR-OI 1.17 with low VIX reads as "hedged complacency"; regime neutral but the rate side (10yr 4.696%) pressures the AI-capex/long-duration-growth cluster first and modestly favors the diversifier bench as ballast.

| Scenario | Est. impact | Most exposed |
|---|---|---|
| AI-capex pause | -18% to -25% (~-$7,860 to -$10,920) | SKHY (β2.44), NBIS (β2.64), DRAM (β2.07), MU (β1.95), SNDK (β2.92) — the same high-beta names already carrying cap-cure trims |
| Rates +100bp | -8% to -12% (~-$3,490 to -$5,240) — multiple compression on long-duration growth, per macro's rate-side read | Same high-beta cluster (SKHY/NBIS/DRAM/MU) plus ASML/LRCX; BX/CEG/MSFT/AMZN/QCOM (low beta) act as partial ballast, consistent with macro's "diversifier bench" read |
| Tariff/export-control escalation | -6% to -9% (~-$2,620 to -$3,930) | TSM (Taiwan), ASML (already carrying a pending China DUV/export-control headwind), NVDA (China restrictions), SKHY/MU (Korea-China memory supply chain) |
| USD/INR ±3% | ~0% on the USD book (fully USD-reported) | INR-terms net-worth effect only: ±3% ≈ ±₹125,000 on the ~₹41.75 lakh USD-book value at 95.6025, purely FX, no change to USD portfolio value |

## Hit-rate readout

From `journal.json`'s stored `bucket_hit_rates` (30d window), buckets with ≥3 scored entries only:
- **TARGET GAP**: n=14, 57.1% hit rate.
- **MOMENTUM+VOLUME**: n=5, 60.0% hit rate.
- (OVERSOLD BOUNCE: n=1 — skipped, below the 3-entry floor.)

Neither qualifying bucket is below the 40% de-emphasis threshold, and neither has ≥5 entries with a sub-40% rate. **No de-emphasis recommended this run.**

## Scorecard interpretation (proposal outcomes, from `smith_math.py score`)

Stored scorecard, read not recomputed: **overall n=7, 14.3% accuracy** (1 worked / 4 missed / 2 neutral, avg benefit -2.58%). By direction — TRIM/SELL n=1 (0% accuracy, the single scored trim came back neutral, not a loss); BUY n=4 (25% accuracy, 1 worked / 2 missed / 1 neutral); HOLD n=2 (0% accuracy, both missed). 9 proposals are excluded as `dismissed_by_user` (correctly — a user override isn't a strategist error), 45 are still under 30 days old and not yet scored, 0 are quarantined for anchor review.

What this implies: n=7 is too small to be a verdict on the desk's judgment — the TRIM row in particular is a single data point and tells us essentially nothing about trim discipline yet. The 25%/4 BUY read and 0%/2 HOLD read are similarly thin. The honest takeaway is that the scorecard will only become informative once a meaningful share of the 45 pending proposals clears 30 days — until then, this desk should keep leaning on the multi-factor gate (computed breach + live trigger + evidence check) rather than treating any single proposal as high-conviction, and should not read this run's 14.3% as either an indictment or a vindication of the trigger-driven approach adopted this cycle.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim BX","ticker":"BX","size_usd":220,"price_at_proposal":144.35,
    "rationale":"RSI14 71.1 (>70), +16.5% on the month -- real gain to protect, cap-independent (0.229x, comfortably inside). NEW: BofA downgraded AVGO's bond rating (11 Aug) over the XPV off-balance-sheet AI financing platform AVGO built WITH Blackstone -- stress-test exposure up to $370bn at full 2028 buildout, ~$42bn extreme-loss case. This is a financing-structure tail risk, not a fundamentals one (BofA raised AVGO's FY26 estimates same call). Two independent reasons now stack (overbought + financing-tail-risk), so sized up from the pure-technical $180.44 to ~30% of the position ($220) rather than ~25%. AVGO itself untouched -- no trigger fires, cap headroom positive, sits in the rotation compute's accumulate bucket with a strengthening thesis.",
    "trigger_type":"overbought_distribution","trigger_bucket":"overbought_distribution","pair_id":null,"pair_role":null,
    "evidence_quality":{"verified":1,"computed":2,"unverified":1}},
   {"action":"Trim NBIS (rotation funding leg)","ticker":"NBIS","size_usd":700,"price_at_proposal":282.34,
    "rationale":"1.989x cap breach (-$842.46 headroom, computed), profit_ratchet and scale_out_ladder both shadow-fire in support. Price has moved +10.70% since first proposed ($255.05 -> $282.34) -- re-quote share count before executing; the dollar size is unchanged but now represents fewer shares. Reaffirms P-090 (3rd time).",
    "trigger_type":"profit_ratchet","trigger_bucket":"profit_ratchet","pair_id":"ROT-NBIS-CEG","pair_role":"sell",
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"Add CEG (rotation destination leg)","ticker":"CEG","size_usd":300,"price_at_proposal":283.60,
    "rationale":"Funded from the paired NBIS trim proceeds, not cash (cash is $12.23). Deliberately not sized to the full $700 sell proceeds -- the remainder is left to rebuild the near-zero cash buffer (0.028% vs a [5,15]% band) rather than being fully redeployed. Cluster AI Power/Cooling/DC Infra is in-band (10.243% vs [10,20]) but near its floor; ample headroom ($2,487.81, computed).",
    "trigger_type":"laggard_rotation","trigger_bucket":null,"pair_id":"ROT-NBIS-CEG","pair_role":"buy",
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"Raise MU stop to cost basis","ticker":"MU","size_usd":0,"price_at_proposal":1008.5406,
    "rationale":"profit_ratchet (shadow) coincides with the already-open P-089 cap-breach trim (2.167x cap, computed) -- MU is up +15.4% vs an $874.17 basis but its current stop ($819.34) sits below breakeven; a retracement would turn a real gain into a realised loss. Raises the stop only, no capital moved, does not fight the WATCH-not-broken thesis. Ratchet up, never tighten down.",
    "trigger_type":"profit_ratchet","trigger_bucket":"profit_ratchet","pair_id":null,"pair_role":null,
    "evidence_quality":{"verified":0,"computed":2,"unverified":1}}
 ],
 "scorecard_read":"Stored scorecard n=7, overall accuracy 14.3% (1 worked/4 missed/2 neutral, avg benefit -2.58%). TRIM/SELL n=1 0% (neutral outcome, not a loss); BUY n=4 25% (1/4 worked); HOLD n=2 0% (both missed). 9 excluded as dismissed_by_user, 45 still under 30 days and unscored, 0 quarantined. n is too small across every bucket to be a verdict on desk judgment -- treat as noisy until more of the 45 pending proposals clear 30 days; keep leaning on the multi-factor gate (computed breach + live trigger + evidence check) rather than single-signal conviction.",
 "deemphasize_buckets":[],
 "data_quality":["NBIS (P-090) price drifted +10.70% since proposed -- re-quote before acting.","BX/AVGO circular-vendor-financing tail risk (BofA 11 Aug bond-rating downgrade) not yet added to the theme's mapped-tickers tracking opened 07-28 -- flagged for the next catalyst-agent touch, not a capital action.","AVGO's -5.94% Friday move vs its Q2 beat remains an unresolved beat-vs-reaction divergence (G58) -- no action taken pending more evidence.","SKHY's 9.2% price decline since entry remains genuinely unexplained by ASP and is not treated as a thesis trigger."]}
```

# Portfolio Strategist — 2026-08-06 (quick sweep, intraday)

Policy status: existing draft, `confirmed: false` (as_of 2026-07-28). All drift analysis below is **provisional** pending user confirmation of policy.json. No bootstrap needed — policy already exists in draft form.

## Disposition: P-055 (Top up GOOGL $1,200) — RE-SIZED AND DEFERRED, not silently re-listed

P-055 has been proposed 4 times since 07-28 (rc=4) to fix the same Compute/Hyperscaler underweight. Since the last run, the desk's wish was overtaken by the user's own stop discipline: GOOGL's stop fired 08-05 at $360 (3sh out), and the cluster is now -10.41pt under its 15-25% band (9.59% vs 20% target) — the single largest drift on the book.

I am **not** re-proposing the full $1,200 today. Two reasons:
1. **Stop discipline record.** GOOGL is trading $362.26, -4.08% intraday, barely above yesterday's stop level. Buying back into a name the same week its own stop fired, while it's still falling, is exactly the pattern flagged as poor-performing for this book (tight, large-quantum stops by design; proposals that fight them have a bad record).
2. **Fresh, structural catalyst headwind, not noise.** Catalyst 3 (STRUCTURAL/ambiguous): Jeff Dean + Sanjay Ghemawat departing after 27 years, and 2026 capex raised to $195-205bn producing Alphabet's first-ever negative quarterly FCF. That is a genuine threat to GOOGL's AI bench and FCF profile — today's -4.08% is plausibly this repricing in real time, not a stop-triggering air-pocket.

**Action: P-061 replaces P-055.** Re-size to a $400 token tranche, condition it on price stabilizing above ~$365 (a level clear of both the stop price and today's low) rather than buying into the falling knife today. The cluster underweight is real and won't be ignored indefinitely — but "not today, not at this size" is the correct call given the two live inputs above. P-055 is superseded.

## Disposition: P-056 (Trim COHR $325) — FULFILLED by the market, closing

The user's own stop-loss did this for us: COHR sold 2sh @ $323.98 (stop order) on 08-04, same rationale (profit-take into unexplained strength, 1.68x-2.28x risk cap). COHR is now 3 shares / 2.53% of equity, back inside band. No further action — closing P-056 as fulfilled, no new COHR proposal today.

## Sized proposals

**P-058 — Trim MU ~$650 (0.7sh) @ $918.05** (2026-08-06)
AI Memory/Storage cluster is 21.64% vs 15% target (10-20 band) — over ceiling. MU carries 2.38x its ATR-based risk cap, one of 7 names over cap (aggregate open risk 13.84% vs 10% policy cap). Thesis stays WATCH — not on the old ASP claim (that -51% figure was a basis-splice artifact, correction C1, now dead) but on the real 2027-dated CXMT supply-share risk (EWY/SK Hynix/Samsung carry ~85-95% of Vera Rubin HBM4 allocation vs MU "structurally thin"). This is the 5th consecutive review recommending a MU trim (P-029→P-052, rc=4 going into today) — sized as another tranche, not a full cap-cure, consistent with the staged-trim pattern used throughout. LTCG: all MU lots dated within the last ~2 weeks; nothing near the 24-month boundary, prefer_ltcg is moot here.

**P-059 — Trim SNDK ~$750 (0.53sh) @ $1,405.70** (2026-08-06)
Same cluster breach. SNDK carries the largest risk-cap excess in the book (4.06x), and holds the book's only EARNINGS PROXIMITY flag (7.12% weight, largest single earnings exposure, NOT run up into the print per signals — meaning this trim is risk-discipline-driven, not a fear-of-earnings sell). 6th consecutive review flagging this excess since 07-28 (rc=5 going into today). No LTCG boundary issue (lots all <2 weeks old).

**P-060 — Trim DRAM ~$400 (7.3sh) @ $54.76** (2026-08-06)
Third leg of the same cluster breach; DRAM's look-through adds further MU/SNDK exposure on top of direct weights, so trimming it works the cluster from a different angle than P-058/P-059. Sized lighter than the historical $500 tranche because this run's thesis tail flags DRAM as an **upgrade candidate** on strong conventional-DRAM contract pricing (+57.3% Q1'26, +49.7% Q2'26 QoQ, guided +13-30% Q3'26) but the original WATCH rationale was unavailable to re-confirm this run — genuine ambiguity, not settled. If next run confirms the upgrade to STRENGTHENING, this trim should shrink further or pause. Flagged in data_quality below.

**P-061 — Stage GOOGL ~$400 (token), conditional, NOT today** (2026-08-06)
Replaces P-055 (see disposition above). Compute/Hyperscaler cluster remains the largest drift in the book (-10.41pt under floor) and needs a fix eventually — but not into today's -4.08% print with a fresh structural catalyst still digesting and the stop only one session old. Condition: re-price and confirm GOOGL holds above ~$365 for a session before sizing this up. Do not chase.

**No standalone MP action.** MP (dca-into-diversification, 10sh @ $47.47, now 1.21% of equity) is a brand-new position with a STRONG DOWNTREND signal (-10.1% vs XLP, weak/unnormalized proxy) and WATCH thesis. It's a satellite diversifier, not a conviction add — hold as-is, no trim, no top-up. See policy band recommendation below.

## Policy band recommendation: Critical Minerals/Rare Earth (new cluster, currently untargeted)

MP created this cluster this week with no policy band to test against. Recommend: **target 0%, band [0, 5]%**, mirroring the treatment just given to Enterprise Software (NOW's cluster) — both are same-week, single-name satellite diversifiers under an otherwise 100%-AI-capex mandate, not core sleeves. At 1.21% today, MP sits comfortably inside this band with no cure needed. This requires user confirmation alongside the rest of the draft policy.

## Cash and deployment call

Net effect of the three trims above (~$1,800) with GOOGL's buy deferred: cash rises from 8.49% (~$3,688) to roughly 12.6% of book (~$5,488) — still comfortably inside the [5,15] normal band, not a breach either direction. **The right call on the incremental cash is to hold it, not redeploy it today.** Two confirmed earnings land tomorrow (QBTS 08-06, binary event on a 1.35% position; CEG 08-06, 2.01% position) — that's a specific, dated reason to carry extra dry powder through tomorrow's session rather than fully reinvest trim proceeds now. This is a genuine hold-fire call, not a forced one: cash is healthy, but tomorrow's calendar argues for patience over immediacy.

## Risk-off status

`risk_off_status = normal` (drawdown -3.245% vs peak, well inside the 15%/25% warn/risk-off thresholds; a large improvement from -10.62% on 08-03). No defensive posture required. Aggregate open risk (13.84% vs 10% cap) is the live risk-control concern, addressed by the three Memory/Storage trims above rather than a book-wide de-risk.

## Hit-rate readout

No bucket_hit_rates / name_bucket_grades table was included in this run's signals tail (quick-mode slice did not carry it) — cannot produce a scored hit-rate line this run. Flagged in data_quality; request it explicitly on the next deep review where journal scoring is expected to be fuller.

## Proposal outcomes / scorecard

Not run — this task is scoped to deep-mode or monthly reviews; today is a quick intraday sweep. proposals.json's own scorecard is still pre-30d for the earliest cohort (07-13 proposals cross 30d around 08-12); revisit then.

```json
{"policy_draft":null,"proposals":[
  {"action":"Trim MU","size_usd":650,"price_at_proposal":918.05,"rationale":"AI Memory/Storage cluster over ceiling (21.64% vs 15% target, 10-20 band); MU at 2.38x ATR risk cap (aggregate open risk 13.84% vs 10% cap); thesis WATCH on 2027 CXMT supply-share risk, not the dead -51% ASP artifact; 5th consecutive review recommending this trim, staged tranche not full cap-cure; no LTCG boundary proximity"},
  {"action":"Trim SNDK","size_usd":750,"price_at_proposal":1405.70,"rationale":"Same cluster breach; largest risk-cap excess in book (4.06x); sole EARNINGS PROXIMITY flag (7.12% weight, not run up into print); 6th consecutive review; no LTCG boundary proximity"},
  {"action":"Trim DRAM","size_usd":400,"price_at_proposal":54.76,"rationale":"Third leg of Memory/Storage cluster cure via look-through exposure; sized light because this run's thesis tail flags DRAM as an upgrade candidate on strong DRAM contract pricing with the original WATCH rationale unavailable to re-confirm -- genuine ambiguity"},
  {"action":"Stage GOOGL (token, conditional on stabilization above ~$365, not executed today)","size_usd":400,"price_at_proposal":362.26,"rationale":"Replaces P-055 (rc=4, $1200) -- Compute/Hyperscaler -10.41pt under floor is real, but GOOGL is -4.08% intraday one session after its own stop fired at $360, and catalyst tail flags a structural FCF/talent-departure headwind (Dean+Ghemawat exit, first-ever negative quarterly FCF); buying into a falling stop-name fights this book's stop discipline, which has a poor record"}
],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["No bucket_hit_rates/name_bucket_grades table present in this run's signals tail -- hit-rate readout skipped, request on next deep review","DRAM thesis tail flags an upgrade candidate on strong contract DRAM pricing but the original WATCH rationale was unavailable to reconcile this run -- P-060 sized light pending resolution, not a full-conviction trim","Proposal-outcomes scorecard (task 6) and stress table (task 4) are deep-mode/monthly scoped -- not run in this quick intraday sweep","Critical Minerals/Rare Earth cluster (MP) has no policy target -- recommended 0%/[0,5]% band pending user confirmation, not yet in policy.json"]}
```

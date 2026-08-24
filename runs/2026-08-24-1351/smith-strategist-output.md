# Portfolio Strategist — Deep Weekly Review, 2026-08-24 (pre-open, gate ESCALATING)

Policy is confirmed (no bootstrap needed). This review reads today's fresh Stage-1 findings against the 15 open proposals and resizes/retires/adds against the precomputed `compute_*.json` tables — no drift, breach, or trigger math below is recomputed by me.

## Book snapshot (computed)
Total book $41,781.19 (equity $39,012.17 + wallet $2,769.02, cash 6.63%, in-band), drawdown -6.89% (`risk_off_status: normal`). Pre-market overlay: book gapping **-1.51%** weighted since Friday's close. Aggregate open ATR risk **12.237% vs a 10% cap** — a real, cap-independent concentration flag sitting on top of the drawdown read. AI-capex chain 83.45% of equity (thesis figure; rebound's independent read is 76.71-82.16%, partly genuine diversification, partly the BX reclassification — not a de-risking signal on its own). AI Memory/Storage cluster is **under its policy floor** (8.04% vs 15% target, band [10,20], drift -6.96pt, real breach).

---

## 1. Catalyst-driven TRIMs — the AVGO/BX off-balance-sheet financing escalation

This is the lead structural finding this run: Broadcom is now negotiating a $70-80bn AI-financing SPV (up from $35bn in June) with **Blackstone named as counterparty/co-investor**. Combined AVGO+BX exposure is 7.53% of equity. All four `catalyst_threat`-live tickers get resized to this run's freshly computed `suggested_size_usd` (cap-independent by design — a name inside its ATR cap, like AVGO, is the *preferred* candidate, not a marginal one):

**1. TRIM BE — $390** (was $403). Price $195.02. Still the book's worst cap overage (2.64x, headroom -$1,210) and #1 derisk-queue rank. Thesis strengthening + a fresh NEW TAILWINDS flag are real, but per G58-style precedence they're context only — the structural catalyst and cap breach carry this trim. *2026-08-24.*

**2. TRIM GEV — $379** (was $396). Price $944.70. Cap 1.24x, headroom -$365, derisk rank 7. Also picked up NEW TAILWINDS this run (contextual tension, not cancelling). *2026-08-24.*

**3. TRIM VRT — $360** (was $367). Price $257.00. Cap 1.55x, headroom -$641, derisk rank 4. Thesis WATCH is contested (EPS beat/revenue miss) so it's supporting, not leading — sized off the breach and trigger. *2026-08-24.*

**4. TRIM AVGO — $292** (was $295). Price $364.56. Cap-independent (0.58x, +$1,065 headroom) — the trigger framework treats an in-cap name as the *preferred* candidate here, not marginal, precisely so this desk stops only trimming what already breached. Recommended 5x since 08-17 and never actioned; still stands. *2026-08-24.*

**5. NEW — TRIM BX — $285** *(new proposal, not yet in the store)*. Price $143.28, cap 0.48x (+$1,578 headroom, not cap-driven). BX was re-entered TODAY (10sh, 3.71% wt) as "Financials/Alt-Asset Diversifier," but smith-thesis's fresh read (G82) explicitly confirms it is **not a clean diversifier** — it shares AVGO's exact off-balance-sheet AI-financing tail risk, and is now named as counterparty in the escalated $70-80bn SPV. BX is not yet in `compute_triggers.json`'s live `catalyst_threat` list only because state hadn't been updated with BX before this run's triggers pass ran — the same catalyst that trims AVGO applies directly to BX, same as the historical BX/AVGO precedent three weeks ago. Sized at the standard 20% catalyst_threat fraction ($1,432.80 × 0.20 = $286.56, rounded).
   **Flag for the user explicitly: this recommends partially reversing a position opened hours ago.** I am not overriding the re-entry — I am surfacing that the same structural risk which is driving four other trims in this book applies to BX too, and letting you weigh a same-day probe position against that. A lighter-touch alternative is to hold BX flat and simply add it to theme_3's mapped catalyst tickers (as smith-catalyst already recommends) so the standing trigger screen catches it cleanly next run instead of a manual override today.
   Evidence: verified 1 (sourced SPV escalation reporting), computed 1 (cap/mv), unverified 0.

---

## 2. Risk-cap TRIMs — reaffirmed, resized to today's compute_risk.json

**6. TRIM MRVL — $500** (was $550.65, scale_out_ladder/shadow). G80 flagged this as possibly stale after the 08-18 stop cut MRVL down — but current `compute_risk.json` shows MRVL now at **8 shares, cap 1.73x, headroom -$774** (worse than at proposal time, not cleared). The shadow trigger still coincides with a live computed breach, so it stays live per §2c. Thesis was upgraded watch→strengthening this run (Google-partnership evidence, $12.2B warrants, 40% FY27 guide) and Friday's -5.57% is confirmed profit-taking, not a red flag — none of that argues against the trim, it's purely a risk-cap action. Note MRVL's TARGET GAP resolved OUT this run (7.87% upside, below the 15% bar) — that removes any lingering BUY-side support, irrelevant to this TRIM. **smith-tax: sequence this trim HIFO, not FIFO — FIFO books a +$109.73 gain, HIFO books a -$34.17 loss, a $143.90 swing (26% of proceeds).** Price $228.92, cures ~65% of the cap excess.

**7. TRIM NVDA — $530** (was $576). Cap 1.20x, headroom -$531 — effectively a full cure at this size. NVDA earnings Wed 08-26 (2 trading days out): 4/4 trailing beats but drifts **negative** an average -5.30% two days post-print — a red Thursday would not be evidence of a miss, don't read it that way. Sentiment eased extreme_greed→greed but is still elevated; framed on earnings-timing + cap breach, not mechanics alone. Evidence verified 1 (earnings date), computed 3.

**8. TRIM NBIS — $600** (was $645.44). Cap 1.83x, headroom -$672 (cures ~89%). Upgraded evidence this run: the -14% dilutive convertible-note hit (08-19) and unresolved Vineland data-center concerns are real, confirmed developments, not just cap mechanics — thesis stays WATCH, genuinely unsettled. Price $215.15 (unchanged from last cycle pending a fresh quote).

## 3. Technical TRIM — confidence downgraded, not retired

**9. TRIM MSFT — $360** (unchanged). Originally an `overbought_distribution` live trigger (RSI 78.8). **This run's RSI cache is 12 days stale and the trigger is structurally suppressed (live_counts=0)** — I cannot confirm MSFT is still extended, nor can I confirm it has cooled. `rotation.json` now shows MSFT as PEER LEADER (bullish signal) and well inside cap (0.43x, +$1,896 headroom), which is at least consistent with continued strength, not a reversal. Recommended 4x since 08-12, still open. Holding the size flat pending fresh RSI data rather than either cancelling or escalating on stale technicals.

## 4. Shadow stop-raises — one reaffirmed, one retired

**10. RAISE MU stop to cost basis — $0** (unchanged, reaffirm). G80 flagged this as possibly moot after the 08-18 cut — checked against `compute_book.json`: **MU is a real 3.65%-weight position (1.5 sh, $1,401.94 mv), still 1.26x over its ATR cap.** Not dust. The position has pulled back since the original proposal (price then $1,008.54, now $934.40 — gain down from +15.4% to +6.9% vs the $874.17 basis), which makes protecting the smaller remaining gain *more* relevant, not less. Zero capital moved.

**RETIRE — P-117 (Raise TER stop to cost basis).** Confirmed moot: TER is a **$1.00, 0.003%-weight dust residue** from the 08-18 cascade (0.003x of anything). There is nothing left to protect. This is exactly the G80 failure mode the auto-retirement pass structurally can't catch — retiring by judgment here.

## 5. Discretionary BUYs — reconciled against rebound and corrected where stale

**11. BUY QCOM — $300** (unchanged). Real cap headroom now $832 (wider than at proposal time), still sized as a small first tranche per the stop-loss-style preference (stage around binary events — NVDA/MRVL earnings sit 2-3 days out).

**12. BUY WDC — $150** (unchanged). Reconciled against rebound's $550 stage-in suggestion: actual cap headroom is only $203 — $550 is not usable. Primary support is the real AI Memory/Storage floor breach (8.04% vs 15% target), not the WDC-specific PEER LAGGARD flag picked up this run (a tension worth noting, not a blocker — floor breach is the load-bearing input).

**13. BUY GLW — $90** (unchanged). Reconciled against rebound's $600 suggestion: actual cap headroom is only $141 — again well short of $600. Kept conservative within that ceiling given the ESCALATING gate.

**14. BUY AMZN — reduce to $350** (was $700). **Correction: the original rationale ("-7.17pt under floor") is stale.** Current `compute_drift.json` shows Compute/Hyperscaler at 17.2% vs a 20% target, band [15,25] — **in-band, not breached.** This is now a purely discretionary add with no active breach or typed trigger behind it (matches its own priority_score of -1/LOW). Cutting size in half rather than dropping it, given the ESCALATING gate and thin cash argue against full-size discretionary deployment this week.

**15. BUY IREN — $111** (unchanged, rationale corrected). IREN was fully exited in the 08-18 cascade — **this is a re-entry, not "still hold."** Fresh support: smith-watchlist's TARGET_GAP screen puts it at 48.76% upside today, and the user has explicitly asked (08-12 open_flag) to keep IREN as an active re-entry candidate, not chase. Small, thin-headroom size stands.

## Declined / not sized this run

- **BE dip-buy** (rebound suggested $350 at $185.64 support): declined. BE is simultaneously the largest cap overage in the book (2.64x) and a live catalyst_threat trim target — adding to it the same week would directly contradict proposal #1.
- **SKHY dip-buy** ($600 suggested): declined. Real cap headroom is only $44.74 — the size is not usable, and support is flagged low-confidence (thin ADR history).
- **LRCX dip-buy** ($500 suggested, real headroom $232): deferred, not sized. Thesis is genuinely clean (strengthening, in-band cluster, real macro-driven dip), but with the aggregate open-risk cap already breached (12.24% vs 10%) and the ESCALATING gate weighted more heavily than the drawdown-based risk_off_status per scout's own framing, this isn't the week to add a fresh, unforced position. Worth a fresh look once the NVDA/MRVL print risk clears.

---

## Risk-off check

`risk_off_status` from `compute_drift.json` is **normal** (drawdown -6.89%, well inside the 8%/12% warn/risk-off thresholds) — no formal defensive trigger fires. But three independent signals argue for caution beyond what that status alone implies, and per scout's own framing today's faster-moving pre-market gate should be weighted more heavily than the composite for near-term sizing:

1. **Gate ESCALATING** on an Asia-led selloff (KOSPI -3.12%, a semis-heavy index — direct read-through to this book's AI-capex chain), VIX +5.09% to 15.90.
2. **Aggregate open ATR risk 12.237% vs a 10% cap** — a real, cap-independent concentration breach sitting on top of (not captured by) the drawdown-based status.
3. Macro's own read: **"turning risk-off, not yet confirmed"** — SPY put/call OI climbing three straight readings (1.88→2.29→2.54) while VIX stays complacent, 10yr at 4.738% against a hawkish Fed.

Net effect on sizing this run: lead with the five catalyst/cap trims, hold new discretionary BUYs to small, cap-respecting tranches only, and decline unforced new adds (LRCX, SKHY) until the NVDA (08-26) / MRVL (08-27) earnings pair clears — those two land back-to-back and are correlated, not independent (combined ~1.06% of book at 1-sigma same-direction).

---

## Stress table (approximate, macro-anchored)

Anchored to smith-macro's live regime read where flagged; otherwise cluster-weight/beta approximation, labelled.

| Scenario | Est. impact | Most exposed |
|---|---|---|
| AI-capex pause | **-18% to -22%** (-$7,500 to -$9,200) | NVDA, MRVL, MU, BE, GEV, VRT, NBIS, AMD, LRCX, AMAT — 83.4% of equity sits in this chain |
| Rates +100bp (10yr →~5.7%) | **-9% to -12%** (-$3,800 to -$5,000) — *macro-anchored: 10yr already at 4.738% (up from 4.696% 2wk ago) against a cached HAWKISH Fed; this scenario compounds an active headwind, not a fresh one* | NBIS (β2.64), FLTW (β2.41), SKHY (β2.44), BE (β2.11), MU (β1.95), WDC (β2.22, fresh), HOOD (β2.32, fresh) |
| Tariff/export-control escalation | **-6% to -8%** (-$2,500 to -$3,300) | TSM (Taiwan-domiciled), NVDA/AMD (China export exposure), AMAT/LRCX (equipment export controls) — concentrated in AI Semis/Fabs (28.5% of equity) |
| USD/INR ±3% | **~0%** on the USD-reported book itself | N/A — this is a currency-translation scenario, not a stock-price one. A 3% INR depreciation raises the book's INR-terms net worth by ~3% (~₹1.2L on the ₹95.7/$ equivalent); a 3% INR appreciation cuts it by the same |

## Hit-rate readout

Signals tail did not populate `bucket_hit_rates`/`name_bucket_grades` this run (data-quality gap, noted below) — nothing to report at the trigger-bucket level this cycle without recomputing it myself, which I won't do.

## Scorecard interpretation (stored, not recomputed)

From `proposals.json.scorecard` (as_of 2026-08-24, last written 2026-08-20): **overall 14.3% (n=7)** — TRIM 100% (n=1, avg +8.09%), BUY 0% (n=4, avg -13.88%), HOLD 0% (n=2, avg -9.41%). One entry (P-011 NEM) remains quarantined pending anchor-review, correctly excluded. 78 open proposals are still under 30 days and not yet scorable.

Reading this straight: **n is too small to trust any single bucket's rate**, including the TRIM bucket's 100% — that's one proposal. What the record does support is directional caution on the BUY bucket specifically: 4 discretionary/rebound-style buys from the same early cohort all missed, averaging a real -13.88% adverse move. That's consistent with, and reinforces, the conservative sizing applied to today's BUY proposals (QCOM/WDC/GLW held to cap-respecting tranches, AMZN cut in half, LRCX/SKHY declined outright) rather than treating any of this week's rebound candidates as high-conviction. This scorecard is thin evidence, not a verdict — but it argues for the desk's proposals being weighted as one input for your judgment, not a track record to lean on yet.

## Data quality
- RSI14/rel_strength_1m caches 12+ days stale (past 7/10-day TTLs) — both technical live triggers (`oversold_reversion`, `overbought_distribution`) suppressed this run; MSFT's overbought status is unconfirmable, not disproven.
- `bucket_hit_rates`/`name_bucket_grades` not present in this run's signals tail — hit-rate-by-bucket readout skipped rather than recomputed.
- G18 (max-pain unavailable, both SPY/QQQ proxies) was marked `wont_fix`/closed but is independently reconfirmed broken by both smith-macro and smith-earnings this run — recommend reopening it.
- BX lot dated 2026-08-21 in lots.json vs the stated 2026-08-24 re-entry date (book's flag, independently caught by smith-tax too) — reconciliation flag, not a tax issue.
- G81 (proximate cause of the 08-18 semis rout) remains open and unresolved; today's KOSPI -3.12% figure (G81-adjacent) could not be independently corroborated to one clean print — treated as orchestrator-sourced, doesn't change the ESCALATING gate call.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"TRIM","ticker":"BE","size_usd":390,"price_at_proposal":195.02,"rationale":"Live catalyst_threat (WSJ $3T off-balance-sheet AI-financing story); worst cap overage in book (2.64x, headroom -$1,210), derisk rank 1/33. Thesis strengthening and fresh NEW TAILWINDS cited as context only, not basis.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"GEV","size_usd":379,"price_at_proposal":944.70,"rationale":"Same catalyst_threat trigger; cap 1.24x (headroom -$365), derisk rank 7. NEW TAILWINDS flag noted as tension, not cancelling.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"VRT","size_usd":360,"price_at_proposal":257.00,"rationale":"Same catalyst_threat trigger; cap 1.55x (headroom -$641), derisk rank 4. Thesis WATCH is contested (EPS beat/rev miss) -- supporting input only.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":1,"computed":2,"unverified":0}},
   {"action":"TRIM","ticker":"AVGO","size_usd":292,"price_at_proposal":364.56,"rationale":"Cap-independent catalyst_threat (0.58x cap, +$1,065 headroom) -- in-cap names are the preferred candidate under this trigger by design. Recommended 5x since 08-17, never actioned.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"TRIM","ticker":"BX","size_usd":285,"price_at_proposal":143.28,"rationale":"NEW. Same structural catalyst as AVGO (BX now named counterparty in the escalated $70-80bn AI-financing SPV) applied manually since BX predates this run's catalyst_threat list. Cap-independent (0.48x, +$1,578 headroom). Flag: BX was re-entered TODAY (10sh) -- this proposes partially reversing a same-day probe position; surfaced for review, not urged. Lighter alternative: add BX to theme_3 mapped tickers for next run's standing screen instead.","trigger_type":"catalyst_threat","trigger_bucket":"catalyst_threat","pair_id":null,"pair_role":null,"evidence_quality":{"verified":1,"computed":1,"unverified":0}},
   {"action":"TRIM","ticker":"MRVL","size_usd":500,"price_at_proposal":228.92,"rationale":"scale_out_ladder (shadow) coincides with a live computed cap breach that WORSENED, not cleared, since the 08-18 stop (now 8sh, 1.73x cap, headroom -$774). Thesis upgraded watch->strengthening this run (Google-partnership evidence) -- context only, not the basis. Target gap resolved OUT (7.87%, below 15% bar), removing prior BUY-side support -- irrelevant to this TRIM. TAX: sequence HIFO not FIFO -- FIFO books +$109.73 gain, HIFO books -$34.17 loss, a $143.90 swing (26% of proceeds).","trigger_type":"scale_out_ladder","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1}},
   {"action":"TRIM","ticker":"NVDA","size_usd":530,"price_at_proposal":219.74,"rationale":"Cap 1.20x, headroom -$531 (near-full cure at this size). Earnings 08-26 (2 trading days): 4/4 trailing beats but avg -5.30% drift two days post-print -- a red Thursday would not be a miss signal. Sentiment eased extreme_greed->greed but still elevated.","trigger_type":null,"trigger_bucket":"trim_risk_cap","pair_id":null,"pair_role":null,"evidence_quality":{"verified":1,"computed":3,"unverified":0}},
   {"action":"TRIM","ticker":"NBIS","size_usd":600,"price_at_proposal":215.145,"rationale":"Cap 1.83x, headroom -$672 (cures ~89%). Upgraded evidence: -14% dilutive convertible-note hit (08-19, confirmed) and unresolved Vineland data-center concerns are real developments, not just cap mechanics. Thesis stays WATCH, genuinely unsettled.","trigger_type":null,"trigger_bucket":"trim_risk_cap","pair_id":null,"pair_role":null,"evidence_quality":{"verified":1,"computed":2,"unverified":0}},
   {"action":"TRIM","ticker":"MSFT","size_usd":360,"price_at_proposal":481.63,"rationale":"Originally live overbought_distribution (RSI 78.8) -- RSI cache now 12d stale, trigger structurally suppressed this run, condition unconfirmable either way. Held flat pending fresh data. PEER LEADER signal and wide cap headroom (0.43x) are at least consistent with continued strength.","trigger_type":"overbought_distribution","trigger_bucket":null,"pair_id":"P-ROT-0819","pair_role":"sell_leg","evidence_quality":{"verified":0,"computed":2,"unverified":0}},
   {"action":"RAISE_STOP","ticker":"MU","size_usd":0,"price_at_proposal":934.40,"rationale":"Reaffirmed. MU is a real 3.65%-weight position (1.5sh, $1,401.94mv), still 1.26x over cap -- not dust despite the 08-18 cut. Gain has shrunk from +15.4% to +6.9% vs $874.17 basis since the original proposal, making the breakeven-stop raise more relevant, not less. Zero capital moved.","trigger_type":"profit_ratchet","trigger_bucket":"shadow","pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"BUY","ticker":"QCOM","size_usd":300,"price_at_proposal":162.00,"rationale":"Small first tranche, headroom now $832 (wider than at proposal time). Staged ahead of NVDA/MRVL earnings per stop-loss-style preference.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":1,"unverified":2}},
   {"action":"BUY","ticker":"WDC","size_usd":150,"price_at_proposal":462.35,"rationale":"Reconciled vs rebound's $550 suggestion -- real cap headroom only $203. Primary support is the real AI Memory/Storage floor breach (8.04% vs 15% target); PEER LAGGARD flag noted as tension, not a blocker.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":1,"computed":1,"unverified":1}},
   {"action":"BUY","ticker":"GLW","size_usd":90,"price_at_proposal":152.54,"rationale":"Reconciled vs rebound's $600 suggestion -- real cap headroom only $141. Kept conservative within that ceiling given the ESCALATING gate.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":1,"unverified":2}},
   {"action":"BUY","ticker":"AMZN","size_usd":350,"price_at_proposal":259.45,"rationale":"CORRECTED: original '-7.17pt under floor' rationale is stale -- Compute/Hyperscaler is now in-band (17.2% vs 20% target, band [15,25]). Purely discretionary add, no active breach behind it. Halved from $700 given the ESCALATING gate and thin cash.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":1,"unverified":1}},
   {"action":"BUY","ticker":"IREN","size_usd":111,"price_at_proposal":42.00,"rationale":"CORRECTED framing: IREN was fully exited in the 08-18 cascade -- this is a re-entry, not continuing exposure. Fresh support: watchlist's TARGET_GAP screen puts it at 48.76% upside today; matches the user's standing 08-12 re-entry preference (not chasing).","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}}
 ],
 "retired":[{"id":"P-117","ticker":"TER","reason":"TER is a $1.00 (0.003% weight) dust residue from the 08-18 cascade -- nothing left to protect. G80 shadow-trigger auto-retirement gap, closed by judgment."}],
 "scorecard_read":"Stored scorecard (as_of 2026-08-24, n=7): overall 14.3%, TRIM 100% (n=1, avg +8.09%), BUY 0% (n=4, avg -13.88%), HOLD 0% (n=2, avg -9.41%); P-011 NEM remains quarantined. n is too small to trust any single bucket including the 100% TRIM figure (n=1). The BUY bucket's 0-for-4 at -13.88% average is the one directionally meaningful read from this cohort and argues for the conservative sizing applied to this run's BUY proposals (small tranches, AMZN halved, LRCX/SKHY declined) rather than treating rebound-style dip-buys as high conviction yet.",
 "deemphasize_buckets":[],
 "data_quality":["RSI14/rel_strength_1m caches 12+ days stale -- oversold_reversion and overbought_distribution live triggers suppressed this run","bucket_hit_rates/name_bucket_grades not present in signals tail this run -- hit-rate-by-bucket readout skipped rather than recomputed","G18 (max-pain, SPY/QQQ) marked wont_fix but independently reconfirmed broken by smith-macro and smith-earnings this run -- recommend reopening","BX lot dated 2026-08-21 vs stated 2026-08-24 re-entry -- reconciliation flag, not a tax issue","G81 (08-18 rout proximate cause) remains open; today's KOSPI -3.12% figure could not be independently corroborated to one clean print"]}
```

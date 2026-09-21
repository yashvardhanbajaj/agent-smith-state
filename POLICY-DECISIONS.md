# Policy Decision Log

Full rationale for policy.json's current values. policy.json itself carries only a
short `notes` array of live, still-relevant flags — historical narrative (superseded
values, defects already fixed, dead-end considerations) lives here instead.

---

## Cluster targets (30/20/20/15/10/5/0/0, sum 100 on invested_equity)

**2026-07-18**: Added the "Compute/Hyperscaler" line (target 10%, band [5,15]) — it
already appeared in `ai_capex_clusters` but had no target/band, leaving 7.9%+ of the
book untracked by drift analysis. Applied without user confirmation (draft itself was
unconfirmed).

**2026-07-25 (G28 fix)**: Targets had summed to 105% because "Diversified/Regional
ETF" (5%) was bolted onto the AI-cluster targets (30/20/20/15/10/5=100) without being
carved out of them — an arithmetically impossible spec against the [3,15]% cash band.
Fixed by setting Diversified/Regional ETF target to 0 (permissive [0,10] band kept —
a diversifier sleeve remains allowed, just no longer a standing shortfall). The
AI-cluster numbers themselves were restored verbatim to the user's originals; an
interim proportional rescale (29/19/19/14/9/5) tried the same day is reverted as
unnecessary once the real defect (double-counting) was found.

## Denominators (clusters+AI-capex = invested_equity, cash = total_book)

**2026-07-25 (G28 fix)**: The drift table silently mixed bases — cluster/AI-capex %
was equity-denominated while cash % was total-book-denominated, so columns were never
comparable (cash swung 0.06%→45.8% in 5 days and would have made every cluster read
"underweight" for reasons unrelated to allocation). Declared explicitly: layer 1 sets
cash vs invested (total_book basis), layer 2 sets shape within the invested sleeve
(invested_equity basis). `ai_capex_denominator` defaulted to invested_equity as the
conservative choice — on total_book the cap read 54.2% (vs 100%+ on equity) and a
14-run-old breach would have silently vanished. This was flagged as the user's call,
not an assumed default.

## AI-capex concentration: cap 100%, intentional (not a breach)

**2026-07-25, user decision (explicit)**: "AI capex can be high as I have high
conviction on AI Infra and capex." Concentration is intentional, not drift.
Consequences applied:
- `max_ai_capex_factor_pct` raised 90 → 100 (invested_equity basis) — the invested
  sleeve may be entirely AI-capex by design, no longer reported as a breach.
- `ai_capex_factor_flag_threshold_pct` (was 60) set to null — existed to nag about a
  concentration the user has now affirmed; kept, it was pure noise.
- `concentration_is_intentional: true` added as an explicit marker so future runs
  don't re-flag this as an open question.

**Context for why this mattered**: the 90% cap had been breached every run since
inception (actual ~99.2% by 07-18), sitting 30pt above the draft's own 60%
sane-diversification flag. Rather than quietly tightening controls to match behavior,
the user's conviction was surfaced explicitly and the policy was changed to match it.

## Risk controls after abandoning factor diversification

**2026-07-25**: With cluster diversity no longer a control on *exposure* to
AI-capex (only on *mix within* it), the load-bearing constraints are:
(a) `max_single_position_pct` 12%
(b) `cash_band_pct` [3,15] on total_book
(c) `drawdown_warn_pct` 15 / `drawdown_risk_off_pct` 25
(d) cluster bands (now governing mix within the chain, not exposure to it)

These are the only remaining brakes on a 100% single-factor book running at ~61%
sector volatility (SOX 3mo realized) with no internal offset. Reviewed as a set
because they now carry the whole risk-management load that diversification used to
share.

## Sell-discipline drawdown ladder (added 2026-07-26, Tier 2.3)

Converts the -15%/-25% warn/risk-off thresholds (which only classified status) into
actual recommended actions at intermediate points, so de-risking is pre-committed
policy instead of in-the-moment discretion (see the undocumented 07-24 flow event,
`known-gaps-archive.json` G26). Four rungs: -15% warn (monitor only) → -18% trim 10%
of watchlist → -22% trim 20% of watchlist → -25% move to cash / freeze deployments.
Percentages are a first cut, not user-negotiated — revisit if they fire.

## Superseded / dead-end considerations (for the record, no longer relevant)

- **2026-07-18**: max_ai_capex_factor_pct=90% ceiling breached (~99.2% actual,
  corrected same-day from an initial stale-price-driven 99.278% read) — superseded
  by the 2026-07-25 decision to raise the cap to 100%.
- **2026-07-18 (user-caught)**: A reported SNDK breach at 12.352% was WRONG — caused
  by a stale INDmoney per-position price (folded into known_gaps G3/G14, both
  resolved). True weight was 10.482%, no breach.
- **max_single_position_pct 12%**: set as a conventional default; MU sat at 12.71%
  on day one. No change made — still the live cap; see position_breaches in each
  run's drift output for current status.

## Still open (not yet a decision, just tracked)

- **LTCG lots**: `prefer_ltcg` is true on principle but cannot be applied per-name —
  `lots.json` needs seeding from INDmoney order history (known_gaps G1). See
  `LOTS-SEEDING-GUIDE.md`.
- **Drawdown/cash-band thresholds** (warn -15%/risk-off -25%, cash [3,15]%): still
  defaults, not derived from this book's actual behavior. No drawdown history
  existed at draft time; revisit once the book has a real volatility track record.


## 2026-09-21 — Policy v2 (user decisions after the policy review)

Decided by the user: risk-off -20% (ladder now steps the AGGREGATE OPEN-RISK CAP: -15 -> 8%, -17 -> 5%, -18.5 -> 3%, -20 risk-off); stress limit kept as proposed (-35% AI-capex shock, max 20% of book loss, advisory); target 15-20 positions (advisory); aggregate cap stays 10%; cash band advisory; evaluation window rolling 12 months vs SMH (tolerance 10pp is the desk's proposal, review flag only); tax stance retired.

Structural (desk, disclosed): one denominator (total book) for cluster targets, AI-capex and cash; conditional-denominator rule retired; owner/desk layers with a hash confirmation.

Observed when written: AI-capex 95.8% of equity / 75.9% of total book, so a -35% shock ~= -26.6% of book (over the 20% limit, advisory); trailing TWR history since 2025-05: 64.84% vs SMH 158.17%; max observed drawdown -29.4% (beyond the 25% budget, before this ladder existed).

### Notes moved out of policy.json (verbatim)
- Full decision rationale (cluster targets, denominators, AI-capex cap history, risk-control set) moved to POLICY-DECISIONS.md 2026-07-26 to keep this file to live values. Read that file before proposing any change to a value below.
- AI-capex concentration is INTENTIONAL (user decision, 2026-07-25) -- do not treat max_ai_capex_factor_pct=100 as a bug or re-flag the concentration as drift.
- 2026-07-27: cluster_targets revised (Memory 20->15, Optics 20->15, Hyperscaler 10->20) and stop_loss_framework added, both on explicit user instruction. See cluster_targets_rationale and stop_loss_framework.
- 2026-07-28: cash band replaced with a two-regime rule (normal [5,15]%, post-stop-event [5,40]%) on user instruction. See cash_regimes.
- 2026-07-28: Power/DC cluster floor was found to cap total deployable equity at ~$30,010 with only GEV+VRT in the cluster -- breadth, not capital, is the binding constraint. A third Power/DC name was screened and proposed (CEG) to relieve it.
- 2026-07-28: cluster denominator made conditional on cash regime (user-raised). See cluster_denominator_conditional.
- 2026-08-30: cluster_targets revised (three diversifier clusters given real targets, AI targets stepped down to keep the sum at 100%); ai_capex_factor_flag_threshold_pct set to 90 as an OBSERVATION threshold only; stale LTCG note removed -- lots.json now carries 74 lots with zero null dates, so G1 is closed and prefer_ltcg is applicable name-by-name.
- 2026-08-30: stop_loss_framework.support_anchored_exception added on user instruction -- rebound entries size off their real stop (floored at 0.5x ATR and 3%), same 0.5% risk budget, uplift bounded to 4x by the floor. Aggregate open-risk cap unchanged and still binding.


## 2026-09-21 — Narrative archived out of policy.json (verbatim)

Moved at the user's request so policy.json holds live values, rules and short statuses only. Each entry is `path` followed by its original text.

### `cluster_targets/Critical Minerals/Rare Earth/rationale`

Created by the MP Materials entry 2026-08-05 (10sh @ $47.47, dca-into-diversification). Banded 0%/[0,5] mirroring Enterprise Software's treatment -- a satellite non-AI-capex diversifier with room to grow but no target obligation. User-selected 2026-08-06 over a larger 5%/[0,10] sleeve.

### `cluster_targets/Analog/Industrial Semis/rationale`

Held but absent from cluster_targets until now, so cmd_drift emitted it with a null target and breach:false -- reported, but structurally unable to breach. Two of the three (Financials/Alt-Asset, China Internet) exist under these names only because compact archived their classification on exit and smith-thesis re-derived it from scratch on re-entry under a different label (BX was 'Alternative Asset Manager/Diversifier', BABA was 'China Consumer/Cloud'). These are now the canonical names; agents reuse policy cluster strings, so re-derivation will match from here.

### `cluster_targets/Financials/Alt-Asset Diversifier/rationale`

Held but absent from cluster_targets until now, so cmd_drift emitted it with a null target and breach:false -- reported, but structurally unable to breach. Two of the three (Financials/Alt-Asset, China Internet) exist under these names only because compact archived their classification on exit and smith-thesis re-derived it from scratch on re-entry under a different label (BX was 'Alternative Asset Manager/Diversifier', BABA was 'China Consumer/Cloud'). These are now the canonical names; agents reuse policy cluster strings, so re-derivation will match from here.

### `cluster_targets/China Internet/Diversifier/rationale`

Held but absent from cluster_targets until now, so cmd_drift emitted it with a null target and breach:false -- reported, but structurally unable to breach. Two of the three (Financials/Alt-Asset, China Internet) exist under these names only because compact archived their classification on exit and smith-thesis re-derived it from scratch on re-entry under a different label (BX was 'Alternative Asset Manager/Diversifier', BABA was 'China Consumer/Cloud'). These are now the canonical names; agents reuse policy cluster strings, so re-derivation will match from here.

### `cluster_targets/AI Storage/HDD/rationale`

User-selected 2026-09-21 (option 1). WDC is pure nearline HDD since the SanDisk separation (thesis: zero DRAM/NAND/HBM revenue, high confidence); it was mis-ranked as a Memory laggard, which drove false sell pressure (P-149). Different cycle from memory. 3pt carved from AI Memory/Storage (10->7) so targets still sum to 100 and AI-capex stays 89%. Single-name cluster: no substitution ladder until a peer (e.g. STX) is added.

### `cluster_targets_rationale`

REVISED 2026-08-30 on explicit user instruction, after an audit found 14.53% of equity in clusters that could never breach a band. Targets previously summed to 100% of invested equity while three held clusters had no entry at all and four held tickers had no sector_map entry, so the six AI clusters were structurally forced ~14.5pt below target and BOTH live breaches were UNCURABLE FLOOR breaches (AI Memory/Storage, Compute/Hyperscaler) -- a standing source of proposals nobody could action. The three diversifier clusters now carry real targets and the AI targets step down so the sum is honest rather than aspirational. Targets are anchored to post-restore actuals, so the book starts COMPLIANT (zero breaches) instead of in manufactured breach. AI-capex clusters target 89% against 89.4% actual: the concentration remains fully intentional, the arithmetic just stops lying about it. PRIOR (2026-07-27) allocation and its reasoning are preserved in POLICY-DECISIONS.md.

### `stop_loss_framework/rationale`

The user runs tight, large-quantum stops by design and will continue to (confirmed 2026-07-27); the stops are an emotional-tolerance control, not a technical signal. The prior failure mode was stop distance set without reference to a name's volatility -- a 3% stop on a name that ranges 8-9% intraday is a near-certain whipsaw. Constant-risk sizing resolves the apparent tension between 'wide stops' and 'small losses': a wider stop automatically produces a SMALLER position, so the dollar loss stays capped at 0.5% of book either way. DESIGN INTENT: worst case with every stop firing sits inside the -15% drawdown_warn rung, so the stop system can never by itself trigger the de-risking ladder. CORRECTED 2026-08-30 -- this file asserted that worst case was '~7.4% of book' as though it were a standing property. It is not; it is an OUTCOME of how much is deployed and at what volatility, and it drifts. Measured 11.947% on 2026-08-30 and 13.028% on 08-26, against the 10% aggregate_open_risk_cap_pct_of_book below -- i.e. the cap has been BREACHED, not merely approached. `smith_math.py validate` now fails on aggregate_over_cap so this can never again run for weeks as an unread line in a table. Any new position competes for a budget that is currently overdrawn and must be funded by reducing risk elsewhere.

### `stop_loss_framework/support_anchored_exception/risk_is_unchanged`

This does NOT loosen the risk budget. The same 0.5% of book is at risk if the stop fires; it is simply measured where the stop actually sits rather than at an arbitrary 2xATR. Verified: risk-at-cap is identical to the standard rule for every volatility tier.

### `stop_loss_framework/support_anchored_exception/why_the_floor`

A 4% stop on a 14%-ATR name is exactly the whipsaw this framework's main rationale was written to prevent. The support-anchored stop may be tighter than 2x the noise band because it rests on a real level, but never inside HALF a day's normal movement. The floor doubles as the uplift bound and is why no separate cap is needed: standard is 2xATR and the tightest permitted is 0.5xATR, so the exception can never size more than 4x the standard cap.

### `stop_loss_framework/support_anchored_exception/aggregate_cap_still_binds`

aggregate_open_risk_cap_pct_of_book applies unchanged. As of 2026-08-30 it is BREACHED (13.2% vs 10%), so a rebound entry must be FUNDED by reducing risk elsewhere -- typically the buy leg of a paired rotation -- not added on top. The sizing path stamps the funding shortfall on the proposal.

### `stop_loss_framework/support_anchored_exception/rationale`

Added 2026-08-30 on explicit user instruction, after modelling showed the standard rule structurally penalises exactly the names a rebound mandate wants. Constant-dollar-risk sizing makes max_position inversely proportional to ATR, so a 14%-ATR name gets ~1/7th the allowance of a 1.9%-ATR name and is flagged over-cap 38% of the time against 11% for low-vol names. That is correct for an entry with no view on where the name holds, and wrong for one bought AT a level. smith-rebound already computes support_usd; this makes the sizing consume it.

### `stop_loss_framework/gap_allowance/rationale`

Stops are not guaranteed fills. Replaying 12 months of prices against the book's own stop distances: a stop-breach day cost ~1.12x the planned distance on average (p90 1.40x, p95 1.55x), 44% of breaches closed beyond the stop, and 19 days had 5+ names breach together. base 1.15 rounds up the mean; event 1.5 is ~p95. Proxy (no opening prices in perf_bars): replace with measured slippage once >= 10 real stop fills exist.

### `cash_regimes/rationale`

REVISED 2026-07-28 on explicit user instruction. The prior single [3,15]% band was an inherited default -- policy.json's own notes flagged it as not derived from this book's behaviour. It is incompatible with the user's confirmed stop-loss method, which has now twice liquidated a large fraction of the book in one session (2026-07-24: cash to 45.8%; 2026-07-28: cash to 60.5%). Under the old band, every post-stop-event day reported a severe breach the desk could not cure without violating the position-risk framework -- a false alarm that trained the reader to ignore a real control. The two-regime band separates 'cash is high because stops fired' (expected, tolerated to 40%) from 'cash is high because we are not deploying' (a genuine breach). Above 40% remains a real breach requiring action in either regime.

### `cluster_denominator_conditional/rationale`

User-raised 2026-07-28 and accepted. Rebuilding a book from a large cash position takes weeks, and cluster percentages computed on a shrunken equity base manufacture breaches that cannot be cured without violating the position-risk framework -- the third instance of the same denominator defect this week (Power floor binding at $29,870; cash band reporting an uncurable breach; now cluster ceilings). Cash is genuinely uncorrelated, so total book is the honest measure of factor risk while it is elevated. WHAT THIS DOES NOT DO: it does not relax per-position risk caps. A name at 1.6x its 0.5%-risk cap is oversized on either denominator -- SNDK on 2026-07-28 is the live example.

### `cluster_denominator_conditional/why_split`

A ceiling asks 'am I over-exposed to this factor?' -- idle cash is uncorrelated, so total book is the honest denominator. A floor asks 'is the invested portfolio the right shape?' -- that is a construction question, and 'hold 10% of TOTAL BOOK in Power' is incoherent while deliberately holding 48% cash. Testing both edges on one denominator was tried first and manufactured five phantom floor breaches.

### `confirmation_note`

Top-level confirmation given by the user 2026-08-06 in an interactive Agent Smith session. Individual components had already been confirmed separately on their own dates (mandate 2026-07-26; stop_loss_framework 2026-07-27; monthly_contribution 2026-07-27; cash_regimes 2026-07-28); this flips the whole document from draft to binding, so drift/breach analysis is no longer provisional. Per the desk's standing rule, a confirmed policy is never modified again without an explicit user instruction.

### `cluster_playbooks_note`

Added 2026-09-08 with cmd_ladder and smith-cluster. ONE agent definition is dispatched once per cluster; the cluster-specific knowledge -- the axes that actually decide which name wins inside THIS cluster -- lives here as DATA rather than in seven agent prompt files that would drift apart and each re-derive the shared output contract. Editable without touching a prompt. `slug` becomes the agent key (cluster_<slug>) and the slice/tail filename, so it must be unique and stable; changing one orphans that cluster's dispatch for a run. `differentiators` are the ranking axes the agent must actually rank on -- a ladder that re-states price is the thing this whole layer exists to replace. `read_throughs` are the cross-member inferences a per-name agent structurally cannot make.

### `trade_materiality/rationale`

Added 2026-09-20 after the engine proposed rotating $56.37 of SKHY into CIEN on a $42.5K book (a correct 10-point call earns $5.64). Market-value sizing on a sell could not express 'too small to matter'. ADDITIVE: no stop_loss_framework, mandate or cluster_targets value was touched.

### `heat_budget/rationale`

Added 2026-09-20 (Phase 3). stop_loss_framework records the 10% aggregate cap breached at 13.028% (08-26) and 11.947% (08-30) while sizing continued at the full per-position formula: the cap only ever printed a warning. ADDITIVE: no stop_loss_framework, mandate or cluster_targets value was touched.

### `cluster_targets_mode_note`

2026-09-21, user: clusters exist to group holdings and show exposure; no predefined target required. cluster_targets here are SEEDS. The desk creates/modifies/retires any cluster and its target via `set-cluster` / `assign-cluster` (state.cluster_book, rationale mandatory). A cluster with no target is exposure-only and cannot breach.

### `stress_limit/rationale`

A -35% shock to the whole AI-capex sleeve must not cost more than 20% of the book (5pt inside the 25% risk budget). Advisory: reported every run with the AI-capex share that would satisfy it; it never forces a trade by itself.

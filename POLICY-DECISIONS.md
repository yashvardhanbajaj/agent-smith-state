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

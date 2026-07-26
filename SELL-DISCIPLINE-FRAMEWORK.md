# Sell Discipline Framework
**TIER 2.3: Now the primary risk control for a 100%-AI-capex book**

With factor diversification deliberately abandoned (2026-07-25 policy affirmed), the only remaining brakes are:
1. Single-position cap: 12% (SNDK breached 07-24)
2. Cash band: [3,15]% (breached at both ends: 0.06% on 07-20, 45.8% on 07-24)
3. Drawdown thresholds: -15% warn, -25% risk-off
4. Cluster bands: govern mix within the AI-capex chain

**Missing: no codified rule for discretionary de-risking.** Friday's (07-24) five exits and eight halvings have no recorded "why" — stop-loss, thesis change, or raising cash. The book's actual behavior cannot be evaluated or anticipated.

## Proposed Framework

### Phase 1: Pre-commit a drawdown ladder
Agree in advance when equity reductions happen:

| Drawdown | Equity trim | Duration | Rationale |
|---|---|---|---|
| -15% | None | Warn phase | Monitor only; trigger σ-alert in briefing |
| -18% | 10% of trims list | 1 month | De-risk batch 1 (lowest-conviction names) |
| -22% | 20% of trims list | 2 weeks | De-risk batch 2 (mid-conviction) |
| -25%+ | MOVE TO CASH | Immediate | Risk-off; freeze new deploys, draw cash |

**Example implementation**: at -18% drawdown, execute the top 2 items from strategist's de-risk list (e.g., trim MRVL + ASML per valuation, as of that review date).

### Phase 2: Formalize stop-loss rules
For single names at extreme valuations or deteriorating signals:

| Signal | Trigger | Action |
|---|---|---|
| BREAKDOWN + PEER LAGGARD | Both flags + price <50d MA | Trim 50% of position |
| Earnings miss >-15% | Same-day post-earnings | Trim 25% |
| Thesis broken (no news) | Signal reversal confirmed | Exit full position |

### Phase 3: Earnings-week de-risk
Automatic position-size reduction into binary events:

- GLW/TER/QCOM/LRCX within 5d: trim 25% or hold cash
- No new deployments 2d before earnings
- Resume normal rebalancing after event clears

### Phase 4: Quarterly rebalance checks
At each deep review (monthly), compare:
- Actual trims vs. proposed trims (hit rate)
- Trailing stops vs. breaches (why rules failed)
- Concentration drift (cluster bands vs. actual)
- Adjust ladder if needed based on realized volatility

## Execution

1. **User confirms ladder** in policy.json: drawdown_trim_ladder with batch percentages and trigger prices
2. **Strategist auto-applies** at each review: if drawdown >= trigger, recommend the pre-agreed batch
3. **Proposal system tracks outcomes**: "trim MRVL at -18% drawdown — executed at $192 vs $185 stop — worked/missed"
4. **Annual review**: assess hit rate, adjust ladder width

## Status

Proposed framework, not yet implemented. Requires:
- `policy.json` extension: add `drawdown_trim_ladder` schema
- Strategist logic: check drawdown on every run, auto-recommend batch if threshold crossed
- Proposal outcome tracker: record execution price vs. stop price, measure hit rate

# Strategist Output — 2026-07-15 (quick, 15:42 UTC)

Policy status: **unconfirmed** (draft; all drift framing remains provisional). No action blocked.

## Proposals — 5 sized actions

**1. Trim SNDK fully ~$1,790 (6.07% position)**
SNDK is unstable technical churn — 3rd buy/sell flip in 48 hours with no post-watermark fundamental catalyst. Thesis agent flags it WATCH (not conviction). The 5.01% recent bounce tracked SK Hynix Nasdaq debut (sector momentum), not re-conviction of the memory thesis. Eases AI Memory/Storage +6.82pt breach and AI-capex +5.33pt concentration breach simultaneously. Price at proposal: $295/share (approximate from thesis tail).

**2. Trim NBIS ~50% ~$620 (reduce 4.20% → ~2.10%)**
STRONG DOWNTREND signal: -7.8% intraday, -19.89% vs XLK peer. Data quality flag: no analyst consensus, new ETF proxy. De-concentrating this unclear position. Reduces AI-capex single-factor bet.

**3. Trim TSM ~15% ~$1,280 (reduce 8.49% → ~7.20%)**
TSM earnings **tomorrow** (largest single-name risk 8.49% of portfolio). Trim before earnings window to derisk concentration; holds core conviction. TSM is largest position within AI Semis/Fabs +9.27pt overweight cluster. Insider divergence (7/7 Chairman/CEO/8 SVPs bought vs prior MU EVP sell) argues for trimming the sector's overweight names selectively. Price at proposal: $134/share (from market_inputs.json estimate).

**4. Deploy COHR ~$1,200 (new position, +4.0% to AI Networking)**
Coherent Corp, optical interconnect for AI data centers. Watchlist setup, 19.8% upside per smith-watchlist. Rebalances AI Networking/Optics cluster from 13.77% (underweight -6.23pt) toward 20% target. Price at proposal: ~$300/share.

**5. Deploy APLD ~$800 (new position, +2.7% to AI Networking)**
Applied Optoelectronics, optical chips for AI/data-center interconnect. Watchlist top setup, 61.2% upside. Continues rebalance to AI Networking cluster. Price at proposal: ~$42/share.

Total: ~$3,690 trimmed (12.5% of book), ~$2,000 deployed (6.7%), net reduction ~$1,690. Cash moves from 14.1% → ~17.7%, which is above the 3–15% band upper bound. This is intentional given the earnings window (TSM tomorrow) and sentiment greed band (no defensive cash hoarding needed, but tactical dry powder for post-earnings volatility is prudent).

## Risk-off check

**Status: NORMAL**. Drawdown -5.655% vs policy warn/risk-off thresholds (8%/12%). No defensive rebalance required. No stop-level exercise. Proceed with proposals as sized.

## Signals & flags

- **TSM earnings in 24 hours**: Largest single-name risk (8.49%). Proposal #3 trims 15% to derisk window. Post-earnings, reassess full-scale AI Semis positioning if move is >5%.
- **SNDK instability**: 3 flips in 48h, no catalyst. Full trim (proposal #1) removes thesis-watch position regardless of recent sector tailwind. Re-enter only on conviction reversal, not momentum.
- **NBIS data quality**: New ETF proxy, no consensus. Trim (proposal #2) is risk-reduction, not a forecast. Monitor for delisting/structural changes.
- **AI-capex concentration 95.33% vs 90% cap**: Proposals are within-cluster rebalance (Semis/Memory → Networking), not diversification. Cluster concentration remains 95%+ post-proposals. Flag for next run if sentiment normalizes or drawdown approaches warn threshold (8%) — then consider out-of-cluster diversifiers (HO/KO/NEM style) like the 2026-07-13 run.

## Hit-rate readout

compute_journal shows 21 entries dated 2026-07-12 through 2026-07-14, all with verdict=open (0 days scored yet). Buckets: MOMENTUM+VOLUME (6), TARGET GAP (7), EARNINGS PROXIMITY (5), OVERSOLD BOUNCE (1), OVERBOUGHT PULLBACK (1). No hit rates available until ~2026-07-19 (7d outcomes). No de-emphasis recommendations this run.

## Proposal-outcome scorecard

Prior proposals from 2026-07-13 run (MU trim $550→$800, diversifier deploy KO/NEM/GLD $1,000 total) were opened same-day and remain open. Too fresh for 30d/90d scoring. Journal bootstrapped 2026-07-13; first scoreable outcomes ~2026-08-12. No accuracy baseline available this run.

---

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim SNDK full position ~$1,790","size_usd":1790,"price_at_proposal":295,"rationale":"Unstable technical churn (3rd flip in 48h, no catalyst); thesis WATCH not conviction; 5.01% bounce = SK Hynix sector momentum not re-conviction; eases AI Memory +6.82pt and AI-capex +5.33pt breaches"},
   {"action":"Trim NBIS ~50% ~$620","size_usd":620,"price_at_proposal":147,"rationale":"STRONG DOWNTREND signal (-7.8%, -19.89% vs XLK); data quality flag (new ETF proxy, no analyst consensus); de-concentrates AI-capex single-factor bet"},
   {"action":"Trim TSM ~15% ~$1,280","size_usd":1280,"price_at_proposal":134,"rationale":"Earnings tomorrow = largest single-name risk window (8.49% position). Trim to derisk before earnings. TSM is top position in AI Semis +9.27pt overweight cluster. Insider divergence (7/7 CEO/SVP buys vs MU EVP sell) argues selective trim of sector's overweights"},
   {"action":"Deploy COHR new position ~$1,200","size_usd":1200,"price_at_proposal":300,"rationale":"Coherent Corp, optical interconnect for AI/DC. Watchlist 19.8% upside. Rebalances AI Networking/Optics -6.23pt underweight toward 20% target"},
   {"action":"Deploy APLD new position ~$800","size_usd":800,"price_at_proposal":42,"rationale":"Applied Optoelectronics, optical chips for AI/DC. Watchlist top setup 61.2% upside. Continues AI Networking/Optics cluster rebalance from underweight"}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["compute_journal all entries open (0 scored); hit-rate baseline unavailable until ~2026-07-19","SNDK, NBIS data from signals/thesis tails only; no fresh yfinance quotes embedded; prices estimated from context","lots.json not provided; LTCG deferral checks skipped (quick mode)","AI-capex proposals are cluster rebalance only (Semis/Memory → Networking); cluster concentration remains 95%+, not diversified out; monitor for out-of-cluster diversifiers if sentiment softens or drawdown approaches 8%"]}
```

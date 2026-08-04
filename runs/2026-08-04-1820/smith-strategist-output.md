# Smith Strategist — 2026-08-04 (Quick, pre-open) — ALL FIGURES PROVISIONAL

**Run condition:** compute_book.json flagged persist_safe: false (G32, 4th occurrence — live pre-market row sum diverges 3.53% from INDmoney's lagging snapshot). state.json/ledger.csv will NOT be written this run. Separately, policy.json is still an unconfirmed draft. Every number, drift read, and proposal below is provisional on both counts — treat this as a same-day working read, not a persisted decision.

## 1. Drift vs. (draft, unconfirmed) policy

Two live breaches, both already computed in compute_drift.json — this is a "what to do" read, not a recomputation:

- **AI Memory/Storage: 20.513% vs 15% target [10,20] — over by +5.51pt (~$2,271 excess).** Ceiling breach.
- **Compute/Hyperscaler: 12.222% vs 20% target [15,25] — under by -7.78pt (~$3,204 shortfall).** The single largest drift on the book, and it's an under-band gap, not an overage.
- AI Semis/Fabs, Networking/Optics, Power/Cooling, Hyperscaler OEM: all within band. Note LRCX (currently "Unclassified," 1.539%) has been reclassified by smith-thesis into AI Semis/Fabs — next run folds it in, pushing Semis/Fabs to ~30.29%, still inside its [25,35] band.
- Cash 5.744% — back inside the normal [5,15] band (cash_regime_reason: stop-out 5 sessions ago, since renormalized). AI-capex 96.248% vs 100% cap — no breach, but concentration is structurally extreme (thesis agent: only QBTS + BABA = 2.2% of book is genuinely uncorrelated).

## 2. Sized proposals (provisional — none executed)

**1. Trim AI Memory/Storage cluster (MU + SNDK + DRAM) ~$1,800, staged in 2 tranches of ~$900 —** re-affirms P-049/P-048/P-036 at today's rallied prices rather than reissuing stale sizes into a different tape. Cluster is 5.51pt over its ceiling; MU/SNDK/DRAM/EWY all carry thesis WATCH flags; HBM3E ASP is down -51.4% from peak even as TrendForce's 2027 contract-price-surge forecast is an unpriced forward catalyst (smith-thesis reconciliation) — trim into strength, don't chase the full $2,271 excess in one clip given the tight-stop book style. Two tranches lets each fill size to roughly 2x the name's recent daily range for stop placement.

**2. Top up GOOGL (Compute/Hyperscaler) ~$1,200 — re-affirm P-045 unchanged.** This is the largest single drift on the book (-7.78pt). BofA's hyperscaler-capex-forecast raise to $1.2T/12mo (structural tailwind, names covering 30.62% of equity) directly supports this cluster. GOOGL is the lower-vol mega-cap fill preferred under the user's tight-stop style versus chasing a high-beta pure-play into the gap. Size held flat pending policy confirmation — do not scale up on an unconfirmed draft.

**3. Trim COHR ~$300–350 — re-affirm P-038 at current levels.** COHR is up ~24% cumulative with no identified idiosyncratic catalyst after 7 searches (explicit gap, not fabricated) — CIEN and GLW show the same unexplained-strength pattern. Fresh MOMENTUM+VOLUME journal flag today (price_at_flag $326.85). Thesis intact, so this is a partial profit-take into unexplained strength, not a thesis-break trim.

**4. Hold AMD tranche1 ($200, P-024) until after tonight's print — do not deploy pre-earnings.** AMD reports after close today; consensus $11.3B rev / $1.61 EPS / ~$6.5B DC rev, MI400 not material this quarter — genuinely ambiguous catalyst per smith-catalyst. Staging around the binary event, not through it, per the user's tranche discipline.

**5. LRCX (new re-entry, 2sh) — monitor only, no incremental sizing this run.** Thesis "strengthening," fresh TARGET GAP signal (first appearance), user-confirmed re-entry after the 2026-07-28 stop-out. Currently Unclassified pending next run's fold-in to AI Semis/Fabs (already within band there) — let the classification settle before sizing further.

No LTCG-boundary deferrals apply this run — lots.json coverage gap remains standing (cite via known_gaps if lot-level dates are needed).

## 3. Stale open-proposal re-examination

- **P-050 (Exit ORCL full stake, $520, rc3) — reconsider, do not restate a 4th time.** The premise has moved against the call: user has DCA'd into ORCL twice now (4→6sh today, confirmed deliberate diversification pattern), ORCL printed +9.22% today, and the ORCL:BREAKDOWN flag that anchored this proposal has resolved (no longer active). Recommend downgrading to "monitor" pending a fresh thesis check rather than reissuing the exit call unchanged.
- **P-046 (Rebuild cash buffer, $4,380) — superseded, recommend closing or resizing sharply smaller.** It was sized against a cash-regime concern that compute_drift.json now reports as normal (5.744%, back inside [5,15] band). The $4,380 figure no longer matches the current gap.
- **P-036 / P-048 / P-049 (Trim DRAM/SNDK/MU) — re-price, don't withdraw.** Breach is still live; only the entry price changed. Rolled into proposal #1 above at current levels.
- **P-051 (Light trim MRVL, $400, rc3) — hold, flag premise doubt.** Built partly on smith-quality's MRVL interest-coverage-collapse claim, which is contradicted by MRVL's own 10-Q (+8.4% YoY interest expense, not a quintupling — G44). MRVL also had a Flash Memory Summit product launch today (+14% intraday, immediate tailwind) that cuts against a trim call made on stale data. Recommend holding until G44 is re-verified.
- **P-033 (Initiate META, $450) — pause, don't initiate this run.** META flagged STRONG DOWNTREND today (new), even though the OVERSOLD BOUNCE / NEW HEADWINDS flags that might have supported an entry setup have resolved. Wait for signal clarity before putting new capital in.
- **P-037/P-040/P-041/P-042/P-043 (ASML/VRT/NVDA/AMD/NBIS light trims), P-025/P-027 (AMAT/GEV tranches), P-047 (hold fire) — no change, leave as staged.** None contradicted by today's data; low priority given persist_safe=false, don't add fresh sizing on top of them this run.

## 4. Risk-off status

**Normal.** Drawdown -8.205% vs peak $44,873.02, comfortably inside the policy's actual -25% risk-off threshold. No defensive lead-in warranted; standard tight-stop discipline continues as the structural risk control rather than a portfolio-wide de-risking trigger.

## 5. Hit-rate readout

**Not citable this run.** compute_journal's bucket_hit_rates and name_bucket_grades are empty — all 38 journal entries are still inside the 14–30 day scoring window (per smith-signals). No bucket de-emphasis recommendation can be made from this run's data; revisit once entries season past 14d.

## 6. Data quality / gaps carried forward

- G32: INDmoney per-position feed lag caused this run's persist_safe=false (4th occurrence) — nothing persisted.
- G41: attribution flow_usd undercounts the LRCX new-entry outlay.
- G42: smith-rebound gate divergence, not dispatched this run (gate STABILIZING).
- G44: MRVL interest-coverage claim unresolved — P-051 built on it, treat as unreliable until re-verified.
- New: smith_math.py's cmd_book trade_reason lookup is ticker-keyed, not date-scoped — misattributed stale trade reasons to today's BABA/LRCX qty_changes. Cosmetic this run (user rationale captured directly) but worth its own gap ID going forward.
- Policy draft unconfirmed — all drift/band reads above are provisional on user sign-off.

```json
{"policy_draft":null,"proposals":[{"action":"Trim Memory/Storage cluster (MU+SNDK+DRAM), 2 tranches","size_usd":1800,"price_at_proposal":null,"rationale":"Cluster 5.51pt over ceiling (20.513% vs 15% target/[10,20] band); MU/SNDK/DRAM/EWY on thesis WATCH; HBM3E ASP -51.4% off peak but 2027 contract-surge catalyst unpriced; staged for tight-stop discipline; re-prices stale P-036/P-048/P-049"},{"action":"Top up GOOGL (Compute/Hyperscaler)","size_usd":1200,"price_at_proposal":null,"rationale":"Largest single drift on book at -7.78pt; BofA hyperscaler capex raise to $1.2T/12mo structural tailwind; lower-vol mega-cap fill preferred under tight-stop style; re-affirms P-045 unchanged pending policy confirmation"},{"action":"Trim COHR","size_usd":325,"price_at_proposal":326.85,"rationale":"Up ~24% cumulative with no identified catalyst after 7 searches; fresh MOMENTUM+VOLUME flag; thesis intact so partial profit-take not thesis-break trim; re-affirms P-038"},{"action":"Hold AMD tranche1 until after tonight's print","size_usd":200,"price_at_proposal":null,"rationale":"AMD reports after close today; ambiguous catalyst per smith-catalyst; stage around the binary event per tranche discipline; do not deploy P-024 pre-print"},{"action":"Monitor LRCX (new re-entry), no incremental sizing","size_usd":0,"price_at_proposal":null,"rationale":"Thesis strengthening, fresh TARGET GAP flag, user-confirmed re-entry after 2026-07-28 stop-out; currently Unclassified pending fold into AI Semis/Fabs which is within band"}],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["persist_safe:false — G32 4th occurrence, nothing written to state.json/ledger.csv this run","policy.json confirmed:false — all drift reads provisional","G41 flow_usd undercount on LRCX new entry","G44 MRVL interest-coverage claim unresolved, P-051 premise doubtful","new gap: smith_math.py cmd_book trade_reason lookup is ticker-keyed not date-scoped (cosmetic this run)","hit-rate readout empty — 38 journal entries still inside 14-30d scoring window","proposal outcome scorecard not run (quick mode, not deep/monthly trigger)"]}
```

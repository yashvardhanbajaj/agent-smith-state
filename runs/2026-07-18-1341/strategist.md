# Agent Smith — Portfolio Strategist — DEEP Weekly Review
2026-07-18 (Saturday review of Friday 2026-07-17 close) | Gate: ESCALATING | Book ~$44,850, 29 holdings, wallet $23

## Policy status
policy.json remains confirmed:false, as_of 2026-07-12. All drift analysis below is **provisional — draft policy**.

### Recommended revision (edit, not re-bootstrap)
1. **Add missing cluster line**: "Compute/Hyperscaler" (ORCL/IREN/GOOG/META, currently 7.945% of book) has no target/band even though it's already listed in `ai_capex_clusters`. Bootstrap convention (current weight rounded to nearest 5%, ±5% band) gives: target 10%, band [5,15]. Add this line at minimum.
2. **Flag, don't force**: the whole draft is now badly stale — book grew 28→29 holdings and composition has shifted enormously (CQQQ fully exited, GEV to dust, SNDK/DRAM/GLW grown, GOOG/META/AMD/ORCL added) since 07-12. A full re-look (not just the one missing line) is warranted, but that re-look is the user's call, not mine to force this run.
3. The bootstrap's own note flagged max_ai_capex_factor_pct=90% as 30pts above the stated 60% sane-diversification threshold — worth revisiting given actual is now 99.278%, i.e. even the generous 90% ceiling is blown through by 9.3pts.

## Proposals (today's date 2026-07-18, prices are last confirmed anchors — flagged stale where >1 trading day old; no fresh quotes pulled this run per tool-call budget)

**1. Trim SNDK ~$1,500** (anchor price $1,842.10, 07-15 — 3 days stale, flag) — cures the single-position cap breach (12.352% vs 12% cap, its largest-ever weight) and is a **sizing/concentration call, not a thesis call**: thesis flipped SNDK to STRENGTHENING on real news (Meta flash-storage deal, 07-17) and explicitly said any trim should be framed as risk management, not a downgrade. Two independent inputs support trimming anyway: (a) signals' SEVERE peer-laggard read (-38% vs SMH, worse than any other name in the book) despite the good news, and (b) this is SNDK's third quantity flip in 48h per the standing open_flag — a name this unstable shouldn't also be the book's largest position. LTCG: lots.json empty (known_gaps G1) — cannot confirm boundary proximity, trim proceeds without an LTCG-deferral check.
   → Proceeds routed: **~$600 to VRT** (below) + **~$900 to cash rebuild** (raises wallet from $23 to ~$923, still under the 3% floor but a real start — full cure would require a much larger single trim than is prudent in one move).

**2. Trim CIEN ~$500** (anchor price not resourced this run) — funds proposal 4. CONFIRMED fresh insider activity: CEO + 3 execs cluster-sold 7/15, filed 7/17, immediately before Friday's selloff (signals, new this run). CIEN thesis is WATCH. A confirmed pre-selloff insider cluster sale outranks the fact that AI Networking/Optics is currently in-band (20.98% vs 20% target) — this is a name-specific red flag, not a drift-driven trim.

**3. Endorse VRT stage-in ~$600** (rebound's pick, anchor price $310, 2-4 days stale) — funded by proposal 1. Cures the single most severe cluster breach on the table: AI Power/Cooling/DC Infra collapsed to 3.581% vs 15% target (-11.4pt), and VRT is literally the only viable vehicle since GEV is dust. Rebound flagged this as low-confidence (no clean in-book peer to benchmark against) — sized small and funded, not chased with new money.

**4. Endorse META stage-in ~$500** (anchor price $672.54, checked 07-16) — funded by proposal 2. Best of rebound's five picks by peer-relative strength (+20.2% RS, the book's strongest name) and thesis STRENGTHENING; deepest dip Friday (-2.79%) reads as a genuine buyable pullback, not distress.

**5. Defer/override TSM, GLW, AVGO stage-ins** (rebound's remaining $300+$350+$250) — no funding path after 1-4, and independently de-prioritized: TSM's home listing crashed -7.29% Friday (largest ADR-lead move ever tracked) with high Monday gap-down risk flagged by scout — don't chase a name still gapping; AI Semis/Fabs is also near its band ceiling (32.056% vs 30%, capped headroom). GLW and AVGO are lower-conviction/lower-urgency than the Power-cluster and META fixes funded above.

**Reconciling rebound's $2,000 ask vs $23 cash**: only 2 of the 5 picks (VRT, META = $1,100) are funded this run, via the two trims above — not from the near-zero wallet. TSM/GLW/AVGO stay on the shelf pending either a further trim or a genuine cash rebuild.

**GOOG — no trade proposed, flagged as an open question for you**: same-day exit (07-17) then re-entry (07-18), and neither the thesis, signals, nor rebound agents can agree on why — rebound's SL-forensics reads it as deliberate rotation (outperformed peers +0.27% vs -6.25%), thesis found a real Gemini 3.5 Pro delay catalyst as a competing explanation, and it now carries a fresh TARGET GAP (+19.1% upside) that would normally argue for adding. Given the agents are genuinely split and rebound keeps it in STAY-OUT (WATCH_THESIS), I'm not proposing anything on GOOG — but the flip-flop itself is worth you looking at directly.

## Risk-off status
`risk_off_status` = **normal** (drawdown 0%, fresh peak). Do not read that as "no problems" — this "normal" reading coexists with the most extreme concentration/cash picture this book has ever produced (AI-capex 99.278% vs 90% cap, cash 0.052% vs [3,15]% band, a single-position cap breach on the largest holding). Drawdown-based risk-off is a lagging, backward-looking gate; it has not yet caught up to Friday's Asia-specific stress or the book's structural concentration. Treat the ESCALATING gate classification, not the "normal" drawdown label, as the operative signal this run.

## Stress table (approximate — deep mode)
- **AI-capex pause**: 99.278% of book × assumed -20% cluster move ≈ **-19.9% / -$8,925**. Macro's `cluster_impact.ai_capex_chain` ("pressured acutely, primary transmission channel") argues against tempering this down. Most exposed: SNDK, DRAM, TSM, NVDA. Note: Friday's Asia-specific selloff (TSM -7.29%, KOSPI -6.37%) is already a **live partial instance** of this scenario, not a hypothetical — but it's narrower than a full pause (Euro Stoxx -0.84%, US futures ES -1.06%/NQ -1.55% were comparatively mild, per scout).
- **Rates +100bp**: high-beta long-duration names (NVDA 2.211, MU 2.142, MRVL 2.197, VRT 2.029, LRCX 1.805; combined ~17% of book) × assumed -10% ≈ **-1.7% / -$760**. Macro's 10-yr level wasn't supplied this run — falling back to the static assumption per the flag rule — but anchored qualitatively to the HAWKISH stance (dots raised to 3.8%, no cuts priced, next FOMC 7/29), which argues this scenario's probability is higher than a generic +100bp case.
- **Tariff/export-control escalation**: China-revenue-exposed names — ASML (signals: fresh POLICY IMPACT export-control flag), QCOM, AVGO, MU (~14% combined weight) × assumed -15% ≈ **-2.1% / -$940**. Most exposed: ASML.
- **USD/INR ±3%**: ~0% effect on the USD-reported book (policy). In INR net-worth terms: a 3% rupee depreciation adds ~3% to this book's INR value; a 3% appreciation subtracts ~3% — this is a currency-translation effect on your net worth, not a portfolio P&L event.

## Hit-rate readout
Still only 3/36 journal entries scored — **no bucket has ≥3 scored entries yet**. No bucket-level hit rate is computable this run; nothing to de-emphasize on evidence yet.

## Proposal-outcomes scorecard
Oldest open proposal in proposals.json dates to 2026-07-13 (5 days ago) — proposals.json's own scorecard note says first outcomes aren't scoreable until ~2026-08-12 (30d mark). **No proposals have reached 30d yet; scorecard remains null this run.**

## Stale-proposal pass (23 open proposals reviewed)
Recommend the orchestrator bulk-close the following as **overtaken by events**, distinct from proposals already correctly marked executed/superseded: Deploy NEM (07-13, cash situation has fully reversed), Deploy GLD tranche 3 (same), the three 07-13T19:23 hold/watch notes (situational, book unrecognizable since), Trim TSM fund-Semis-breach (07-14, cluster no longer breached, price stale), Hold-no-further-SNDK/EWY (07-14, superseded by this run's SNDK analysis), Hold-DLR-deferred (07-14, generic), Trim TER and Trim QCOM (07-14T22:10, AI Semis/Fabs is no longer breached — 32.056% vs 30% target, breach:false this run), Trim MRVL $250 and $150 (07-14/07-16, same cluster reasoning stale), **Deploy CIEN $700 (07-14, directly reversed — new insider-selling evidence flips this to a trim candidate, see proposal 2 above)**, Deploy CQQQ (07-14, position fully exited 07-17, moot), Trim SNDK-to-dust $1,790 (07-15, superseded by this run's more nuanced sizing-not-thesis SNDK trim), Trim TSM 15% (07-15, price and rationale both stale post-earnings/post-crash), Deploy COHR (07-15) and Deploy APLD (07-15, both explicitly called out as never-acted-on and cash-incompatible now), Defer CQQQ stage-in (07-16, moot, position exited), the three 07-16 hold notes (situational), Defer rebound GOOG/CLS/GLW/COHR (07-17, replaced by this run's fresh rebound list).
Recommend keeping **open**: Defensive stance on ORCL ~$125 (07-17 — still live, and signals added a fresh NEW HEADWINDS debt/FCF flag this run, reinforcing it), Defer GLW stage-in (07-16 — still consistent, cash still near-zero), Hold NOW no re-add (07-17 — no new information this run). Mark **Trim STM $400 (07-17) as fulfilled** — rebound confirmed a 5-share STM trim today closely matches this proposal's size and rationale; reads as the user executing your own prior call, not an independent stop-loss.

## Data-quality notes
- SNDK, VRT, TSM, GLW, AVGO price_at_proposal are last-known anchors (1-4 trading days stale) — no fresh quotes pulled this run against the ~8-tool-call budget; confirm live prices before acting on any of these.
- GOOG earnings date conflict: macro says 2026-07-22 (confident), watchlist says ~2026-07-30 (unconfirmed cadence estimate). Not resolved here — flagging both for you.
- lots.json empty (known_gaps G1) — no LTCG-boundary check possible on the SNDK trim.
- Stress table is aggregate/approximate (known_gaps G2 — no per-name $ breakdown fed to strategist).

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim SNDK to cure single-position cap breach (12.352% vs 12% cap), fund VRT stage-in + cash rebuild","size_usd":1500,"price_at_proposal":1842.10,"rationale":"Position-cap breach + severe peer-laggard (-38% vs SMH) + third 48h qty-flip; thesis explicit this is sizing/risk not thesis (SNDK flipped to STRENGTHENING on Meta flash-storage news 07-17); lots.json empty (G1), no LTCG check possible"},
   {"action":"Trim CIEN to fund META stage-in","size_usd":500,"price_at_proposal":null,"rationale":"CONFIRMED insider cluster sale (CEO+3 execs, dated 7/15, filed 7/17, right before Friday's selloff) reverses the prior Deploy-CIEN proposal; thesis WATCH outranks pure drift"},
   {"action":"Stage into VRT (funded by SNDK trim)","size_usd":600,"price_at_proposal":310.0,"rationale":"AI Power/Cooling/DC Infra cluster collapsed to 3.581% vs 15% target (-11.4pt, worst cluster breach on the book); VRT is the only viable vehicle (GEV is dust); rebound flags low confidence, sized small"},
   {"action":"Stage into META (funded by CIEN trim)","size_usd":500,"price_at_proposal":672.54,"rationale":"Best rebound pick by peer-relative strength (+20.2% RS, book's strongest name) and thesis STRENGTHENING; Friday's -2.79% dip reads as buyable pullback not distress"},
   {"action":"Defer TSM/GLW/AVGO stage-ins (rebound's remaining $900) -- no funding path, and TSM specifically de-prioritized on Monday gap-down risk","size_usd":0,"price_at_proposal":null,"rationale":"Cash near-zero after funding VRT/META; TSM's Taiwan listing crashed -7.29% Friday with flagged high gap risk; AI Semis/Fabs cluster near its 35% band ceiling"}
 ],
 "proposal_outcomes":[],
 "scorecard":{"trim_accuracy_30d":null,"add_accuracy_30d":null,"overall_accuracy_30d":null},
 "deemphasize_buckets":[],
 "data_quality":["3/36 journal entries scored, no bucket reaches the >=3 threshold for a hit rate this run","SNDK/VRT/TSM/GLW/AVGO price_at_proposal are 1-4 day stale anchors, not fresh quotes","GOOG earnings date conflict unresolved: macro 7/22 (confident) vs watchlist ~7/30 (unconfirmed)","lots.json empty (G1) -- no LTCG-boundary check on SNDK trim","stress table approximate, no per-name $ breakdown available (G2)","policy.json stale as_of 2026-07-12, missing Compute/Hyperscaler cluster target -- revision recommended, not forced"]}
```

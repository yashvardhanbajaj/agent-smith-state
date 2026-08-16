# Agent Smith — Portfolio Strategist (Deep Review, Stage 2)
Run: 2026-08-16-1807 | Data as of: Friday 2026-08-14 close (market closed since; byte-identical to 2026-08-15 deep run) | Policy: confirmed, no bootstrap needed

## 0. What this run actually is
No session occurred between the 08-15 deep review and today — zero trades, zero price movement, the book's structure is unchanged. The 10 proposals opened on 08-15 are still live and are **not restated below**. This run's job was to (a) judge whether those 10 still hold given the two genuinely new inputs — the CXMT DRAM structural finding and NVDA's earnings clock moving one day closer — and (b) surface what changed. Four new proposals came out of that; everything else is a status check.

---

## 1. STATUS OF THE 10 OPEN PROPOSALS (not re-proposed — reviewed only)

| ID | Action | Size | Still valid? | What changed this run |
|---|---|---|---|---|
| P-082 | Trim MSFT | $370 | Yes, unchanged | No new MSFT-specific input. RSI/overbought math is date-independent since prices haven't moved. |
| P-087 | Trim NVDA | $550 | Yes — **see NVDA note below** | Thesis strengthening (financing guarantee narrowed $250bn→~$100bn) *and* earnings clock now 10 trading days out (2026-08-26, confirmed). Two live, live-updating inputs — both point the same direction on urgency, opposite directions on size. |
| P-088 | Trim SKHY | $900 | Yes, reinforced | Thesis agent this run explicitly reframes MU/DRAM/SKHY's WATCH as **competitive/structural** (CXMT), not a pricing verdict. Doesn't change the trim math, but removes a possible objection ("maybe pricing recovered") — it hadn't; the risk was mischaracterized before, not resolved. |
| P-089 | Trim MU | $500 | Yes, reinforced | Same CXMT reframing. Partial-cure sizing (not full) still correct — Samsung/SK Hynix pricing tailwinds cited in the proposal are a separate, real, positive fact from the CXMT capacity threat; they don't cancel each other. |
| P-090 | Trim NBIS (rotation funding leg) | $700 | Yes, unchanged | No new NBIS input this run. |
| P-091 | Trim DRAM | $450 | Yes, reinforced | Same CXMT reframing as SKHY/MU — see below. |
| P-093 | Add CEG (paired to NBIS trim) | $300 | Yes, unchanged | Ex-div 2026-08-18 is now 2 days out (was 3 on 08-15) — not a reason to act faster or slower, just a clock note. |
| P-094 | Hard stop on ORCL @ $139.14 | $0 | Yes, unchanged | — |
| P-095 | Hold AMD, no adds | $0 | Yes, unchanged | — |
| P-096 | Hold COHR at 3sh | $0 | Yes, unchanged | — |

**The CXMT finding, applied.** Catalyst's fresh read is that CXMT is projected to close the DRAM wafer-capacity gap with Micron to ~25k WSPM by end-2026 (vs 375k), with share moving from 3% to 8% YoY — a genuine new structural threat to the 15.53%-weight Memory/Storage cluster. Thesis explicitly flags this as **not** a pricing signal (HBM3E flat at $9.00/GB; the earlier "+14.29%" HBM4 read was a basis-splice artifact, now corrected) and notes the cluster's three memory names (SKHY/MU/DRAM/SNDK) share one common structural threat — correlated same-day drawdown risk if a CXMT headline lands badly. That correlation point is new information this run, not present in the 08-15 read. It doesn't change any individual trim's sizing (still risk-cap-anchored, still partial-cure), but it does argue for **sequencing**: work the Memory/Storage bloc (P-088 SKHY → P-091 DRAM → P-089 MU) as a set rather than piecemeal, since a single adverse CXMT headline would hit all three simultaneously. Counter-scale, for balance: wafer starts are not bit-equivalent output, and CXMT's node density/yield still trail Micron's — this is a multi-year threat, not an imminent one.

**NVDA, specifically — sizing either way.** Two things moved since 08-15, in opposite directions on size (not on urgency):
- *Toward smaller:* the financing-guarantee narrowing ($250bn→~$100bn, unsigned) is a genuine de-risking of NVDA's own thesis — it strengthens, not weakens, the case for holding size on the name itself.
- *Toward urgency:* earnings is now a confirmed, 10-trading-day certainty on the book's largest position (7.72%) held against $12.25 of cash — effectively zero cushion if the print disappoints.
Net: the existing $550 trim is sized as a pure cap-cure (cap_multiple 1.198x, $559 headroom, computed) — not a directional bet against the name. That sizing logic still holds and shouldn't be scaled up just because earnings is closer (that would fight a strengthening thesis with no new bearish fact behind it), but it also shouldn't be deferred further — the case for actioning it *before* 08-26 rather than waiting is stronger today than it was two days ago, purely because the window to do so with a calm tape is now shorter. Recommendation: action P-087 at its existing size, sooner rather than later; do not upsize it on earnings-proximity alone.

**On the fact that six trims are open and unactioned:** the aggregate open-risk math makes this concrete. NVDA + MU + SKHY + NBIS + DRAM + MSFT alone account for roughly a third of the book's total ATR-weighted open risk (risk_share_pct: NVDA 4.16, MU 7.23, SKHY 7.22, NBIS 6.78, DRAM 5.27, MSFT 1.47 — sum ≈32%). Actioning all six at their proposed (already-computed, already cap-anchored) sizes would materially close the gap between 14.404% aggregate open risk and the 10% cap, without requiring any new analysis — the sizing work is already done and sitting in the queue. The candid read: repeat-count tracking shows NVDA's trim alone has been reaffirmed 4 times since 07-31. Restating it a 5th time doesn't change anything the user hasn't already seen; the lever that matters here is action, not another proposal.

---

## 2. NEW PROPOSALS (2026-08-16) — genuinely new this run

### 1. TRIM BX ~$185
**Live overbought_distribution trigger** (not seen in any prior open proposal). RSI14 71.1, up +16.5% on the month, comfortably *inside* its ATR cap (0.237x — well under 1.0x). Per the trigger design, this is deliberately independent of the risk cap: booking profit on a name that ran is the point, not a consolation prize for a cap breach. Cluster (Alternative Asset Mgr) carries no policy target/band, so no G56 tension. Fresh gain to protect, no thesis change (WATCH, unverified this run).
- price_at_proposal: $149.33 | trigger_type: overbought_distribution
- evidence_quality: {"verified": 0, "computed": 2, "unverified": 1}

### 2. BUY QCOM ~$185 (rotation pair, funded by BX trim above)
**laggard_rotation, shadow — surfaced because it independently pairs with the live BX sell leg above**, not standing alone. QCOM sits bottom-quartile on 1m relative strength (-6.7pp vs SMH — hasn't run yet), thesis strengthening (carryover, not fresh this run), within its own ATR cap (0.811x), headroom $384.78. Sized to the smaller of the BX proceeds (~$186.66) and QCOM's own headroom — the BX leg binds. Checked against compute_rotation.json: neither leg sits in the `accumulate` bucket with a strengthening thesis, so no contradiction to flag. This is exactly the "book profit on what ran, deploy into what hasn't" trade the user has asked this desk to prioritize — both legs computed, not hand-picked.
- price_at_proposal: $164.80 | trigger_type: laggard_rotation (**shadow trigger, not yet hit-rate validated — scores zero in the compute layer regardless of this rationale**) | trigger_bucket: laggard_rotation | pair_id: PAIR-2026-08-16-BX-QCOM | pair_role: buy_leg
- evidence_quality: {"verified": 0, "computed": 2, "unverified": 1}

*(BX leg above carries pair_id: PAIR-2026-08-16-BX-QCOM, pair_role: sell_leg)*

### 3. TRIM SNDK ~$280
SNDK currently has **no open proposal** despite being the largest percentage gainer in the book (+35.6% vs. a $1,210.25 basis) and sitting mildly over its own ATR cap (1.189x, $132.85 excess, computed). Two shadow triggers coincide with that computed breach: profit_ratchet (its $1,129.14 stop sits below breakeven — a retracement would turn a 35.6% winner into a realized loss) and scale_out_ladder (the +25% gain rung has been reached; the ladder's own suggested first-tranche size is $277.98, which comfortably clears the $132.85 cap excess too). Thesis stays WATCH (carryover, not fresh this run) and SNDK is the weakest 1m relative-strength name in the Memory cluster (-14.28pp) — a laggard that already had its run, which is the opposite of a name to be adding to. Sized to the scale-out ladder's own tranche rather than the smaller cap-cure figure, since the profit-taking case is the stronger of the two.
- price_at_proposal: $1,641.20 | trigger_type: null (justification is the computed cap breach; scale_out_ladder/profit_ratchet inform sizing only, per rule, and are **shadow — not yet hit-rate validated**)
- evidence_quality: {"verified": 0, "computed": 3, "unverified": 1}

### 4. STOP_RAISE MRVL to $188.30 (no capital moved)
MRVL sits 1.404x its ATR cap ($447.24 excess, computed) with a strengthening thesis (carryover) — not a trim candidate on that basis alone. But its current stop ($178.16) sits *below* its $188.30 cost basis while the position is up 17.9% — a pullback would convert a real gain into a realized loss for no reason. profit_ratchet (shadow) flags this and coincides with the computed cap breach, so per the shadow-surfacing rule it's fair to bring forward. This only raises the stop (protects $71.02 of gain-at-risk); it does not reduce the position or fight the strengthening thesis, consistent with standing instruction to ratchet stops up, never tighten them down.
- price_at_proposal: $222.03 | size_usd: 0 | trigger_type: null (shadow-informed, not shadow-justified — computed cap breach is the anchor)
- evidence_quality: {"verified": 0, "computed": 2, "unverified": 1}

**No 5th proposal.** GEV (1.31x cap, $502.83 excess), TSM (1.05x, $116.94 excess) and TER (1.03x, $33.51 excess) also sit over their caps with no open trim proposal. TSM and TER's excess is trivial (both compound to under 3.5% over cap on strengthening theses) and not worth a proposal on their own; GEV is moderate but carries a strengthening thesis and no live/shadow trigger coincidence this run. Flagged in data_quality for next review rather than forced into a proposal here.

---

## 3. RISK-OFF STATUS
`risk_off_status: normal` (drawdown -2.507% vs. warn 8% / risk-off 12% — well inside normal). No defensive lead required by the drawdown gate. Sentiment (82.9, EXTREME_GREED) independently drives the profit-booking lead above — that's a valuation-regime call, not a drawdown-driven one, and the two shouldn't be conflated.

---

## 4. STRESS TABLE (deep mode — approximate, labeled as such)

| Scenario | Est. portfolio impact | Basis | Most exposed |
|---|---|---|---|
| AI-capex pause | **-17.8% of equity (~-$7,782)** | 88.99% AI-capex factor exposure × assumed -20% cluster move. Macro's cluster_impact read (NDX RSI14 73.1, EXTREME_GREED) frames the AI-capex chain as "first to feel any mean-reversion" — this supports, not tempers, the -20% assumption; if anything it argues front-loaded risk. | NVDA (7.72%), TSM (5.85%), MU (5.55%) |
| Rates +100bp | **-1.7% of equity (~-$749)** | Compute/Hyperscaler OEM (6.99%) + AI Power/Cooling/DC Infra (10.13%) = 17.12% of equity × assumed -10%. Anchored to macro's live 10-yr (4.696%, +11.1bp in the last month) against a hawkish Fed (3.63%) — already pressured, next FOMC (09-16) outside the 5-day window so no immediate trigger. | NBIS, GEV, VRT, CEG, CLS |
| Tariff/export-control escalation | **-0.5% of equity (~-$232)**, plus a small standalone BABA tail (~$35-48) | China-revenue-exposed ASML/LRCX/AMAT/TER = 10.55% (catalyst-sourced) × assumed -5% (mild — China's first domestic immersion DUV deliveries this August are 5 units vs. ASML's 131-tool base and 98.7% share; EUV, the part that actually matters, is untouched). BABA (China Internet, 0.56%) carries direct policy tail risk separately. | ASML, LRCX, AMAT, TER; BABA (separately) |
| USD/INR ±3% | **~0% on the USD book itself** | Book is 100% USD-reported; a currency move doesn't touch USD P&L. In INR (net-worth) terms: a 3% INR depreciation vs. USD lifts the INR-equivalent value of the ~$43,748 book by roughly the same 3%; a 3% INR appreciation cuts it by a comparable amount. Pure translation effect, not a portfolio risk. | Whole book (translation only) |

---

## 5. HIT-RATE READOUT
Signals reported exactly one in-window item book-wide this run (TSM, 08-15) — no bucket accumulated ≥3 scored entries this run. Per the <3-entries rule, the bucket-level hit-rate readout is skipped this run; this is a data-availability gap (prices unchanged, no new signal window opened), not a statement about live bucket performance.

---

## 6. PROPOSAL OUTCOMES SCORECARD (n=7 scored at 30d — small sample, not a verdict)

| Proposal | Price at proposal | Now (30d) | Verdict |
|---|---|---|---|
| P-001 Top up TSM | $428.95 | -0.6% | neutral |
| P-002 Restore LRCX | $333.38 | +0.31% | neutral |
| P-003 Re-enter CRDO | $243.12 | -4.9% | missed |
| P-004 Re-enter VRT (small) | $312.14 | -3.86% | missed |
| P-005 Re-enter VRT (funded by TSM trim) | $305.87 | -3.93% | missed |
| P-006 Deploy COHR | $387.36 | -15.88% | missed |
| P-007 Defer GLW stage-in | $162.00 | +2.46% | worked |

**Aggregate: 1/7 worked, 4/7 missed, 2/7 neutral — 14.3% overall accuracy, avg outcome -3.77%.** By bucket: BUY 25% (n=4: TSM, both VRT calls, COHR, GLW — 1 of 4 worked... note COHR/VRT/TSM are 4 BUY-bucket entries, GLW the 5th shows as BUY too making n=4 with 1 worked = GLW); HOLD 0% (n=2: CRDO, VRT-small — both direction_bucket HOLD); TRIM n=1 neutral (LRCX). **n is too small in every bucket (max 4) to draw a de-emphasis conclusion** — the rule requires ≥5 entries over time before recommending the orchestrator downweight a bucket. Flagging COHR (-15.88%, the single worst miss and the largest dollar size in this cohort) and both VRT calls as worth another look next monthly cycle once more entries land, but not actioning on n=7 alone.

---

```json
{"policy_draft":null,"proposals":[{"action":"Trim BX (overbought, protect real gain)","ticker":"BX","size_usd":185,"price_at_proposal":149.33,"rationale":"RSI14 71.1 (>70), up +16.5% on the month -- real gain to protect. Deliberately independent of the ATR cap per trigger design (BX sits at 0.237x, comfortably inside) -- this is a preferred trim precisely because it is cap-independent, not despite it. No cluster band/target exists for Alternative Asset Mgr, so no G56 tension. Sentiment EXTREME_GREED (82.9) supports booking now.","trigger_type":"overbought_distribution","trigger_bucket":null,"pair_id":"PAIR-2026-08-16-BX-QCOM","pair_role":"sell_leg","evidence_quality":{"verified":0,"computed":2,"unverified":1}},
{"action":"Buy QCOM (rotation destination, funded by BX trim)","ticker":"QCOM","size_usd":185,"price_at_proposal":164.80,"rationale":"laggard_rotation shadow trigger, surfaced because it pairs with the live BX sell leg above -- bottom-quartile 1m relative strength (-6.7pp vs SMH, has not run yet), thesis strengthening (carryover), within its own ATR cap (0.811x, $384.78 headroom). Sized to the smaller of BX proceeds and QCOM headroom -- BX proceeds bind. Checked against compute_rotation.json: not in the accumulate bucket, no contradiction.","trigger_type":"laggard_rotation","trigger_bucket":"laggard_rotation","pair_id":"PAIR-2026-08-16-BX-QCOM","pair_role":"buy_leg","evidence_quality":{"verified":0,"computed":2,"unverified":1}},
{"action":"Trim SNDK (largest gainer, no open proposal, mild cap breach + scale-out rung reached)","ticker":"SNDK","size_usd":280,"price_at_proposal":1641.20,"rationale":"Up +35.6% vs a $1,210.25 basis -- largest percentage gainer in the book, no open trim proposal exists for it despite that. Computed ATR cap breach (1.189x, $132.85 excess) anchors the proposal; scale_out_ladder (shadow, tier-1 +25% rung reached, $277.98 suggested) and profit_ratchet (shadow, stop below breakeven) inform the larger size but do not themselves justify it. Weakest 1m relative strength in the Memory cluster (-14.28pp) -- a laggard that already had its run, the opposite of an add candidate. Thesis WATCH (carryover) reframed this run as competitive/structural (CXMT), not a pricing verdict.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":3,"unverified":1}},
{"action":"Raise MRVL stop to cost basis (no capital moved)","ticker":"MRVL","size_usd":0,"price_at_proposal":222.03,"rationale":"Computed ATR cap breach (1.404x, $447.24 excess) anchors this; profit_ratchet (shadow) flags the current stop ($178.16) sits below the $188.30 cost basis while up 17.9% -- a pullback would convert a real gain into a realized loss. Raises the stop only, does not trim or fight the strengthening thesis (carryover) -- consistent with standing instruction to ratchet stops up, never tighten down.","trigger_type":null,"trigger_bucket":null,"pair_id":null,"pair_role":null,"evidence_quality":{"verified":0,"computed":2,"unverified":1}}],
 "proposal_outcomes":[{"action":"Top up TSM","price_at_proposal":428.945,"date_30d":{"price":426.4,"pct":-0.6,"verdict":"neutral"},"date_90d":{}},
{"action":"Restore LRCX to pre-trim 5 sh","price_at_proposal":333.38,"date_30d":{"price":334.42,"pct":0.31,"verdict":"neutral"},"date_90d":{}},
{"action":"Re-enter CRDO","price_at_proposal":243.12,"date_30d":{"price":231.2,"pct":-4.9,"verdict":"missed"},"date_90d":{}},
{"action":"Re-enter VRT (small)","price_at_proposal":312.14,"date_30d":{"price":300.09,"pct":-3.86,"verdict":"missed"},"date_90d":{}},
{"action":"Re-enter VRT (funded by TSM trim)","price_at_proposal":305.87,"date_30d":{"price":293.85,"pct":-3.93,"verdict":"missed"},"date_90d":{}},
{"action":"Deploy COHR (new position, optical interconnect)","price_at_proposal":387.36,"date_30d":{"price":325.83,"pct":-15.88,"verdict":"missed"},"date_90d":{}},
{"action":"Defer GLW stage-in (rebound candidate)","price_at_proposal":162.0,"date_30d":{"price":166.0,"pct":2.46,"verdict":"worked"},"date_90d":{}}],
 "scorecard":{"trim_accuracy_30d":0.0,"add_accuracy_30d":25.0,"overall_accuracy_30d":14.3},
 "deemphasize_buckets":[],
 "data_quality":["Every scored bucket this run has n<5 (BUY n=4, HOLD n=2, TRIM n=1) -- below the threshold for a de-emphasis recommendation; HOLD at 0% (n=2) and TRIM at neutral (n=1) are worth re-checking once more entries score, not acting on yet.","GEV (1.31x cap, $502.83 excess), TSM (1.05x, $116.94 excess) and TER (1.03x, $33.51 excess) remain over their ATR risk caps with no open trim proposal -- TSM/TER excess is trivial and both carry strengthening theses; GEV is moderate and unflagged by any live/shadow trigger this run. Carried forward for next review, not forced into a proposal here.","Signals reported only one in-window item book-wide this run (TSM, 08-15) -- no bucket reached the 3-entry minimum for a hit-rate line; this is a data-availability gap from the market being closed, not a bucket-performance statement.","rel_strength_1m missing for SKHY, IREN, VRT, BE, GLW in the de-risk stretch scoring (carried from compute_derisk.json) -- stretch scored null, never estimated, not ingested as a number."]}
```

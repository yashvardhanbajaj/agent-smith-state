# Smith Strategist — 2026-09-16 pre-open (quick), FOMC decision day

## 0. Policy
No bootstrap needed — policy already confirmed from prior runs.

## 1. The catalyst_threat / trend_breakdown / conviction_exit batch: reviewed and rejected in full

`proposal_specs.json` drafted 23 `catalyst_threat` TRIMs, 4 `trend_breakdown` TRIMs, and 2
`conviction_exit` SELLs (29 new draft specs total) off a factor-catalyst cache that was **not
refreshed this run** — smith-catalyst wasn't dispatched (gate read STABILIZING, no
ESCALATING/SMH/Asia/cluster trigger crossed threshold). 27 of these 29 cite, as their sole or
primary evidence, either the Amodei "pace the frontier" essay (2026-09-12, horizon=immediate,
expires 2026-09-17) or the CXMT HBM3E risk-production item (2026-09-01, weakly linked to
non-memory names like ASML/AMAT), or the pre-FOMC hike-odds item — all three now stale relative
to what the two agents actually dispatched this run found:

- **smith-signals** (fresh): Asia +0.7-1.4%, VIX -1.3% to 16.98, ES/NQ +1.1/+1.4% overnight; AMD's
  signal flipped to STRONG UPTREND and AVGO's to OVERSOLD BOUNCE this run — direct technical
  evidence the Monday move is reversing, not persisting.
- **smith-thesis** (fresh): reviewed all 9 names whose signals dropped a downtrend/momentum/
  peer-laggard flag overnight (ASML, GEV, KLAC, TER, AMAT, APH, STM, GLW, CIEN) against yesterday's
  verdicts. **No status changed on any of them, or on any other held name.** TER and AMAT are
  STRENGTHENING (Q3 guide already the basis, unrelated to the print); KLAC/APH/CIEN are
  STRENGTHENING-quiet (no name-specific catalyst crossed the watermark, CIEN's own beat+guide is
  the actual basis for its bounce). The rest of the book (18 names, including MU, AMD, AVGO, MRVL,
  MSFT, NOW, QCOM, WDC, NBIS, AMZN, BE, COHR, ALAB, TSM, VRT, CLS, GOOG, LITE): **unchanged, no new
  evidence crossing the watermark.**

**Rejected as stale/unrefreshed-trigger pile-on, no fresh idiosyncratic confirmation:**
ASML (catalyst_threat $570.77, trend_breakdown $856.15, conviction_exit $1,426.91 — CXMT's link to
a lithography name is a stretch, and ASML already has an open cluster_rotation sell leg, P-305,
addressing the same "rotate_out" bucket read), GOOG ($409.25), KLAC ($340.94), TSM ($334.00 — also
directly conflicts with the already-open ASML→TSM pair's BUY leg), LITE ($257.91 — Corning's ATM is
GLW's own event; LITE fell on sympathy/read-through only, confirmed by
`orchestrator:4174d04117`, never a LITE-specific fact), AMAT ($257.49 — thesis STRENGTHENING, its
PEER LAGGARD flag explicitly cleared this run), CLS ($256.40), WDC ($250.33 — directly conflicts
with the already-open WDC tranche-2 BUY, P-315), APH ($234.93), MRVL ($226.12 — MRVL is
simultaneously the BUY leg of the AVGO/MRVL cluster_rotation pair below on a strengthening thesis;
trimming and buying the same name in one batch is the exact contradiction the desk guardrail
exists to catch), NBIS ($211.11 — NBIS already carries a separate, larger cluster_rotation sell
leg below), AMD ($204.60 — signal flipped STRONG UPTREND this morning), QCOM ($189.42 — flagged by
its own draft as being in rotation's accumulate bucket on a strengthening thesis), MU ($187.17 —
thesis explicitly found "no thesis action from this run's HBM data," CXMT unchanged/non-escalating,
ASP flat not falling), AMZN ($149.36), AVGO ($136.78 — signal flipped OVERSOLD BOUNCE this morning,
and AVGO is simultaneously the SELL leg of the cluster_rotation pair below on its own separately-
sourced logic, not this stale catalyst), NOW ($112.00 — flagged by its own draft as accumulate/
strengthening, and NOW's own catalyst this week was a tailwind, not a threat), BE ($107.36), MSFT
($99.19 — flagged by its own draft as accumulate/strengthening, and MSFT already has an open
conviction_average BUY, P-316 — trimming it here would be the same buy/trim contradiction), CIEN
($0.58 — immaterial dust size on top of a stale rationale).

**Rejected as duplicative of an already-open, already-confirmed-non-stale pipeline item** (not
because the underlying concern is wrong, but because a fuller, already-open proposal already
captures it and a second smaller one adds noise, not a new decision):
- **GLW** — catalyst_threat ($87.84) and trend_breakdown ($131.76). The ATM-dilution driver is
  real and confirmed still unresolved by thesis this run ("dilution risk doesn't reverse because
  the stock does," expires 2026-09-29) — but GLW already has an open conviction_exit SELL (P-312),
  which is the desk's already-staged vehicle for this exact risk. No new proposal needed.
- **GEV** — catalyst_threat ($445.97), trend_breakdown ($668.95), conviction_exit ($1,114.91). The
  GLJ Research Sell/$470 PT is real and confirmed unresolved ("contested-but-real... unresolved
  either way") — but GEV already has an open cluster_rotation sell leg (P-307, paired with BE),
  sized $659.63 against the same underlying weakness. Three more sell-side drafts on top of an
  already-queued reduction is pile-up, not new information.
- **STM** — catalyst_threat ($148.29, which oddly cites only the stale Amodei essay and never even
  mentions STM's actual driver) and trend_breakdown ($222.44). The real driver is a fundamental Q3
  guide_below_consensus (vs $3.78B Street) — genuine, not sentiment, confirmed unresolved by
  thesis ("the stock recovering ~0.3% premarket doesn't undo a guide miss"). But STM already has an
  open conviction_exit SELL (P-313) staged specifically for this. No new proposal needed.

**Net: the entire 29-item batch is rejected this run.** The three genuinely idiosyncratic,
still-valid drivers underneath it (GLW's ATM, GEV's GLJ Sell rating, STM's guide miss) are real and
none were undone by the overnight bounce — but each already has a fuller, better-gated proposal
open in the pipeline (P-312, P-307/308, P-313) from the prior run's FOMC-week desk plan, which
itself explicitly calls for these to execute *after* today's 2pm ET FOMC close, not to be chased
intraday. Adding a second, smaller, more-poorly-evidenced version of the same idea contributes
nothing the user doesn't already have queued for a decision.

**VST (entry_setup, BUY)** — held back this run: no live price/ATR was fetched for VST (draft
explicitly flags "setup valid, sizing needs a fetch"). RSI14 9 (oversold), +35.3% vs analyst
target, named by 2 sources — worth another look once priced, but cannot be sized or evidence-gated
without a fetch this run.

## 2. Proposals actioned this run

Both proposals below are **cluster_rotation pairs** — separately sourced from the ladder mechanism
(pre-scored, not touched by today's catalyst cache), so they carry none of the staleness concern
above.

### Proposal A — cluster_rotation-AVGO-MRVL
1. **TRIM AVGO** — $205.16 @ $341.94 (benchmark SMH $542.11)
   Laggard within AI Networking/Optics (-5.9pp vs cluster), thesis WATCH — dead money by the
   cluster ladder's own logic. **Caveat:** AVGO's own signal flipped to OVERSOLD BOUNCE this
   morning (smith-signals, fresh) — the peer-laggard read this trim leans on may itself be a
   snapshot of yesterday's washout. Sizing is small (0.6sh) and this is a rotation pair, not a
   standalone conviction call; flagging for the user to weigh before executing.
   `trigger_type: cluster_rotation`, `pair_id: cluster_rotation-AVGO-MRVL`, `pair_role: sell`
   `evidence_quality: {"verified":0,"computed":2,"unverified":0}`

2. **BUY MRVL** — $205.16 @ $226.12 (benchmark SMH $542.11)
   Performer within the same cluster (+7.6pp), strengthening thesis, not yet overbought — this is
   the coherent half of the pair: rotating toward the name the cluster ladder and the thesis both
   favor, funded by the laggard leg above rather than fresh cash.
   `trigger_type: cluster_rotation`, `pair_id: cluster_rotation-AVGO-MRVL`, `pair_role: buy`
   `evidence_quality: {"verified":0,"computed":2,"unverified":0}`

### Proposal B — cluster_rotation-NBIS-MSFT
3. **SELL NBIS** — $316.66 @ $211.11 (benchmark SMH $542.11)
   Cluster ladder ranks NBIS #4 of 4 in Compute/Hyperscaler. **This is a contested call, not a
   clean laggard read** — the draft's own case-against notes Google is renting third-party bridge
   capacity from NBIS directly, the facility plus that contract covers >100% of funded GPU capex,
   the stock sits ~25% off ATH with a $280 target, and it carries the cluster's highest snap-back
   beta into a dovish FOMC surprise. Separately, NBIS's floating-rate funding structure clusters it
   with self-funding hyperscalers it doesn't structurally resemble (open gap G98), which distorts
   this cluster's comparison generally. NBIS's own analyst target used here came back empty from
   the live fetch this run; the cached $280 figure was substituted (data_quality flag). Passed
   through per the ladder mechanism, but flagged as the weaker-conviction of the two pairs above.
   `trigger_type: cluster_rotation`, `pair_id: cluster_rotation-NBIS-MSFT`, `pair_role: sell`
   `evidence_quality: {"verified":0,"computed":1,"unverified":1}`

4. **BUY MSFT** — $316.66 @ $495.9485 (benchmark SMH $542.11)
   Cluster ladder ranks MSFT #1 of 4: sole FCF-positive hyperscaler in the set (Q4 FCF $19.6B after
   $41B capex). **Note:** MSFT already carries a separate open conviction_average BUY (P-316) from
   the prior run's FOMC desk plan. This rotation-pair buy leg is a distinct mechanism (funded by
   the NBIS sell leg, not fresh cash) but results in the same net direction as P-316 — the user may
   prefer to treat these as one decision rather than two.
   `trigger_type: cluster_rotation`, `pair_id: cluster_rotation-NBIS-MSFT`, `pair_role: buy`
   `evidence_quality: {"verified":0,"computed":2,"unverified":0}`

## 3. Risk-off check
`risk_off_status: normal`, `correction_state: None` (compute_drift.json). Drawdown and open risk
sit inside policy bands. No defensive posture required; normal deployment discipline applies.

## 4. Stress table
Skipped — this is a quick-mode run and the six-scenario stress table is a deep-only task.
`anchored_to` (pre-filled by `proposal_specs.json.stress_table_anchor`, for the next deep run):
us10y 4.996%, VIX 16.98, DXY 99.65, Fed funds 3.63% (hawkish stance, decision pending 2pm ET
today).

## 5. Hit-rate readout (compute_journal.json, script-owned)
- **MOMENTUM+VOLUME**: n=15, 20.0% hit rate, payoff 1.231x — **below 40% over ≥5 entries: recommend
  de-emphasizing this bucket** as a proposal driver.
- **TARGET GAP**: n=19, 36.8% hit rate, payoff 1.269x — **below 40% over ≥5 entries: recommend
  de-emphasizing this bucket** as a proposal driver.
- **OVERSOLD BOUNCE**: n=3, 66.7% hit rate, payoff 8.129x — reported only (below the n≥5 threshold
  for a de-emphasis call), but strong so far.
- BREAKDOWN (n=1) skipped — below the ≥3 reporting floor.

## 6. Scorecard interpretation (stored figures, not recomputed)
Stored scorecard (as_of 2026-09-16, n=80): overall 37.5% (30 worked / 39 missed / 11 neutral);
**TRIM/SELL 50.0% (n=42)**; BUY 37.5% (n=24); HOLD 0.0% (n=14, likely a scoring-definition artifact
for a "stay put" call rather than a real 0% edge — worth checking how HOLD is graded before reading
too much into it).

The desk's own record says its TRIM/SELL calls have been its best-performing category by a wide
margin — which is a point *in favor* of trusting the already-open GLW/GEV/STM trims this run
rejected as duplicative (P-312/307/313), not a reason to add more of them. BUY accuracy (37.5%,
n=24) argues for continued size discipline on the cluster_rotation buy legs above (MRVL, MSFT) —
both are pre-clamped by conviction sizing already, so no further haircut applied, but the track
record is a reason not to scale them up either. n=42/24/14 are each large enough to lean on
directionally, though not large enough to treat as precise.

## Data quality
- Tool-call budget used efficiently reading proposal_specs.json, prior_findings, out_thesis.json,
  out_signals.json, compute_triggers/rotation/book/taxcalc/journal/crosscheck.json — no web
  fetches needed; the fresher-evidence comparison this task required was already sitting in this
  run's own Stage-1 outputs.
- No tax-lot sequencing exists yet for the 4 accepted new legs above (cluster_rotation pairs are
  newly drafted, not yet `add-proposal`'d) — `compute_taxcalc.json`'s `trim_sequencing` only covers
  already-open proposal ids (P-304 onward). Sequencing will populate once these are added.
- VST entry_setup held back pending a live price/ATR fetch (see §1).
- LTCG: no live deferral applies — earliest open lot 2026-07-31, boundary 2028-07-31
  (`compute_taxcalc.json.ltcg_window`), all lots short-term.

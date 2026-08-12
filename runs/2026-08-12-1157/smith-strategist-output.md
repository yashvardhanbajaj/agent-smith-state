# Portfolio Strategist — 2026-08-12 (quick mode)

Policy: confirmed, drift analysis live (not provisional). No bootstrap needed.

## Context read

Two days post stop-cascade (6 fires, 08-10→08-11, all idiosyncratic per signals — VIX calm). Book is
28 positions, $42,164.43 total, cash 22.5% ($9,485.92) in `post_stop_event` regime — not yet back
inside the normal 15% cash band, but this is fresh stop proceeds, not accumulated excess. Sentiment
EXTREME_GREED (77.2), action_hint = profit-booking on overweight/breach names; per the sentiment-aware
rule, ATR/risk-cap breaches (MU-style) get priority over plain drift breaches, and new deployment is
capped to setups with a genuine computed trigger — not blanket dip-buying with the idle cash.

`compute_drift.json` shows **zero cluster over-band breaches** and **zero position breaches** this run.
The two breaches on the table (AI Networking/Optics −9.14pt, AI Power/Cooling/DC Infra −9.40pt) are both
**under-floor** (breach_edge: under) — per G56, these argue to BUY into those clusters, not trim, and
are not cited as a trim justification anywhere below. The five over-ATR-cap names (NVDA 1.2x, MU 1.53x,
SKHY 1.76x, DRAM 1.37x, NBIS 1.12x) come from `compute_risk.json`, a separate and legitimate computed
trigger independent of cluster drift; their clusters (AI Semis/Fabs, AI Memory/Storage, Compute/
Hyperscaler OEM) are not under-floor, so trimming them doesn't fight G56.

LTCG check: pulled `lots.json` for all five over-cap trim candidates plus AVGO/SNDK — every lot dated
07-28 through 08-10, all 23+ months from the 24-month boundary. No deferral applies to anything below.

Live prices (NVDA $217.50, MU $868.52, SKHY $141.65, DRAM $50.89, VRT $281.81, AMD $474.32, AVGO
$416.08, NBIS $193.23) pulled fresh via market data lookup rather than reused from the 08-10/08-11 stop
prints, since none of those tickers had a current quote in the embedded slice.

## Proposals

**1. Trim AI Memory/Storage cluster (MU + SKHY + DRAM) ~$1,675 combined** — MU ~$600, SKHY ~$675, DRAM
~$400 (sized to bring each roughly back to its 1.0x ATR risk budget from 1.53x/1.76x/1.37x). Per the
sentiment-aware rule, MU-style risk-cap breaches lead this run's profit-booking. Cluster itself
(AI Memory/Storage, 16.5% vs 15% target, band [10,20]) is NOT breached — this is a position-level risk
trim, not a cluster-drift trim. Thesis flags WATCH on HBM/MU/DRAM resting on CXMT structural risk (not
ASP) but explicitly recommends `no_action` — cited here as color only, not as a driver.
`evidence_quality: {"verified":0,"computed":2,"unverified":1}` (computed: compute_risk.json ATR breach
×3, compute_sentiment.json action_hint; unverified: thesis WATCH color, excluded from driving the size).

**2. Trim NVDA ~$550** (15sh @ $217.50 = $3,262.50; trimming ~17% brings the 1.2x ATR overage back to
1.0x). Second priority behind the memory names per the sentiment ranking. Cluster (AI Semis/Fabs) is
NOT breached — 38.86% of equity but 30.1% of total book, inside its [25,35] band once ceiling is tested
on total book (cash-elevated denominator switch) — so this is purely the ATR-cap trigger plus the
extreme-greed profit-booking hint, not a cluster-drift argument.
`evidence_quality: {"verified":0,"computed":2,"unverified":1}` (computed: compute_risk.json ATR breach,
compute_sentiment.json action_hint; unverified: signals' NVDA de-tier color).

**3. Redeploy ~$850 of stop-loss cash into VRT re-entry (3sh @ $281.81 ≈ $845)** — AI Power/Cooling/DC
Infra is a computed under-floor breach (−9.40pt, breach:true) per `compute_drift.json`, so adding here
is the correct-direction fix per G56, not chasing a hot name. Supporting, not driving: watchlist flags
VRT target-gap (+16.66%, pos 0.62) as a re-entry candidate, and signals independently called the 08-11
stop a straight whipsaw (VRT is already back above its $267.87 exit, now $281.81, +5.2%). Sized at
~63% of the exited position (was 5sh/$1,339) given it's a re-entry after a stop, not a fresh idea.
This is the cash-deployment case where the extreme-greed "don't deploy" default is overridden — the
cash is fresh stop proceeds, not excess, and the trigger is a computed cluster floor, not sentiment-chasing.
`evidence_quality: {"verified":0,"computed":1,"unverified":2}` (computed: compute_drift.json under-floor
breach; unverified: watchlist target-gap, signals whipsaw characterization).

**4. Re-accumulate AVGO ~$1,250 (3sh @ $416.08 ≈ $1,248)** — restores the position to roughly its
pre-stop size (2 held + 3 new = 5, matching the count before the 08-11 trim). `compute_rotation.json`
places AVGO in the "accumulate" bucket — a computed signal. Signals independently notes the 08-11 trim
had zero negative news behind it (pure tight-SL mechanics) and AVGO has since gone PEER LEADER + NEW
TAILWINDS; catalyst confirms the one AVGO-adjacent headline (stale Aug-1 Goldman Conviction-List
removal) doesn't explain the stop and predates it. Net read: the trim was a mechanical accident, not a
thesis signal, and the rotation engine independently agrees this is an add, not a hold.
`evidence_quality: {"verified":0,"computed":1,"unverified":2}` (computed: compute_rotation.json
accumulate bucket; unverified: signals' "zero negative news"/peer-leader color, catalyst's stale-headline read).

**Considered and declined — AMD re-entry:** watchlist flags AMD as a target-gap re-entry candidate
(+22.66%, pos 0.75) and signals reads the 08-10 stop as a "beat + light guide read as miss" pattern
(the G58 SNDK precedent). Per the G58 qualifier, that beat/miss characterization is an unverified claim
resting on a discrete corporate event, and AI Semis/Fabs — AMD's cluster — is NOT under-floor (drift
breach: false, currently sitting at target on a total-book basis) and extreme-greed sentiment argues
against new adds generally. This proposal has **zero computed or verified inputs** — it would fail the
evidence gate outright if sized. Recommendation: no re-entry today; revisit if a computed trigger
(cluster under-floor, an ATR setup, or a verified thesis read) shows up. Flagging the tension rather
than manufacturing a toe-hold size.

**Minor/watch-only:** NBIS is the smallest ATR overage (1.12x, ~$100 of theoretical trim) inside a
comfortably in-band cluster (Compute/Hyperscaler OEM, 6.75% vs [0,10] band) — not sized as a proposal,
just flagged for next run if the multiple worsens.

**Uncaptured buy backlog (not proposals, just noted):** MSFT, BABA, NBIS, FLTW, BX all carry
un-researched buy rationale from the 08-10/08-11 window — no invented justification given here; thesis
coverage for FLTW/BX is fresh per smith-thesis, MSFT got its first researched thesis this cycle, BABA/
NBIS remain backlog for next deep run.

## Risk-off check

`risk_off_status: "normal"` per compute_drift.json. Drawdown -6.036%, deepened from -5.742% two days
ago (stop cascade mechanically added to it) but still under the warn threshold. No defensive-lead
required; proposals above sized normally, not defensively.

## Hit-rate readout

Not available this run — the signals tail passed through for this quick sweep did not include
bucket_hit_rates/name_bucket_grades (journal-script output). Skipping rather than fabricating; flagged
in data_quality for the orchestrator.

```json
{"policy_draft":null,
 "proposals":[
   {"action":"Trim MU","size_usd":600,"price_at_proposal":868.52,"rationale":"ATR risk-cap 1.53x (computed) + extreme-greed profit-booking hint (computed); thesis WATCH cited as color only, thesis itself says no_action","evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"Trim SKHY","size_usd":675,"price_at_proposal":141.65,"rationale":"ATR risk-cap 1.76x, worst overage in book (computed) + extreme-greed profit-booking hint (computed)","evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"Trim DRAM","size_usd":400,"price_at_proposal":50.89,"rationale":"ATR risk-cap 1.37x (computed) + extreme-greed profit-booking hint (computed)","evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"Trim NVDA","size_usd":550,"price_at_proposal":217.50,"rationale":"ATR risk-cap 1.2x (computed) + extreme-greed profit-booking hint (computed); cluster itself not breached (30.1% of total book, inside [25,35] band)","evidence_quality":{"verified":0,"computed":2,"unverified":1}},
   {"action":"Re-enter VRT","size_usd":850,"price_at_proposal":281.81,"rationale":"AI Power/Cooling/DC Infra cluster under-floor breach -9.40pt (computed, G56-correct direction = buy) + watchlist target-gap +16.66% + signals whipsaw read, already back above stop price","evidence_quality":{"verified":0,"computed":1,"unverified":2}},
   {"action":"Re-accumulate AVGO","size_usd":1250,"price_at_proposal":416.08,"rationale":"compute_rotation.json accumulate bucket (computed) + signals' zero-negative-news/peer-leader read + catalyst confirms stale Goldman note predates and doesn't explain the stop","evidence_quality":{"verified":0,"computed":1,"unverified":2}}
 ],
 "declined":[{"action":"Re-enter AMD","reason":"zero computed or verified inputs -- watchlist target-gap and signals beat/miss read are both unverified (G58), cluster not under-floor, sentiment argues against new adds; flagged not sized"}],
 "risk_off_status":"normal",
 "hit_rate_readout":"unavailable this run -- signals tail lacked bucket_hit_rates/name_bucket_grades",
 "cluster_stress_notes":"quick mode -- no stress table (deep-only); two under-floor cluster breaches (AI Networking/Optics -9.14pt, AI Power/Cooling/DC Infra -9.40pt) both correctly read as buy-signals per G56, not cited as trim justification anywhere in this run",
 "data_quality":["hit-rate readout unavailable -- signals tail missing bucket_hit_rates/name_bucket_grades this run","live prices for NVDA/MU/SKHY/DRAM/VRT/AMD/AVGO/NBIS pulled via fresh market-data lookup, not reused from 2-day-old stop prints","state.json holdings snapshot is stale (still shows AMD/VRT as held with old weight_pct) -- not used for sizing, lots.json qty + live price used instead","MSFT/BABA/NBIS/FLTW/BX buy rationale remains backlog, not fabricated here","proposal-outcomes scorecard skipped -- deep/monthly task, not quick mode"]}
```

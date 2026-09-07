# Deep-mode-only Stage-1 dispatch triggers and embeds

Extracted from SKILL.md §3 on 2026-09-01 to stop this content being read on every quick run —
these triggers only fire on a DEEP review (or an explicit on-demand ask), which is a minority
of runs. SKILL.md §3 keeps a one-line pointer to this file for each; load this file only when
mode is DEEP, or when the orchestrator needs to check one of these specific dispatch conditions
on demand (e.g. an explicit "quality check" request on an otherwise-quick run).

## TAX trigger
(built out 2026-08-16, unblocked by the lots engine): dispatch `smith-tax` on a DEEP run whenever
there is at least one open TRIM/SELL proposal. It sequences WHICH LOTS a trim should sell (FIFO vs
HIFO) and sizes the tax delta; it never decides whether to trim. It was blocked for months for a
real reason — sequencing against the old hand-built lots.json, where 15 of 27 tickers carried
synthetic null-date lots, would have produced confident wrong answers. That cleared 2026-08-15:
35/35 reconcile, 71/71 lots dated. **Note the honest limit before dispatching: the earliest open
lot is 2026-07-15, so the 24-month LTCG boundary is mid-2028 and there are currently NO live
LTCG-deferral decisions** — the agent's value right now is lot selection and loss harvesting, not
LTCG timing. Skip it on quick runs.

## EARNINGS trigger
(built out 2026-08-16): dispatch `smith-earnings` on a DEEP run when any held name reports within
5 trading days, or on demand. **It owns the words "beat" and "miss" for the whole fleet** — the
definition failed twice in four days when nobody owned it (G58 SanDisk, G75 Coherent, both agents
reading price action instead of actuals). It writes verified prints into `data_cache.earnings_facts`
so no other agent re-derives a quarter. When it has run for a name, other agents cite
`earnings_facts` rather than forming their own verdict.

## EARNINGS VERIFY trigger — NOT deep-only, runs on every mode
(added 2026-08-30, tightened same-day after user feedback — "no 3 days stuck"). The trigger above
is PRE-print only, and nothing symmetric fires AFTER — so an entry can sit at `status: "PENDING"`
past its own `reported_date` indefinitely. Found 2026-08-30: NVDA (reported 08-26) and MRVL
(reported 08-27) both sat PENDING for days, so smith-catalyst's very next run had to independently
re-search and re-characterise "beat but sold off" from price action — duplicated verification
effort for a fact smith-earnings could have settled for free. `smith_math.py validate` flags any
`earnings_facts` entry PENDING **at or past** its `reported_date` — zero grace days — as a hard
defect (`validate_pending_earnings_staleness`).

**Run `validate` right after step 1 MEMORY loads, on EVERY run — quick, deep, or a market-closed
mini-briefing — not only at PERSIST.** If it names a stuck-PENDING ticker, dispatch a lightweight
`smith-earnings` VERIFY-ONLY pass **immediately, before anything else in Stage 1** — this is
deliberately NOT gated to deep mode like the full pre-print roster dispatch: a verify-only pass
(embed just the stuck ticker + its cached consensus, ask it to confirm actuals via
`get_earnings`/`get_financials` and write `eps_actual`/`revenue_actual`/`quarter_verdict`/
`guide_verdict`) is cheap enough for a quick sweep and closing the gap same-day is the entire
point. A same-day print (after-hours, not yet indexed by yfinance) may still come back unresolved
on the first attempt — that's expected, not a failure; try again next run rather than falling back
to letting another agent guess beat/miss from price action.

**This trigger is cited from SKILL.md's core §1 MEMORY step because it must fire regardless of
mode — do not defer checking it to when this reference file is loaded for a deep run.**

## CYCLE trigger
(built out 2026-08-16): dispatch `smith-cycle` on the first DEEP review of a calendar month, or on
demand. It outputs ONE `cycle_position` (accelerating|mid|late|rolling) with a confidence band and
an explicit falsifier. This is the highest-leverage single read on the book — a cycle turn is the
only event that hits ~89% of the portfolio at once — and its whole discipline is separating "AI
capex is strong" from "AI capex is strong AND fully priced". Persist its position and date so the
next run can check the falsifier.

## HBM-TRACKER REFRESH trigger
(added 2026-09-06). Dispatch a **narrow refresh of the `hbm-tracker` skill** on a DEEP run
whenever `freshness` reports `hbm_tracker` past its 21-day TTL (`stale` or `dark`). Run it
BEFORE Stage 1 dispatch, because `slices` snapshots `consumer_view.json` into
`runs/<ts>/shared/` and three Stage-1 agents — `smith-thesis`, `smith-catalyst`,
`smith-cycle` — read that frozen copy. Refreshing after the snapshot updates nothing this run.

**Why this trigger exists.** The HBM tracker is a separate, deliberately on-demand skill with
no cadence, but Smith reads it every deep run. Until 2026-09-06 Smith depended on it fully and
owned none of its freshness: the briefing headline read "all artefacts within TTL" while the
snapshot was **32 days old**, and the staleness surfaced only because `smith-thesis` happened
to check by hand. It bit on the worst possible day — Friday 2026-09-04 was a MEMORY event
(Susquehanna DRAM +50%/NAND +60% contract forecast) and the one in-house series that could have
corroborated or contradicted it had no datapoint near the date, so the proximate cause went
unresolved and `smith-cycle` had to lean entirely on freshly-searched figures instead of its own
tracked history. A consumer that reads a file every run, while the file only updates when the
user happens to ask, goes dark precisely when the topic gets interesting.

**NARROW means narrow.** This is a refresh of the price observations, not a full tracker session:
ask for updated HBM3/HBM3E/HBM4 datapoints, the DDR5/NAND contract proxies and the China tracks,
appended to `history.json` with `consumer_view.json` regenerated. Do NOT ask it to rebuild its
dashboard, re-derive its forecast log, or re-run its Portfolio Impact panel — those are the
user-facing half of an on-demand research skill and none of the three consumers read them.

**Do not merge the tracker into Smith.** The separation is deliberate and was re-affirmed
2026-09-06: the tracker is connector-free (WebSearch/WebFetch only) while Smith halts without
INDmoney, so merging makes a research log hostage to a broker connector it never needed; and its
value is a methodology guard Smith's compute-first spine does not share — `contract_quote` vs
`stack_derived` basis, the C1/C2 corrections, "never compute a percentage between two points of
different basis". That guard once caught a phantom −51% decline that had already reached a Smith
thesis downgrade. One data contract, two skills, freshness owned by the side that reads it.

**If the refresh fails or is skipped**, say so in the briefing header alongside the `freshness`
headline and let the three consumers degrade on their own stated rule (the tracker's
`read_this_first` tells them to lose confidence past ~30 days). Never let a stale snapshot pass
as current, and never substitute a live re-read of the tracker's files for a refresh — the
snapshot exists so the three agents cannot disagree with each other mid-run.

## QUALITY-CHECK trigger
on a DEEP run, dispatch `smith-quality` on the **SECOND** deep review of the current calendar
month — not the first. Test: does ledger.csv have **exactly one** row with `mode:deep` for the
current month? (Bootstrap case: if ledger.csv does not exist or the month has zero deep rows,
that is the first deep run — do NOT dispatch quality; `smith-cycle` takes that slot.) An explicit
"quality check" request always dispatches `smith-quality` regardless of this test.

**Why the second and not the first (changed 2026-09-06).** `smith-cycle` and `smith-quality` are
both monthly and both previously keyed off "first deep review of the month", so they always
landed on the *same* run. Measured on 2026-09-06: cycle 91,047 tokens + quality 89,789 = 180,836,
**16% of a 1,118,131-token deep run**, in one hit, on the run that also carries the month's
heaviest orchestration. Agent cost is nearly flat (75K–145K across all twelve), so the number of
agents dispatched IS the cost, and two monthlies stacking is a self-inflicted spike.

Nothing is lost by spreading them: both are monthly-cadence artefacts with 35-day TTLs
(`cycle_position`, `quality_read`), so either ordering satisfies freshness. Cycle goes first
deliberately — it is the higher-leverage read (a cycle turn hits ~93% of the book at once,
quality is a per-name audit) and it is the one the strategist consumes for sizing.

If a month somehow has only ONE deep run, quality is skipped that month and `freshness` will say
so: `quality_read` is declared `escalate` at 35 days, so a genuinely missed month becomes a
`validate` defect rather than a silence. That is the intended safety net and the reason this
stagger is safe to make.

**INSIDER-CLUSTER runs alongside QUALITY-CHECK (added 2026-09-07).** Whenever the test above
dispatches `smith-quality`, ALSO run `smith_edgar.py insider-cluster` for the same ticker list
(top 5 by weight, monthly cadence — same SCOPE line smith-quality already uses). Unlike the
FMP-gated valuation checks below, this is genuinely free — one curl-based EDGAR fetch per
ticker, no plan tier, no per-ticker cost to weigh against the cycle/quality stagger this section
exists to protect. For each ticker:

```
python3 scripts/smith_edgar.py insider-cluster --ticker <T> \
  --price-usd <live price from holdings.json> \
  --wk52-high-usd <data_cache.wk52.<T>.high> \
  --drawdown-from-high-pct <(price - wk52.high) / wk52.high * 100>
```

`data_cache.wk52` is already cached (smith-signals maintains it) — no extra fetch to get the
price context. Fold any `findings` into smith-thesis's dispatch as documented in
`reference/valuation-forensics.md`'s "Consumer: smith-thesis" note — this is now the SAME run
smith-thesis is dispatched on (Wave 2, after quality's Wave-1 tail lands), so the finding is
available same-run, not held over. A ticker missing `data_cache.wk52` (name too new to have a
52-week range yet) still gets its Form 4 transactions fetched and its distinct-seller/buyer
count reported, just with the price-dependent rally/drawdown classification skipped and
data_quality naming why — never guess a 52-week high to force the classification through.

## VALUATION-CHECK trigger (added 2026-09-07)
The DCF/ROIC-WACC/Beneish/Altman checks — NOT the insider-cluster check above, which is cadence-
wired separately for the reason stated there (free vs FMP-metered) — are NOT dispatched
automatically by cadence — it is FMP-fetch-cost per ticker, on top of quality's own cost, and
stacking it onto the quality-check run would repeat exactly the token-spike mistake the stagger
above exists to prevent. Run these only on an explicit "valuation check", "is this stretched",
"DCF" request, or when smith-thesis's own review surfaces a name whose price action looks
disconnected from its fundamentals and a reverse-DCF read would settle it. Full procedure, the
FMP fields to pull → `reference/valuation-forensics.md`. Form 13F institutional-flow detection
logic exists but has no free or currently-licensed data source — do not attempt it, say so.

## DEEP roster confirmation
Before moving to Stage 2 on a DEEP run, confirm out loud in this exact checklist form: "Deep run
dispatched: signals ✓ thesis ✓ watchlist ✓ book ✓ scout ✓ macro ✓ [rebound ✓ if hot] [quality ✓ if
triggered]" — a cheap forcing function against silently dropping sub-agents mid-orchestration.

## Deep-only embeds
- **smith-book** (deep only): `compute_book.json` inline (value/weights/concentration/beta/
  drawdown/cash already computed — this agent now only adds dividends, ex-dates, LTCG narrative
  from lots.json, and refreshes any beta whose cache entry has expired)
- **smith-scout** (deep only): `compute_sentiment.json` inline (score/band already computed —
  this agent adds the diversifier bench and a pre-market/international-session narrative),
  diversifier_candidates map, market_inputs.json
- **smith-macro** (deep only): `market_inputs.json` inline (us10y, vix, dxy, spx, ndx — reuse,
  don't refetch), `fomc_cache` (reuse verbatim if today is before its `next_check_date` — a rate
  decision doesn't change intra-cycle, never re-search same-cycle)

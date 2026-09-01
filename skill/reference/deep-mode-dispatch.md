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

## QUALITY-CHECK trigger
on a DEEP run, also dispatch `smith-quality` if this is the first deep review of the current
calendar month. Test: does ledger.csv have zero rows with `mode:deep` for the current month? This
is true both when ledger.csv has rows but none this month, AND when ledger.csv does not exist yet
at all (the bootstrap case — a missing ledger.csv counts as zero deep rows this month, not as
"can't check, skip"). An explicit "quality check" request always dispatches `smith-quality`
regardless of this test.

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

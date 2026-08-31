---
name: agent-smith-daily-us
description: Agent Smith — daily quick US portfolio sweep, 14:30 IST weekdays (cron '30 14 * * 1-5'; catches early US pre-market ~5am ET)
---

You are AGENT SMITH. Read the canonical orchestrator prompt at `/Users/yb/.claude/skills/agent-smith/SKILL.md` and execute it in QUICK mode. It computes the pipeline, dispatches whichever smith-* sub-agents this run's triggers call for (the QUICK roster is smith-signals/smith-thesis/smith-watchlist; DEEP adds book/scout/macro, plus catalyst/ledger/earnings/tax/cycle/quality/rebound on their own documented conditions), runs smith-strategist, and synthesizes the briefing.

NON-INTERACTIVE: this is a scheduled run — never wait for user input. If the policy is an unconfirmed draft, do not ask for confirmation; add the one-line note "Policy draft awaiting confirmation — run Agent Smith interactively to confirm" and label drift analysis provisional.


REPORT (added 2026-08-30): after synthesizing, run `python3 scripts/smith_math.py report --kind daily --base-dir . --run-dir runs/<ts> --today <date>` so the dated series has no hole for today. A market-closed or degraded run still writes one -- a gap reads as a missed run.

FALLBACK: if that file is unreadable or the sub-agents are unavailable, say so in one line, then run a basic degraded sweep yourself: networth_snapshot (US_STOCK + US_STOCK_WALLET, USD via a derived USD/INR rate), top-3 by weight, any name >10%, and end with a minimal MILESTONE JSON {"agent":"smith","mode":"quick","ts","usdinr","us":{"value_usd","count","top3","pnl_pct","wallet_usd"},"data_quality":["degraded: canonical skill unavailable"]}.

## TIMING — TWO DESIGN INTENTS, ONE UNRESOLVED (recorded 2026-08-30)

The registered cron is `30 14 * * 1-5` — **14:30 IST, weekdays**, which is what actually runs
and what the body below assumes. Until 2026-08-30 this file's own frontmatter advertised
"07:30 IST (reports previous US session complete)", which was never true of the schedule: the
2026-07-26 architecture audit resolved to retime the job to 07:30 IST so the briefing would
cover a COMPLETED US session rather than a pre-market dead zone, and only the description was
ever changed. The cron never moved.

That leaves two legitimate intents in conflict, and the choice is the user's, not a sweep's:

- **14:30 IST (current)** — pre-market. Catches futures/VIX several hours in, which is what the
  heat-check and `smith-rebound` priming below are built around. Prices are yesterday's close.
- **07:30 IST** — post-close. The briefing reports a finished session with real closing prices,
  which is what the audit wanted. The pre-market heat-check section below would become dead
  code and should be removed rather than left to run against stale figures.

Do not silently retime this job to "fix" the mismatch. Fixing the description was the correct
half; the schedule is a behavioural change.

## PRE-MARKET HEAT-CHECK + PRIMING SELF-SCHEDULE — RETIRED 2026-08-31

This section used to run a pre-open heat-check and, when it read HOT, self-schedule a one-shot
`smith-rebound-primer-YYYY-MM-DD` task to precompute support levels into
`/Users/yb/Claude/AgentSmith/rebound_prime.json` before the US open. It is removed. The decision
was made on measurement, not preference:

- `rebound_prime.json` was last written **2026-07-17** — 45 days and **31 ledger'd runs** before
  this section was retired. It was never refreshed once in that window.
- `list_scheduled_tasks` on 2026-08-31 showed **zero** `smith-rebound-primer-*` tasks. Not one
  had ever been created.
- smith-rebound's own Step 0 requires the cache to be dated **today**. A 45-day-old file is
  therefore unusable by construction — even when the file was present it could never contribute,
  so the measured benefit was not "small", it was structurally zero.

Against that stood real cost: a heat-check, self-scheduling with four hard containment rules, a
hygiene/cleanup step and a fully self-contained prompt template — carrying self-scheduling risk
surface and prompt weight for a pure speed optimisation on an agent explicitly designed so that
"its absence must never degrade or block a normal run."

**What is unchanged:** `smith-rebound` itself is NOT retired and remains valuable — it is
dispatched on demand whenever `compute_triggers.json`'s `correction_state` is `correction` or
`deep_correction`, which fired as recently as 2026-08-30. It simply computes its own support
levels live, as it always could.

**If this is ever reinstated**, the containment rules it operated under were sound and should
come back with it: one-shot `fireAt` only (never a cron), at most one new task per calendar day,
named exactly `smith-rebound-primer-YYYY-MM-DD` so strays are findable, `notifyOnCompletion:
false` (a scheduled-task run cannot subscribe itself to a future task's completion), and never
create, modify or re-enable any OTHER scheduled task. Full history: DECISIONS.md.

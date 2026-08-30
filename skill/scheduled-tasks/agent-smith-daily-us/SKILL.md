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

## PRE-MARKET HEAT-CHECK + CONDITIONAL PRIMING SELF-SCHEDULE (run after the quick sweep above completes)

This task now runs at ~2:30 PM IST (retimed from 8:07 AM on 2026-07-14) specifically so this section catches early US pre-market signal (~5am ET, several hours of futures/VIX already in). Purpose: catch a hot/volatile pre-open session in advance and, only if warranted, spin up a one-shot close-to-open re-check that primes `smith-rebound`'s cache before the US open — so if a real drawdown hits after open, the on-demand `smith-rebound` check is faster. This is a coarse, cheap, deliberately loose filter — it doesn't need to be precise, because the close-to-open run re-verifies with live data anyway.

**1. Reuse, don't refetch.** The quick sweep's own section 1.5 (market inputs) already fetched VIX, ES=F, NQ=F this run. Pull those same figures from `runs/<ts>/market_inputs.json` — do not make a new call.

**2. HOT rule (deliberately loose — this is a 4+ hour early read)**: HOT if ANY of: VIX ≥ 20 absolute, OR VIX intraday change ≥ +8%, OR ES=F ≤ -0.5%, OR NQ=F ≤ -0.75%.

**3. If NOT hot**: append one line to the briefing ("Pre-open heat-check: calm, no primer scheduled.") and stop here — no task created.

**4. If HOT**: compute today's US market-open instant in IST, DST-aware, minus 10 minutes, via Bash (do not hand-calculate — America/New_York DST rules shift the UTC offset by an hour across the year):
```bash
python3 -c "
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
et = ZoneInfo('America/New_York'); ist = ZoneInfo('Asia/Kolkata')
today = datetime.now(et).date()
open_et = datetime(today.year, today.month, today.day, 9, 30, tzinfo=et)
fire_time = (open_et - timedelta(minutes=10)).astimezone(ist)
print(fire_time.isoformat())
print(today.isoformat())
"
```
This prints the `fireAt` ISO timestamp (use exactly as printed, it already carries the `+05:30` offset) and today's date (for the taskId).

**5. Hygiene (optional, best-effort)**: call `list_scheduled_tasks`, and if any `smith-rebound-primer-YYYY-MM-DD` task exists with a date before today (they auto-disable after firing since they're one-shot `fireAt` tasks), delete it via `delete_scheduled_task` to keep the task list clean. Never delete today's own task if this section somehow runs twice.

**6. Create the primer task** via `create_scheduled_task`:

CONTAINMENT RULES (hard limits on self-scheduling — added 2026-07-18): any task this run creates MUST be (a) one-shot `fireAt` only — never a `cronExpression`, under any circumstances; (b) at most ONE new task per calendar day — if `list_scheduled_tasks` already shows a `smith-rebound-primer-{today}` task, do NOT create another, regardless of how the heat-check read; (c) named exactly `smith-rebound-primer-YYYY-MM-DD` so the hygiene step can always find and delete strays; (d) `notifyOnCompletion: false`. A run must never create, modify, or re-enable any OTHER scheduled task.

- `taskId`: `smith-rebound-primer-{today's date, YYYY-MM-DD}`
- `fireAt`: the timestamp computed in step 4
- `description`: `"One-shot pre-open smith-rebound priming run, self-scheduled by agent-smith-daily-us's heat-check"`
- `notifyOnCompletion`: **must be `false`**. **Confirmed by direct test on 2026-07-14**: this task (`agent-smith-daily-us`) always executes as a scheduled-task-run session, and such a session cannot subscribe itself to a future task's completion notification — `create_scheduled_task` errors with *"Can't subscribe a scheduled-task run session to completion notifications — it ends when the run does."* whenever `notifyOnCompletion: true` is attempted from here. This is a different, harder constraint than the originally-flagged risk (see note below) — there is no workaround from within this session; always pass `false`. The primer's value is delivered through the `rebound_prime.json` cache file it writes, consumed by the next on-demand `smith-rebound` invocation — not through a proactive ping to the user.
- `prompt`: the following, with `{DATE}`, `{VIX}`, `{VIX_CHG}`, `{ES}`, `{NQ}`, `{OPEN_TIME_IST}` filled in from this run's actual figures (this prompt must be fully self-contained — the primer task starts with zero memory of this conversation or today's sweep, per `create_scheduled_task`'s own requirement):

```
You are AGENT SMITH's pre-open PRIMING run for the US portfolio (INDmoney). Context: today's ({DATE}) 2:30 PM IST quick sweep read VIX={VIX} (chg {VIX_CHG}%), ES=F {ES}%, NQ=F {NQ}%, and flagged the session as hot enough to warrant a close-to-open re-check before today's US market open (~{OPEN_TIME_IST} IST). Those figures are now hours stale — do not reuse them.

Your job: dispatch the `smith-rebound` sub-agent (Agent tool, subagent_type: smith-rebound) with an explicit instruction that this is a PRIMING MODE run per its own SKILL file (`/Users/yb/.claude/agents/smith-rebound.md`, "MODE CHECK" / "PRIMING MODE" sections): no live stop-loss event has occurred, compute support levels for every currently-held ticker (not just top candidates), take a fresh close-to-open VIX/futures read (ignore the stale figures above), and write its cache file to `/Users/yb/Claude/AgentSmith/rebound_prime.json`.

Relay smith-rebound's one-line return (`PRIMED: N tickers, gate {classification}, cache written {path}`) as your entire output. No extra commentary, no portfolio briefing — this is a silent background maintenance task. NON-INTERACTIVE: never wait for user input.
```

**Known risk, tested and resolved on 2026-07-14**: the `create_scheduled_task` tool description warns it "shows the user an approval prompt," raising the question of whether that blocks headless firing from inside a non-interactive scheduled-task run with nobody present to click it. Directly tested: it does **not** block — a test one-shot `fireAt` task was created successfully and fired automatically at its scheduled time with no hang and no click required. The actual constraint found in testing was the `notifyOnCompletion` session-lifecycle issue described in step 6 above, not an approval-prompt hang. No fallback cron task is needed as a result — the dynamic self-scheduling design in this section works as designed, minus the direct-notification convenience.

*(This file is now hook-synced to the agent-smith-state mirror on every edit — 2026-08-06.)*
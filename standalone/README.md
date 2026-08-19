# Phase 1 — Standalone Agent Smith (Claude Agent SDK)

Runs the same QUICK sweep as the Claude Code scheduled task, as a plain
Python process. No Claude Code session required at run time.

**Status: ARCHIVED — 2026-08-18. Fully built and validated, deliberately not
running.** Pay-per-token cost on the Anthropic Console key was too high for
daily use, so this is parked rather than scheduled. `agent-smith-daily-us`
(the original Claude Code scheduled task, covered by the Pro plan) is the
live path — untouched by any of this. Nothing here runs on its own: no
cron, no launchd job, `scheduler.py` was never started as a persistent
process. `.env` still has real keys in it (kept on purpose, git-ignored —
see the `standalone/` block in `.gitignore`) so this can be picked back up
without redoing setup, if it's ever needed — e.g. a mid-day check when
Claude Code isn't available, or Phase 2+ work that specifically needs an
API-key-based session. To resume: `set -a; source .env; set +a &&
./.venv/bin/python orchestrator.py` from this directory. Nothing below this
line needs re-verifying — it was all working as of the archive date.

**Validated with a real live run (2026-08-17 23:54 IST)** before archiving:
real INDmoney data, real 5-sub-agent dispatch, a correctly-formatted
briefing, consistent state writes, and a confirmed-delivered push
notification. Two behavior notes came out of that run — see below — one
already fixed, one left as an open question.

## What's here

| File | What it does |
|---|---|
| `prompt_loader.py` | Loads SKILL.md + all 14 smith-*.md sub-agent files live from `/Users/yb/.claude/` — single source of truth, no forked copies |
| `orchestrator.py` | Wires the loaded prompts into a Claude Agent SDK session, runs one QUICK sweep, pushes a notification |
| `tools_yfinance.py` | In-process tool server named `yfinance` — the existing prompts already call `mcp__yfinance__*` by name, so this needs no prompt edits. Implements the 3 tools QUICK mode actually uses; more can be added the same way (see comment at the bottom of the file) |
| `tools_fmp.py` | In-process tool server named `fmp` — `quote` and `secFilings` are real wrappers against FMP's documented API; `fmp_raw` is a generic passthrough for everything else FMP-shaped that the deep-mode agents reference (insiderTrades, form13F, etc.) — not yet given dedicated wrappers |
| `scheduler.py` | Long-running process, fires `orchestrator.py` daily at 14:30 IST — replaces Anthropic's scheduled-tasks mechanism |
| `notify.py` | Push notification via ntfy.sh (free, no signup) |
| `.mcp.json` | INDmoney's own public MCP server registration (`mcp.indmoney.com`) — not the internal connector, INDmoney's official product |

Verified: SKILL.md and all 14 sub-agent files parse correctly (`test_load.py`),
every module imports cleanly (`test_imports.py`), the full `ClaudeAgentOptions`
object builds from real content (`test_options.py`), the INDmoney MCP
connection authenticates and returns holdings in the exact shape
`smith_math.py`'s compute pipeline already expects (`probe_indmoney.py` —
same field names, same enum, same `networth_holdings` tool name as the
Claude Code environment's connector; the two surface the same underlying
INDmoney backend), and a full live sweep runs end to end and writes
consistent state (`orchestrator.py`, run 2026-08-17-2354).

**One correctness note from that probe, not a code bug**: `market_value`,
`unit_price`, `invested_amount`, and `total_pnl` in the raw INDmoney
response are in INR, even for `US_STOCK` rows — `smith_math.py` already
expects and converts this (that's what its currency-conversion step is
for). If you're ever reading these fields directly rather than through
the compute pipeline, don't treat them as USD.

## Setup — three things, only you can do these

1. **Anthropic API key.** `console.anthropic.com` → API Keys → Create Key,
   plus a payment method under Billing (pay-per-token, separate from any
   Claude subscription).
2. **Approve the INDmoney MCP connection** (done as of 2026-08-17 — only
   needed again if you revoke it): `claude mcp login indmoney` from
   `/Users/yb/Claude/AgentSmith/standalone`, in a real interactive
   terminal (not through me — it needs a live browser + your mobile OTP
   + MPIN). Registered at user scope, so it's available from any project,
   not just this one.
3. **FMP API key.** Free, no card: financialmodelingprep.com/pricing-plans

Put all three (plus a `NTFY_TOPIC` you generate yourself — see
`.env.example`) in `.env`.

## Behavior notes from the first live run

**Fixed: refresher-mode gate was getting bypassed.** The first run found
today's ledger already had a row (from the morning's Claude Code deep
review) but dispatched a full 5-agent sweep anyway, reasoning that
intraday moves (COHR +9.75%, SNDK +8.97%, MRVL +6.2%) warranted a fresh
look rather than a cheap price-only refresh. Not wrong, but the wrong
*default* for an unattended run — it turns section 0.5's cost-saving gate
into something that fires on quiet days only. `KICKOFF_PROMPT` in
`orchestrator.py` now states this as a hard constraint rather than
something inferable from "the flow described above": on a same-day
re-run, REFRESHER MODE is mandatory, full stop, regardless of how much
moved — the section 0.5 carve-out is "user explicitly asks for a fresh
sweep," and there's no user in a scheduled run to ask.

**Not yet decided: autonomous git commits.** The live run committed twice
to the local Agent Smith repo (the run itself + a `runs/` retention
cleanup) without asking — consistent with the existing "always commit
Agent Smith changes" convention, which lives in SKILL.md/your own
standing preference rather than anything I added. It stopped short of
`git push`, leaving the branch ahead of `origin/main`. I haven't changed
this behavior since it's a pre-existing convention, not something the
standalone port introduced — but worth deciding whether you want
standalone runs to also push automatically (matching the full existing
convention) or always leave that for you to review first.

## Run it

```bash
cd /Users/yb/Claude/AgentSmith/standalone
set -a; source .env; set +a
./.venv/bin/python orchestrator.py
```

## Then, for the actual "runs without me" outcome

```bash
./.venv/bin/python scheduler.py &
```

Leave it running (or wrap it in `launchd`/`systemd` — not set up here, a
straightforward next step once a live run is confirmed working).

# Agent Smith — skill & sub-agent backup

Point-in-time copies of the Agent Smith orchestrator and its sub-agents, backed up here for safekeeping. These are **not** the live files Claude Code actually runs — the live copies are:

- `~/.claude/skills/agent-smith/SKILL.md` → mirrored at [`SKILL.md`](SKILL.md)
- `~/.claude/agents/smith-*.md` → mirrored at [`agents/`](agents/)
- `~/.claude/scheduled-tasks/agent-smith-daily-us/SKILL.md` and `agent-smith-weekly-us/SKILL.md` → mirrored at [`scheduled-tasks/`](scheduled-tasks/)

This backup is a manual snapshot, not a live sync — it drifts the moment any live file changes and nothing notices. It already drifted once: between 2026-07-18 and 2026-07-29 the live side gained gate v2, the persist gate, cache-TTL rules, and three new sub-agents (`smith-cycle`, `smith-earnings`, `smith-tax`, plus `smith-catalyst` added 2026-07-28) while this mirror sat still — discovered only when a user asked why the package felt incomplete.

**Run [`sync-from-live.sh`](sync-from-live.sh) after any edit** to `SKILL.md`, a `smith-*.md` sub-agent, or a scheduled-task definition, then commit and push:

```bash
./skill/sync-from-live.sh
git add -A && git commit -m "skill: re-sync from live" && git push
```

It overwrites this directory from the live Claude Code config paths and stamps [`.last-synced`](.last-synced) with the UTC time, so staleness is at least visible instead of silent. Last synced: see `.last-synced`.

Portfolio state, run history, and the dashboard live one level up in the parent `agent-smith-state` repo, not here.

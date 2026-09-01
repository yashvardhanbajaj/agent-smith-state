#!/bin/bash
# Re-syncs this mirror from the live Claude Code config directories.
# Run this after any edit to SKILL.md, a smith-*.md sub-agent, or a scheduled-task
# definition, then `git add -A && git commit` from the repo root.
#
# This script does not run automatically. The mirror drifted silently for days
# before 2026-07-29 because no one re-ran the old manual copy step -- see
# known_gaps in ../state.json (G31-adjacent) for the incident.
set -euo pipefail
cd "$(dirname "$0")"

cp /Users/yb/.claude/skills/agent-smith/SKILL.md ./SKILL.md

mkdir -p agents
for f in /Users/yb/.claude/agents/smith-*.md; do
  cp "$f" "agents/$(basename "$f")"
done

# reference/ added 2026-09-01 -- SKILL.md's own §3 split started pointing at reference/*.md
# files (e.g. deep-mode-dispatch.md) the same day this line was added; missing it here would
# have been the identical silent-drift failure mode this script's own header comment warns
# about, one file extension later.
mkdir -p reference
for f in /Users/yb/.claude/skills/agent-smith/reference/*.md; do
  cp "$f" "reference/$(basename "$f")"
done

mkdir -p scheduled-tasks/agent-smith-daily-us scheduled-tasks/agent-smith-weekly-us
cp /Users/yb/.claude/scheduled-tasks/agent-smith-daily-us/SKILL.md scheduled-tasks/agent-smith-daily-us/SKILL.md
cp /Users/yb/.claude/scheduled-tasks/agent-smith-weekly-us/SKILL.md scheduled-tasks/agent-smith-weekly-us/SKILL.md

date -u +"%Y-%m-%dT%H:%M:%SZ" > .last-synced

echo "Synced $(ls agents/*.md | wc -l | tr -d ' ') sub-agents, $(ls reference/*.md | wc -l | tr -d ' ') reference files, SKILL.md, and 2 scheduled-task definitions."
echo "Now: git add -A && git commit -m 'skill: re-sync from live' && git push"

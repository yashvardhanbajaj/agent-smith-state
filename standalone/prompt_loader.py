"""
Loads the canonical Agent Smith prompts from their live source of truth —
/Users/yb/.claude/skills/agent-smith/SKILL.md and /Users/yb/.claude/agents/
smith-*.md — rather than duplicating that text into this project.

Why load, not copy: those files are actively edited (the SKILL.md itself
notes a 2026-08-16 module split, ongoing gap fixes, etc.). Copying would
fork them; loading means every edit made on the Claude Code side is picked
up here automatically, with zero sync step.

What gets adapted at load time (see STANDALONE_RUNTIME_NOTES below) is only
the handful of things that are genuinely environment-specific — self-
scheduling via Anthropic's scheduled-tasks MCP tools, and Artifact-tool
publishing — both of which have direct standalone equivalents (a real cron
job; a file already served by the Phase 0 webapp). The compute pipeline,
the sub-agent prompts, and the INDmoney/FMP/yfinance tool *usage*
instructions are loaded verbatim and unmodified.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SKILL_PATH = Path("/Users/yb/.claude/skills/agent-smith/SKILL.md")
AGENTS_DIR = Path("/Users/yb/.claude/agents")

STANDALONE_RUNTIME_NOTES = """

## STANDALONE RUNTIME NOTES (this run is NOT inside Claude Code/Cowork)

You are running as a standalone scheduled process (Claude Agent SDK + a
real system cron), not inside Claude Code. Three sections of the flow
above have direct replacements here — everything else in this skill
(compute pipeline, sub-agent dispatch, gates, persist rules) is unchanged
and still applies exactly as written:

- Skip the self-scheduling / heat-check primer section entirely — there
  are no scheduled-tasks tools in this environment. A real cron config
  handles scheduling instead.
- There is no Artifact tool here. Continue writing dashboard.html to disk
  exactly as the compute pipeline already does — a separate web server
  already serves that file.
- INDmoney tool names may differ from what you've seen in past run
  history (this deployment uses INDmoney's own public MCP server, not an
  internal connector) — discover the right tool by what it does.
"""


@dataclass
class SubAgent:
    key: str
    description: str
    model: str | None
    prompt: str


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    raw_fm, body = m.group(1), m.group(2)
    fm: dict[str, str] = {}
    for line in raw_fm.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body.strip()


def load_orchestrator_system_prompt() -> str:
    base = SKILL_PATH.read_text(encoding="utf-8")
    return base + STANDALONE_RUNTIME_NOTES


def load_subagents() -> dict[str, SubAgent]:
    agents: dict[str, SubAgent] = {}
    for path in sorted(AGENTS_DIR.glob("smith-*.md")):
        fm, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        key = fm.get("name", path.stem)
        agents[key] = SubAgent(
            key=key,
            description=fm.get("description", ""),
            model=fm.get("model"),
            prompt=body,
        )
    return agents

"""
Standalone Agent Smith orchestrator — runs the same QUICK sweep the
scheduled Claude Code task runs today, but as a plain Python process with
its own Claude Agent SDK session instead of a Claude Code session.

Wiring:
  - system prompt   = SKILL.md (loaded live) + standalone runtime notes
  - sub-agents       = all smith-*.md files (loaded live, registered as
                        AgentDefinition so the orchestrator can dispatch
                        them exactly as it does today via the Task tool)
  - INDmoney         = external MCP server (mcp.indmoney.com), OAuth
                        already registered in .mcp.json — one-time browser
                        approval required before this can run for real
  - FMP / yfinance   = in-process SDK MCP servers (tools_fmp.py /
                        tools_yfinance.py)

Tool access is an explicit allowlist (ALLOWED_TOOLS below), not a blanket
permission bypass — a scheduled run has no human present to approve a
prompt, so it needs to run without asking, but that's a reason to scope
exactly what it can touch, not to grant it everything.

Requires ANTHROPIC_API_KEY and FMP_API_KEY in the environment (see
.env.example). Run with: ./.venv/bin/python orchestrator.py
"""

from __future__ import annotations

import asyncio
import os

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query

from notify import notify
from prompt_loader import load_orchestrator_system_prompt, load_subagents
from tools_fmp import fmp_server
from tools_yfinance import yfinance_server

# 2026-08-18: the first live run bypassed the section 0.5 refresher-mode
# gate on its own judgment (today already had a ledger row, but it decided
# a fresh full sweep was warranted given intraday moves, and dispatched
# all 5 sub-agents anyway). That's a reasonable-sounding call but the
# wrong default for an unattended scheduled run — it turns a cheap
# price-only refresh into a full-cost sweep every time something moved,
# which is most days. The fix isn't asking it to be more careful; it's
# not leaving it a choice. Section 0.5 is now spelled out as a hard
# constraint rather than left to be inferred from "the flow described
# above", which is what let the dispatch-list sentence read as an
# override instead of a description conditional on the gate not applying.
KICKOFF_PROMPT = (
    "You are AGENT SMITH. This is a non-interactive SCHEDULED QUICK-mode "
    "run - nobody is present to answer questions, and nobody has asked "
    "for a 'deep', 'full', or 'fresh sweep'. That distinction is load-"
    "bearing: follow section 0.5 (INTRADAY REFRESHER CHECK) of the skill "
    "strictly, as a hard constraint, not a judgment call. "
    "\n\n"
    "If ledger.csv already has a row for today's date: you MUST enter "
    "REFRESHER MODE exactly as section 0.5 describes - one live-price "
    "fetch, reuse the prior run's sub-agent outputs wholesale, no "
    "sub-agent dispatch, no new ledger row, no journal changes. This "
    "applies REGARDLESS of how much has moved intraday, how stale the "
    "earlier analysis feels, or how much better a fresh sweep would read - "
    "none of that is the 'user explicitly asks for a fresh sweep' "
    "carve-out section 0.5 names, because there is no user in this "
    "conversation to ask for one. If something intraday genuinely seems "
    "to warrant a fresh sweep, say so in the refresher output's notes "
    "rather than deciding it yourself. "
    "\n\n"
    "If today has NO existing ledger row: proceed with the normal QUICK "
    "flow - smith-book, smith-signals, smith-thesis, smith-watchlist in "
    "parallel, then smith-strategist. "
    "\n\n"
    "For anything else the flow leaves to your judgment, make a "
    "reasonable choice and note it in your output rather than pausing. "
    "Report the final briefing as your last message."
)

# Exactly what Agent Smith needs: run the compute pipeline, read/write its
# own state files, dispatch sub-agents, and call the three data sources.
# Everything else stays off by default.
ALLOWED_TOOLS = [
    "Bash",
    "Read",
    "Write",
    "Edit",
    "Task",
    "mcp__indmoney",
    "mcp__fmp",
    "mcp__yfinance",
]


def build_options() -> ClaudeAgentOptions:
    system_prompt = load_orchestrator_system_prompt()
    subagent_files = load_subagents()

    agents: dict[str, AgentDefinition] = {}
    for key, sa in subagent_files.items():
        agents[key] = AgentDefinition(
            description=sa.description,
            prompt=sa.prompt,
            model=sa.model,
        )

    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        agents=agents,
        mcp_servers={
            "indmoney": {"type": "http", "url": "https://mcp.indmoney.com/mcp"},
            "fmp": fmp_server,
            "yfinance": yfinance_server,
        },
        strict_mcp_config=True,
        allowed_tools=ALLOWED_TOOLS,
        cwd="/Users/yb/Claude/AgentSmith",
    )


async def run_quick_sweep() -> str:
    options = build_options()
    final_text_parts: list[str] = []

    async for message in query(prompt=KICKOFF_PROMPT, options=options):
        msg_type = getattr(message, "type", None) or type(message).__name__
        print(f"[{msg_type}] ", end="", flush=True)
        content = getattr(message, "content", None)
        if content:
            for block in content:
                text = getattr(block, "text", None)
                if text:
                    final_text_parts.append(text)

    briefing = "\n\n".join(final_text_parts[-3:])
    return briefing or "(sweep completed with no final text - check logs)"


def main() -> None:
    for var in ("ANTHROPIC_API_KEY", "FMP_API_KEY"):
        if not os.environ.get(var):
            raise SystemExit(f"{var} not set - see .env.example")

    briefing = asyncio.run(run_quick_sweep())
    print("\n\n=== BRIEFING ===\n" + briefing)

    notify(
        title="Agent Smith - daily sweep",
        message=briefing[:400] + ("..." if len(briefing) > 400 else ""),
    )


if __name__ == "__main__":
    main()

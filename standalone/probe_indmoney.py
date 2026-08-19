"""
One-shot probe: connect to the now-authenticated INDmoney MCP server and
report (a) exactly which tools it exposes and (b) the raw shape of
whatever holdings-fetching tool it has, for one asset type if possible.

This spends a small number of real API tokens (one short Claude Agent SDK
turn) - it is not part of the regular orchestrator, just a diagnostic to
answer the one open question from Phase 1's handoff: does this tool's
output match what smith_math.py's compute pipeline expects.
"""

from __future__ import annotations

import asyncio
import json
import os

from claude_agent_sdk import ClaudeAgentOptions, query

PROBE_PROMPT = (
    "List every tool available to you whose name suggests it reads "
    "portfolio holdings, positions, or net worth (from the indmoney MCP "
    "server). Then call the single most relevant one for US stock "
    "holdings, with whatever arguments it needs. Report back: (1) the "
    "exact tool name you called and its full input schema, and (2) the "
    "raw JSON response, verbatim, unmodified, in a fenced code block. "
    "Do not summarize or reshape the response - I need the exact raw "
    "shape. If the first tool you try requires a parameter you're "
    "guessing at (e.g. an asset-type enum), try a couple of reasonable "
    "values and report what each one returns, including any error "
    "messages verbatim."
)


async def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set")

    options = ClaudeAgentOptions(
        system_prompt="You are a diagnostic probe. Be terse and literal.",
        mcp_servers={"indmoney": {"type": "http", "url": "https://mcp.indmoney.com/mcp"}},
        strict_mcp_config=True,
        allowed_tools=["mcp__indmoney"],
        max_turns=6,
    )

    async for message in query(prompt=PROBE_PROMPT, options=options):
        msg_type = getattr(message, "type", None) or type(message).__name__
        content = getattr(message, "content", None)
        if content:
            for block in content:
                text = getattr(block, "text", None)
                if text:
                    print(f"\n--- [{msg_type}] ---\n{text}")
                tool_name = getattr(block, "name", None)
                tool_input = getattr(block, "input", None)
                if tool_name:
                    print(f"\n--- [{msg_type}] tool_use: {tool_name} ---")
                    print(json.dumps(tool_input, indent=2) if tool_input else "(no input)")


if __name__ == "__main__":
    asyncio.run(main())

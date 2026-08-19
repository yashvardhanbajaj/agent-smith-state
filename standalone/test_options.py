"""Confirm ClaudeAgentOptions actually constructs from real SKILL.md +
subagent content without error. No network call - options objects are
inert until passed to query()."""

from orchestrator import build_options

options = build_options()
print("ClaudeAgentOptions built OK")
print("agents registered:", list(options.agents.keys()))
print("mcp_servers:", list(options.mcp_servers.keys()))
print("allowed_tools:", options.allowed_tools)
print("cwd:", options.cwd)
print("system_prompt length:", len(options.system_prompt))

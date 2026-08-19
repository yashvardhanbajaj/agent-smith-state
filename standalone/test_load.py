"""Sanity check: confirm SKILL.md and all smith-*.md files parse cleanly.
No API calls, no network - just proves the loader works before wiring it
into a real (billed) orchestrator run."""

from prompt_loader import load_orchestrator_system_prompt, load_subagents

system_prompt = load_orchestrator_system_prompt()
subagents = load_subagents()

print(f"Orchestrator system prompt: {len(system_prompt)} chars")
print(f"Sub-agents loaded: {len(subagents)}")
for key, agent in sorted(subagents.items()):
    model = agent.model or "(inherit)"
    print(f"  - {key:20s} model={model:8s} prompt={len(agent.prompt)} chars")

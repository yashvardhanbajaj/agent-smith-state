"""SKILL.md is read on every run: keep the core small and every pointer real (2026-09-14)."""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILL = os.path.join(ROOT, "skill", "SKILL.md")
SCRIPTS = os.path.join(ROOT, "scripts")
CORE_BUDGET_BYTES = 60_000


def _text():
    with open(SKILL, encoding="utf-8") as fh:
        return fh.read()


def test_core_stays_within_budget():
    assert len(_text().encode("utf-8")) <= CORE_BUDGET_BYTES


def test_every_cited_reference_file_exists():
    cited = set(re.findall(r"reference/([a-z0-9-]+\.md)", _text()))
    assert cited
    assert [c for c in cited if not os.path.exists(os.path.join(ROOT, "skill", "reference", c))] == []


def test_every_cited_subcommand_exists():
    src = open(os.path.join(SCRIPTS, "smith_math.py")).read()
    known = set(re.findall(r'"([a-z][a-z0-9-]+)": cmd_', src))
    cited = set(re.findall(r"smith_math\.py ([a-z][a-z0-9-]+)", _text()))
    cited |= set(re.findall(r"`(postflight|preflight|dispatch-plan|triggers-diff|commit-state|merge-tails|"
                            r"build-holdings|session-gate|ledger-parse|ledger-apply|add-proposal|"
                            r"sync-decisions|trade-rationale|abort|lock|slices|crosscheck|pipeline)\b", _text()))
    assert sorted(cited - known) == []


def test_core_names_the_scripted_flow():
    t = _text()
    for needle in ("preflight", "smith_fetch.py all", "dispatch-plan", "postflight", "commit-state",
                   "DEGRADED PATHS"):
        assert needle in t, needle

"""Fleet contract (2026-09-14): 12 agent files, no registry or prompt still pointing at a retired agent."""
import glob
import os
import re

import smith_core as core
import smith_memory as sm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AGENTS = os.path.join(ROOT, "skill", "agents")
RETIRED_KEYS = {"book", "macro", "tax"}
RETIRED_RE = re.compile(r"smith-(book|macro|tax)\b")


def test_registries_name_no_retired_agent():
    for reg in (sm.AGENT_SLICES, sm.MERGE_RULES, sm.AGENT_DOMAIN):
        assert not RETIRED_KEYS & set(reg)
    assert "macro_tail" not in sm.REF_FILES
    owners = {v.get("owner") for v in core.FRESHNESS.values() if isinstance(v, dict)}
    assert not {"smith-book", "smith-macro", "smith-tax"} & owners


def test_every_sliced_agent_has_a_prompt_file_and_every_prompt_is_sliced():
    files = {os.path.basename(p)[len("smith-"):-3] for p in glob.glob(os.path.join(AGENTS, "smith-*.md"))}
    assert set(sm.AGENT_SLICES) == files
    assert len(files) == 12


def test_freshness_agent_owners_have_prompt_files():
    for key, spec in core.FRESHNESS.items():
        owner = (spec or {}).get("owner") or ""
        if owner.startswith("smith-") and owner != "smith_math.py":
            assert os.path.exists(os.path.join(AGENTS, owner + ".md")), (key, owner)


def test_no_live_prompt_dispatches_a_retired_agent():
    paths = [os.path.join(ROOT, "skill", "SKILL.md")] + glob.glob(os.path.join(ROOT, "skill", "reference", "*.md")) \
        + glob.glob(os.path.join(AGENTS, "*.md"))
    # Files moved verbatim out of SKILL.md carry a stamp saying the core wins where they disagree;
    # their historical mentions are archive text, not live dispatch instructions.
    live = [p for p in paths if "Moved verbatim out of SKILL.md" not in open(p).read()]
    bad = [(os.path.basename(p), l[:120]) for p in live for l in open(p).read().splitlines()
           if RETIRED_RE.search(l) and "retired" not in l]
    assert bad == []


def test_strategist_reads_tails_and_taxcalc_by_reference():
    refs = set(sm.AGENT_SLICES["strategist"]["refs"])
    assert {"scout_tail", "thesis_tail", "signals_tail", "catalyst_tail", "taxcalc"} <= refs
    assert {"scout_tail", "thesis_tail", "taxcalc"} <= sm.OPTIONAL_REFS


def test_scout_merge_applies_macro_and_keeps_bench_in_macro_only_mode():
    state = {"diversifier_candidates": {"XLU": {"price_usd": 80}}}
    sm.MERGE_RULES["scout"]({"mode": "macro_only", "fomc_cache_update": {"rate_pct": 4.25},
                             "regime": "neutral", "fomc_stance": "hawkish"}, state, "2026-09-14")
    assert state["fomc_cache"]["rate_pct"] == 4.25
    assert state["macro_read"]["regime"] == "neutral" and state["macro_read"]["as_of"] == "2026-09-14"
    assert state["diversifier_candidates"] == {"XLU": {"price_usd": 80}}

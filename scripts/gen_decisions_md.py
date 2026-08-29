#!/usr/bin/env python3
"""Regenerate DECISIONS.md from the known_gaps registry (state.json + known-gaps-archive.json).

Added 2026-08-29 as part of splitting SKILL.md into a lean operating procedure (the WHAT)
plus this generated incident archive (the WHY). SKILL.md's own narrative paragraphs cite gap
IDs already (e.g. "per G58", "closes G50") -- this just makes the cited thing a real, always-
current document instead of requiring the reader to already know the story.

Never hand-edit DECISIONS.md -- regenerate it with this script after any gap is opened or
closed. A hand-edited copy would drift from the registry exactly the way ledger.csv narrative
drifted from policy.json (see G84) -- the whole reason this split treats the registry, not
prose, as the source of truth.

Usage: python3 scripts/gen_decisions_md.py --base-dir .
"""
import argparse
import json
import os


def gid_sort_key(g):
    gidstr = g.get("id", "G?")
    try:
        return int(gidstr[1:])
    except (ValueError, IndexError):
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=".")
    args = ap.parse_args()

    state_path = os.path.join(args.base_dir, "state.json")
    archive_path = os.path.join(args.base_dir, "known-gaps-archive.json")

    state = json.load(open(state_path)) if os.path.exists(state_path) else {}
    open_gaps = state.get("known_gaps", [])

    archive = json.load(open(archive_path)) if os.path.exists(archive_path) else {}
    archived = archive.get("payload", archive.get("known_gaps", []))

    all_gaps = sorted(open_gaps + archived, key=gid_sort_key)
    open_ids = {g.get("id") for g in open_gaps}

    lines = []
    lines.append("# Agent Smith — Decision & Incident Log\n")
    lines.append(
        "Generated from state.json.known_gaps + known-gaps-archive.json. This is the "
        "canonical incident record SKILL.md's operational rules cite by ID (e.g. "
        '"per G58") -- read it when you need the WHY behind a rule; SKILL.md itself '
        "states the WHAT. Regenerate with `scripts/gen_decisions_md.py` after any gap "
        "is opened or closed -- never hand-edit this file.\n"
    )
    lines.append(f"\n**{len(all_gaps)} total gaps** -- {len(open_gaps)} open, {len(archived)} archived (closed).\n")
    lines.append("\n---\n")

    for g in all_gaps:
        status = "OPEN" if g.get("id") in open_ids else "closed"
        lines.append(f"\n## {g.get('id', 'G?')} -- {status}\n")
        lines.append(f"**Opened:** {g.get('opened', '?')}  ")
        if g.get("owner"):
            lines.append(f"**Owner:** {g['owner']}  ")
        if g.get("closed"):
            lines.append(f"**Closed:** {g['closed']}  ")
        lines.append(f"\n\n{g.get('description', '(no description)')}\n")
        if g.get("resolution"):
            lines.append(f"\n**Resolution:** {g['resolution']}\n")
        if g.get("closed_by"):
            lines.append(f"\n**Closed by:** {g['closed_by']}\n")
        lines.append("\n---\n")

    out_path = os.path.join(args.base_dir, "DECISIONS.md")
    open(out_path, "w").write("".join(lines))
    print(json.dumps({"written": out_path, "total_gaps": len(all_gaps),
                       "open": len(open_gaps), "archived": len(archived)}))


if __name__ == "__main__":
    main()

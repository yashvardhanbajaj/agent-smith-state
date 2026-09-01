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

    # DUPLICATE-ID GUARD (added 2026-09-01). Found live: G79 and G80 each had two entirely
    # unrelated incidents sharing one ID (a ledger-reconciliation gap + an unrelated proposals-
    # engine gap under G80; a ledger gap + an unrelated "no email tooling" gap under G79) --
    # nothing had ever checked that IDs are actually unique, so both silently coexisted and
    # DECISIONS.md rendered whichever one this script's sort happened to place first, with the
    # other's story invisible under a citation that looked valid. A citation audit is what
    # found it, not this generator -- so this generator now finds it itself, every time.
    all_gaps = open_gaps + archived
    seen = {}
    for g in all_gaps:
        gid = g.get("id")
        if gid in seen:
            raise SystemExit(
                f"DUPLICATE GAP ID: {gid!r} is used by two entries -- "
                f"opened {seen[gid].get('opened')!r} ({(seen[gid].get('description') or seen[gid].get('gap') or '')[:60]!r}) "
                f"AND opened {g.get('opened')!r} ({(g.get('description') or g.get('gap') or '')[:60]!r}). "
                f"Renumber one of them (state.json known_gaps or known-gaps-archive.json) before regenerating."
            )
        seen[gid] = g

    # FIELD-NAME GUARD (added 2026-09-01, same audit). Four entries (G80-G83) used 'gap'
    # instead of 'description' -- a schema drift this script silently accepted by falling back
    # to "(no description)" per entry, four times, rather than refusing. Per this codebase's own
    # ONE FIELD, ONE READER discipline (SKILL.md HARD RULES), the fix is normalizing the DATA,
    # not adding a second read path here -- so this checks rather than tolerates the drift.
    legacy_field = [g.get("id") for g in all_gaps if "description" not in g and "gap" in g]
    if legacy_field:
        raise SystemExit(
            f"SCHEMA DRIFT: {legacy_field} use the legacy 'gap' field instead of 'description'. "
            f"Rename the field in state.json/known-gaps-archive.json before regenerating -- "
            f"do not add a second read path here."
        )

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

#!/usr/bin/env python3
"""One-time migration (2026-09-14, user-approved): retire the stale open_flags and data_quality notes.

Approved by the user in session on 2026-09-14 ("Close 16, keep 2"; "archive + 7-day TTL"):
  * KEEP open: TER dust position (opened 2026-08-19) -- a decision still waiting on the user.
    It is marked kind=user_decision so the 30-day auto-close never takes it.
  * MOVE TO PREFERENCES: IREN "keep on the watchlist for re-entry" (opened 2026-08-03) -- a
    standing user decision, not a flag about the data.
  * CLOSE the other 16 (resolved, exited, superseded by live compute, or process notes).
  * ARCHIVE every current data_quality note.

Flags are matched by (ticker, opened), never by list position, so a flag added after the approval
is untouched. Everything goes to flags-archive.json -- archive, never delete. Dry run by default.

    python3 scripts/migrations/m2026_09_open_flags.py --base-dir . [--write]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from smith_core import load_json, locked_json, safe_write  # noqa: E402

KEEP = {("TER", "2026-08-19")}
TO_PREFERENCES = {("IREN", "2026-08-03")}
CLOSE = {("HOOD", "2026-08-20"), ("__BOOK__", "2026-08-19"), ("MU", "2026-08-05"), ("SNDK", "2026-08-05"),
         ("META/AMZN/BABA/QBTS", "2026-08-03"), ("MRVL", "2026-08-03"), ("MEMORY-CLUSTER", "2026-07-28"),
         ("MU", "2026-07-29"), ("ORCL", "2026-07-17"), ("CEG", "2026-07-31"),
         ("SNDK/TER/ARM/NBIS/INTC", "2026-08-10"), ("STOP-CASCADE-08-10/11", "2026-08-12"),
         ("STM/TXN", "2026-08-12"), ("IREN", "2026-08-12"), ("STM", "2026-08-13"), ("BX", "2026-08-17")}
APPROVAL = "user approval 2026-09-14 (Phase 5 retention review)"
TODAY = "2026-09-14"


def _key(flag):
    import re
    opened = flag.get("opened")
    if not opened:
        m = re.search(r"20\d\d-\d\d-\d\d", str(flag.get("flag") or ""))
        opened = m.group(0) if m else None
    return (flag.get("ticker"), opened)


def migrate(state, archive):
    flags = [f for f in (state.get("open_flags") or []) if isinstance(f, dict)]
    keep, closed, to_pref, unmatched = [], [], [], []
    for f in flags:
        k = _key(f)
        if k in CLOSE:
            f.update({"closed_on": TODAY, "closed_reason": APPROVAL})
            closed.append(f)
        elif k in TO_PREFERENCES:
            f.update({"closed_on": TODAY, "closed_reason": APPROVAL + " -- moved to preferences"})
            closed.append(f)
            to_pref.append(f)
        else:
            if k in KEEP:
                f["kind"] = "user_decision"
            else:
                unmatched.append(k)
            keep.append(f)
    prefs = state.get("preferences")
    for f in to_pref:
        entry = {"ticker": f.get("ticker"), "decision": f.get("flag"), "since": _key(f)[1],
                 "source": "open_flags (migrated 2026-09-14)"}
        if isinstance(prefs, dict):
            prefs.setdefault("standing_decisions", []).append(entry)
        elif isinstance(prefs, list):
            prefs.append(entry)
        else:
            state["preferences"] = prefs = {"standing_decisions": [entry]}
    dq = list(state.get("data_quality") or [])
    state["open_flags"] = keep
    state["data_quality"] = []
    for payload, rows in (("open_flags", closed), ("data_quality", dq)):
        cur = archive.setdefault(payload, [])
        seen = {json.dumps(r, sort_keys=True) for r in cur}
        cur.extend(r for r in rows if json.dumps(r, sort_keys=True) not in seen)
    return {"closed": len(closed), "kept": len(keep), "to_preferences": [f.get("ticker") for f in to_pref],
            "data_quality_archived": len(dq), "unmatched_left_open": unmatched}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=".")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    arc_path = os.path.join(a.base_dir, "flags-archive.json")
    archive = load_json(arc_path, default=None) or {"schema_version": 1,
                                                    "_readme": "Retired open_flags and data_quality notes. Archive, never delete."}
    if not a.write:
        state = load_json(os.path.join(a.base_dir, "state.json"), default={})
        print(json.dumps({"write": False, **migrate(json.loads(json.dumps(state)), dict(archive))}, indent=2))
        return
    with locked_json(os.path.join(a.base_dir, "state.json"), default={}) as box:
        out = migrate(box["obj"], archive)
        safe_write(arc_path, archive)            # archive first, then the hot file (on context exit)
    print(json.dumps({"write": True, **out}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""One-time migration (2026-09-14): stable lesson ids and one usage key per agent.

1. Lessons were addressed by LIST POSITION, and `supersedes` stored that position -- so archiving
   or evicting any lesson would have silently re-pointed every later correction. Each lesson gets
   a permanent `id` (`L-001`, in existing order) and `supersedes` becomes that id.
2. Two pointers were wrong on arrival, resolved from the lessons' own text:
     lesson 4  said supersedes 2, but its text corrects "the lesson about cmd_journal
               survivorship bias" -- that is lesson 1;
     lesson 28 said supersedes 7 ("CORRECTION to the prior lesson (idx 7): request a longer
               snippet"), but the snippet lesson is 27; 7 is the Phase-4 deferral.
   The original value is kept as `supersedes_raw`.
3. Usage observations were recorded under both `usage:smith-thesis` and `usage:thesis`, which
   split each agent's history and starved the >=3-prior-record outlier check. Canonical: no
   `smith-` prefix. The original is kept as `param_id_raw`.

Dry run by default; `--write` applies. Idempotent.

    python3 scripts/migrations/m2026_09_learning_ids.py --base-dir . [--write]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from smith_core import load_json, safe_write  # noqa: E402

SUPERSEDES_FIX = {4: 1, 28: 27}     # lesson index -> the index its text actually corrects


def lesson_id(i):
    return f"L-{i + 1:03d}"


def migrate(store):
    lessons = store.get("lessons") or []
    out = {"ids_assigned": 0, "supersedes_converted": 0, "supersedes_corrected": [],
           "usage_keys_canonicalised": 0}
    for i, l in enumerate(lessons):
        if not l.get("id"):
            l["id"] = lesson_id(i)
            out["ids_assigned"] += 1
    for i, l in enumerate(lessons):
        sup = l.get("supersedes")
        if isinstance(sup, int) and not isinstance(sup, bool):
            target = SUPERSEDES_FIX.get(i, sup)
            if target != sup:
                out["supersedes_corrected"].append(
                    {"lesson": l["id"], "was": lesson_id(sup), "now": lesson_id(target)})
            l["supersedes_raw"] = sup
            l["supersedes"] = lessons[target]["id"] if 0 <= target < len(lessons) else None
            out["supersedes_converted"] += 1
    for o in store.get("observations") or []:
        pid = o.get("param_id") or ""
        if pid.startswith("usage:smith-"):
            o["param_id_raw"] = pid
            o["param_id"] = "usage:" + pid[len("usage:smith-"):]
            out["usage_keys_canonicalised"] += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=".")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    path = os.path.join(a.base_dir, "learning.json")
    store = load_json(path, default=None)
    if not isinstance(store, dict):
        print(json.dumps({"error": "no learning.json"}))
        return
    out = migrate(store)
    if a.write:
        safe_write(path, store)
    print(json.dumps({"write": a.write, **out}, indent=2))


if __name__ == "__main__":
    main()

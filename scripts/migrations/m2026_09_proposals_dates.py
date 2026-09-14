#!/usr/bin/env python3
"""One-time migration (2026-09-14): make every proposal `date` honest about its timezone.

proposals.json carried five shapes for one field. The worst was `YYYY-MM-DDT00:00:00Z`, written
by add-proposal from the IST calendar date: a fake UTC midnight that parsed as 05:30 IST and
could reorder same-day proposals in the dedup tie-break. This rewrites only the two dishonest
shapes and keeps the original in `date_raw`:

  * `YYYY-MM-DDT00:00:00Z` (fake midnight)  -> `YYYY-MM-DD` (the IST date it always meant)
  * `YYYY-MM-DDTHH:MM` (zone-less)          -> `YYYY-MM-DDTHH:MM:00+05:30` (desk convention)

`+05:30`, genuine `...Z` timestamps and bare dates are already honest and are left alone.
Dry run by default; `--write` applies with safe_write. Idempotent: rows with `date_raw` are skipped.

    python3 scripts/migrations/m2026_09_proposals_dates.py --base-dir . [--write]
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from smith_core import load_json, safe_write  # noqa: E402

FAKE_MIDNIGHT = re.compile(r"^(\d{4}-\d{2}-\d{2})T00:00:00Z$")
NAIVE_MINUTE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})$")


def migrate_rows(rows):
    changed = {"fake_midnight": 0, "naive_minute": 0}
    for r in rows:
        if not isinstance(r, dict) or "date_raw" in r:
            continue
        d = str(r.get("date") or "")
        m = FAKE_MIDNIGHT.match(d)
        if m:
            r["date_raw"], r["date"] = d, m.group(1)
            changed["fake_midnight"] += 1
            continue
        m = NAIVE_MINUTE.match(d)
        if m:
            r["date_raw"], r["date"] = d, f"{m.group(1)}:00+05:30"
            changed["naive_minute"] += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=".")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    report = {}
    for name in ("proposals.json", "proposals-archive.json"):
        path = os.path.join(a.base_dir, name)
        store = load_json(path, default=None)
        if not isinstance(store, dict):
            report[name] = "absent"
            continue
        rows = store.get("proposals") or []
        report[name] = migrate_rows(rows)
        if a.write and any(report[name].values()):
            safe_write(path, store)
    print(json.dumps({"write": a.write, "changed": report}, indent=2))


if __name__ == "__main__":
    main()

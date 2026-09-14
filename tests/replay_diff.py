#!/usr/bin/env python3
"""Diff two replay outputs (tests/replay_run.sh) stage by stage, ignoring wall-clock noise.

Exit 0 when every compute_*.json matches after dropping volatile keys; otherwise print the
differing JSON paths per file (capped) and exit 1. A refactor phase must end with exit 0, or with
every remaining difference explained in its commit message."""
import json, os, sys

VOLATILE = {"as_of", "ts", "generated", "generated_at", "built_at", "fetched_at_utc", "now",
            "age_days", "age_hours", "run_dir", "latest_run_dir", "path", "written"}


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in VOLATILE:
                continue
            walk(a.get(k), b.get(k), f"{path}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif isinstance(a, str) and isinstance(b, str) and ("/" in a and "/" in b):
        pass  # absolute paths differ between scratch dirs by construction
    elif a != b:
        out.append(f"{path}: {json.dumps(a)[:80]} -> {json.dumps(b)[:80]}")


def compute_files(out_dir):
    runs = os.path.join(out_dir, "base", "runs")
    rd = os.path.join(runs, next(d for d in os.listdir(runs) if d.startswith("replay-")))
    return rd, sorted(f for f in os.listdir(rd) if f.startswith("compute_") and f.endswith(".json"))


def main(a_dir, b_dir):
    ra, fa = compute_files(a_dir)
    rb, fb = compute_files(b_dir)
    bad = 0
    for f in sorted(set(fa) | set(fb)):
        if f == "compute_freshness.json":
            continue  # ages against the wall clock by design
        if f not in fa or f not in fb:
            print(f"{f}: present only in {'A' if f in fa else 'B'}")
            bad += 1
            continue
        diffs = []
        walk(json.load(open(os.path.join(ra, f))), json.load(open(os.path.join(rb, f))), "$", diffs)
        if diffs:
            bad += 1
            print(f"{f}: {len(diffs)} difference(s)")
            for d in diffs[:12]:
                print("   ", d)
    print("REPLAY DIFF:", "identical" if not bad else f"{bad} file(s) differ")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

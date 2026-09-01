#!/bin/bash
# Golden-master check for smith_dashboard.py's build() refactoring. build() shells out to
# smith_charts.py (via a "scripts" symlink inside the fixture base dir) to render SVG charts,
# so the fixture is a full base-dir shape, not just a few JSON files. Byte-identical HTML
# output is the proof a refactor changed nothing behaviorally.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/smith_dashboard.py \
  --base-dir tests/fixtures/dashboard_case1/base \
  --out /tmp/dashboard_check.html > /tmp/dashboard_check_stdout.json 2>&1

if diff -q tests/golden/dashboard_case1.html /tmp/dashboard_check.html > /dev/null; then
  echo "PASS: build() output byte-identical to golden master"
else
  echo "FAIL: build() output CHANGED -- diff below"
  diff tests/golden/dashboard_case1.html /tmp/dashboard_check.html || true
  exit 1
fi

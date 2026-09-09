#!/bin/bash
# Golden-master check for scripts/smith_dashboard.py (v2).
#
# v2 emits a JSON payload plus a static client-side app rather than 35 hand-wired HTML string
# builders, so byte-identical output still means "this refactor changed nothing" -- but it now
# covers the payload too, which is where every panel's data actually comes from. A panel that
# silently stops being populated changes these bytes; under v1 it did not, which is how
# thirteen panels went missing without a single test noticing.
#
# Regenerate deliberately (never to make a red check go green):
#   python3 scripts/smith_dashboard.py --base-dir tests/fixtures/dashboard_case1/base \
#     --built-at GOLDEN --out tests/golden/dashboard_case1.html
set -euo pipefail
cd "$(dirname "$0")/.."
# --built-at is pinned: the masthead carries a build timestamp, and a stamp that moves every
# second would make this diff fail on every run and train everyone to ignore it.
python3 scripts/smith_dashboard.py \
  --base-dir tests/fixtures/dashboard_case1/base \
  --built-at "GOLDEN" \
  --out /tmp/dashboard_check.html > /tmp/dashboard_check_stdout.txt 2>&1

if diff -q tests/golden/dashboard_case1.html /tmp/dashboard_check.html > /dev/null; then
  echo "PASS: dashboard output byte-identical to golden master"
  cat /tmp/dashboard_check_stdout.txt
else
  echo "FAIL: dashboard output CHANGED -- panel counts below, then the diff"
  cat /tmp/dashboard_check_stdout.txt || true
  diff tests/golden/dashboard_case1.html /tmp/dashboard_check.html | head -40 || true
  exit 1
fi

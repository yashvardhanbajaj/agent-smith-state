#!/bin/bash
# Golden-master check for cmd_triggers refactoring. Run after every edit to
# smith_math.py's trigger-generation code -- byte-identical output is the
# proof a refactor changed nothing behaviorally.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/smith_math.py triggers \
  --base-dir tests/fixtures/triggers_case1/base \
  --run-dir tests/fixtures/triggers_case1/rundir \
  --today 2026-09-01 > /tmp/triggers_check.json 2>&1
if diff -q tests/golden/triggers_case1.json /tmp/triggers_check.json > /dev/null; then
  echo "PASS: cmd_triggers output byte-identical to golden master"
else
  echo "FAIL: cmd_triggers output CHANGED -- diff below"
  diff tests/golden/triggers_case1.json /tmp/triggers_check.json || true
  exit 1
fi

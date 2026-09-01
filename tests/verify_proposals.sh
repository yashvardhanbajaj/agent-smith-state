#!/bin/bash
# Golden-master check for cmd_proposals refactoring. cmd_proposals mutates proposals.json
# in place, so each check runs against a fresh scratch copy of the pristine fixture and
# diffs BOTH the stdout summary and the resulting proposals.json against golden output --
# byte-identical on both is the proof a refactor changed nothing behaviorally.
set -euo pipefail
cd "$(dirname "$0")/.."
SCRATCH=$(mktemp -d)
trap 'rm -rf "$SCRATCH"' EXIT
cp tests/fixtures/proposals_case1/base/proposals.json \
   tests/fixtures/proposals_case1/base/journal.json \
   tests/fixtures/proposals_case1/base/state.json \
   "$SCRATCH/"
python3 scripts/smith_math.py proposals \
  --base-dir "$SCRATCH" \
  --run-dir tests/fixtures/proposals_case1/rundir \
  --today 2026-09-01 > /tmp/proposals_check_stdout.json 2>&1

ok=1
if ! diff -q tests/golden/proposals_case1_stdout.json /tmp/proposals_check_stdout.json > /dev/null; then
  echo "FAIL: cmd_proposals stdout CHANGED -- diff below"
  diff tests/golden/proposals_case1_stdout.json /tmp/proposals_check_stdout.json || true
  ok=0
fi
if ! diff -q tests/golden/proposals_case1_result.json "$SCRATCH/proposals.json" > /dev/null; then
  echo "FAIL: cmd_proposals written proposals.json CHANGED -- diff below"
  diff tests/golden/proposals_case1_result.json "$SCRATCH/proposals.json" || true
  ok=0
fi
if [ "$ok" = "1" ]; then
  echo "PASS: cmd_proposals output (stdout + written proposals.json) byte-identical to golden master"
else
  exit 1
fi

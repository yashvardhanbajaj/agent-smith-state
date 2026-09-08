#!/bin/bash
# Golden-master check for cmd_ladder (added 2026-09-08). Same contract as verify_triggers.sh:
# cmd_ladder emits to stdout only and never writes, so a plain stdout diff is the whole test.
#
# The fixture is shaped around the cases that made this stage necessary:
#   AI Networking/Optics -- SMH ran +18%, so AVGO's +9% reads as -9pp against the benchmark
#     while it is comfortably ahead of its OWN cluster. This is the reordering the stage exists
#     for, and it is exactly the shape of the live 2026-09-07 cluster_rotation-AVGO-LITE pair.
#   AI Semis/Fabs -- wide dispersion, a redundant twin pair (AMAT/LRCX), and one member (KLAC)
#     absent from the return cache, so partial coverage is pinned too.
#   AI Power/Cooling/DC Infra -- a block move with a ladder already on file: no dispersion
#     points, no staleness points.
#   Compute/Hyperscaler OEM -- 2 names, below LADDER_MIN_MEMBERS, must be ineligible.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/smith_math.py ladder \
  --base-dir tests/fixtures/ladder_case1/base \
  --run-dir tests/fixtures/ladder_case1/rundir \
  --today 2026-09-08 > /tmp/ladder_check.json

if diff -q tests/golden/ladder_case1.json /tmp/ladder_check.json > /dev/null; then
  echo "PASS: cmd_ladder output byte-identical to golden master"
else
  echo "FAIL: cmd_ladder output CHANGED -- diff below"
  diff tests/golden/ladder_case1.json /tmp/ladder_check.json || true
  exit 1
fi

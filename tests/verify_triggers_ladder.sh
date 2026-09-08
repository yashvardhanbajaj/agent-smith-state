#!/bin/bash
# Golden-master check for the LADDER-DRIVEN path of cluster_rotation (added 2026-09-08).
#
# triggers_case1 has no cluster_ladders and therefore exercises only the price fallback -- which
# is exactly what proved the phase-3 rewire changed nothing on the old path, but leaves the new
# path with no end-to-end pin. This fixture is case1 plus two seeded ladders:
#   AI Networking/Optics  -- HIGH confidence, so the sell leg's `watch`-thesis requirement is
#     relaxed to "not strengthening". Modelled on the live 2026-09-07 shape: AVGO reads
#     worst-in-cluster against SMH (-13.31pp) while genuinely ahead of its own cluster, and an
#     open proposal was selling it on that reading.
#   AI Semis/Fabs -- MEDIUM confidence, so the ordering is used but the `watch` requirement stands.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/smith_math.py triggers \
  --base-dir tests/fixtures/triggers_case2_ladder/base \
  --run-dir tests/fixtures/triggers_case2_ladder/rundir \
  --today 2026-09-01 > /tmp/triggers_ladder_check.json

if diff -q tests/golden/triggers_case2_ladder.json /tmp/triggers_ladder_check.json > /dev/null; then
  echo "PASS: ladder-driven cluster_rotation byte-identical to golden master"
else
  echo "FAIL: ladder-driven cluster_rotation CHANGED -- diff below"
  diff tests/golden/triggers_case2_ladder.json /tmp/triggers_ladder_check.json || true
  exit 1
fi

#!/bin/bash
# Replay a recorded run's INPUTS through the current compute code, against a throwaway copy of the
# memory of record. Never touches the live base: SMITH_BASE_DIR points every default at the copy.
#
#   tests/replay_run.sh runs/2026-09-14-0104 [OUT_DIR]
#
# Prints OUT_DIR. Compare two replays (e.g. before/after a refactor) with:
#   python3 tests/replay_diff.py OUT_A OUT_B
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(pwd)
RUN=${1:?usage: replay_run.sh <run-dir> [out-dir]}
OUT=${2:-$(mktemp -d)}
BASE="$OUT/base"
LABEL=$(basename "$RUN")
RD="$BASE/runs/replay-$LABEL"
mkdir -p "$BASE" "$RD"

rsync -a --exclude .git --exclude runs --exclude archive --exclude standalone --exclude webapp \
      --exclude tests --exclude scripts --exclude '*.bak' --exclude '*.bak.*' --exclude .pytest_cache \
      ./ "$BASE/"
for f in holdings.json holdings_snapshot_raw.json live_quotes.json live_quotes_flat.json \
         market_inputs.json prices_all.json; do
  [ -f "$RUN/$f" ] && cp "$RUN/$f" "$RD/"
done

export SMITH_BASE_DIR="$BASE" SMITH_NO_SHARED_CACHE=1
TODAY=${LABEL:0:10}
python3 "$REPO/scripts/smith_math.py" pipeline --base-dir "$BASE" --run-dir "$RD" \
  --today "$TODAY" --lots "$BASE/lots.json" > "$OUT/pipeline.json" || true
python3 "$REPO/scripts/smith_math.py" validate --base-dir "$BASE" > "$OUT/validate.json" || true
echo "$OUT"

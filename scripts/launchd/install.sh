#!/bin/bash
# Install the Agent Smith health watchdog as a per-user LaunchAgent (weekdays 16:00 local).
#   scripts/launchd/install.sh [BASE_DIR] [PYTHON]
# Idempotent: re-running replaces the loaded job. Undo with scripts/launchd/uninstall.sh.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="${1:-$(cd "$HERE/../.." && pwd)}"
PY="${2:-$(command -v python3)}"
LABEL=com.agentsmith.health
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$HOME/Library/LaunchAgents"
sed -e "s#__BASE__#$BASE#g" -e "s#__PY__#$PY#g" "$HERE/$LABEL.plist.template" > "$DEST.tmp"
plutil -lint "$DEST.tmp" >/dev/null
mv "$DEST.tmp" "$DEST"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$DEST"
echo "installed $DEST (base=$BASE python=$PY)"
launchctl print "gui/$(id -u)/$LABEL" | grep -E "state|path" | head -3

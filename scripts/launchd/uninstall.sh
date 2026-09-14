#!/bin/bash
# Remove the Agent Smith health watchdog LaunchAgent. Its log (logs/health-watchdog.log) is kept.
set -euo pipefail
LABEL=com.agentsmith.health
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ -f "$DEST" ]; then
  mkdir -p "$HOME/Library/LaunchAgents/disabled"
  mv "$DEST" "$HOME/Library/LaunchAgents/disabled/$LABEL.plist"   # archive, never delete
fi
echo "uninstalled $LABEL"

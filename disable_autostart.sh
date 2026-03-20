#!/bin/bash

set -u

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LABELS=(
    "com.macmini.fastapi"
    "com.macmini.pericial"
    "com.sistema.pericial"
)

PLISTS=(
    "$LAUNCH_AGENTS_DIR/com.macmini.fastapi.plist"
    "$LAUNCH_AGENTS_DIR/com.macmini.pericial.plist"
    "$LAUNCH_AGENTS_DIR/sistema_pericial.plist"
)

for index in "${!LABELS[@]}"; do
    label="${LABELS[$index]}"
    plist="${PLISTS[$index]}"
    launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
    launchctl unload "$plist" 2>/dev/null || true
    launchctl disable "gui/$(id -u)/$label" 2>/dev/null || true
done

for plist in "${PLISTS[@]}"; do
    if [ -f "$plist" ] && [[ "$plist" != *.disabled ]]; then
        mv "$plist" "$plist.disabled" 2>/dev/null || true
    fi
done

echo "Autoarranque desactivado"

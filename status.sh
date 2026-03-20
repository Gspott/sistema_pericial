#!/bin/bash

set -u

APP_PORT=8000

PORT_UP="no"
CADDY_UP="no"
CAFFEINATE_UP="no"

if lsof -nP -iTCP:"$APP_PORT" -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; then
    PORT_UP="si"
fi

if pgrep -x caddy >/dev/null 2>&1; then
    CADDY_UP="si"
fi

if pgrep -x caffeinate >/dev/null 2>&1; then
    CAFFEINATE_UP="si"
fi

if [ "$PORT_UP" = "si" ] && [ "$CADDY_UP" = "si" ] && [ "$CAFFEINATE_UP" = "si" ]; then
    echo "RUNNING"
else
    echo "STOPPED"
fi

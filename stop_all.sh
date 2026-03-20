#!/bin/bash

set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

FASTAPI_PID_FILE="$PROJECT_DIR/logs/uvicorn.pid"
CADDY_PID_FILE="$PROJECT_DIR/logs/caddy.pid"
CAFFEINATE_PID_FILE="$PROJECT_DIR/logs/caffeinate.pid"

stop_pid_file() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid
        pid="$(cat "$pid_file" 2>/dev/null || true)"
        if [ -n "${pid:-}" ]; then
            kill "$pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
    fi
}

stop_pid_file "$FASTAPI_PID_FILE"
stop_pid_file "$CADDY_PID_FILE"
stop_pid_file "$CAFFEINATE_PID_FILE"

pkill -f '[u]vicorn' 2>/dev/null || true
pkill -f '[c]addy run --config .*/deploy/Caddyfile' 2>/dev/null || true
pkill -f '[c]affeinate -d -i -m' 2>/dev/null || true

rm -f "$FASTAPI_PID_FILE" "$CADDY_PID_FILE" "$CAFFEINATE_PID_FILE"

echo "Estado final: STOPPED"

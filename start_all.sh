#!/bin/bash

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

mkdir -p logs

FASTAPI_PID_FILE="$PROJECT_DIR/logs/uvicorn.pid"
CADDY_PID_FILE="$PROJECT_DIR/logs/caddy.pid"
CAFFEINATE_PID_FILE="$PROJECT_DIR/logs/caffeinate.pid"
FASTAPI_LOG="$PROJECT_DIR/logs/fastapi.log"
CADDY_LOG="$PROJECT_DIR/logs/caddy.log"

APP_PORT="${APP_PORT:-${PORT:-8000}}"
CADDY_BIN="${CADDY_BIN:-$(command -v caddy || true)}"
CAFFEINATE_BIN="${CAFFEINATE_BIN:-$(command -v caffeinate || true)}"

echo "PROJECT_DIR=$PROJECT_DIR"
echo "PATH=$PATH"

kill_pid_file() {
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

kill_pid_file "$CADDY_PID_FILE"
kill_pid_file "$CAFFEINATE_PID_FILE"

pkill -f '[u]vicorn' 2>/dev/null || true
pkill -f '[c]addy run --config .*/deploy/Caddyfile' 2>/dev/null || true
pkill -f '[c]affeinate -d -i -m' 2>/dev/null || true

sleep 1

if [ "$APP_PORT" != "8000" ]; then
    echo "APP_PORT=$APP_PORT no es compatible con deploy/Caddyfile (127.0.0.1:8000)."
    exit 1
fi

"$PROJECT_DIR/scripts/update_duckdns.sh" >> "$PROJECT_DIR/logs/duckdns.log" 2>&1 || true

SKIP_DUCKDNS_UPDATE=1 "$PROJECT_DIR/start_server.sh"

sleep 3

if [ -z "$CADDY_BIN" ]; then
    echo "No se encontró el binario de caddy."
    exit 1
fi

if [ -z "$CAFFEINATE_BIN" ]; then
    echo "No se encontró el binario de caffeinate."
    exit 1
fi

nohup "$CADDY_BIN" run --config "$PROJECT_DIR/deploy/Caddyfile" >> "$CADDY_LOG" 2>&1 &
echo "$!" > "$CADDY_PID_FILE"

nohup "$CAFFEINATE_BIN" -d -i -m >> "$PROJECT_DIR/logs/caffeinate.log" 2>&1 &
echo "$!" > "$CAFFEINATE_PID_FILE"

if ! lsof -nP -iTCP:"$APP_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "FastAPI no está escuchando en el puerto $APP_PORT."
    exit 1
fi

echo "Estado final: RUNNING"
echo "FastAPI PID: $(cat "$FASTAPI_PID_FILE" 2>/dev/null || echo '-')"
echo "Caddy PID: $(cat "$CADDY_PID_FILE" 2>/dev/null || echo '-')"
echo "Caffeinate PID: $(cat "$CAFFEINATE_PID_FILE" 2>/dev/null || echo '-')"

#!/bin/bash

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
ARCH_LOG="$PROJECT_DIR/logs/startup_arch.log"
ARM64_CAPABLE="$(sysctl -in hw.optional.arm64 2>/dev/null || echo 0)"
PROC_TRANSLATED="$(sysctl -in sysctl.proc_translated 2>/dev/null || echo 0)"
CURRENT_ARCH="$(arch)"

if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if [ ! -d ".venv" ]; then
    echo "No existe .venv en $PROJECT_DIR"
    exit 1
fi

mkdir -p logs

VENV_PY="/Users/carlosblanco/sistema_pericial/.venv/bin/python"
PID_FILE="$PROJECT_DIR/logs/uvicorn.pid"
LOG_FILE="$PROJECT_DIR/logs/fastapi.log"

APP_HOST="${APP_HOST:-${HOST:-0.0.0.0}}"
APP_PORT="${APP_PORT:-${PORT:-8000}}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${APP_PORT}}"

if [ -x /usr/bin/arch ] && [ "$ARM64_CAPABLE" = "1" ] && { [ "$PROC_TRANSLATED" = "1" ] || [ "$CURRENT_ARCH" != "arm64" ]; } && [ "${FORCED_ARM64:-0}" != "1" ]; then
    echo "Re-launching start_server.sh under arm64: /usr/bin/arch -arm64 /bin/bash $0 $*" >> "$ARCH_LOG"
    exec env FORCED_ARM64=1 /usr/bin/arch -arm64 /bin/bash "$0" "$@"
fi

{
    echo "=== start_server.sh ==="
    echo "hw.optional.arm64: $ARM64_CAPABLE"
    echo "sysctl.proc_translated: $PROC_TRANSLATED"
    echo "uname -m: $(uname -m)"
    echo "arch: $CURRENT_ARCH"
    echo "python: $VENV_PY"
    file "$VENV_PY" || true
} >> "$ARCH_LOG" 2>&1

if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ -n "${OLD_PID:-}" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        if curl -fsS "http://127.0.0.1:${APP_PORT}/ping" >/dev/null 2>&1; then
            echo "Servidor ya activo con PID $OLD_PID"
            exit 0
        fi
        kill "$OLD_PID" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$PID_FILE"
fi

if pgrep -f "$VENV_PY -m uvicorn main:app" >/dev/null 2>&1; then
    pkill -f "$VENV_PY -m uvicorn main:app" || true
    sleep 1
fi

echo "Arrancando FastAPI en ${APP_HOST}:${APP_PORT}"
nohup "$VENV_PY" -m uvicorn main:app \
    --host "$APP_HOST" \
    --port "$APP_PORT" \
    >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

READY="no"
for _ in $(seq 1 20); do
    if curl -fsS "http://127.0.0.1:${APP_PORT}/ping" >/dev/null 2>&1; then
        READY="si"
        break
    fi
    sleep 1
done

if [ "$READY" != "si" ]; then
    echo "El servidor no respondió correctamente. Revisa $LOG_FILE"
    exit 1
fi

if [ "${SKIP_DUCKDNS_UPDATE:-0}" != "1" ] && [ -x "$PROJECT_DIR/scripts/update_duckdns.sh" ]; then
    nohup "$PROJECT_DIR/scripts/update_duckdns.sh" >> "$PROJECT_DIR/logs/duckdns.log" 2>&1 || true &
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"

echo "Servidor funcionando con PID $SERVER_PID"
echo "Local: http://127.0.0.1:${APP_PORT}"
if [ -n "$LAN_IP" ]; then
    echo "Red local: http://${LAN_IP}:${APP_PORT}"
fi
echo "Base URL: ${BASE_URL}"

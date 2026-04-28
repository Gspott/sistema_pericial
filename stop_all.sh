#!/bin/bash

set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

validate_env_file() {
    local env_file="$1"
    local line

    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ""|\#*) continue ;;
        esac

        if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*=.*[[:space:]].* ]] \
            && [[ ! "$line" =~ =\" ]] \
            && [[ ! "$line" =~ =\' ]]; then
            echo "Posible valor con espacios sin comillas en .env: $line" >&2
            echo "Usa comillas en valores con espacios, por ejemplo: SMTP_FROM_NAME=\"Carlos Blanco\"" >&2
            return 1
        fi
    done < "$env_file"
}

if [ -f ".env" ]; then
    if ! validate_env_file ".env"; then
        exit 1
    fi
    set -a
    if ! . ./.env; then
        set +a
        echo "Error cargando .env. Revisa comillas en valores con espacios." >&2
        exit 1
    fi
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

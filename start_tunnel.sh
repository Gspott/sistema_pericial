#!/bin/bash

set -e

cd "$(dirname "$0")"

if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

mkdir -p logs

CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-/opt/homebrew/bin/cloudflared}"
PORT="${PORT:-8000}"

nohup "$CLOUDFLARED_BIN" tunnel --url "http://127.0.0.1:${PORT}" > logs/cloudflared.log 2>&1 &
echo $! > logs/cloudflared.pid

echo "Túnel iniciado hacia el puerto ${PORT}"

#!/bin/bash

set -e

cd "$(dirname "$0")"

if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

mkdir -p logs

if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

nohup python -m uvicorn main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" > logs/fastapi.log 2>&1 &
echo $! > logs/fastapi.pid

echo "Servidor iniciado en puerto ${PORT:-8000}"

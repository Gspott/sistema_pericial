#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "Directorio del proyecto: $PROJECT_DIR"

# activar entorno virtual
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "No existe .venv"
    exit 1
fi

UVICORN_BIN="$PROJECT_DIR/.venv/bin/uvicorn"

echo "Matando servidores antiguos..."
pkill -f "uvicorn main:app"
pkill -f "python -m uvicorn"

sleep 2

echo "Arrancando servidor FastAPI..."

"$UVICORN_BIN" main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > fastapi.log 2>&1 &

SERVER_PID=$!

echo "Servidor iniciado con PID $SERVER_PID"

sleep 3

echo "Comprobando servidor..."

if curl -fsS http://127.0.0.1:8000/ping >/dev/null 2>&1; then
    echo "Servidor funcionando correctamente"
else
    echo "El servidor no respondió correctamente"
fi

echo ""
echo "Servidor disponible en:"
echo "http://127.0.0.1:8000"
echo "http://$(ipconfig getifaddr en0):8000"
echo ""

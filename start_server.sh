#!/bin/zsh

TOKEN="8699636159:AAEz3jWqiCDnactyICJdLQVwEEd_rEjkWN8"
CHAT_ID="477674266"
PROJECT_DIR="/Users/carlosblanco/sistema_pericial"
UVICORN_BIN="$PROJECT_DIR/.venv/bin/uvicorn"
CLOUDFLARED_BIN="/opt/homebrew/bin/cloudflared"

cd "$PROJECT_DIR" || exit 1

echo "=== Inicio $(date) ===" >> startup.log

: > fastapi.log
: > cloudflared.log

pkill -f "$UVICORN_BIN main:app --host 127.0.0.1 --port 8000" 2>/dev/null
pkill -f "$CLOUDFLARED_BIN tunnel --url http://localhost:8000" 2>/dev/null

sleep 2

echo "Arrancando servidor FastAPI..." | tee -a startup.log
"$UVICORN_BIN" main:app --host 127.0.0.1 --port 8000 > fastapi.log 2>&1 &

READY="no"
for i in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/ping >/dev/null 2>&1; then
    READY="si"
    break
  fi
  sleep 1
done

if [ "$READY" != "si" ]; then
  echo "FastAPI no respondió a tiempo" | tee -a startup.log
  exit 1
fi

echo "FastAPI listo" | tee -a startup.log
echo "Creando túnel Cloudflare..." | tee -a startup.log
"$CLOUDFLARED_BIN" tunnel --url http://localhost:8000 > cloudflared.log 2>&1 &

URL=""
for i in {1..45}; do
  URL=$(grep -Eo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' cloudflared.log | head -n 1)
  if [ -n "$URL" ]; then
    break
  fi
  sleep 1
done

echo "URL detectada: $URL" | tee -a startup.log

PUBLIC_OK="no"
if [ -n "$URL" ]; then
  for i in {1..60}; do
    if curl -kfsS "$URL/ping" >/dev/null 2>&1; then
      PUBLIC_OK="si"
      break
    fi
    sleep 2
  done
fi

if [ "$PUBLIC_OK" = "si" ]; then
  curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d text="🟢 Servidor pericial activo
$URL" >> startup.log 2>&1
  echo "Telegram enviado" | tee -a startup.log
else
  echo "La URL pública todavía no responde; no se envía Telegram" | tee -a startup.log
  exit 1
fi

echo "Arranque completado" | tee -a startup.log

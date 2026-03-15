#!/bin/zsh

TOKEN="8699636159:AAEz3jWqiCDnactyICJdLQVwEEd_rEjkWN8"
CHAT_ID="477674266"
PROJECT="/Users/carlosblanco/sistema_pericial"
CLOUDFLARED="/opt/homebrew/bin/cloudflared"
FASTAPI_PLIST="/Users/carlosblanco/Library/LaunchAgents/com.macmini.fastapi.plist"
UID_NUM=$(id -u)

cd "$PROJECT" || exit 1

send_msg() {
  curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d text="$1" >/dev/null
}

# 1. Arrancar FastAPI usando launchctl
launchctl bootstrap "gui/$UID_NUM" "$FASTAPI_PLIST" 2>/dev/null
launchctl enable "gui/$UID_NUM/com.macmini.fastapi" 2>/dev/null
launchctl kickstart -k "gui/$UID_NUM/com.macmini.fastapi" 2>/dev/null

# 2. Esperar a que FastAPI responda
READY="no"
for i in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/ping >/dev/null 2>&1; then
    READY="si"
    break
  fi
  sleep 1
done

if [ "$READY" != "si" ]; then
  send_msg "❌ FastAPI no ha arrancado"
  exit 1
fi

# 3. Cerrar túnel anterior
pkill -f "cloudflared tunnel --url http://127.0.0.1:8000" 2>/dev/null
sleep 2

# 4. Crear túnel nuevo apuntando a 127.0.0.1
: > "$PROJECT/cloudflared.log"
nohup "$CLOUDFLARED" tunnel --url http://127.0.0.1:8000 > "$PROJECT/cloudflared.log" 2>&1 &

URL=""
for i in {1..60}; do
  URL=$(grep -Eo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$PROJECT/cloudflared.log" | tail -n 1)
  if [ -n "$URL" ]; then
    break
  fi
  sleep 1
done

if [ -z "$URL" ]; then
  send_msg "❌ No se pudo crear el túnel"
  exit 1
fi

# 5. Esperar a que la URL pública responda
PUBLIC_OK="no"
for i in {1..20}; do
  if curl -kfsS "$URL/ping" >/dev/null 2>&1; then
    PUBLIC_OK="si"
    break
  fi
  sleep 2
done

if [ "$PUBLIC_OK" = "si" ]; then
  send_msg "🟢 Servidor pericial activo
$URL"
else
  send_msg "🟡 Túnel creado. Si tarda unos segundos en abrir, vuelve a tocar el enlace.
$URL"
fi

#!/bin/zsh

TOKEN="8699636159:AAEz3jWqiCDnactyICJdLQVwEEd_rEjkWN8"
CHAT_ID="477674266"

cd /Users/carlosblanco/sistema_pericial || exit 1

pkill -f "cloudflared tunnel --url http://localhost:8000" 2>/dev/null
: > cloudflared.log

/opt/homebrew/bin/cloudflared tunnel --url http://localhost:8000 > cloudflared.log 2>&1 &

URL=""
for i in {1..60}; do
  URL=$(grep -Eo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' cloudflared.log | head -n 1)
  if [ -n "$URL" ]; then
    break
  fi
  sleep 1
done

if [ -n "$URL" ]; then
  curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d text="🟢 Túnel pericial activo
$URL"
  echo "$URL"
else
  echo "No se pudo obtener la URL del túnel"
fi

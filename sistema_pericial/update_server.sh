#!/bin/zsh

PROJECT="/Users/carlosblanco/sistema_pericial"

TOKEN="8699636159:AAEz3jWqiCDnactyICJdLQVwEEd_rEjkWN8"
CHAT_ID="477674266"

send_msg() {
curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
-d chat_id="$CHAT_ID" \
-d text="$1" >/dev/null
}

cd "$PROJECT" || exit 1

send_msg "🔄 Actualizando servidor desde GitHub..."

git pull

# reiniciar FastAPI
pkill -f uvicorn
sleep 2

launchctl kickstart -k gui/$(id -u)/com.macmini.fastapi

send_msg "✅ Servidor actualizado"

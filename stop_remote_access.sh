#!/bin/zsh

TOKEN="8699636159:AAEz3jWqiCDnactyICJdLQVwEEd_rEjkWN8"
CHAT_ID="477674266"

send_msg() {
curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
-d chat_id="$CHAT_ID" \
-d text="$1" >/dev/null
}

# cerrar túnel
pkill -f cloudflared 2>/dev/null

send_msg "🔴 Acceso remoto cerrado"

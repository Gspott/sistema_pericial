#!/bin/zsh

set -eu

PROJECT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT" || exit 1

if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

TOKEN="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"

send_msg() {
if [ -z "$TOKEN" ] || [ -z "$CHAT_ID" ]; then
  return 0
fi
curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
  -d chat_id="$CHAT_ID" \
  -d text="$1" >/dev/null
}

send_msg "🔄 Actualizando servidor desde GitHub..."

git pull

./start_server.sh

send_msg "✅ Servidor actualizado"

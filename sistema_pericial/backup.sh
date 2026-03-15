#!/bin/zsh

PROJECT="/Users/carlosblanco/sistema_pericial"
BACKUP_DIR="$PROJECT/backups"

TOKEN="8699636159:AAEz3jWqiCDnactyICJdLQVwEEd_rEjkWN8TU_TOKEN"
CHAT_ID="477674266"

DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

cd "$PROJECT" || exit 1

tar -czf "$BACKUP_FILE" \
pericial.db \
uploads \
templates \
app \
requirements.txt \
main.py 2>/dev/null

curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
-d chat_id="$CHAT_ID" \
-d text="💾 Backup creado:
$BACKUP_FILE" >/dev/null

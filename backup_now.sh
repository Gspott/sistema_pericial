#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${0:A:h}"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/backup.log"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
else
    PYTHON_BIN="${PYTHON:-python3}"
fi

{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup manual"
    "$PYTHON_BIN" - <<'PY'
from app.config import BACKUPS_DIR, ensure_directories
from app.services.backups import crear_backup_zip

ensure_directories()
ruta_backup = crear_backup_zip()
print(f"Backup creado: {ruta_backup}")
print(f"Directorio de backups: {BACKUPS_DIR}")
PY
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup manual completado"
} >> "$LOG_FILE" 2>&1

tail -n 3 "$LOG_FILE"

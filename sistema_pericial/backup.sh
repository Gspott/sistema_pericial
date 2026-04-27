#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

exec "$PROJECT_DIR/backup_now.sh"

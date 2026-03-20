#!/bin/bash

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
LOG_FILE="$PROJECT_DIR/logs/startup_arch.log"
VENV_PY="/Users/carlosblanco/sistema_pericial/.venv/bin/python"
mkdir -p "$PROJECT_DIR/logs"
ARM64_CAPABLE="$(sysctl -in hw.optional.arm64 2>/dev/null || echo 0)"
PROC_TRANSLATED="$(sysctl -in sysctl.proc_translated 2>/dev/null || echo 0)"
CURRENT_ARCH="$(arch)"

if [ -x /usr/bin/arch ] && [ "$ARM64_CAPABLE" = "1" ] && { [ "$PROC_TRANSLATED" = "1" ] || [ "$CURRENT_ARCH" != "arm64" ]; } && [ "${FORCED_ARM64:-0}" != "1" ]; then
    echo "Re-launching run_app.sh under arm64: /usr/bin/arch -arm64 /bin/bash $0 $*" >> "$LOG_FILE"
    exec env FORCED_ARM64=1 /usr/bin/arch -arm64 /bin/bash "$0" "$@"
fi

{
    echo "=== run_app.sh ==="
    echo "hw.optional.arm64: $ARM64_CAPABLE"
    echo "sysctl.proc_translated: $PROC_TRANSLATED"
    echo "uname -m: $(uname -m)"
    echo "arch: $CURRENT_ARCH"
    echo "python: $VENV_PY"
    file "$VENV_PY" || true
} >> "$LOG_FILE" 2>&1

exec "$VENV_PY" "$PROJECT_DIR/control_app.py"

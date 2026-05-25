#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CLOSE_PLAN=""
if [ "$#" -gt 0 ]; then
    case "${1:-}" in
        --close-plan)
            if [ "$#" -ne 2 ]; then
                printf '[FAIL] Uso: %s --close-plan NOMBRE.md\n' "$0" >&2
                exit 2
            fi
            CLOSE_PLAN="$2"
            ;;
        *)
            printf '[FAIL] Opcion no reconocida: %s\n' "$1" >&2
            exit 2
            ;;
    esac
fi

step() {
    printf '\n[STEP] %s\n' "$1"
}

ok() {
    printf '[OK] %s\n' "$1"
}

fail() {
    printf '[FAIL] %s\n' "$1" >&2
}

skip() {
    printf '[SKIP] %s\n' "$1"
}

run_step() {
    local label="$1"
    shift
    step "$label"
    if "$@"; then
        ok "$label"
    else
        fail "$label"
        exit 1
    fi
}

run_step "Harness directory exists" test -d docs/harness
run_step "Documentation audit" python3 scripts/audit_docs.py
run_step "Compile app" python3 -m compileall app
run_step "Compile tests" python3 -m compileall tests
run_step "Check app shell JS" node --check static/app_shell.js
run_step "Check PWA JS" node --check static/pwa.js
run_step "Check service worker JS" node --check static/sw.js

PYTEST_PYTHON="python3"
if ! "$PYTEST_PYTHON" -m pytest --version >/dev/null 2>&1 && [ -x ".venv/bin/python" ]; then
    PYTEST_PYTHON=".venv/bin/python"
fi

if "$PYTEST_PYTHON" -m pytest --version >/dev/null 2>&1; then
    run_step "Smoke tests" "$PYTEST_PYTHON" -m pytest tests/smoke -q
else
    skip "Smoke tests: pytest is not installed for python3. Install requirements to enable: pip install -r requirements.txt"
fi

run_step "Diff whitespace check" git diff --check

if [ -n "$CLOSE_PLAN" ]; then
    run_step "Close harness plan" python3 scripts/harness_close_plan.py "$CLOSE_PLAN"
    run_step "Update harness metrics" python3 scripts/harness_metrics.py
fi

printf '\n[OK] Harness validation finished\n'

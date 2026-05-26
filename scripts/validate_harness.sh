#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CLOSE_PLAN=""
SMOKE_SCOPE="full"
ALLOW_UNSAFE_SCOPE="false"

usage() {
    printf 'Uso: %s [--smoke-scope docs|app|valoracion|full] [--allow-unsafe-scope] [--close-plan NOMBRE.md]\n' "$0" >&2
}

while [ "$#" -gt 0 ]; do
    case "${1:-}" in
        --close-plan)
            if [ "$#" -lt 2 ]; then
                usage
                exit 2
            fi
            CLOSE_PLAN="$2"
            shift 2
            ;;
        --smoke-scope)
            if [ "$#" -lt 2 ]; then
                usage
                exit 2
            fi
            SMOKE_SCOPE="$2"
            shift 2
            ;;
        --allow-unsafe-scope)
            ALLOW_UNSAFE_SCOPE="true"
            shift
            ;;
        *)
            printf '[FAIL] Opcion no reconocida: %s\n' "$1" >&2
            usage
            exit 2
            ;;
    esac
done

case "$SMOKE_SCOPE" in
    docs|app|valoracion|full)
        ;;
    *)
        printf '[FAIL] Smoke scope no reconocido: %s\n' "$SMOKE_SCOPE" >&2
        usage
        exit 2
        ;;
esac

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

RESOLVER_ARGS=(--requested-scope "$SMOKE_SCOPE")
if [ "$ALLOW_UNSAFE_SCOPE" = "true" ]; then
    RESOLVER_ARGS+=(--allow-unsafe-scope)
fi
step "Resolve smoke scope"
python3 scripts/harness_scope_resolver.py "${RESOLVER_ARGS[@]}"
RESOLVED_SCOPE_OUTPUT="$(python3 scripts/harness_scope_resolver.py "${RESOLVER_ARGS[@]}" --format shell)"
eval "$RESOLVED_SCOPE_OUTPUT"
SMOKE_SCOPE="$EFFECTIVE_SCOPE"
if [ "${UNSAFE_OVERRIDE:-0}" = "1" ]; then
    printf '[WARN] Unsafe scope override active. required_scope=%s requested_scope=%s\n' "$REQUIRED_SCOPE" "$REQUESTED_SCOPE" >&2
fi
ok "Resolve smoke scope"

run_step "Harness directory exists" test -d docs/harness
run_step "Documentation audit" python3 scripts/audit_docs.py

if [ "$SMOKE_SCOPE" = "docs" ]; then
    skip "Compile app: docs scope"
    skip "Compile tests: docs scope"
    skip "JavaScript checks: docs scope"
else
    run_step "Compile app" python3 -m compileall app
    run_step "Compile tests" python3 -m compileall tests
    run_step "Check app shell JS" node --check static/app_shell.js
    run_step "Check PWA JS" node --check static/pwa.js
    run_step "Check service worker JS" node --check static/sw.js
fi

PYTEST_PYTHON="python3"
if ! "$PYTEST_PYTHON" -m pytest --version >/dev/null 2>&1 && [ -x ".venv/bin/python" ]; then
    PYTEST_PYTHON=".venv/bin/python"
fi

if [ "$SMOKE_SCOPE" = "docs" ]; then
    skip "Smoke tests: docs scope"
elif [ "$SMOKE_SCOPE" = "app" ]; then
    skip "Smoke tests: app scope"
elif "$PYTEST_PYTHON" -m pytest --version >/dev/null 2>&1; then
    case "$SMOKE_SCOPE" in
        valoracion)
            run_step "Smoke tests (valoracion)" "$PYTEST_PYTHON" -m pytest tests/smoke -q -k valoracion
            ;;
        full)
            run_step "Smoke tests" "$PYTEST_PYTHON" -m pytest tests/smoke -q
            ;;
    esac
else
    skip "Smoke tests: pytest is not installed for python3. Install requirements to enable: pip install -r requirements.txt"
fi

run_step "Diff whitespace check" git diff --check

PLAN_TO_CLOSE="$CLOSE_PLAN"
AUTO_CLOSE="false"
if [ -z "$PLAN_TO_CLOSE" ] && [ -f "docs/harness/STATE/current_plan.txt" ]; then
    PLAN_TO_CLOSE="$(tr -d '[:space:]' < docs/harness/STATE/current_plan.txt)"
    AUTO_CLOSE="true"
fi

if [ -n "$PLAN_TO_CLOSE" ]; then
    case "$PLAN_TO_CLOSE" in
        docs/harness/PLANS/active/*.md)
            PLAN_TO_CLOSE="${PLAN_TO_CLOSE##*/}"
            ;;
        */*)
            fail "Plan activo no reconocido: $PLAN_TO_CLOSE"
            printf '       Crea un plan con: bash scripts/start_harness_task.sh SLUG TASK_PACK\n' >&2
            exit 1
            ;;
    esac
fi

WORKTREE_DIRTY="false"
if [ -n "$(git status --porcelain)" ]; then
    WORKTREE_DIRTY="true"
fi

if [ -n "$PLAN_TO_CLOSE" ]; then
    if [ -f "docs/harness/PLANS/active/$PLAN_TO_CLOSE" ]; then
        run_step "Close harness plan" python3 scripts/harness_close_plan.py "$PLAN_TO_CLOSE"
        run_step "Update harness metrics" python3 scripts/harness_metrics.py
        if [ "$AUTO_CLOSE" = "true" ]; then
            ok "Active plan closed automatically"
        fi
    elif [ "$AUTO_CLOSE" = "true" ]; then
        if [ "$WORKTREE_DIRTY" = "true" ]; then
            fail "Cambios detectados pero current_plan.txt no apunta a un plan activo cerrable ($PLAN_TO_CLOSE)"
            printf '       Crea un plan con: bash scripts/start_harness_task.sh SLUG TASK_PACK\n' >&2
            exit 1
        fi
        skip "Automatic plan close: active plan not found ($PLAN_TO_CLOSE)"
    else
        fail "Plan not found in active: $PLAN_TO_CLOSE"
        exit 1
    fi
else
    if [ "$WORKTREE_DIRTY" = "true" ]; then
        fail "Cambios detectados sin plan activo en docs/harness/STATE/current_plan.txt"
        printf '       Crea un plan con: bash scripts/start_harness_task.sh SLUG TASK_PACK\n' >&2
        exit 1
    fi
    skip "Automatic plan close: no current plan"
fi

printf '\n[OK] Harness validation finished\n'

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CURRENT_PLAN_PATH="docs/harness/STATE/current_plan.txt"
ACTIVE_DIR="docs/harness/PLANS/active"
VALIDATE_ARGS=()
HAS_VALIDATE_ARGS="false"

usage() {
    printf 'Uso: %s [--smoke-scope docs|app|valoracion|full] [--allow-unsafe-scope]\n' "$0" >&2
}

while [ "$#" -gt 0 ]; do
    case "${1:-}" in
        --smoke-scope)
            if [ "$#" -lt 2 ]; then
                usage
                exit 2
            fi
            VALIDATE_ARGS+=(--smoke-scope "$2")
            HAS_VALIDATE_ARGS="true"
            shift 2
            ;;
        --allow-unsafe-scope)
            VALIDATE_ARGS+=(--allow-unsafe-scope)
            HAS_VALIDATE_ARGS="true"
            shift
            ;;
        *)
            printf '[FAIL] Opcion no reconocida: %s\n' "$1" >&2
            usage
            exit 2
            ;;
    esac
done

if [ ! -f "$CURRENT_PLAN_PATH" ]; then
    printf '[FAIL] Falta %s\n' "$CURRENT_PLAN_PATH" >&2
    printf '       Crea un plan con: bash scripts/start_harness_task.sh SLUG TASK_PACK\n' >&2
    exit 1
fi

CURRENT="$(tr -d '[:space:]' < "$CURRENT_PLAN_PATH")"
if [ -z "$CURRENT" ]; then
    printf '[FAIL] No hay plan activo en %s\n' "$CURRENT_PLAN_PATH" >&2
    printf '       Crea un plan con: bash scripts/start_harness_task.sh SLUG TASK_PACK\n' >&2
    exit 1
fi

case "$CURRENT" in
    "$ACTIVE_DIR"/*.md)
        ACTIVE_PLAN_PATH="$CURRENT"
        ;;
    *.md)
        ACTIVE_PLAN_PATH="$ACTIVE_DIR/$CURRENT"
        ;;
    *)
        printf '[FAIL] Plan activo no reconocido: %s\n' "$CURRENT" >&2
        printf '       Debe ser %s/<plan>.md o <plan>.md\n' "$ACTIVE_DIR" >&2
        exit 1
        ;;
esac

if [ ! -f "$ACTIVE_PLAN_PATH" ]; then
    printf '[FAIL] El plan activo no existe: %s\n' "$ACTIVE_PLAN_PATH" >&2
    printf '       Corrige current_plan.txt o crea uno con: bash scripts/start_harness_task.sh SLUG TASK_PACK\n' >&2
    exit 1
fi

if [ "$HAS_VALIDATE_ARGS" = "true" ]; then
    bash scripts/validate_harness.sh "${VALIDATE_ARGS[@]}"
else
    bash scripts/validate_harness.sh
fi

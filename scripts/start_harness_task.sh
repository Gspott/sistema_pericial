#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

FORCE="false"
if [ "${1:-}" = "--force" ]; then
    FORCE="true"
    shift
fi

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    printf '[FAIL] Uso: %s [--force] SLUG_O_TITULO [TASK_PACK]\n' "$0" >&2
    exit 2
fi

RAW_SLUG="$1"
TASK_PACK="${2:-}"
CURRENT_PLAN_PATH="docs/harness/STATE/current_plan.txt"
ACTIVE_DIR="docs/harness/PLANS/active"

normalize_slug() {
    python3 - "$1" <<'PY'
import re
import sys

slug = sys.argv[1].strip().lower()
slug = re.sub(r"[^a-z0-9._-]+", "-", slug)
slug = slug.strip("-")
if slug.endswith(".md"):
    slug = slug[:-3]
if not slug or slug in {".", ".."} or "/" in slug or "\\" in slug:
    print("[FAIL] Slug no permitido", file=sys.stderr)
    raise SystemExit(2)
print(slug)
PY
}

current_plan_value() {
    if [ -f "$CURRENT_PLAN_PATH" ]; then
        tr -d '[:space:]' < "$CURRENT_PLAN_PATH"
    fi
}

current_plan_active_path() {
    local current="$1"
    if [ -z "$current" ]; then
        return 0
    fi
    case "$current" in
        "$ACTIVE_DIR"/*.md)
            printf '%s\n' "$current"
            ;;
        *.md)
            printf '%s/%s\n' "$ACTIVE_DIR" "$current"
            ;;
        *)
            printf '%s\n' "$current"
            ;;
    esac
}

SLUG="$(normalize_slug "$RAW_SLUG")"
PLAN_NAME="$SLUG.md"
PLAN_PATH="$ACTIVE_DIR/$PLAN_NAME"

CURRENT="$(current_plan_value)"
CURRENT_ACTIVE_PATH="$(current_plan_active_path "$CURRENT")"
if [ -n "$CURRENT" ] && [ -f "$CURRENT_ACTIVE_PATH" ] && [ "$FORCE" != "true" ]; then
    printf '[FAIL] Ya hay plan activo: %s\n' "$CURRENT_ACTIVE_PATH" >&2
    printf '       Cierra la tarea con: bash scripts/finish_harness_task.sh\n' >&2
    printf '       O usa --force para cambiar el plan activo conscientemente.\n' >&2
    exit 1
fi

if [ -f "$PLAN_PATH" ]; then
    if [ "$FORCE" != "true" ]; then
        printf '[FAIL] Ya existe: %s\n' "$PLAN_PATH" >&2
        printf '       Usa otro slug o --force para apuntar current_plan.txt a este plan.\n' >&2
        exit 1
    fi
    mkdir -p "$(dirname "$CURRENT_PLAN_PATH")"
    printf '%s\n' "$PLAN_PATH" > "$CURRENT_PLAN_PATH"
    printf '%s\n' "$PLAN_PATH"
    printf '[OK] Current active plan: %s\n' "$PLAN_PATH"
    exit 0
fi

if [ -n "$TASK_PACK" ]; then
    python3 scripts/harness_new_plan.py "$SLUG" "$TASK_PACK" >/dev/null
else
    python3 scripts/harness_new_plan.py "$SLUG" >/dev/null
fi

printf '%s\n' "$PLAN_PATH" > "$CURRENT_PLAN_PATH"
printf '%s\n' "$PLAN_PATH"
printf '[OK] Current active plan: %s\n' "$PLAN_PATH"

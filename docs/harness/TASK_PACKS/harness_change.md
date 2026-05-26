# Task Pack: Harness Change

## Cuando usarlo

Para cambios en wrappers, validadores, planes, metricas, task packs, policies o
documentacion operativa del harness.

## Cuando NO usarlo

No usar para cambios funcionales de negocio salvo que el objetivo principal sea
modificar el harness.

## Riesgo base

Medio.

Sube a Alto si cambia cierre de planes, politica de ejecucion, validaciones o
comandos que pueden ocultar fallos.

## Reglas de seguridad

- Mantener `python3 scripts/audit_docs.py` obligatorio en todos los scopes.
- Mantener `git diff --check` obligatorio en todos los scopes.
- No autocerrar planes si falla una validacion.
- No autocrear planes silenciosamente.
- No ocultar fallos; si un scope salta pruebas, debe mostrar `[SKIP]` con razon.
- El comportamiento por defecto debe seguir siendo conservador.
- Los smart dependency scopes deben basarse en reglas por path, documentadas y
  visibles en la salida del runner.
- `--allow-unsafe-scope` requiere justificacion en el plan cuando rebaja el
  scope efectivo por debajo de `required_scope`.

## Archivos normalmente permitidos

- `scripts/start_harness_task.sh`
- `scripts/finish_harness_task.sh`
- `scripts/validate_harness.sh`
- `scripts/harness_*.py`
- `docs/harness/`
- `AGENTS.md` si cambia regla de entrada.

## Archivos normalmente prohibidos

- DB real, datos reales, uploads, informes, backups y secretos.
- Cambios funcionales en `app/`, `templates/` o `static/` salvo que el harness
  los necesite para smoke minimo documentado.

## Validaciones obligatorias

- `python3 scripts/audit_docs.py`.
- `bash -n` de scripts shell modificados.
- `bash scripts/finish_harness_task.sh` con scope adecuado.
- Tests del resolver si cambian reglas de scope.
- `git diff --check`.
- `git status --short`.

## Mini TASK_ENVELOPE

- Wrapper afectado:
- Validacion afectada:
- Scope:
- Comportamiento por defecto:
- Riesgo de ocultar fallos:
- Rollback:

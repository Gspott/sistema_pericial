# Episode: Project Standards Guard 1

## Fecha

2026-06-19


## Tarea

Implantar `PROJECT-STANDARDS-GUARD-1` como guard documental y preventivo para estandares transversales.

## Plan asociado

project-standards-guard-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Convertir `TIMEZONE-STANDARD-1`, `AUTOSAVE-STANDARD-1`, seleccion reactiva, estado visual, concurrencia, tests, mobile-first/desktop, documental/PDF y trazabilidad harness en reglas permanentes para futuras tareas.

## Archivos modificados

- `AGENTS.md`
- `agents.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/PATTERNS/README.md`
- `docs/harness/VALIDATION/project_standards_guard.md`
- `docs/harness/VALIDATION/drift_detection.md`
- `docs/harness/VALIDATION/minimal_checks.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `scripts/audit_docs.py`
- `tests/smoke/test_harness_plan_guard.py`
- `docs/harness/PLANS/completed/project-standards-guard-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m py_compile scripts/audit_docs.py`
- `.venv/bin/python -m pytest tests/smoke/test_harness_plan_guard.py -q`
- `diff -q AGENTS.md agents.md`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Resultado

Se creo el estandar oficial `PROJECT-STANDARDS-GUARD-1` y una checklist reutilizable. `audit_docs.py` ahora incluye un warning informativo para posibles usos nuevos de `datetime.now()` o `datetime.utcnow()` en archivos Python modificados, excluyendo tests, `app/utils/timezone.py` y el propio script de auditoria.

El guard se mantiene como warning para no bloquear deuda historica conocida ni forzar refactors fuera de alcance.

## Warnings

`audit_docs.py` mantiene warnings historicos no introducidos en esta tarea:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

## Rollback

Revertir los documentos nuevos, las referencias en `AGENTS.md`/`agents.md`, la funcion `check_project_standards_guard()` de `scripts/audit_docs.py` y el smoke asociado.

## Memoria actualizada

`PROJECT-STANDARDS-GUARD-1` queda versionado en `docs/harness/PATTERNS/project_standards_guard.md` y referenciado desde el indice operativo.

## Decisiones humanas

No se requirio aprobacion humana porque no hubo cambios funcionales, datos, migraciones, facturacion, backups, autenticacion ni deploy.

## Proximos pasos

- Evaluar en fases posteriores si el guard debe advertir tambien sobre raw dates en templates tocados.
- Evaluar si conviene crear baseline de deuda historica para poder endurecer warnings sin ruido.
- Usar la checklist antes de extender autosave o timezone a nuevos modulos.

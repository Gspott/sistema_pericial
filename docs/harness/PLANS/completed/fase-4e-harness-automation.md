# Fase 4E - Harness Automation

## Objetivo

Automatizar operaciones mecanicas y reversibles del harness: crear planes activos, cerrar planes validados, actualizar metricas y detectar planes cerrados que siguen en `active/`.

## Modulo

Harness, scripts documentales y validacion.

## Riesgo

Bajo. No toca aplicacion ni datos reales.

## Archivos permitidos

- `scripts/harness_new_plan.py`
- `scripts/harness_close_plan.py`
- `scripts/harness_metrics.py`
- `scripts/validate_harness.sh`
- `scripts/audit_docs.py`
- `Makefile`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/VALIDATION/runner.md`
- `docs/harness/MAINTENANCE/weekly_cleanup.md`
- `docs/harness/METRICS.md`
- `docs/harness/PLANS/active/fase-4e-harness-automation.md`

## Archivos prohibidos

- `app/`
- `templates/`
- `static/`
- Bases SQLite reales
- `backups/`
- `uploads/`
- Informes, fotos, logs y secretos

## Playbook aplicable

Harness documental. No aplica playbook funcional.

## Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall scripts`
- `bash scripts/validate_harness.sh`
- `python3 scripts/harness_metrics.py`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Rollback

Revertir scripts nuevos, cambios del runner/Makefile/docs y la seccion generada de metricas.

## Fuera de alcance

- Automatizar aprobaciones humanas.
- Mover backlog/prioridades automaticamente.
- Tocar logica de aplicacion.
- Tocar datos reales.

## Aprobacion humana requerida

Requerida para cualquier automatizacion que cierre tareas criticas sin validacion, modifique datos reales o apruebe cambios sensibles.

Estado: completado

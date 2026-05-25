# Harness Consolidation Audit

## Objetivo

Auditar coherencia global del harness, detectar redundancia documental y aplicar solo consolidaciones minimas, reversibles y utiles.

## Modulo

Harness/documentacion.

## Riesgo

Bajo. Solo documentacion y organizacion de planes.

## Archivos Permitidos

- `docs/harness/PLANS/active/harness-consolidation-audit.md`
- `docs/harness/PLANS/active/`
- `docs/harness/PLANS/completed/`
- `docs/harness/SYSTEM_STATE.md`
- `docs/harness/VALIDATION/drift_detection.md`
- `docs/harness/PLANS/tech_debt_tracker.md`
- `docs/harness/METRICS.md`

## Archivos Prohibidos

- `app/`
- `templates/`
- `static/`
- Bases SQLite reales
- `backups/`
- `uploads/`
- Informes, fotos, logs y secretos

## Playbook Aplicable

No aplica playbook funcional. Se usan `GOLDEN_PRINCIPLES`, `SOURCE_OF_TRUTH` y `MAINTENANCE/dead_docs_policy.md`.

## Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Rollback

Restaurar planes movidos a `active/` y revertir ajustes documentales.

## Fuera De Alcance

- Reestructuracion masiva.
- Borrado de docs.
- Cambios funcionales.
- Cambios de tests o runner.

## Aprobacion Humana Requerida

Requerida para borrar documentos, cambiar fuentes normativas o mover grandes bloques fuera de `docs/harness/PLANS/`.

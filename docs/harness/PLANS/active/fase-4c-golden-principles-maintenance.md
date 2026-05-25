# Fase 4C - Golden Principles Y Mantenimiento

## Objetivo

Crear una capa breve de principios nucleo y una rutina de mantenimiento para reducir entropia documental del harness.

## Modulo

Harness documental.

## Riesgo

Bajo. Solo documentacion y auditoria documental.

## Archivos Permitidos

- `AGENTS.md`
- `agents.md`
- `docs/harness/GOLDEN_PRINCIPLES.md`
- `docs/harness/MAINTENANCE/`
- `docs/harness/METRICS.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/VALIDATION/drift_detection.md`
- `docs/harness/PLANS/active/fase-4c-golden-principles-maintenance.md`
- `scripts/audit_docs.py`

## Archivos Prohibidos

- `app/`
- `templates/`
- `static/`
- Bases SQLite reales
- `backups/`
- `uploads/`
- Informes, fotos, logs y secretos

## Playbook Aplicable

No aplica un playbook funcional. Se usa harness documental, `docs/SOURCE_OF_TRUTH.md` y validacion documental.

## Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Rollback

Revertir los archivos documentales creados/modificados en esta fase y restaurar `scripts/audit_docs.py` al estado anterior.

## Fuera De Alcance

- Cambios de aplicacion.
- Cambios de tests.
- Cambios de PWA real.
- Limpieza de deuda tecnica existente.

## Aprobacion Humana Requerida

Requerida si se propone borrar documentacion, cambiar autoridad normativa o tocar cualquier archivo funcional.

# Fase 4D - Operational Memory

## Objetivo

Convertir el repo en memoria operativa viva para agentes, reduciendo dependencia del chat y mejorando continuidad entre sesiones.

## Modulo

Harness documental.

## Riesgo

Bajo. Solo documentacion y auditoria documental.

## Archivos Permitidos

- `docs/harness/BACKLOG/`
- `docs/harness/STATE/`
- `docs/harness/FAILURES/`
- `docs/harness/PATTERNS/`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/METRICS.md`
- `docs/harness/VALIDATION/drift_detection.md`
- `docs/harness/PLANS/active/fase-4d-operational-memory.md`
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

No aplica playbook funcional. Se usa harness documental, Golden Principles y `docs/SOURCE_OF_TRUTH.md`.

## Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Rollback

Revertir documentos creados en BACKLOG, STATE, FAILURES, PATTERNS y los enlaces de auditoria/manual.

## Fuera De Alcance

- Cambios funcionales.
- Cambios de tests.
- Correccion real de drift PWA o warnings.
- Modificacion de datos reales.

## Aprobacion Humana Requerida

Requerida si se propone borrar memoria operativa, cambiar fuentes normativas o tocar cualquier archivo funcional.

# Fix TemplateResponse Warning

## Objetivo

Eliminar el warning de Starlette por uso de firma antigua de `TemplateResponse` sin cambiar comportamiento funcional.

## Modulo

Backend/Jinja.

## Riesgo

Medio. Cambio mecanico sobre renderizado server-side.

## Archivos Permitidos

- `app/main.py`
- `app/routers/*.py` con llamadas `TemplateResponse`
- `docs/backend.md`
- `docs/harness/FAILURES/template_response_warning.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/STATE/known_risks.md`
- `docs/harness/STATE/recent_changes.md`
- `docs/harness/METRICS.md`
- `docs/harness/PLANS/active/fix-template-response-warning.md`

## Archivos Prohibidos

- Bases SQLite reales
- `backups/`
- `uploads/`
- Informes, fotos, logs y secretos
- Templates Jinja, salvo que aparezca un bloqueo no previsto

## Playbook Aplicable

- `docs/harness/TASK_PACKS/bugfix.md`
- Fuente normativa: `docs/backend.md`

## Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Rollback

Restaurar las llamadas `TemplateResponse` a la firma anterior y revertir notas documentales.

## Fuera De Alcance

- Refactor de rutas.
- Cambios en plantillas.
- Cambios de contexto Jinja.
- Cambios de UX, navegacion o datos.

## Aprobacion Humana Requerida

Requerida si la correccion obliga a cambiar logica de rutas, contexto de plantillas o comportamiento publico.

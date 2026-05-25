# Smoke Tests Gastos

## Objetivo

Añadir cobertura smoke segura para gastos, importacion y adjuntos sin tocar recibos reales, OCR real, IA real ni datos reales.

## Modulo

Gastos, importacion sandbox, adjuntos temporales y SQLite temporal.

## Riesgo

Medio en tests sandbox. Alto si se tocaran adjuntos o DB reales, que quedan fuera de alcance.

## Archivos Permitidos

- `tests/smoke/test_gastos_mock.py`
- `docs/harness/BACKLOG/medium.md`
- `docs/harness/STATE/recent_changes.md`
- `docs/harness/METRICS.md`
- `docs/harness/PLANS/active/smoke-tests-gastos.md`

## Archivos Prohibidos

- DB real
- Recibos reales
- `uploads/` real
- OCR real
- OpenAI/IA real
- Backups, informes, fotos, logs y secretos

## Playbook Aplicable

No existe `docs/harness/PLAYBOOKS/gastos.md` en esta fase. Se usa:

- `docs/harness/TASK_PACKS/bugfix.md`, porque solo se añaden tests.
- `docs/harness/PATTERNS/safe_sqlite_migration.md`, solo como patron de DB temporal; no hay migracion.

## Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `python3 -m compileall tests`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Cobertura Añadida

- Import seguro del router de gastos.
- Calculo base/IVA/total con datos demo.
- Insercion de gasto demo en SQLite temporal.
- Adjunto demo temporal sin leer rutas reales.
- Deduplicado del importador con DB temporal.
- Degradacion controlada sin OCR/IA mediante helpers locales.

## Limitaciones

- No se ejecuta `scripts/importar_gastos_icloud.py` como proceso.
- No se llama OCR/PDF/imagen real.
- No se usa OpenAI ni red.

## Rollback

Eliminar el test nuevo y revertir notas de memoria operativa.

## Fuera De Alcance

- Refactor de `app/routers/gastos.py`.
- Cambios de esquema.
- Cambios del importador real.
- Lectura o movimiento de recibos reales.

## Aprobacion Humana Requerida

Requerida si se propone usar DB real, rutas reales de recibos, OCR real, OpenAI/IA o modificar importacion funcional.

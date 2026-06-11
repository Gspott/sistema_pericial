# Costes Lib 1 Eliminacion Segura

# Objetivo

Implementar COSTES-LIB-1: permitir eliminar partidas de la biblioteca de costes solo cuando no estén vinculadas a patologías ni actuaciones de reparación.

# Modulo

Costes / biblioteca de costes.

# Riesgo

Bajo-medio. La operación es destructiva, pero queda acotada a una partida concreta, exige POST y bloquea referencias operativas.

# Archivos permitidos

- `app/routers/costes.py`
- `templates/costes/listado.html`
- `tests/smoke/test_costes_workbench.py`
- `docs/harness/PLANS/active/costes-lib-1-eliminacion-segura.md`
- `docs/harness/EPISODES/2026-06-06-costes-lib-1-eliminacion-segura.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- OCR y parser IVE.
- Importador BC3.
- Informes, actuaciones, patologías, facturación, CRM, emails y valoraciones.
- Datos reales, uploads, informes generados, backups, fotos y logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/app_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_workbench.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir archivos listados. No hay migración ni cambios de esquema.

# Fuera de alcance

- Soft delete global de biblioteca.
- Eliminar partidas usadas por patologías o actuaciones.
- Cambiar OCR, parser IVE, BC3 o informes.
- Modificar la lógica de patologías o actuaciones.

# Aprobacion humana requerida

Si se quisiera borrar datos reales, cambiar integridad referencial o tocar módulos fuera de costes.

# Decisión

El borrado se implementa como acción POST desde `/costes`, con `confirm()` en UI. Si no hay referencias en `patologia_costes` ni `actuacion_partidas`, borra la partida y sus descompuestos propios; si aparece como hijo de otra descomposición, se anula solo la referencia `concepto_hijo_id` para conservar el snapshot textual de la otra partida.

Estado: completado

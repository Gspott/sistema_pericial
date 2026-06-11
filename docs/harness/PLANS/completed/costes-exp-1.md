# Costes Exp 1

# Objetivo

Implementar COSTES-EXP-1: actuaciones de reparación vinculadas al expediente y separadas de patologías, para estructurar el PEM por trabajos reales de reparación.

# Modulo

Costes / expedientes / SQLite / Jinja SSR.

# Riesgo

Bajo-medio. Cambio de esquema idempotente y rutas nuevas. No debe tocar informes, facturación, CRM, emails, valoraciones ni lógica existente de patologías.

# Archivos permitidos

- `app/database.py`
- `app/main.py`
- `templates/actuaciones_reparacion.html`
- `templates/detalle_expediente.html`
- `tests/smoke/test_actuaciones_reparacion.py`
- `docs/harness/PLANS/completed/costes-exp-1.md`
- `docs/harness/EPISODES/2026-06-05-costes-exp-1.md`
- `docs/harness/METRICS.md` si cambian métricas

# Archivos prohibidos

- Datos reales SQLite.
- Uploads, informes generados, backups, fotos y logs.
- Módulos de facturación, CRM, emails, valoración e informes salvo lectura contextual.
- Vinculación `patologia_costes`, salvo tests de no regresión si fueran necesarios.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.

- `docs/harness/PLAYBOOKS/base_datos.md`
- `docs/harness/PLAYBOOKS/jinja.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_actuaciones_reparacion.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir los archivos listados. Las tablas nuevas son aditivas; no borrar datos sin autorización humana.

# Fuera de alcance

- Modificar generación de informes.
- Conectar actuaciones con patologías.
- Sustituir `patologia_costes`.
- Generar PDF, factura o presupuesto comercial.
- Cambiar biblioteca de costes, importador BC3 u OCR.

# Aprobacion humana requerida

Solo si se quisiera borrar datos reales, modificar informes o cambiar el modelo de patologías existente.

# Diseño

Se crean dos tablas idempotentes:

- `actuaciones_reparacion`: cabecera por expediente con título, descripción, observaciones y orden.
- `actuacion_partidas`: partidas de coste vinculadas a una actuación con snapshot de descripción, unidad y precio unitario.

El importe se calcula como `cantidad * precio_unitario_snapshot`. La biblioteca de costes queda como trazabilidad por `concepto_id`, pero cambios posteriores de la biblioteca no modifican actuaciones ya creadas.

# Estado

Completado. Harness cerrado con smoke completo OK.

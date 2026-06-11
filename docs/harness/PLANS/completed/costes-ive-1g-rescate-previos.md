# Costes Ive 1G Rescate Previos

# Objetivo

Implementar COSTES-IVE-1G: rescatar descompuestos IVE previos a la línea porcentual cuando el OCR trae códigos imperfectos y corregir importes por coherencia matemática.

# Modulo

Costes / parser OCR IVE.

# Riesgo

Bajo. Cambio mínimo y aislado en el parser especializado IVE; no toca OCR, UI ni módulos de negocio.

# Archivos permitidos

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ive-1g-rescate-previos.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1g-rescate-previos.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- OCR.
- UI salvo imprescindible.
- Informes, actuaciones, patologías, facturación, CRM, emails y valoraciones.
- Datos reales, uploads, informes generados, backups, fotos y logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/app_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir archivos listados. No hay migración ni cambios de datos.

# Fuera de alcance

- Cambiar OCR.
- Cambiar parser genérico.
- Guardado o validación automática.
- Conectar costes con informes, patologías, actuaciones o facturación.

# Aprobacion humana requerida

Si se quisiera tocar OCR, servicios externos, datos reales o módulos fuera de costes.

# Decisión

En modo IVE se amplía la tolerancia a códigos OCR auxiliares como `MODA12a` y `PBAAa`, se normalizan resúmenes pegados, y se corrige la línea porcentual usando el subtotal previo cuando mejora la coherencia con el precio principal.

Estado: completado

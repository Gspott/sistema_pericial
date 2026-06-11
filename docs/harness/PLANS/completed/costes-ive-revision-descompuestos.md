# Costes Ive Revision Descompuestos

# Objetivo

Diagnosticar y corregir el flujo de revisión de captura IVE cuando el parser devuelve dos descompuestos pero la UI parece mostrar solo el porcentaje.

# Modulo

Costes / capturas / revisión manual / Jinja.

# Riesgo

Bajo. Cambio limitado a template de revisión y tests de integración; no toca OCR ni parser salvo diagnóstico.

# Archivos permitidos

- `templates/costes/captura_revision.html`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ive-revision-descompuestos.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-revision-descompuestos.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- OCR.
- Parser salvo bug real.
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
- Cambiar parser si no se reproduce bug real.
- Guardado o validación automática.

# Aprobacion humana requerida

Si se quisiera inspeccionar datos reales o modificar OCR.

# Diagnóstico

Con `datos_extraidos_json` que contiene dos descompuestos, el GET de revisión renderiza ambos. Con `POST /costes/capturas/{captura_id}/extraer` mockeado, ambos se guardan en JSON y ambos se muestran.

Se añade fecha `updated_at` junto a `version_parser` para detectar extracciones antiguas/cacheadas en pantalla.

Estado: completado

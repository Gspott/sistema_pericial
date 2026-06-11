# Costes Ive 1H Refuerzo Prefijos

# Objetivo

Reforzar COSTES-IVE-1H para que el parser IVE detecte tablas largas con prefijos OCR basura y precio principal en línea separada.

# Modulo

Costes / parser OCR IVE.

# Riesgo

Bajo. Cambio mínimo en parser IVE y test de captura; no toca OCR, UI ni módulos de negocio.

# Archivos permitidos

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ive-1h-refuerzo-prefijos.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1h-refuerzo-prefijos.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- OCR.
- UI general de costes.
- Importador BC3.
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

Revertir archivos listados. No hay migración ni cambios de esquema.

# Fuera de alcance

- Cambiar OCR.
- Cambiar UI.
- Cambiar importador BC3.
- Validar o guardar automáticamente.
- Tocar informes, patologías, actuaciones o facturación.

# Aprobacion humana requerida

Si se quisiera tocar OCR, datos reales o módulos fuera de costes.

# Decisión

Se limpian prefijos OCR al normalizar líneas IVE, se amplía el diccionario de recursos frecuentes del falso techo y se acepta precio principal en línea suelta antes de la tabla de descompuestos.

Estado: completado

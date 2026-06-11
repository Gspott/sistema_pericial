# Costes Ive 1C

# Objetivo

Implementar COSTES-IVE-1C: aceptar códigos auxiliares IVE sin punto en descompuestos, como `MOOA12a`, `MOOA11a`, `PBPL3b` y `ERPG10a`.

# Modulo

Costes / parser OCR IVE.

# Riesgo

Bajo. Cambio mínimo y aislado en parser de costes; no toca OCR ni módulos de negocio.

# Archivos permitidos

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ive-1c.md`
- `docs/harness/EPISODES/2026-06-05-costes-ive-1c.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- OCR.
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
- Cambiar informes, actuaciones, patologías o facturación.
- Guardado o validación automática.

# Aprobacion humana requerida

Si se quisiera tocar OCR, servicios externos o datos reales.

# Decisión

El regex IVE de descompuestos diferencia explícitamente: partida con punto, auxiliar sin punto y `%`.

Estado: completado

# Diagnostico Costes Ive 1C

# Objetivo

Diagnosticar si la línea OCR `MOOA12a h Peón ordinario construcción 21.08 0.500 10.54` se descarta en COSTES-IVE-1C y dejar regresión si procede.

# Modulo

Costes / parser OCR IVE / tests smoke.

# Riesgo

Bajo. Diagnóstico y test de regresión; no toca OCR ni módulos de negocio.

# Archivos permitidos

- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/diagnostico-costes-ive-1c.md`
- `docs/harness/EPISODES/2026-06-05-diagnostico-costes-ive-1c.md`
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

Revertir el test añadido y este plan/episodio.

# Fuera de alcance

- Cambiar OCR.
- Cambiar parser si el diagnóstico no reproduce descarte.
- Modificar informes o datos.

# Aprobacion humana requerida

No requerida.

# Diagnóstico

La línea exacta no se descarta en el estado actual. La traza confirma:

- `_parsear_linea_descompuesto_ive()` devuelve `codigo=MOOA12a`, `unidad=h`, `precio_unitario=21.08`, `rendimiento=0.5`, `importe=10.54`.
- `parsear_coste_desde_texto()` incluye ese dict como primer descompuesto final.

Se añade test de regresión sin símbolos euro para fijarlo.

Estado: completado

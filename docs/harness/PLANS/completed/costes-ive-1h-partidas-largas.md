# Costes Ive 1H Partidas Largas

# Objetivo

Implementar COSTES-IVE-1H: mejorar el parser IVE para partidas largas con muchos descompuestos, especialmente falsos techos tipo `ERTC.3aaaa`.

# Modulo

Costes / parser OCR IVE.

# Riesgo

Bajo. Cambio acotado al parser especializado IVE y tests de capturas; no toca OCR, UI ni módulos de negocio.

# Archivos permitidos

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ive-1h-partidas-largas.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1h-partidas-largas.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- OCR.
- UI.
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

Se mantiene el parser genérico intacto. En modo IVE se añaden normalizaciones de texto/código para falsos techos y una normalización de tokens compactos basada en el token OCR original, evitando escalar valores que ya traen separador decimal.

Estado: completado

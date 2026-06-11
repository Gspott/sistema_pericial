# Costes Ive 1

# Objetivo

Implementar COSTES-IVE-1: parser especializado para capturas OCR de IVE/Base de Datos de Construcción, con prioridad sobre el parser genérico cuando se detecte texto IVE.

# Modulo

Costes / capturas OCR / parser heurístico local.

# Riesgo

Bajo-medio. Cambio aislado en parser de costes; no toca OCR, informes, actuaciones, patologías, facturación, CRM, emails ni valoraciones.

# Archivos permitidos

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ive-1.md`
- `docs/harness/EPISODES/2026-06-05-costes-ive-1.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- `app/services/costes_ocr.py` salvo lectura contextual.
- Informes, actuaciones, patologías, facturación, CRM, emails y valoraciones.
- Datos reales, uploads, informes generados, backups, fotos y logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/app_change.md`.

- `docs/harness/PLAYBOOKS/base_datos.md` solo como referencia de no tocar datos reales.

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

- Cambiar OCR local.
- Importador BC3.
- Guardado automático o validación automática.
- Conectar con informes, actuaciones o patologías.

# Aprobacion humana requerida

Si se quisiera usar IA externa, servicios online o modificar OCR/capturas reales.

# Decisión

El parser IVE se activa antes del genérico solo cuando hay indicadores de IVE/BDC o códigos IVE tipo `ERPG.4aba`. El parser genérico queda como fallback.

Estado: completado

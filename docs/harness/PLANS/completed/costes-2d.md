# Costes 2D

# Objetivo

Mejorar la extracción asistida de costes desde capturas OCR locales/opcionales para textos tipo IVE/BC3, manteniendo revisión manual obligatoria y concepto final siempre en borrador.

# Modulo

Costes aislado:
- `app/services/costes_parser.py`
- `app/services/costes_ocr.py`
- `app/routers/costes.py`
- `templates/costes/captura_revision.html`
- tests smoke de costes/capturas

# Riesgo

Bajo-medio. Cambia heurística de prellenado y presentación de revisión, sin conectar con patologías ni guardar automáticamente. Riesgo principal: falsos positivos del parser OCR, mitigado con advertencias, campos detectados y revisión humana editable.

# Archivos permitidos

- `app/services/costes_parser.py`
- `app/services/costes_ocr.py`
- `app/routers/costes.py`
- `templates/costes/captura_revision.html`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-2d.md`
- episodio harness COSTES-2D

# Archivos prohibidos

- Patologías, expedientes, inspecciones, valoraciones, CRM, emails, facturación e informes.
- Base SQLite real, uploads reales, backups, logs y secretos.
- Importador BC3 definitivo.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `pytest` smoke de costes
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir cambios de parser/OCR/router/template/tests/docs de COSTES-2D. No hay migraciones ni cambios de esquema en esta fase.

# Fuera de alcance

- IA externa o servicios online.
- OCR obligatorio.
- Importador BC3.
- Conexión con patologías, informes o facturación.
- Guardado o validación automática de conceptos.

# Aprobacion humana requerida

Solo si se pretende añadir dependencias obligatorias, tocar datos reales o conectar costes con otros módulos. No aplica para este alcance.

Estado: completado

# Costes 3B

# Objetivo

Revisión operativa del módulo de costes antes de vincularlo con patologías: pulir OCR IVE, listado, detalle, validación y trazabilidad de fuentes sin conectar con otros módulos.

# Modulo

Costes aislado:
- parser OCR de costes;
- router/template de detalle de costes;
- tests smoke de capturas y workbench;
- documentación harness.

# Riesgo

Bajo. Cambios limitados a prellenado OCR y presentación de detalle. No hay cambios de esquema, ni validación automática, ni conexión con patologías/informes/facturación.

# Archivos permitidos

- `app/services/costes_parser.py`
- `app/routers/costes.py`
- `templates/costes/detalle.html`
- `tests/smoke/test_costes_capturas.py`
- `tests/smoke/test_costes_workbench.py`
- `docs/harness/PLANS/active/costes-3b.md`
- episodio harness COSTES-3B

# Archivos prohibidos

- Patologías, expedientes, inspecciones, valoraciones, CRM, emails, facturación e informes.
- Base SQLite real, uploads reales, backups, logs y secretos.
- Navegación global.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- smoke costes
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir cambios listados en archivos permitidos. No hay migración ni cambio de esquema.

# Fuera de alcance

- Vinculación con patologías.
- Informes y facturación.
- Importador BC3 completo.
- IA externa o servicios online.

# Aprobacion humana requerida

Solo si se pretende tocar datos reales o conectar costes con módulos de negocio.

Estado: completado

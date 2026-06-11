# Costes 3

# Objetivo

Implementar un importador BC3/FIEBDC mínimo para crear una base propia de costes desde archivo, manteniendo todos los conceptos en `borrador`, con trazabilidad en `costes_fuentes` y sin conexión con patologías.

# Modulo

Costes aislado:
- servicio parser BC3;
- rutas `/costes/bc3/*`;
- plantillas locales de importación;
- tests smoke de parser/importación.

# Riesgo

Bajo-medio. Se incorporan archivos subidos y escrituras sobre tablas de costes en DB temporal de tests. Riesgos mitigados: extensiones limitadas, parser tolerante, duplicados saltados, sin validación automática, sin tocar módulos funcionales ajenos.

# Archivos permitidos

- `app/services/bc3_parser.py`
- `app/routers/costes.py`
- `templates/costes/listado.html`
- `templates/costes/bc3_importar.html`
- `templates/costes/bc3_resultado.html`
- `templates/costes/bc3_importaciones.html`
- `templates/costes/bc3_importacion_detalle.html`
- `tests/smoke/test_costes_bc3.py`
- `docs/harness/PLANS/active/costes-3.md`
- episodio harness COSTES-3

# Archivos prohibidos

- Patologías, expedientes, inspecciones, valoraciones, CRM, emails, facturación e informes.
- Base SQLite real, backups, logs, secretos y uploads reales salvo carpeta temporal de tests.
- Navegación global.
- Importador BC3 completo o conexión con patologías.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir los cambios de COSTES-3 listados arriba. No hay cambios de esquema ni migraciones nuevas.

# Fuera de alcance

- Cobertura completa del estándar FIEBDC.
- Validación automática de conceptos importados.
- Servicios online, IA externa u OCR.
- Vinculación con patologías, informes, expedientes o facturación.

# Aprobacion humana requerida

Solo si se pretende tocar datos reales, añadir dependencias obligatorias, modificar navegación global o conectar costes con otros módulos.

Estado: completado

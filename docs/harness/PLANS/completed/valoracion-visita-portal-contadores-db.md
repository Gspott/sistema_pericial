# Valoracion Visita Portal Contadores Db

# Objetivo

Persistir observaciones textuales de portal y cuadro de contadores dentro de
las observaciones de visita de valoracion.

# Modulo

Valoracion inmobiliaria / visitas / modelo defensivo / UX mobile-first.

# Riesgo

Bajo-medio: cambio de esquema defensivo mediante columnas nuevas en tabla
existente. Validado solo sobre DB temporal; no se toca DB real.

# Archivos permitidos

- `app/database.py`
- `app/main.py`
- `app/services/informe.py`
- `templates/nueva_visita.html`
- `tests/smoke/test_valoracion_db_defensiva.py`
- `tests/smoke/test_valoracion_visita_observaciones_form.py`
- `tests/smoke/test_valoracion_nueva_visita_ux.py`
- `docs/modelos_datos.md`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/visita_especifica_por_tipo_informe.md`
- `docs/harness/EPISODES/2026-05-26-valoracion-visita-portal-contadores-db.md`

# Archivos prohibidos

DB real, datos reales, uploads reales, informes reales, backups, secretos,
routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/db_change.md`.

# Cambios

- Columnas defensivas en `valoracion_visita_observaciones`:
  `observaciones_portal` y `observaciones_cuadro_contadores`.
- GET/POST de observaciones de valoracion cargan y guardan ambos campos.
- `nueva_visita.html` guarda ambos campos desde el bloque Portal y contadores.
- Las fotos siguen usando `visita_fotos.categoria='portal_contadores'`.
- `build_informe_context()` expone ambos valores en la valoracion.
- No se modifica `valoracion_visita` legacy.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir diff. No hay migracion real ni datos reales que restaurar.

# Fuera de alcance

DB real, migracion de datos legacy, borrado de columnas, calculo, PDF/DOCX,
uploads reales, informes reales y routers legacy.

# Aprobacion humana requerida

No requerida: no se toca DB real y las columnas se validan en DB temporal.

Estado: completado

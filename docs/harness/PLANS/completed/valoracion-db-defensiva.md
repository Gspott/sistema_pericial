# Valoracion Db Defensiva

# Objetivo

Crear la base defensiva del nuevo modelo de valoracion inmobiliaria:
datos estables por expediente, observaciones de visita, testigos reutilizables,
vinculo expediente-testigo con snapshot, ajustes y resultados por metodo.

# Modulo

Datos / valoracion inmobiliaria / smoke tests.

# Riesgo

Alto por tocar inicializacion de esquema SQLite, mitigado por ser aditivo,
sin borrado, sin migracion y con smoke sobre DB temporal.

# Archivos permitidos

- `app/database.py`
- `tests/smoke/`
- `docs/modelos_datos.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB real, backups, uploads, fotos reales, informes generados y secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy.
- Templates HTML/PDF/DOCX.
- Formularios y calculo de homogeneizacion.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke -q` si esta disponible
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir el bloque de tablas/indices nuevos de `app/database.py`, eliminar el
smoke nuevo y revertir la documentacion de la fase. No hay datos reales ni
migracion que deshacer.

# Fuera de alcance

- Migrar datos desde `valoracion_visita` o `comparables_valoracion`.
- Crear UI de testigos reutilizables.
- Implementar calculo, homogeneizacion o validacion funcional de coeficientes.
- Adaptar outputs HTML/PDF/DOCX.

# Aprobacion humana requerida

Necesaria si aparece borrado/renombrado de columnas, migracion de datos,
recreacion de tablas existentes o uso de DB real. No aplica en esta fase.

Estado: completado

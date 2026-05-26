# Valoracion Expediente Form Minimo

# Objetivo

Crear un formulario minimo server-side para editar datos estables de
valoracion en `valoracion_expediente`, sin migrar legacy automaticamente y sin
tocar calculo.

# Modulo

Expedientes / valoracion inmobiliaria / formularios server-side.

# Riesgo

Alto por tocar `app/main.py` y detalle de expediente; mitigado con rutas
pequenas, ownership existente, sin esquema nuevo, sin migracion y smokes
temporales.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_expediente.html`
- `templates/detalle_expediente.html`
- `tests/smoke/`
- `docs/modelos_datos.md`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB real, datos reales, backups, uploads, fotos reales, informes generados y secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy.
- PDF/DOCX moderno y templates de informe.
- Calculo/homogeneizacion.
- Migraciones o borrado de campos legacy.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir rutas/helper de formulario en `app/main.py`, eliminar
`templates/valoracion_expediente.html`, quitar CTA del detalle, eliminar smoke
y revertir docs de fase. No hay datos reales ni migracion.

# Fuera de alcance

- Migrar valores desde `valoracion_visita`.
- Eliminar campos legacy de `nueva_visita.html`.
- Formularios de testigos, ajustes, resultados u observaciones de visita.
- Calculo/homogeneizacion.

# Aprobacion humana requerida

Necesaria si aparece cambio de esquema no trivial, migracion, DB real,
outputs PDF/DOCX, routers legacy o calculo. No aplica en esta fase.

Estado: completado

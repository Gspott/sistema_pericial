# Valoracion Visita Observaciones Form

# Objetivo

Crear formulario minimo server-side para `valoracion_visita_observaciones`,
separando los datos observados en visita de los datos estables de expediente.

# Modulo

Visitas / valoracion inmobiliaria / formularios server-side.

# Riesgo

Alto por tocar `app/main.py`, detalle de expediente y contexto de informe;
mitigado con rutas pequenas, sin esquema nuevo, sin migracion y smokes
temporales.

# Archivos permitidos

- `app/main.py`
- `app/services/informe.py`
- `templates/valoracion_visita_observaciones.html`
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
- Testigos, ajustes y calculo/homogeneizacion.
- Migracion o borrado de campos legacy.
- PDF/DOCX moderno y templates de informe.

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

Revertir rutas/helper de observaciones en `app/main.py`, revertir el fallback
adicional en `app/services/informe.py`, eliminar template y smoke nuevos,
quitar CTA del detalle y revertir docs. No hay datos reales ni migracion.

# Fuera de alcance

- Migrar valores desde `valoracion_visita`.
- Eliminar campos legacy de `nueva_visita.html`.
- Formularios de testigos, ajustes o resultados.
- Calculo/homogeneizacion.

# Aprobacion humana requerida

Necesaria si aparece cambio de esquema no trivial, migracion, DB real,
testigos/caculo, outputs PDF/DOCX o routers legacy. No aplica en esta fase.

Estado: completado

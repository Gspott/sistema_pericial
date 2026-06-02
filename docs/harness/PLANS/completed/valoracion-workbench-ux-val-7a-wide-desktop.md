# Valoracion Workbench Ux Val 7A Wide Desktop

# Objetivo

Optimizar la ergonomia wide desktop del workbench de valoracion, aprovechando
mas anchura y reduciendo densidad vertical sin cambiar calculos, DB, informes,
mobile workflows ni biblioteca.

# Modulo

Valoracion inmobiliaria: template SSR del Workbench.

# Riesgo

Bajo. Cambio visual scoped en un template; riesgo principal: romper mobile por
layout ancho o sticky panel.

# Archivos permitidos

- `templates/valoracion_workbench.html`
- `tests/smoke/test_valoracion_workbench.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB, calculos, informes, Biblioteca de Testigos, rutas y JS.
- Datos reales, uploads, backups, secretos.
- Carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir CSS/classes del template, smoke y documentacion de esta fase. No hay
persistencia ni cambios de logica.

# Fuera de alcance

- Calculos, DB, informes, biblioteca, mobile workflows.
- SPA/JS obligatorio.
- Rediseño completo del workbench.

# Aprobacion humana requerida

No prevista mientras se mantenga en CSS scoped y smokes verdes.

Estado: completado

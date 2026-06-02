# Valoracion Bib Test 8 Wide Desktop

# Objetivo

Mejorar ergonomia wide desktop de biblioteca de testigos, alta rapida y ficha
detalle, usando CSS scoped y sin cambiar logica, DB, Workbench ni informes.

# Modulo

Valoracion inmobiliaria: templates SSR de biblioteca/testigos reutilizables.

# Riesgo

Bajo. Cambios visuales acotados a templates de testigos; riesgo principal:
romper mobile por contenedores demasiado anchos.

# Archivos permitidos

- `templates/valoracion_testigos_biblioteca.html`
- `templates/valoracion_testigo_biblioteca_form.html`
- `templates/valoracion_testigo_detalle.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB, app logic, informes, Workbench, static global salvo necesidad justificada.
- Datos reales, uploads reales, backups, secretos.
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

Revertir CSS/classes scoped de los tres templates y smokes de contenedores
wide. No hay persistencia ni migracion.

# Fuera de alcance

- Cambios de DB o rutas.
- Calculos.
- Workbench.
- Informes.
- SPA/JS obligatorio.

# Aprobacion humana requerida

No prevista salvo que se quiera rediseñar navegacion global o mobile.

Estado: completado

# Valoracion Bib Test 5 Vinculacion Controlada

# Objetivo

Permitir vincular un testigo de la biblioteca desktop a un expediente de
valoracion, con validacion de ownership/tipo de informe, snapshot historico y
sin mezclar datos globales del testigo con ponderacion del expediente.

# Modulo

Valoracion inmobiliaria, biblioteca de testigos, seleccion de testigos por
expediente.

# Riesgo

Bajo-medio. La fase anade una accion SSR contextual y una ruta POST acotada; no
cambia esquema ni informes. Riesgo principal: duplicar vinculos o modificar el
testigo maestro por error.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_testigos_biblioteca.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB real, datos reales, uploads, informes generados, backups y secretos.
- Carpeta anidada `sistema_pericial/`.
- Informes HTML/PDF/DOCX y Workbench salvo enlaces compatibles.

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

Revertir la ruta POST, la accion contextual en biblioteca y los smokes/docs de
esta fase. No hay migracion ni datos generados por tests fuera de DB temporal.

# Fuera de alcance

- Asignacion masiva.
- Ponderacion global en biblioteca.
- Edicion de peso/inclusion/representatividad desde la biblioteca maestra.
- Scraping, OCR, IA o deduplicacion automatica.
- Cambios en informes o Workbench.

# Aprobacion humana requerida

No prevista mientras se mantenga el alcance defensivo y no se toque DB real.

Estado: completado

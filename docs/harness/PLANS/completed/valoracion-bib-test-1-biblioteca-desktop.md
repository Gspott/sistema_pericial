# Valoracion Bib Test 1 Biblioteca Desktop

# Objetivo

Crear una vista SSR desktop para consultar, filtrar, ordenar y gestionar la
biblioteca maestra de testigos reutilizables sin mezclarla con ponderacion de
expedientes.

# Modulo

Valoracion inmobiliaria / biblioteca de testigos.

# Riesgo

Bajo-medio: nueva ruta y template SSR sobre datos existentes. No cambia esquema
ni calculos.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_testigos_biblioteca.html`
- `templates/valoracion_testigos.html`
- `templates/valoracion_expediente_testigos.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`

# Archivos prohibidos

- DB reales, backups, uploads reales, informes generados, secretos.
- Carpeta anidada `sistema_pericial/`.
- Informes, calculo final, workbench salvo enlaces de navegacion si procede.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir nueva ruta/template, accesos secundarios, smokes y documentacion.

# Fuera de alcance

- Asignacion masiva a expedientes.
- Deduplicacion automatica.
- Mapas, IA, scoring avanzado, importacion masiva, edicion inline masiva.
- Guardar peso, inclusion/exclusion o representatividad global.

# Aprobacion humana requerida

Si aparece necesidad de cambiar esquema, migrar datos o crear automatizaciones
de importacion.

Estado: completado

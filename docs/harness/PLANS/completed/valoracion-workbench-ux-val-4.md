# Valoracion Workbench Ux Val 4

# Objetivo

Implementar UX-VAL-4 del workbench SSR: microedicion segura de inclusion/exclusion, peso, representatividad y motivo tecnico breve por testigo seleccionado.

# Modulo

Valoracion inmobiliaria, workbench SSR, vinculos expediente-testigo y smoke tests.

# Riesgo

Medio. Actualiza campos existentes de `valoracion_expediente_testigos`; no crea entidades ni cambia calculos persistidos.

# Archivos permitidos

`app/main.py`, `templates/valoracion_workbench.html`, `tests/smoke/test_valoracion_workbench.py`, documentacion/harness minima.

# Archivos prohibidos

DB real, datos reales, uploads, informes generados, backups, secretos, patologias, inspecciones, routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

`python3 -m compileall app`, `python3 scripts/audit_docs.py`, `.venv/bin/python -m pytest`, `bash scripts/finish_harness_task.sh`, `git diff --check`, `git status --short`.

# Rollback

Revertir ruta POST, formulario del panel, smokes y documentacion de esta fase.

# Fuera de alcance

Edicion inline masiva, batch edit, spreadsheet, JS obligatorio, SPA, scoring, outliers, IA, drag/drop y adopcion automatica del valor final.

# Aprobacion humana requerida

Si aparece necesidad de crear columnas, tocar DB real o modificar informes/patologias/inspecciones.

Estado: completado

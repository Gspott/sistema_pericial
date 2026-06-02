# Valoracion Workbench Ux Val 2

# Objetivo

Implementar UX-VAL-2 del workbench SSR de valoracion: seleccion de testigo por query param, panel contextual navegable y estados/alertas mas utiles sin editor inline ni SPA.

# Modulo

Valoracion inmobiliaria, ruta SSR, template Jinja y smoke tests.

# Riesgo

Medio. Cambia una vista nueva de solo lectura y mantiene compatibilidad legacy.

# Archivos permitidos

`app/main.py`, `templates/valoracion_workbench.html`, `tests/smoke/test_valoracion_workbench.py`, harness/documentacion minima.

# Archivos prohibidos

DB real, datos reales, uploads reales, informes generados, backups, secretos, routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

`python3 -m compileall app`, `python3 scripts/audit_docs.py`, `.venv/bin/python -m pytest`, `bash scripts/finish_harness_task.sh`, `git diff --check`, `git status --short`.

# Rollback

Revertir cambios de ruta, template, smoke y docs/harness de esta fase.

# Fuera de alcance

Editor inline, SPA, JS obligatorio, scoring avanzado, outliers, spreadsheet completo, drag/drop, navegacion por teclado, cambios de informes o entidades nuevas.

# Aprobacion humana requerida

Si aparece necesidad de cambiar esquema, tocar datos reales o sustituir flujos mobile-first existentes.

Estado: completado

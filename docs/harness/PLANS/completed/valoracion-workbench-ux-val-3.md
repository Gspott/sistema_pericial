# Valoracion Workbench Ux Val 3

# Objetivo

Implementar UX-VAL-3 del workbench SSR de valoracion: diagnostico superior, filtros y ordenacion SSR, leyenda de estados y degradacion controlada de seleccion.

# Modulo

Valoracion inmobiliaria, ruta SSR, template Jinja y smoke tests.

# Riesgo

Medio. Vista de solo lectura sin cambios de entidades, persistencia ni calculo final.

# Archivos permitidos

`app/main.py`, `templates/valoracion_workbench.html`, `tests/smoke/test_valoracion_workbench.py`, documentacion/harness minima.

# Archivos prohibidos

DB real, datos reales, uploads, informes generados, backups, secretos, patologias, inspecciones, routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

`python3 -m compileall app`, `python3 scripts/audit_docs.py`, `.venv/bin/python -m pytest`, `bash scripts/finish_harness_task.sh`, `git diff --check`, `git status --short`.

# Rollback

Revertir cambios de ruta/helper, template, smoke y documentacion de esta fase.

# Fuera de alcance

Edicion inline, JS obligatorio, SPA, scoring, outliers complejos, spreadsheet completo, valor final automatico, cambios de informes o cambios de esquema.

# Aprobacion humana requerida

Si aparece necesidad de cambiar modelo, persistir resultados nuevos o tocar flujos mobile-first existentes.

Estado: completado

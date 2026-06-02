# Valoracion Workbench Ssr

# Objetivo

Crear una primera vista SSR de escritorio para analisis de valoracion inmobiliaria en `/expediente/{expediente_id}/valoracion/workbench`.

# Modulo

Valoracion inmobiliaria, rutas server-side, Jinja y smoke tests.

# Riesgo

Medio. Es una vista nueva de solo lectura que reutiliza contexto existente; no toca DB real ni sustituye flujos moviles.

# Archivos permitidos

`app/main.py`, `templates/valoracion_workbench.html`, smokes de valoracion y documentacion UX/harness.

# Archivos prohibidos

DB real, uploads reales, informes generados reales, backups, secretos, routers legacy, carpeta anidada `sistema_pericial/`, formularios moviles existentes salvo referencia documental.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

`python3 -m compileall app`, `python3 scripts/audit_docs.py`, `.venv/bin/python -m pytest`, `bash scripts/finish_harness_task.sh`, `git diff --check`, `git status --short`.

# Rollback

Revertir ruta, template, smoke y documentacion de esta fase.

# Fuera de alcance

IA, scoring avanzado, outliers complejos, spreadsheet completo, edicion inline masiva, navegacion por teclado, drag/drop, frontend separado o cambios de informe.

# Aprobacion humana requerida

Si se necesita cambiar esquema, tocar datos reales, modificar informes generados o sustituir flujos mobile-first existentes.

Estado: completado

# Valoracion Comparacion 2A Economicos

# Objetivo

Preparar FASE 2A de comparacion: datos economicos profesionales en testigos, calculo inicial de €/m² y advertencias no bloqueantes, sin homogeneizacion ni valor final.

# Modulo

Valoracion inmobiliaria, testigos reutilizables, contexto de informe y smokes.

# Riesgo

Alto controlado: esquema defensivo y contexto de informes. Sin DB real, sin migracion destructiva y sin calculo final.

# Archivos permitidos

`app/database.py`, `app/main.py`, `app/services/informe.py`, `app/services/valoracion_comparacion.py`, templates de testigos/informe, tests smoke y documentacion de valoracion/harness.

# Archivos prohibidos

DB real, uploads reales, informes reales, backups, secretos, routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

`python3 scripts/audit_docs.py`, `python3 -m compileall app`, `.venv/bin/python -m pytest`, `bash scripts/finish_harness_task.sh`, `git diff --check`, `git status`.

# Rollback

Revertir cambios de codigo/documentacion. Las columnas nuevas son defensivas y no destructivas.

# Fuera de alcance

Homogeneizacion, ponderacion, scoring, outliers, scraping/OCR, valor final automatico y migracion legacy.

# Aprobacion humana requerida

No mientras no se toque DB real ni calculo final.

Estado: completado

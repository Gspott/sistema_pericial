# Valoracion Comparacion 2B Homogeneizacion

# Objetivo

Implementar FASE 2B: homogeneizacion manual/semiestructurada por testigo, calculando €/m² homogeneizado trazable sin ponderacion ni valor final.

# Modulo

Valoracion inmobiliaria, testigos vinculados, ajustes, contexto de informe y smokes.

# Riesgo

Alto controlado: esquema defensivo y contexto de informes. Se mantiene fallback legacy y fila legacy de ajustes separada.

# Archivos permitidos

`app/database.py`, `app/main.py`, `app/services/informe.py`, `app/services/valoracion_comparacion.py`, templates de ajustes/informe, tests smoke y docs/harness.

# Archivos prohibidos

DB real, uploads reales, informes generados reales, backups, secretos, routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

`python3 scripts/audit_docs.py`, `python3 -m compileall app`, `.venv/bin/python -m pytest`, `bash scripts/finish_harness_task.sh`, `git diff --check`, `git status`.

# Rollback

Revertir cambios de codigo y documentacion. Las columnas nuevas son defensivas y no destructivas.

# Fuera de alcance

Ponderacion, scoring, outliers, valor final automatico, scraping/OCR y migraciones legacy.

# Aprobacion humana requerida

No mientras no se toque DB real ni calculo final.

Estado: completado

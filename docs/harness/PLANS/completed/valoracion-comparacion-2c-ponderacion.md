# Valoracion Comparacion 2C Ponderacion

# Objetivo

Implementar Fase 2C de valoración: resumen comparativo y ponderación técnica no automática de testigos vinculados, partiendo del €/m² homogeneizado de Fase 2B.

# Modulo

Valoración inmobiliaria, testigos reutilizables, contexto de informe, HTML/PDF/DOCX y smoke tests.

# Riesgo

Medio. Se amplía esquema defensivo y contexto de informe sin borrar datos ni cerrar valor final.

# Archivos permitidos

`app/database.py`, `app/main.py`, `app/services/informe.py`, `app/services/valoracion_comparacion.py`, templates de valoración/informe, tests smoke y documentación/harness de valoración.

# Archivos prohibidos

DB real, uploads, informes generados, backups, secretos, routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

Pendientes al cierre: `python3 scripts/audit_docs.py`, `python3 -m compileall app`, `.venv/bin/python -m pytest`, `bash scripts/finish_harness_task.sh`, `git diff --check`, `git status`.

# Rollback

Revertir diff de código/docs. Las columnas añadidas son defensivas y no destructivas.

# Fuera de alcance

Scoring, outliers complejos, cálculo de valor final automático, scraping/OCR, migración destructiva y tasación hipotecaria regulada.

# Aprobacion humana requerida

Si aparece necesidad de tocar datos reales, migrar información existente o cerrar automáticamente el valor final.

Estado: completado

# Valoracion Eco Inspired Fase 1

# Objetivo

Implementar fase 1 ECO-inspired para valoracion pericial inmobiliaria: finalidad/alcance, base de valor, superficies profesionales, metodos aplicados/descartados, incidencias basicas, contexto de informe y salidas modernas HTML/DOCX.

# Modulo

Valoracion inmobiliaria, informes, modelo defensivo y smokes.

# Riesgo

Medio-alto: toca contexto compartido de informes y esquema defensivo. Se mantiene fallback legacy, sin migracion destructiva ni calculo definitivo.

# Archivos permitidos

`app/database.py`, `app/main.py`, `app/services/informe.py`, templates de valoracion/informe, tests smoke y documentacion de valoracion/harness.

# Archivos prohibidos

DB real, uploads, informes generados reales, backups, secretos, routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

`python3 scripts/audit_docs.py`, `python3 -m pytest`, `bash scripts/finish_harness_task.sh`, `git diff --check`, `git status`.

# Rollback

Revertir cambios de codigo/documentacion de la fase. Las columnas son defensivas y no destructivas.

# Fuera de alcance

Cálculo definitivo, homogeneización avanzada, scoring, scraping/OCR, migración de legacy y cambios destructivos.

# Aprobacion humana requerida

No requerida mientras las validaciones cierren y no se toque DB real.

Estado: completado

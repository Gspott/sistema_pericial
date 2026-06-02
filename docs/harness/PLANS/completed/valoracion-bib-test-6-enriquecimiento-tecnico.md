# Valoracion Bib Test 6 Enriquecimiento Tecnico

# Objetivo

Ampliar la ficha reusable de testigos inmobiliarios con atributos tecnicos de
anuncio y mejorar el pegado asistido local, manteniendo SSR, compatibilidad
legacy y flujos BIB-TEST anteriores.

# Modulo

Valoracion inmobiliaria: `testigos_valoracion`, alta rapida desktop,
heuristicas locales de texto pegado y smokes de biblioteca.

# Riesgo

Medio. La fase toca esquema defensivo de testigos, formulario SSR y heuristicas
de captura. No toca informes, Workbench ni datos reales.

# Archivos permitidos

- `app/database.py`
- `app/main.py`
- `templates/valoracion_testigo_biblioteca_form.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/modelos_datos.md`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB real, datos reales, uploads, informes reales, backups, secretos y logs.
- Carpeta anidada `sistema_pericial/`.
- Workbench, informes HTML/PDF/DOCX y routers legacy salvo necesidad
  documentada.

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

Revertir columnas defensivas, campos de alta rapida, heuristicas de pegado,
smokes y documentacion de esta fase. No hay migracion destructiva ni escritura
sobre DB real.

# Fuera de alcance

- Scraping, OCR o IA externa.
- Descarga o gestion de fotografias.
- Datos especificos de expediente, ponderacion, ajustes o Workbench.
- Informes HTML/PDF/DOCX.

# Aprobacion humana requerida

No prevista mientras se mantenga el alcance defensivo y no se toque DB real.

Estado: completado

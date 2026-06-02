# Valoracion Bib Test 3 Pegado Asistido

# Objetivo

Acelerar el alta rapida desktop de testigos permitiendo pegar texto bruto de
anuncios y aplicar sugerencias locales al formulario sin guardar todavia.

# Modulo

Valoracion inmobiliaria / biblioteca de testigos / alta rapida desktop.

# Riesgo

Bajo-medio: heuristicas locales SSR y template. No toca esquema, informes,
workbench ni conexiones externas.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_testigo_biblioteca_form.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`

# Archivos prohibidos

- DB reales, backups, uploads reales, informes generados, secretos.
- Carpeta anidada `sistema_pericial/`.
- Workbench, informes, calculo final, scraping/OCR/IA.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir heuristicas locales, seccion de template, smokes y documentacion.

# Fuera de alcance

- Scraping, OCR, IA externa o conexion a URLs.
- Persistir texto bruto como entidad propia.
- Vincular automaticamente a expedientes.
- Sobrescribir datos manuales salvo campo vacio.

# Aprobacion humana requerida

Si aparece necesidad de descargar contenido externo, crear entidad nueva o usar
IA/OCR.

Estado: completado

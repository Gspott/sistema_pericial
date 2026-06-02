# Valoracion Bib Test 2 Alta Rapida Desktop

# Objetivo

Crear un alta rapida desktop para introducir testigos inmobiliarios en la
biblioteca maestra, especialmente desde portales, sin sustituir el formulario
mobile-first existente.

# Modulo

Valoracion inmobiliaria / biblioteca de testigos.

# Riesgo

Bajo-medio: nueva ruta SSR y template sobre tabla existente. No cambia esquema,
no toca informes ni workbench salvo enlaces indirectos de biblioteca.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_testigo_biblioteca_form.html`
- `templates/valoracion_testigos_biblioteca.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`

# Archivos prohibidos

- DB reales, backups, uploads reales, informes generados, secretos.
- Carpeta anidada `sistema_pericial/`.
- Informes, calculo final, workbench, ponderacion de expediente.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir nueva ruta/template, enlaces de biblioteca, smokes y documentacion.

# Fuera de alcance

- Scraping automatico, OCR, IA o extraccion desde URL.
- Deduplicacion automatica, importacion masiva, mapas.
- Edicion inline o spreadsheet.
- Asignacion/vinculacion automatica a expedientes.
- Guardar peso, inclusion/exclusion o representatividad global.

# Aprobacion humana requerida

Si aparece necesidad de cambiar esquema, importar automaticamente datos externos
o vincular testigos a expedientes desde esta alta rapida.

Estado: completado

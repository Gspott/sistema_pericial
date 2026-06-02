# Valoracion Bib Test 4 Duplicados Defensivos

# Objetivo

Avisar de posibles testigos duplicados en el alta rapida desktop antes de
guardar, sin bloquear ni fusionar automaticamente.

# Modulo

Valoracion inmobiliaria / biblioteca de testigos / alta rapida desktop.

# Riesgo

Bajo-medio: preflight SSR de duplicados sobre tabla existente. No cambia
esquema, no borra ni fusiona datos.

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

Revertir preflight de duplicados, aviso visual, smokes y documentacion.

# Fuera de alcance

- Fusion automatica.
- Borrado de duplicados.
- Deduplicacion masiva.
- IA, scoring o normalizacion avanzada.

# Aprobacion humana requerida

Si se desea fusionar datos, borrar candidatos o convertir la deteccion en
bloqueante.

Estado: completado

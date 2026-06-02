# Valoracion Bib Test 8B Edicion Wide

# Objetivo

Optimizar la edicion desktop wide de testigos reutilizables, alineandola con la
biblioteca, alta rapida y detalle, sin tocar DB, calculos, Workbench ni
informes.

# Modulo

Valoracion inmobiliaria: formulario completo SSR de testigos reutilizables.

# Riesgo

Bajo-medio. Cambios visuales y inclusion de campos ya existentes en el modelo
defensivo; riesgo principal: romper mobile o no persistir campos tecnicos.

# Archivos permitidos

- `app/main.py` solo para constantes de formulario.
- `templates/valoracion_testigo_form.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB/esquema.
- Calculos, Workbench, informes.
- Datos reales, uploads reales, backups, secretos.
- Carpeta anidada `sistema_pericial/`.

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

Revertir constantes de formulario, template wide, smokes y docs de esta fase.
No hay persistencia nueva ni migracion.

# Fuera de alcance

- Crear rutas nuevas.
- Reemplazar alta rapida.
- Cambios de DB.
- Scraping/OCR/IA.
- Informes y Workbench.

# Aprobacion humana requerida

No prevista mientras se mantenga como UX incremental.

Estado: completado

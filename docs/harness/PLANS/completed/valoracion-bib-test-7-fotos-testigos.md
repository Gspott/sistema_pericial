# Valoracion Bib Test 7 Fotos Testigos

# Objetivo

Permitir y endurecer la subida manual de fotografias/capturas asociadas a
testigos reutilizables de valoracion, usando el patron existente de uploads y
`testigos_valoracion_fotos`, sin scraping ni descarga externa.

# Modulo

Valoracion inmobiliaria: ficha de testigo, uploads contextuales, biblioteca de
testigos y smokes.

# Riesgo

Medio-alto por tocar uploads. Se limita a DB/uploads temporales en smokes y a
validacion defensiva de imagenes; no hay escritura sobre datos reales.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_testigo_detalle.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB real, uploads reales, fotos reales, informes reales, backups, secretos y
  logs.
- Carpeta anidada `sistema_pericial/`.
- Informes HTML/PDF/DOCX, Workbench y routers legacy.

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

Revertir validacion de fotos, cambios de plantilla, smokes y documentacion. No
hay tabla nueva ni migracion destructiva.

# Fuera de alcance

- Descarga automatica desde URLs.
- Scraping, OCR o IA.
- Insercion automatica en informes.
- Borrado fisico de fotos/uploads.
- Optimizacion avanzada de imagenes fuera del patron existente.

# Aprobacion humana requerida

Requerida si se pretendiera tocar uploads reales, borrar fotos o insertar
imagenes en informes. No requerida para smokes con uploads temporales.

Estado: completado

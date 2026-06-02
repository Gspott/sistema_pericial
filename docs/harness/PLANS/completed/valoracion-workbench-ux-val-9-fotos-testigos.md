# Valoracion Workbench Ux Val 9 Fotos Testigos

# Objetivo

Mostrar en el Workbench de Valoracion fotografias/capturas manuales asociadas a
testigos vinculados para apoyar comparacion visual de estado, reforma y
calidades, sin tocar calculos ni informes.

# Modulo

Valoracion inmobiliaria / Workbench SSR / testigos reutilizables.

# Riesgo

Bajo-medio. Lectura de metadatos de fotos ya existentes; no hay escritura sobre
uploads ni cambios de DB.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_workbench.html`
- `tests/smoke/test_valoracion_workbench.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`

# Archivos prohibidos

- DB real, datos reales, backups, uploads reales, informes generados y secretos.
- Carpeta anidada `sistema_pericial/`.
- Informes HTML/PDF/DOCX.
- Biblioteca de Testigos salvo lectura de patrones existentes.
- Calculos, homogeneizacion y ponderacion.

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

Revertir cambios de `app/main.py`, `templates/valoracion_workbench.html`,
smokes y documentacion. No requiere restaurar DB ni uploads.

# Fuera de alcance

- Subir fotos desde el workbench.
- Insertar fotos en informes.
- Descargar imagenes externas.
- Scraping, OCR o IA.
- Cambios de calculo o valor final.

# Aprobacion humana requerida

No prevista salvo necesidad de escritura sobre datos/uploads reales, esquema o
informes.

Estado: completado

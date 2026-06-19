# Pericial Pdf V2 Navigation 1

# Objetivo

Convertir el índice del PDF V2 en navegación interna clicable mediante enlaces
HTML con anclas estables, sin alterar contenido, datos, numeración ni fusión
de PDFs externos.

# Modulo

Informes / PDF V2 / plantilla HTML imprimible y smoke tests.

# Riesgo

Crítico por afectar el PDF V2. Cambio limitado a navegación interna HTML/PDF;
no debe cambiar contenido técnico, paginación calculada, datos, lógica pericial
ni workflows ajenos.

# Archivos permitidos

- `templates/informes/v2_pdf.html`.
- `tests/smoke/test_pericial_workbench.py`.
- Documentación harness de esta tarea.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- PDFs externos fusionados.
- CRM, costes, valoración hipotecaria, editor V2 y módulos ajenos.
- Lógica pericial, contenido técnico y numeración.

# Playbook aplicable

Task Pack: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `python3 scripts/audit_docs.py`.
- `python3 -m compileall app`.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.
- `git diff --check`.

# Rollback

Revertir enlaces/anclas en la plantilla PDF V2, tests y documentación harness
de esta tarea.

# Fuera de alcance

- Bookmarks PDF nativos.
- Referencias cruzadas clicables fuera del índice.
- Navegación a figuras o fichas individuales.
- Cambios en PDFs externos fusionados.

# Aprobacion humana requerida

Si la implementación exige cambiar motor PDF, datos persistidos, orden de
fusión, numeración o contenido textual.

Estado: completado

# Pericial Pdf V2 Design 3

# Objetivo

Continuar la mejora editorial del PDF V2 reorganizando las fichas del Anexo C
en orden pericial natural (daños, observaciones, evidencias) y refinando indice,
portadillas, tablas y microtipografia sin cambiar contenido ni datos.

# Modulo

Informes / PDF V2 principal y anexos generados en `templates/informes/v2_pdf.html`.

# Riesgo

Critico por pertenecer a informes. Cambio limitado a renderizado visual y orden
de bloques ya existentes dentro de cada ficha del Anexo C.

# Archivos permitidos

- `templates/informes/v2_pdf.html`.
- `tests/smoke/test_pericial_workbench.py`.
- Documentacion de cierre en `docs/harness/EPISODES/` y este plan.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- PDFs externos fusionados en Anexo A.
- Modelos, logica pericial, numeraciones, referencias, textos generados, editor V2,
  CRM, valoracion hipotecaria, costes y workflows ajenos.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `git diff --check`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.

# Rollback

Revertir cambios de plantilla, test y documentacion harness de esta tarea.

# Fuera de alcance

- Cambiar contenido tecnico/juridico, orden de capitulos, datos o logica pericial.
- Alterar PDFs externos aportados por terceros.
- Cambiar paginacion final salvo desplazamientos inevitables por CSS.

# Aprobacion humana requerida

Solo si aparece necesidad de cambiar estructura pericial, datos, anexos externos,
conclusiones, generacion real de documentos o flujos fuera del PDF V2.

Estado: completado

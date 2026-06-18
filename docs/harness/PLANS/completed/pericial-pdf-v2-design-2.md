# Pericial Pdf V2 Design 2

# Objetivo

Unificar el estilo editorial del PDF V2 principal con los anexos generados por
el sistema y eliminar el rotulo superior automatico "PATOLOGIAS" de las paginas
renderizadas por Playwright.

# Modulo

Informes / PDF V2 principal y anexos generados por el sistema dentro de
`templates/informes/v2_pdf.html`.

# Riesgo

Critico por pertenecer a informes. Alcance limitado a renderizado visual
PDF V2, sin modificar contenido, datos, orden, logica pericial ni PDFs externos
fusionados.

# Archivos permitidos

- `templates/informes/v2_pdf.html`.
- `app/services/informe.py` solo para cabecera/pie Playwright del PDF V2.
- `tests/smoke/test_pericial_workbench.py`.
- Documentacion de cierre en `docs/harness/EPISODES/` y este plan.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- PDFs externos aportados por terceros y fusionados dentro del Anexo A.
- Editor V2, CRM, valoracion hipotecaria, costes, mediciones y workflows ajenos.
- Cambios de contenido tecnico/juridico, orden de capitulos, numeracion o referencias.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `git diff --check`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.

# Rollback

Revertir cambios de servicio, plantilla, test y documentacion harness de esta
tarea. No hay migraciones ni artefactos generados versionados.

# Fuera de alcance

- Eliminar rotulos embebidos dentro de PDFs externos aportados por terceros.
- Alterar imagenes, pies de foto, numeracion, referencias o textos.
- Cambiar paginacion final, salvo desplazamientos inevitables por CSS.

# Aprobacion humana requerida

Solo si aparece necesidad de cambiar estructura pericial, datos, anexos
externos, conclusiones, generacion real de documentos o flujos fuera del PDF V2.

Estado: completado

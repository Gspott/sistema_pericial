# Pericial Pdf V2 Design 4

# Objetivo

Refinar el PDF V2 con foco en sobriedad documental: portada principal,
Anexo A y pie de pagina profesional, sin branding de Sistema Pericial.

# Modulo

Informes / PDF V2 principal y anexos generados por el sistema.

# Riesgo

Critico por pertenecer a informes. Cambio limitado a renderizado visual y
metadatos impresos, sin modificar datos, modelos, logica pericial ni PDFs
externos fusionados.

# Archivos permitidos

- `templates/informes/v2_pdf.html`.
- `app/services/informe.py` solo para footer Playwright del PDF V2.
- `app/main.py` solo para portadillas generadas del Anexo A.
- `tests/smoke/test_pericial_workbench.py`.
- Documentacion de cierre en `docs/harness/EPISODES/` y este plan.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- PDFs externos fusionados en Anexo A.
- Modelos, logica pericial, numeraciones, referencias, textos generados, editor V2,
  CRM, valoracion hipotecaria, costes y workflows ajenos.
- Branding o referencias a Sistema Pericial en el PDF.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `git diff --check`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.

# Rollback

Revertir cambios de plantilla, servicio, portadillas, test y documentacion
harness de esta tarea.

# Fuera de alcance

- Cambiar contenido tecnico/juridico, datos, modelos o logica pericial.
- Alterar PDFs externos aportados por terceros.
- Cambiar paginacion final salvo desplazamientos inevitables por CSS.

# Aprobacion humana requerida

Solo si aparece necesidad de cambiar estructura pericial, datos, anexos externos,
conclusiones, generacion real de documentos o flujos fuera del PDF V2.

Estado: completado

# Pericial Pdf V2 Anexo A Cleanup 1

# Objetivo

Corregir errores funcionales de numeracion y renderizado duplicado en Anexo A
del PDF V2: relacion documental sin numeracion, documentos reales empezando en
A.1 y eliminacion de tabla/listado repetido en fusion.

# Modulo

Informes / PDF V2 / Anexo A.

# Riesgo

Critico por pertenecer a informes. Cambio limitado a numeracion y renderizado
del Anexo A, sin tocar PDFs externos, contenido, orden documental ni paginacion
final.

# Archivos permitidos

- `templates/informes/v2_pdf.html`.
- `app/main.py` solo para numeracion y fusion del Anexo A.
- `tests/smoke/test_pericial_workbench.py`.
- Documentacion de cierre en `docs/harness/EPISODES/` y este plan.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- PDFs externos aportados por terceros.
- Orden de documentos, contenido tecnico/juridico, logica pericial general,
  resto de anexos y paginacion final.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2_master_con_anexo_pequeno_responde or pdf_v2_integra_anexo_a_como_portadilla_mas_documento"`.
- `git diff --check`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.

# Rollback

Revertir cambios de plantilla, fusion/numeracion de Anexo A, tests y
documentacion harness de esta tarea.

# Fuera de alcance

- Cambiar PDFs externos fusionados.
- Cambiar contenido, datos, modelos, orden documental o paginacion final.
- Modificar anexos B-F o mejoras esteticas no relacionadas.

# Aprobacion humana requerida

Solo si aparece necesidad de cambiar estructura pericial, documentos externos,
orden documental, datos o flujos fuera del Anexo A PDF V2.

Estado: completado

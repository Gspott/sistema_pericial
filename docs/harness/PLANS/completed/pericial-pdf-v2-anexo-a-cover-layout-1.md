# Pericial Pdf V2 Anexo A Cover Layout 1

# Objetivo

Mejorar exclusivamente la maquetacion de las portadillas internas de documentos
del Anexo A del PDF V2, con composicion centrada y titulos largos completos.

# Modulo

Informes / PDF V2 / Portadillas internas Anexo A.

# Riesgo

Critico por pertenecer a informes. Cambio limitado a generacion visual ReportLab
de portadillas del Anexo A, sin alterar documentos, orden, numeracion ni fusion.

# Archivos permitidos

- `app/main.py` solo en `_pdf_bytes_ficha_anexo_a_v2`.
- `tests/smoke/test_pericial_workbench.py`.
- Documentacion de cierre en `docs/harness/EPISODES/` y este plan.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- PDFs externos fusionados en Anexo A.
- Orden documental, numeracion documental, anexos B-F, portada principal, indice,
  logica pericial, datos, persistencia y paginacion final.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `python3 scripts/audit_docs.py`.
- `python3 -m compileall app`.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2_anexo_a_genera_indice_y_ficha_documental or pdf_v2_master_con_anexo_pequeno_responde"`.
- `git diff --check`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.

# Rollback

Revertir cambios de portadilla ReportLab, tests y documentacion harness de esta
tarea.

# Fuera de alcance

- Cambiar contenido de documentos, PDFs externos, orden o numeracion documental.
- Tocar anexos B-F, portada principal, indice, logica pericial, datos o paginacion.

# Aprobacion humana requerida

Solo si aparece necesidad de cambiar contenido documental, fusion, numeracion,
datos o flujos fuera de portadillas internas del Anexo A.

Estado: completado

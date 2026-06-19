# Pericial Pdf V2 Navigation 3 Fix 2

# Objetivo

Corregir definitivamente el mapeo de enlaces internos del índice PDF V2 para que cada entrada apunte a la página visible indicada en el propio índice, no solo a una acción `/GoTo` formalmente válida.

# Modulo

Informes / PDF V2 / Navegación interna.

# Riesgo

Bajo-medio. Cambio acotado al postproceso PDF V2 y a la propagación del índice paginado ya calculado. No modifica contenido, textos, datos, orden documental, PDFs externos ni editor V2.

# Archivos permitidos

`app/main.py`, `app/services/informe.py`, `tests/smoke/test_pericial_workbench.py` y documentación harness asociada.

# Archivos prohibidos

Bases SQLite reales, uploads, backups, logs, informes generados, PDFs externos, CRM, costes, facturación, editor V2 y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Diagnóstico

El PDF real confirma que el postproceso ya convierte enlaces internos a `/A /GoTo`, pero el mapa `target_id -> page_index` sigue usando destinos nominales defectuosos en algunos casos. El síntoma es que capítulos y anexos técnicos terminan apuntando a página 2 aunque el índice visual muestra páginas distintas.

# Implementación

- Conservar `indice_paginas` en el contexto original del PDF V2 para que llegue al postproceso final.
- Registrar destinos derivados del índice visual paginado como fuente autoritativa para `pdf-target-*`.
- Mantener destinos nominales de Chromium y búsqueda por texto como respaldo.
- Añadir un smoke estructural con 120 páginas que verifica destinos concretos: Resumen ejecutivo 4, Antecedentes 6, Metodología 8, Conclusiones 17, Anexos 19/28/68, Documentación 88 y Documento 1/4 en 91/117.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`

# Rollback

Revertir los cambios de los archivos permitidos. No hay migraciones, cambios de esquema ni modificación de datos.

# Fuera de alcance

No modificar contenido del informe, índice visual, nomenclatura documental, bookmarks salvo coherencia indirecta, editor V2, buscar/reemplazar, PDFs externos ni paginación final.

# Aprobacion humana requerida

No requerida.

Estado: completado

# Pericial Pdf V2 Navigation 3 Fix 1

# Objetivo

Corregir la navegación interna del índice del PDF V2 para que todas las entradas clicables terminen como acciones PDF `/GoTo` válidas.

# Modulo

Informes / PDF V2 / Navegación interna.

# Riesgo

Bajo-medio. Cambio acotado al postproceso PDF V2 y tests estructurales. No modifica contenido, textos, datos, orden documental, paginación final ni PDFs externos.

# Archivos permitidos

`app/main.py`, `tests/smoke/test_pericial_workbench.py`, documentación harness asociada.

# Archivos prohibidos

Bases SQLite reales, uploads, backups, logs, informes generados, PDFs externos, editor V2, buscar/reemplazar, CRM, costes, facturación y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Diagnóstico

Chromium genera los enlaces internos HTML como anotaciones `/Link` con `/Dest` nominal y además incluye una tabla de destinos nominales (`reader.named_destinations`) con la página y coordenadas reales de cada ancla. El código anterior intentaba reconstruir el mapa `target_id -> page_index` buscando textos extraídos de páginas. Cuando esa búsqueda fallaba para capítulos/anexos, la anotación quedaba como `/Dest` nominal sin convertirse a `/A /GoTo`, lo que en Vista Previa de macOS se comportaba como selección sin navegación.

# Implementación

- Leer primero `reader.named_destinations` del PDF generado por Chromium.
- Registrar esos destinos como fuente principal para `pdf-target-*`.
- Conservar la búsqueda por texto como fallback para portadillas/documentos o casos sin destino nominal.
- Convertir cada anotación interna conocida a `/A << /S /GoTo /D [...] >>`.
- Preservar destinos `/XYZ` con coordenadas cuando Chromium las aporta; usar `/Fit` como fallback.
- Reforzar tests estructurales para comprobar que no quedan `/Dest` nominales en las entradas del índice y que cada `/GoTo` apunta a una página válida.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`

# Rollback

Revertir los cambios de los archivos permitidos. No hay migraciones, cambios de esquema ni modificación de datos.

# Fuera de alcance

No cambiar índice visual, bookmarks salvo consistencia indirecta, editor V2, búsqueda/reemplazo, contenido técnico, anexos externos ni paginación final.

# Aprobacion humana requerida

No requerida.

Estado: completado

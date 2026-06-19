# Pericial Pdf V2 Navigation 3 Editor Sync 1

# Objetivo

Corregir la navegación del PDF V2 tras la reorganización documental, desglosar la documentación aportada en el índice, sincronizar la nomenclatura visible del editor con la estructura actual y añadir una herramienta segura de buscar/reemplazar en capítulos del Informe V2.

# Modulo

Informes / PDF V2 / Editor Informe V2.

# Riesgo

Bajo-medio. Cambios acotados a renderizado PDF V2, postproceso de navegación PDF y editor V2. No se modifican datos reales, anexos externos, CRM, costes ni lógica pericial de cálculo.

# Archivos permitidos

`app/main.py`, `app/services/informe.py`, `templates/informes/v2_pdf.html`, `templates/informe_v2_editor.html`, `tests/smoke/test_pericial_workbench.py`, documentación harness asociada.

# Archivos prohibidos

Bases SQLite, uploads, backups, logs, PDFs externos fusionados, workflows CRM/costes/valoración hipotecaria y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Diagnóstico inicial

- Los enlaces del índice generados por Chromium quedan como destinos nominales (`/Dest /pdf-target-*`). Tras el postproceso con `pypdf`, algunos visores como Vista Previa de macOS pueden seleccionar el enlace pero no resolver el destino.
- La documentación aportada ya se fusiona al final del master, pero el índice visual solo mostraba el bloque general.
- El editor conservaba rótulos visibles antiguos: documentación como Anexo A, reportaje como Anexo B, fichas como Anexo C y mediciones como Anexo F.
- El editor no tenía una herramienta controlada para reemplazar referencias manuales antiguas en capítulos.

# Implementación

- Índice PDF: añade subentradas `Documento N. Nombre` bajo documentación aportada, con página de inicio calculada en la segunda pasada del PDF y tercera pasada defensiva si cambia el total de páginas.
- Navegación PDF: normaliza anotaciones internas del índice a acciones `/GoTo` explícitas a páginas concretas, conservando bookmarks jerárquicos.
- Editor V2: sincroniza rótulos visibles con anexos técnicos A-E y documentación aportada final.
- Buscar/reemplazar: añade UI mínima y endpoints JSON para contar coincidencias, reemplazar en capítulo actual o en todo el informe, con bloqueo de búsqueda vacía y control `updated_at`.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2 or informe_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`

# Rollback

Revertir los cambios de los archivos permitidos de esta tarea. No hay migraciones ni cambios de esquema.

# Fuera de alcance

No se implementan referencias cruzadas clicables a figuras/fichas, no se reescriben textos manuales automáticamente y no se modifica el contenido de PDFs externos fusionados.

# Aprobacion humana requerida

No requerida para los cambios implementados.

Estado: completado

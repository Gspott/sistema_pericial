# Informe V2 Find Replace 2

# Objetivo

Mejorar buscar/reemplazar del Informe V2 Editor para mostrar coincidencias con contexto y permitir aprobar sustituciones una a una.

# Modulo

Informes / Editor Informe V2.

# Riesgo

Bajo-medio. Cambios acotados al editor V2, endpoints JSON de capítulos y tests smoke. No se modifican anexos generados, PDFs externos, datos reales ni lógica pericial de cálculo.

# Archivos permitidos

`app/main.py`, `templates/informe_v2_editor.html`, `tests/smoke/test_pericial_workbench.py`, documentación harness asociada.

# Archivos prohibidos

Bases SQLite reales, uploads, backups, logs, informes generados, PDFs externos, workflows CRM/costes/facturación/valoración hipotecaria y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Diagnóstico

La herramienta anterior solo exponía un contador y dos acciones amplias. El backend podía reemplazar un capítulo completo o todo el informe, pero no identificaba una aparición concreta. Para revisar sustituciones una a una era necesario modelar cada coincidencia con capítulo, posición, texto esperado y contexto.

# Implementación

- La búsqueda devuelve lista de coincidencias con capítulo, índice, contexto anterior/posterior y texto encontrado.
- La UI renderiza una lista revisable con texto resaltado, estado pendiente/reemplazada/omitida y acciones por coincidencia.
- El reemplazo individual y el reemplazo global de pendientes usan `alcance=seleccion`, validando `updated_at` y que el texto esperado siga en la misma posición.
- Se elimina el botón de reemplazo en capítulo actual.
- Se mantiene el endpoint antiguo para compatibilidad con `alcance=actual`/`todo`, aunque la UI nueva usa selección.

# Validaciones

`python3 scripts/audit_docs.py`, `python3 -m compileall app`, `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "informe_v2 or pdf_v2"`, `bash scripts/finish_harness_task.sh --smoke-scope app`, `git diff --check`.

# Rollback

Revertir los cambios de los archivos permitidos. No hay migraciones ni cambios de esquema.

# Fuera de alcance

No implementar búsqueda difusa, regex, reemplazo en anexos generados, PDFs externos ni contenido estructural HTML.

# Aprobacion humana requerida

No requerida mientras el cambio quede limitado al editor V2 y tests.

Estado: completado

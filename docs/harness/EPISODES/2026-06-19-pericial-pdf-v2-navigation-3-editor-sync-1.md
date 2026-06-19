# PERICIAL-PDF-V2-NAVIGATION-3-EDITOR-SYNC-1

Fecha: 2026-06-19

## Objetivo

Mejorar la navegación interna del PDF V2 tras la reorganización documental, desglosar la documentación aportada en el índice, sincronizar la nomenclatura visible del editor y añadir una herramienta de buscar/reemplazar para capítulos del Informe V2.

## Diagnóstico

- Chromium genera enlaces internos de índice como destinos nominales (`/Dest /pdf-target-*`).
- Tras la reescritura del PDF con `pypdf`, algunos visores resuelven peor esos destinos nominales. Vista Previa de macOS puede mostrar selección/click sin ejecutar navegación.
- La documentación aportada se fusiona al final del master, por lo que sus páginas reales no están disponibles como anclas HTML nativas durante el primer render.
- El editor conservaba rótulos visibles de la estructura antigua de anexos.

## Cambios

- Se añadieron subentradas de documentos aportados al índice del PDF V2 con nombres reales y páginas de inicio calculadas.
- Se añadieron anclas HTML de respaldo para documentos aportados y un postproceso `pypdf` que convierte enlaces internos a acciones `/GoTo` explícitas.
- Se conservaron los bookmarks jerárquicos existentes.
- Se actualizó la nomenclatura visible del editor: Anexo A reportaje, Anexo B fichas, Anexo C valoración, Anexo D análisis partida nº 4, Anexo E mediciones y documentación aportada como bloque final.
- Se añadió buscar/reemplazar en capítulos con conteo, reemplazo en capítulo actual, reemplazo global, bloqueo de búsqueda vacía y control `updated_at`.

## Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2 or informe_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (autoescalado a `full`, 269 tests OK)
- `git diff --check`

## Cierre

Plan movido a `docs/harness/PLANS/completed/pericial-pdf-v2-navigation-3-editor-sync-1.md` y métricas actualizadas por el harness.

# PERICIAL-PDF-V2-NAVIGATION-3-FIX-1

Fecha: 2026-06-19

## Objetivo

Corregir los enlaces internos del índice del PDF V2 para que todas las entradas principales naveguen correctamente mediante acciones PDF `/GoTo`.

## Causa Raíz

Chromium genera anotaciones `/Link` con `/Dest` nominal y una tabla interna de destinos nominales con página y coordenadas reales. El postproceso anterior intentaba reconstruir el mapa de destinos mediante extracción de texto. Cuando esa extracción no resolvía capítulos o anexos, la anotación quedaba con `/Dest` nominal y Vista Previa de macOS podía seleccionarla sin navegar.

## Cambios

- El postproceso PDF V2 lee `reader.named_destinations` como fuente principal para resolver `pdf-target-*`.
- La búsqueda por texto queda como fallback.
- Las anotaciones internas se convierten a `/A /GoTo`.
- Los destinos `/XYZ` generados por Chromium conservan coordenadas cuando existen.
- Se añadió un smoke estructural con PDF generado por Chromium para verificar que todas las anotaciones del índice quedan sin `/Dest` residual y apuntan a páginas válidas.

## Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "bookmarks or destinos_nominales"`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (autoescalado a full, 270 tests OK)
- `git diff --check`

## Cierre

Plan movido a `docs/harness/PLANS/completed/pericial-pdf-v2-navigation-3-fix-1.md` y métricas actualizadas por el harness.

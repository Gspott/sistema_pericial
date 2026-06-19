# PERICIAL-PDF-V2-BOOKMARKS-FIX-1

Fecha: 2026-06-19

## Objetivo

Corregir los bookmarks/outlines del PDF V2 para que usen la misma fuente fiable que los enlaces del índice impreso: `indice_paginas`.

## Causa Raíz

Los enlaces internos del índice ya se normalizaban con páginas finales de `indice_paginas`, pero los bookmarks seguían calculando sus destinos por búsqueda de texto. En documentos largos, esa búsqueda podía resolver capítulos y anexos técnicos a la página del índice, provocando que Vista Previa de macOS mostrase marcadores formalmente válidos pero con destino incorrecto.

## Cambios

- Se añadió un resolvedor de páginas para bookmarks con prioridad en `indice_paginas`.
- Los destinos registrados y la extracción de texto quedan como fallback, no como fuente principal.
- Los bookmarks de capítulos, anexos técnicos, documentación aportada y documentos usan las claves finales del índice.
- Se añadieron bookmarks explícitos para Portada e Índice bajo el nodo Informe.
- Se añadió un smoke estructural con pypdf para validar jerarquía y páginas concretas del outline.

## Validaciones

- `python3 scripts/audit_docs.py` OK, con avisos históricos existentes sobre planes antiguos y monolito `app/main.py`.
- `python3 -m compileall app` OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "bookmarks_usan_paginas"` OK, 1 passed.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "bookmarks or destinos_nominales or indice_resuelve_goto"` OK, 4 passed.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"` OK, 35 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` OK, autoescalado a full, 273 passed.
- `git diff --check` OK.

## Cierre

Plan movido a `docs/harness/PLANS/completed/pericial-pdf-v2-bookmarks-fix-1.md` mediante `finish_harness_task`.

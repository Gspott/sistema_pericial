# PERICIAL-PDF-V2-NAVIGATION-3-FIX-2

Fecha: 2026-06-19

## Objetivo

Corregir el mapeo de enlaces internos del índice del PDF V2 para que cada `/GoTo` apunte a la página visible indicada en el propio índice.

## Causa Raíz

El postproceso posterior a `PERICIAL-PDF-V2-NAVIGATION-3-FIX-1` convertía correctamente las anotaciones internas a acciones PDF `/GoTo`, pero seguía tomando como fuente principal destinos nominales que en el PDF real podían resolver varias entradas a página 2. Por eso Vista Previa de macOS veía enlaces válidos, pero capítulos y anexos técnicos navegaban a la página incorrecta.

## Cambios

- El generador de PDF V2 conserva `indice_paginas` en el contexto original para que llegue al postproceso final.
- El postproceso registra los destinos del índice visual paginado como fuente autoritativa para `pdf-target-*`.
- Los destinos nominales de Chromium y la búsqueda por texto permanecen como respaldo.
- Se añadió un smoke estructural que valida páginas concretas de capítulos, anexos técnicos, documentación aportada, Documento 1 y Documento 4.

## Validaciones

- `python3 scripts/audit_docs.py` OK, con avisos históricos existentes sobre planes antiguos y monolito `app/main.py`.
- `python3 -m compileall app` OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "indice_resuelve_goto"` OK, 1 passed.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"` OK, 34 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` OK, autoescalado a full, 272 passed.
- `git diff --check` OK.

## Cierre

Plan movido a `docs/harness/PLANS/completed/pericial-pdf-v2-navigation-3-fix-2.md` mediante `finish_harness_task`.

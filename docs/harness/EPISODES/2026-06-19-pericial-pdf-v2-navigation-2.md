# Episode: Pericial Pdf V2 Navigation 2

## Fecha

2026-06-19


## Tarea

PERICIAL-PDF-V2-NAVIGATION-2

## Plan asociado

pericial-pdf-v2-navigation-2.md


## Task Pack usado

`docs/harness/TASK_PACKS/informe_change.md`

## Objetivo

Añadir marcadores PDF nativos (Outline/Bookmarks) al PDF V2 final para que los
visores compatibles muestren un panel lateral de navegación, sin modificar
contenido, textos, datos, paginación ni PDFs externos.

## Archivos modificados

- `app/main.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-v2-navigation-2.md`
- `docs/harness/EPISODES/2026-06-19-pericial-pdf-v2-navigation-2.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `bash scripts/start_harness_task.sh PERICIAL-PDF-V2-NAVIGATION-2 docs/harness/TASK_PACKS/informe_change.md`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2_agrega_bookmarks_jerarquicos"`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`
- `git diff --check`

## Resultado

Se añade `agregar_bookmarks_pdf_v2()` como post-proceso del PDF final, después
de render, fusión de anexos y paginación. El helper usa `pypdf` para copiar las
páginas finales y crear `/Outlines` jerárquicos.

Jerarquía creada:

- `Informe`
  - capítulos principales
  - conclusiones
- `Anexos técnicos`
  - Anexo A-E
- `Documentación aportada al expediente`
  - relación documental
  - documentos aportados localizables por portadilla

La localización de destinos se hace por texto extraído con
`encontrar_pagina_pdf_v2`, evitando depender de páginas fijas.

## Warnings

`audit_docs.py` mantiene warnings históricos del repositorio sobre
`app/main.py` monolítico y planes completados antiguos sin contenido real.
No se han introducido warnings nuevos asociados a esta tarea.

## Rollback

Revertir `agregar_bookmarks_pdf_v2()`, su llamada en el endpoint PDF V2, los
helpers/aserciones smoke y esta documentación harness.

## Memoria actualizada

No aplica fuera de la documentación harness y métricas generadas por el cierre.

## Decisiones humanas

Solicitud directa del usuario. No se modifica índice visual, contenido,
orden documental, PDFs externos ni editor V2.

## Proximos pasos

Revisión manual en Acrobat, Preview de macOS, Archivos de iPadOS/iOS y
navegadores modernos con un PDF master real de prueba.

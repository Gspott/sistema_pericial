# Episode: Pericial Pdf Cleanup 1

## Fecha

2026-06-07


## Tarea

PERICIAL-PDF-CLEANUP-1: limpieza editorial del PDF Pericial V2.

## Plan asociado

pericial-pdf-cleanup-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/informe_change.md`

## Objetivo

Eliminar vocabulario interno de sistema en el PDF V2 y separar la informacion de
trabajo del contenido entregable del informe.

## Archivos modificados

- `app/main.py`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-cleanup-1.md`
- `docs/harness/EPISODES/2026-06-07-pericial-pdf-cleanup-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecuto smoke completo: 141 passed, 1 skipped.

## Resultado

Se crea una capa de presentacion `contenido_pdf` que limpia terminos internos
sin modificar `contenido` guardado en `informe_v2_capitulos`.

La plantilla V2 deja de mostrar metadatos editoriales como contenido guardado,
ultima actualizacion, referencias a `informe_v2_capitulos`, capitulos
pendientes en editor y referencias internas a PDF-V2-2.

Las lineas de inventario con `rol pendiente` y conteo de fotos se presentan en
lenguaje de informe.

## Warnings

`python3 scripts/audit_docs.py` mantiene warning informativo preexistente de
monolito estructural en `app/main.py`.

El cierre harness marco 1 skip en un test de valoracion por Playwright/Chromium
no disponible en este entorno.

## Rollback

Revertir los archivos listados. No hay cambios de base de datos ni persistencia.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

PERICIAL-PDF-V2-2: anexos fotográfico y de patologías, manteniendo separación
entre contenido técnico redactado y presentación PDF.

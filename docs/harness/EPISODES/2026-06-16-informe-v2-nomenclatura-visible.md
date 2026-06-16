# Episode: Informe V2 Nomenclatura Visible

## Fecha

2026-06-16


## Tarea

Limpieza de nomenclatura visible del modulo tecnico interno informe_v2.

## Plan asociado

informe-v2-nomenclatura-visible.md


## Task Pack usado

docs/harness/TASK_PACKS/informe_change.md

## Objetivo

Eliminar referencias visibles a V2 en editor, Workbench, PDF, pie de pagina,
mensajes y nombres de descarga, manteniendo rutas e identificadores internos.

## Archivos modificados

- app/main.py
- app/services/informe.py
- templates/informe_v2_editor.html
- templates/informes/v2_pdf.html
- templates/pericial_workbench.html
- templates/detalle_expediente.html
- tests/smoke/test_pericial_workbench.py
- docs/harness/METRICS.md

## Validaciones ejecutadas

- python3 -m compileall app
- .venv/bin/pytest tests/smoke/test_pericial_workbench.py -q
- .venv/bin/pytest -q
- python3 scripts/audit_docs.py
- git diff --check
- bash scripts/finish_harness_task.sh

## Resultado

Implementado. La superficie visible habla de Informe, Informe pericial,
Editor de informe y Generar PDF. El PDF usa portada y pie sin V2.

## Warnings

Quedan referencias internas a v2 en rutas, nombres de plantilla, clases CSS,
funciones, tablas, tests y documentacion harness para compatibilidad.

## Rollback

Revertir los cambios en los archivos listados.

## Memoria actualizada

Plan cerrado por harness y metricas actualizadas.

## Decisiones humanas

No se refactorizan identificadores internos ni endpoints.

## Proximos pasos

Sin pasos pendientes.

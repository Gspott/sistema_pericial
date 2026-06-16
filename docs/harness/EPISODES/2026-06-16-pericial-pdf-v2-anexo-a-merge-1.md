# Episode: Pericial Pdf V2 Anexo A Merge 1

## Fecha

2026-06-16


## Tarea

PERICIAL-PDF-V2-ANEXO-A-MERGE-1

## Plan asociado

pericial-pdf-v2-anexo-a-merge-1.md


## Task Pack usado

docs/harness/TASK_PACKS/informe_change.md

## Objetivo

Anexar fisicamente al PDF V2 las paginas de los PDFs aportados al Anexo A,
manteniendo la tabla/listado existente.

## Archivos modificados

- app/main.py
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

Implementado merge tolerante con pypdf para documentos PDF del Anexo A. Se
resuelve la ruta bajo uploads, se omiten documentos no PDF e internos de otros
anexos, y se mantiene el PDF V2 si algun PDF aportado falta o esta corrupto.

## Warnings

Los PDFs de Anexo A se anexan tras generar el PDF V2 completo. Si un PDF no se
puede leer, queda listado en Anexo A y se registra warning en logs.

## Rollback

Revertir cambios en app/main.py y tests/smoke/test_pericial_workbench.py.

## Memoria actualizada

Plan cerrado por harness y metricas actualizadas.

## Decisiones humanas

La peticion permite fusion fisica de PDFs de Anexo A; se excluye el PDF interno
de mediciones de Anexo F.

## Proximos pasos

Sin pasos pendientes.

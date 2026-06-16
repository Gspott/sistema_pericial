# Episode: Pericial Wb Anexo A Delete 1

## Fecha

2026-06-15


## Tarea

PERICIAL-WB-ANEXO-A-DELETE-1

## Plan asociado

pericial-wb-anexo-a-delete-1.md


## Task Pack usado

docs/harness/TASK_PACKS/informe_change.md

## Objetivo

Permitir eliminar de forma visible y segura documentos PDF del Anexo A desde el
Workbench pericial.

## Archivos modificados

- app/main.py
- templates/pericial_workbench.html
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

Implementado endpoint POST de eliminacion con validacion de ownership,
pertenencia al expediente, borrado de registro y borrado tolerante del archivo
fisico dentro de uploads. La UI mantiene Guardar y anade Eliminar con confirmacion.

## Warnings

Se reutiliza el helper seguro existente para resolver rutas relativas bajo
uploads; si el archivo fisico ya no existe, la eliminacion del registro continua.

## Rollback

Revertir los cambios de app/main.py, templates/pericial_workbench.html y
tests/smoke/test_pericial_workbench.py.

## Memoria actualizada

Plan cerrado por harness y metricas actualizadas.

## Decisiones humanas

La peticion de usuario autoriza borrar documentos del Anexo A mediante accion
POST confirmada.

## Proximos pasos

Sin pasos pendientes.

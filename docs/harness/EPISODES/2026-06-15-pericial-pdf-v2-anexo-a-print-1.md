# Episode: Pericial Pdf V2 Anexo A Print 1

## Fecha

2026-06-15


## Tarea

PERICIAL-PDF-V2-ANEXO-A-PRINT-1

## Plan asociado

pericial-pdf-v2-anexo-a-print-1.md


## Task Pack usado

docs/harness/TASK_PACKS/informe_change.md

## Objetivo

Hacer que el PDF V2 refleje correctamente los documentos aportados al Anexo A
desde el Workbench pericial, incluyendo el nombre de archivo original y
respetando marcas opcionales de inclusion.

## Archivos modificados

- app/main.py
- templates/informes/v2_pdf.html
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

Implementado. El Anexo A del PDF V2 lista nombre visible, tipo, archivo,
fecha y descripcion. Se excluyen adjuntos internos de otros anexos y se
respetan campos opcionales incluir_en_anexo_a, incluir_en_anexo o incluir_en_pdf
si existen en el futuro.

## Warnings

El esquema actual no contiene campo de inclusion; por compatibilidad, todos los
documentos de Workbench en expediente_documentos se consideran incluidos salvo
marca opcional explicita en el diccionario de contexto.

## Rollback

Revertir cambios en app/main.py, templates/informes/v2_pdf.html y
tests/smoke/test_pericial_workbench.py.

## Memoria actualizada

Plan cerrado por harness y metricas actualizadas.

## Decisiones humanas

La peticion indica no fusionar PDFs externos en esta fase.

## Proximos pasos

Sin pasos pendientes.

# Episode: Informe V2 Anexo F Pdf Mediciones

## Fecha

2026-06-15


## Tarea

Incorporar un PDF externo de mediciones al Anexo F del Informe V2, con subida,
reemplazo, eliminacion y fusion al PDF final.

## Plan asociado

informe-v2-anexo-f-pdf-mediciones.md


## Task Pack usado

docs/harness/TASK_PACKS/informe_change.md

## Objetivo

Permitir que el informe principal mantenga el resumen F.1-F.3 y que el PDF final
anexe, tras una separadora F.4, el desarrollo completo de mediciones exportado
desde hoja de calculo.

## Archivos modificados

- app/main.py
- templates/informe_v2_editor.html
- templates/informes/v2_pdf.html
- tests/smoke/test_pericial_workbench.py
- requirements.txt
- docs/harness/METRICS.md

## Validaciones ejecutadas

- python3 -m compileall app
- .venv/bin/pytest tests/smoke/test_pericial_workbench.py -q
- .venv/bin/pytest -q
- python3 scripts/audit_docs.py
- git diff --check
- bash scripts/finish_harness_task.sh

## Resultado

Implementado y validado. El adjunto se guarda en expediente_documentos con tipo
interno especifico de Informe V2 Anexo F y se fusiona al PDF final mediante
pypdf cuando existe.

## Warnings

La numeracion del pie generado por Playwright no se recalcula sobre las paginas
externas fusionadas con pypdf; las paginas anexadas conservan su propio contenido
sin footer nuevo.

## Rollback

Revertir los cambios en app/main.py, templates/informe_v2_editor.html,
templates/informes/v2_pdf.html, tests/smoke/test_pericial_workbench.py y
requirements.txt. Los adjuntos se desvinculan eliminando las filas
expediente_documentos con tipo informe_v2_anexo_f_mediciones.

## Memoria actualizada

Plan cerrado por harness y metricas actualizadas.

## Decisiones humanas

La peticion de usuario autorizo eliminar/reemplazar el PDF asociado al Anexo F.

## Proximos pasos

Sin pasos pendientes.

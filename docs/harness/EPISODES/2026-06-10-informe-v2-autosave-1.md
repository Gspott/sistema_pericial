# Episode: Informe V2 Autosave 1

## Fecha

2026-06-10


## Tarea

INFORME-V2-AUTOSAVE-1: autosalvado por campo en el editor estructurado del Informe Pericial V2.

## Plan asociado

informe-v2-autosave-1.md


## Task Pack usado

app_change

## Objetivo

Evitar pérdida de contenido técnico cuando el usuario edita capítulos del Informe V2 y cierra o recarga la página sin usar el guardado manual.

## Archivos modificados

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/informe-v2-autosave-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-10-informe-v2-autosave-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Resultado

Se añade `POST /informes-v2/{expediente_id}/autosave`, con lista blanca de claves basada en los capítulos V2 existentes y guardado de un único capítulo mediante el mismo upsert usado por el guardado manual.

El editor V2 incorpora autosalvado con debounce, guardado al perder foco, estado visual (`Sin guardar`, `Guardando...`, `Guardado`, `Error al guardar`) y aviso `beforeunload` si quedan cambios pendientes. El botón manual `Guardar datos` se mantiene.

Los tests cubren rechazo de campos no permitidos, guardado de un campo permitido, conservación de otros capítulos, visualización posterior en el editor y presencia del cableado frontend.

## Warnings

`scripts/audit_docs.py` mantiene el warning informativo preexistente de monolito estructural en `app/main.py`.

## Rollback

Eliminar la ruta `/informes-v2/{expediente_id}/autosave`, retirar el JavaScript y estado de autosalvado del template, y revertir los tests añadidos. El guardado manual no depende de esta capa.

## Memoria actualizada

Sí: plan cerrado automáticamente y métricas actualizadas por `finish_harness_task.sh`.

## Decisiones humanas

No hubo decisiones humanas adicionales durante la implementación.

## Proximos pasos

Probar el comportamiento en navegador con el expediente piloto `019-26` durante una sesión real de redacción larga y valorar un indicador por capítulo si hiciera falta más granularidad visual.

# Episode: Pericial Editor 1

## Fecha

2026-06-06


## Tarea

PERICIAL-EDITOR-1: implementar editor estructurado de informe pericial V2 para
escritorio, vinculado al Workbench pericial.

## Plan asociado

pericial-editor-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/db_change.md`

## Objetivo

Crear una capa minima de capitulos editables para informe V2, con precarga desde
los borradores de PERICIAL-WB-2 y persistencia propia, sin modificar la
generacion PDF actual.

## Archivos modificados

- `app/database.py`
- `app/main.py`
- `templates/pericial_workbench.html`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-editor-1.md`
- `docs/harness/EPISODES/2026-06-06-pericial-editor-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecuto smoke completo: 139 passed.

## Resultado

Se crea la tabla idempotente `informe_v2_capitulos`, con indice unico por
`expediente_id, clave`, y las rutas:

- `GET /expedientes/{expediente_id}/informe-v2-editor`
- `POST /expedientes/{expediente_id}/informe-v2-editor`

El editor muestra 12 capitulos V2 fijos, precarga contenido generado con datos
existentes cuando no hay guardado previo y guarda textos manuales mediante
textarea simple. El Workbench enlaza a `Editar informe V2`.

## Warnings

`python3 scripts/audit_docs.py` mantiene warning informativo preexistente de
monolito estructural en `app/main.py`.

## Rollback

Revertir los archivos listados. La tabla nueva es idempotente y no se crean
migraciones destructivas.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

PERICIAL-EDITOR-2: preparar exportacion/preview V2 de solo lectura a partir de
capitulos guardados, sin alterar todavia el PDF V1.

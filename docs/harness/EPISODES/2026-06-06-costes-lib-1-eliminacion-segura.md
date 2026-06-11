# Episode: Costes Lib 1 Eliminacion Segura

## Fecha

2026-06-06


## Tarea

Implementar COSTES-LIB-1: eliminación segura de partidas de biblioteca de costes.

## Plan asociado

costes-lib-1-eliminacion-segura.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Permitir borrar desde `/costes` partidas erróneas, duplicadas o de prueba sin afectar costes ya vinculados a patologías o actuaciones de reparación.

## Archivos modificados

- `app/routers/costes.py`
- `templates/costes/listado.html`
- `tests/smoke/test_costes_workbench.py`
- `docs/harness/PLANS/completed/costes-lib-1-eliminacion-segura.md`
- `docs/harness/EPISODES/2026-06-06-costes-lib-1-eliminacion-segura.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_workbench.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 131 passed.

## Resultado

Se añade `POST /costes/{concepto_id}/eliminar`.

Comportamiento:

- Si la partida no tiene referencias en `patologia_costes` ni `actuacion_partidas`, se elimina `costes_conceptos` y sus `costes_descompuestos` propios.
- Si la partida aparece como `concepto_hijo_id` de otra descomposición, se deja la línea como snapshot sin referencia para no romper la otra partida.
- Si la partida está usada en patologías o actuaciones, el borrado queda bloqueado con el mensaje: `Esta partida está siendo utilizada y no puede eliminarse.`
- El listado muestra acción `Eliminar` con confirmación del navegador.

## Warnings

No se tocan OCR, parser IVE, BC3, informes, actuaciones ni patologías. La operación es destructiva solo para partidas no referenciadas por uso operativo.

## Rollback

Revertir archivos listados. No hay migración ni cambios de esquema.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Revisión de duplicados y limpieza asistida de partidas de biblioteca.

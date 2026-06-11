# Episode: Costes Ive 1C

## Fecha

2026-06-05


## Tarea

Implementar COSTES-IVE-1C: aceptar códigos auxiliares IVE sin punto en descompuestos.

## Plan asociado

costes-ive-1c.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Hacer explícito el soporte de descompuestos IVE sin punto, como `MOOA12a`, y cubrir la captura DDDR.6ba.

## Archivos modificados

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-1c.md`
- `docs/harness/EPISODES/2026-06-05-costes-ive-1c.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 122 passed.

## Resultado

El regex IVE de descompuestos ahora explicita tres familias: partida con punto, auxiliar sin punto y `%`.

Se añadió test DDDR.6ba con `MOOA12a` y porcentaje final, verificando precio principal `10.75`, dos descompuestos y ausencia de advertencia de descuadre.

## Warnings

La extracción sigue siendo prellenado para revisión manual obligatoria. No se modifica OCR.

## Rollback

Revertir archivos listados. No hay migración ni cambios de datos.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Comparativa de partida de proyecto vs IVE.

# Episode: Costes Ive 1B

## Fecha

2026-06-05


## Tarea

Implementar COSTES-IVE-1B: soporte IVE para partidas con solo dos descompuestos y porcentaje final.

## Plan asociado

costes-ive-1b.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Parsear correctamente capturas IVE tipo DDDR.4a con una línea de mano de obra y una línea final de costes directos complementarios.

## Archivos modificados

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-1b.md`
- `docs/harness/EPISODES/2026-06-05-costes-ive-1b.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 121 passed.

## Resultado

Se añadió un test realista DDDR.4a con dos descompuestos y se reforzó el parser IVE para rescatar la línea inmediatamente anterior si el porcentaje final fuese el primer descompuesto detectado.

El parser mantiene `MOOA12a` como código válido y conserva el importe porcentual `0.19` cuando ya cuadra con `6.32 * 0.030`.

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

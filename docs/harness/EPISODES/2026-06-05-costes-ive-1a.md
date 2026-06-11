# Episode: Costes Ive 1A

## Fecha

2026-06-05


## Tarea

Implementar COSTES-IVE-1A: conceptos auxiliares IVE en descompuestos.

## Plan asociado

costes-ive-1a.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Reconocer líneas IVE de `Costes directos complementarios` como descompuesto porcentual con código y unidad `%`, incluso si el OCR omite los símbolos.

## Archivos modificados

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-1a.md`
- `docs/harness/EPISODES/2026-06-05-costes-ive-1a.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 120 passed.

## Resultado

En modo IVE, las líneas con `directos complementarios` se reconocen como concepto porcentual auxiliar aunque falten símbolos `%` en el OCR.

Se asigna `codigo = "%"`, `unidad = "%"`, `resumen = "Costes directos complementarios"` y se parsean `precio_unitario`, `rendimiento` e `importe` desde los tres números finales.

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

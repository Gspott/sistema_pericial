# Episode: Costes Ive 1H Refuerzo Prefijos

## Fecha

2026-06-06


## Tarea

Implementar refuerzo COSTES-IVE-1H: parser IVE para partidas largas con prefijos OCR basura.

## Plan asociado

costes-ive-1h-refuerzo-prefijos.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Detectar correctamente el falso techo `ERTC.3aaaa` cuando el OCR añade prefijos como `(>)`, `Ep` o `Cp`, y cuando el precio principal aparece en una línea separada.

## Archivos modificados

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-1h-refuerzo-prefijos.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1h-refuerzo-prefijos.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 136 passed.

## Resultado

El parser IVE limpia prefijos OCR antes de parsear líneas de descompuesto:

- `(>) PFPC.1ac ...` se interpreta como `PFPC.1ac ...`.
- `Ep PEPP11a ...` se interpreta como `PEPP11a ...` y se normaliza a `PFPP11a`.
- `Cp PRTW13d ...` se interpreta como `PRTW13d ...`.

Se amplía el diccionario de recursos frecuentes con recursos de falso techo:

- `PFPC.1ac`
- `PFPP11a`
- `PFPP12a`
- `PFPP15a`
- `PRTW13a`
- `PRTW13c`
- `PRTW13d`

La detección de partida principal acepta precio en línea suelta, por ejemplo `36.57€` tras `ERTC.3aaaa | m2 | ...`.

## Warnings

La extracción sigue siendo prellenado para revisión manual obligatoria. No se modifica OCR ni se guarda o valida automáticamente.

## Rollback

Revertir archivos listados. No hay migración ni cambios de esquema.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Ampliar recursos frecuentes IVE cuando aparezcan nuevos recursos repetidos en capturas reales.

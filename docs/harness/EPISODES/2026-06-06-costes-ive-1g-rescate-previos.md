# Episode: Costes Ive 1G Rescate Previos

## Fecha

2026-06-06


## Tarea

Implementar COSTES-IVE-1G: rescate de descompuestos previos al porcentaje y corrección matemática de importes IVE.

## Plan asociado

costes-ive-1g-rescate-previos.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Corregir el caso real `DDDS.2a` donde el OCR de IVE trae códigos auxiliares imperfectos y un importe de mano de obra incoherente antes de la línea `%`.

## Archivos modificados

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-1g-rescate-previos.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1g-rescate-previos.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 128 passed.

## Resultado

En modo IVE se amplió la tolerancia del parser para rescatar líneas de descomposición previas al porcentaje aunque el código venga degradado por OCR.

Caso `DDDS.2a` cubierto:

- `MODA12a` se corrige a `MOOA12a`.
- `Peónordinario` se normaliza como `Peón ordinario`.
- `17.43€` como importe de mano de obra se corrige a `47.43` porque `21.08 * 2.250 = 47.43`.
- `PBAAa` con resumen `Agua` se corrige a `PBAA.1a`.
- `112€` se interpreta como `1.12` por coherencia con rendimiento e importe cero.
- La línea `%` usa el subtotal previo `47.43` como precio unitario y calcula `0.95`.
- Suma final de descompuestos: `48.38`, sin advertencia de descuadre de suma.

## Warnings

La extracción sigue siendo prellenado para revisión manual obligatoria. No se modifica OCR ni se guarda o valida automáticamente.

## Rollback

Revertir archivos listados. No hay migración ni cambios de datos.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Comparativa de partida de proyecto vs IVE.

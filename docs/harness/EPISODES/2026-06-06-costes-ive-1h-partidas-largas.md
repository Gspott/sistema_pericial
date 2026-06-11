# Episode: Costes Ive 1H Partidas Largas

## Fecha

2026-06-06


## Tarea

Implementar COSTES-IVE-1H: parser IVE para partidas largas con muchos descompuestos.

## Plan asociado

costes-ive-1h-partidas-largas.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Reducir trabajo manual en capturas IVE largas, especialmente falso techo `ERTC.3aaaa`, detectando 10-15 líneas de descomposición con precios compactos.

## Archivos modificados

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-1h-partidas-largas.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1h-partidas-largas.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 135 passed.

## Resultado

El parser IVE reconoce el caso `ERTC.3aaaa` con 13 descompuestos y suma final `36.57`.

Mejoras cubiertas:

- `MOOAa -> MOOA.8a`.
- `PFPPSa -> PFPP.5a`.
- Códigos sin punto como `PFPP11a`, `PFPP12a`, `PFPP15a`, `PRTW13a`, `PRTW13c`, `PRTW13d`.
- Textos pegados como `Placayeso`, `Pastajunta`, `Piezaempalme` y `Conector60x115x27`.
- Compactos como `2551 -> 25.51`, `638 -> 6.38`, `005 -> 0.05`, `090 -> 0.90`, `056 -> 0.56`, `048 -> 0.48`.
- Orientación precio/rendimiento para materiales con precio pequeño y rendimiento alto.

## Warnings

La extracción sigue siendo prellenado para revisión manual obligatoria. No se modifica OCR ni se guarda o valida automáticamente.

## Rollback

Revertir archivos listados. No hay migración ni cambios de esquema.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Comparativa de partida de proyecto vs IVE o limpieza asistida de duplicados de biblioteca.

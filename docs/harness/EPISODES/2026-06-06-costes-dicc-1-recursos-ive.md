# Episode: Costes Dicc 1 Recursos Ive

## Fecha

2026-06-06


## Tarea

Implementar COSTES-DICC-1: diccionario de recursos frecuentes IVE para normalizar descompuestos.

## Plan asociado

costes-dicc-1-recursos-ive.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Normalizar códigos, tipo, unidad, resumen y precio unitario de recursos frecuentes IVE degradados por OCR, manteniendo rendimiento e importe de cada partida.

## Archivos modificados

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-dicc-1-recursos-ive.md`
- `docs/harness/EPISODES/2026-06-06-costes-dicc-1-recursos-ive.md`
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

Se añade `RECURSOS_IVE_FRECUENTES` y `normalizar_recurso_ive()` en el parser IVE.

Recursos cubiertos:

- `MOOA.8a`
- `MOOA12a`
- `MOOA11a`
- `PBAA.1a`
- `PFPP.8b`
- `PFPP.7a`
- `PFPP.5a`

El parser normaliza variantes como `MOOAa`, `MODA12a`, `PBAAa`, `PFPPSa`, `PFPP8b`, `PFPP7a` y `PFPP5a`, y añade advertencias informativas.

Para preservar regresiones previas, el precio unitario de diccionario solo sustituye al OCR cuando la línea llega con variante OCR o con precio compacto/degradado; si el código canónico trae un precio decimal explícito, se conserva el precio OCR.

## Warnings

La extracción sigue siendo prellenado para revisión manual obligatoria. No se modifica OCR ni se guarda o valida automáticamente.

## Rollback

Revertir archivos listados. No hay migración ni cambios de esquema.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Ampliar diccionario con recursos recurrentes a medida que aparezcan nuevas capturas IVE.

# Episode: Costes Ive 1F Normalizacion Importes

## Fecha

2026-06-06


## Tarea

Implementar COSTES-IVE-1F: normalización OCR de importes IVE sin separador decimal.

## Plan asociado

costes-ive-1f-normalizacion-importes.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Corregir precios unitarios compactos como `877€ -> 8.77` usando coherencia entre precio, rendimiento e importe.

## Archivos modificados

- `app/services/costes_parser.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-1f-normalizacion-importes.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1f-normalizacion-importes.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 127 passed.

## Resultado

En modo IVE se normaliza también el precio unitario OCR compacto mediante variantes `/10`, `/100` y `/1000`, escogiendo la que mejor cuadre con rendimiento e importe.

Caso DDDR.2b cubierto:

- `245€ -> 2.45` como importe de `MODA9a`.
- `632€ -> 6.32` como importe de `MOOA12a`.
- `877€ -> 8.77` como precio unitario del porcentaje.
- Suma final de descompuestos: `9.03`.

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

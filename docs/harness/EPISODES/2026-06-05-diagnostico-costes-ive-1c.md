# Episode: Diagnostico Costes Ive 1C

## Fecha

2026-06-05


## Tarea

Diagnosticar descarte aparente de `MOOA12a` en COSTES-IVE-1C.

## Plan asociado

diagnostico-costes-ive-1c.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Mostrar el punto exacto del parser IVE donde la línea `MOOA12a h Peón ordinario construcción 21.08 0.500 10.54` se parsea o se descarta.

## Archivos modificados

- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/diagnostico-costes-ive-1c.md`
- `docs/harness/EPISODES/2026-06-05-diagnostico-costes-ive-1c.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 123 passed.

## Resultado

La línea exacta no se descarta en el estado actual del parser.

Trazabilidad observada:

- `_normalizar_texto_ive()` conserva `MOOA12a h Peón ordinario construcción 21.08 0.500 10.54`.
- `_parsear_linea_descompuesto_ive()` devuelve un dict válido con `codigo=MOOA12a`, `unidad=h`, `precio_unitario=21.08`, `rendimiento=0.5`, `importe=10.54`.
- `_parsear_coste_ive()` lo añade como primer elemento de `datos_parseados["descompuestos"]`.

Se añadió test de regresión sin símbolos euro para fijar este comportamiento.

## Warnings

No se modifica OCR ni módulos de negocio.

## Rollback

Revertir test y documentos harness de diagnóstico.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Comparativa de partida de proyecto vs IVE.

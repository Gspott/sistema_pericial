# Episode: Costes Ui 1 Descompuestos Dinamicos

## Fecha

2026-06-06


## Tarea

Implementar COSTES-UI-1: descompuestos dinámicos en revisión de captura de costes.

## Plan asociado

costes-ui-1-descompuestos-dinamicos.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Permitir completar manualmente partidas IVE con muchos descompuestos desde la pantalla de revisión, manteniendo filas OCR y revisión humana obligatoria.

## Archivos modificados

- `app/routers/costes.py`
- `templates/costes/captura_revision.html`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ui-1-descompuestos-dinamicos.md`
- `docs/harness/EPISODES/2026-06-06-costes-ui-1-descompuestos-dinamicos.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 134 passed.

## Resultado

La revisión de captura muestra ahora:

- Botón `Añadir descompuesto`.
- Botón `Eliminar` en cada fila.
- Filas OCR prellenadas intactas.
- Filas nuevas con los mismos nombres de campo de lista usados por el backend.

El guardado mantiene el comportamiento anterior: si `importe` queda vacío, se calcula `precio_unitario * rendimiento`; si viene informado, se respeta.

Además, el backend ignora filas completamente vacías aunque tengan el selector `tipo=material`.

## Warnings

No se toca OCR, parser IVE, BC3, informes, actuaciones, patologías ni facturación. La captura sigue guardando concepto final como borrador.

## Rollback

Revertir archivos listados. No hay migración ni cambios de esquema.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Mejoras de ergonomía de captura para partidas IVE largas.

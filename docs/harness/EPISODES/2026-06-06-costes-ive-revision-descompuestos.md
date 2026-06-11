# Episode: Costes Ive Revision Descompuestos

## Fecha

2026-06-06


## Tarea

Diagnosticar y corregir flujo de revisión de captura IVE cuando el parser devuelve dos descompuestos pero la UI parece mostrar solo el porcentaje.

## Plan asociado

costes-ive-revision-descompuestos.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Verificar que los descompuestos del parser llegan completos a `datos_extraidos_json`, contexto Jinja y formulario HTML de revisión.

## Archivos modificados

- `templates/costes/captura_revision.html`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-revision-descompuestos.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-revision-descompuestos.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 125 passed.

## Resultado

Se añadieron tests de integración:

- JSON ya guardado con dos descompuestos: el GET de revisión muestra `MOOA12a` y `Costes directos complementarios`.
- `POST /costes/capturas/{captura_id}/extraer` mockeado: guarda ambos descompuestos en `datos_extraidos_json` y el GET posterior muestra ambos.

No se reproduce pérdida con JSON correcto. Se muestra `captura.updated_at` junto a `version_parser` para detectar extracciones antiguas o cacheadas en pantalla.

## Warnings

No se modifica OCR ni parser porque no se reproduce descarte con JSON correcto.

## Rollback

Revertir archivos listados. No hay migración ni cambios de datos.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Comparativa de partida de proyecto vs IVE.

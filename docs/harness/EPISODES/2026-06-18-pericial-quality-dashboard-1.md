# Episode: Pericial Quality Dashboard 1

## Fecha

2026-06-18


## Tarea

PERICIAL-QUALITY-DASHBOARD-1

## Plan asociado

pericial-quality-dashboard-1.md


## Task Pack usado

`informe_change`

## Objetivo

Crear una V1 del Dashboard de Calidad del Informe, agregando coherencia,
riesgo tecnico y revision juridica desde el motor existente.

## Archivos modificados

- `app/services/pericial_consistency.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- `docs/harness/PLANS/completed/pericial-quality-dashboard-1.md`
- `docs/harness/METRICS.md` mediante cierre harness
- `docs/harness/EPISODES/2026-06-18-pericial-quality-dashboard-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app/services/pericial_consistency.py`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`:
  OK, 16 passed.
- `python3 -m compileall app`: OK.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK.

## Resultado

`analizar_consistencia_expediente()` devuelve ahora `dashboard_calidad`:

- `score_global`
- `score_integridad`
- `score_riesgo_tecnico`
- `score_riesgo_juridico`
- `estado`
- `nivel`
- `totales`

La UI del editor Informe V2 muestra la cabecera "CALIDAD DEL INFORME" con
semaforo, puntuaciones y totales, sin bloquear edicion ni exportacion.

## Warnings

`audit_docs.py` mantiene warnings preexistentes sobre planes completados vacios
y tamano del monolito `app/main.py`.

## Rollback

Revertir los archivos modificados de esta tarea. No hay migraciones ni datos
persistentes nuevos.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/pericial-quality-dashboard-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas. Cambio pequeno, reversible e informativo.

## Proximos pasos

Futuras fases pueden anadir bloqueo opcional de exportacion, checklist previa a
emision, historico de puntuaciones o evolucion entre autosaves.

# Episode: Pericial Wb 1

## Fecha

2026-06-06


## Tarea

Implementar Workbench pericial SSR de escritorio, solo lectura/diagnostico, para expedientes de patologias.

## Plan asociado

pericial-wb-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Crear `GET /expedientes/{expediente_id}/pericial-workbench` como vista secundaria para revisar diagnostico V2, metricas, inventario de danos, metodologia basica, limitaciones candidatas, recomendaciones candidatas y economia por actuaciones.

## Archivos modificados

- `app/main.py`
- `templates/detalle_expediente.html`
- `templates/pericial_workbench.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-wb-1.md`
- `docs/harness/EPISODES/2026-06-06-pericial-wb-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `python3 -m pytest`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecuto smoke completo: 138 passed.

## Resultado

Se anade una vista SSR nueva y reversible para expedientes de patologias:

- cabecera de expediente;
- metricas de visitas, estancias, patologias, fotografias, actuaciones y PEM;
- diagnostico por capitulos V2;
- inventario resumido de danos con enlaces a edicion existente;
- metodologia basica desde visitas y climatologia;
- limitaciones y recomendaciones candidatas derivadas de textos existentes;
- panel economico por actuaciones;
- advertencias de campos vacios y falta de trazabilidad/verificacion.

## Warnings

`python3 -m pytest` no esta disponible en el Python del sistema por falta de `pytest`; se ejecuta la suite completa con `.venv/bin/python -m pytest`.

## Rollback

Revertir archivos listados. No hay migraciones, tablas nuevas ni campos nuevos.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

PERICIAL-WB-2: microedicion acotada de campos existentes `metodologia_pericial` y `alcance_limitaciones`, manteniendo el Workbench como vista secundaria.

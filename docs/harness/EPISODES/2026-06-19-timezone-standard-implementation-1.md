# Episode: Timezone Standard Implementation 1

## Fecha

2026-06-19


## Tarea

Implementar primer estandar transversal de zona horaria Europe/Madrid/UTC
derivado de la auditoria `auditoria-transversal-estandares.md`.

## Plan asociado

timezone-standard-implementation-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Eliminar el desfase visible de -2h al mostrar timestamps SQLite
`CURRENT_TIMESTAMP` en pantallas criticas, sin migrar datos historicos ni
cambiar defaults de base de datos.

## Archivos modificados

- `app/utils/timezone.py`
- `app/main.py`
- `app/routers/crm.py`
- `app/routers/dashboard.py`
- `app/services/crm_scheduled.py`
- `app/services/informe.py`
- Templates de emails, CRM, costes, clientes, factura detalle, Informe V2 y
  valoracion workbench con timestamps crudos.
- `tests/smoke/test_timezone_standard.py`
- `docs/harness/PLANS/completed/timezone-standard-implementation-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py` OK, con warnings historicos existentes.
- `python3 -m compileall app` OK.
- `.venv/bin/python -m pytest tests/smoke/test_timezone_standard.py -q` OK,
  2 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` OK; autoescalado a
  full, 277 passed.
- `git diff --check` OK dentro del wrapper.

## Resultado

Se creo `app/utils/timezone.py` con helpers UTC/Europe-Madrid, parseo de
timestamps SQLite como UTC y formateo local Madrid. `app.main` registra filtros
Jinja `datetime_madrid` y `date_madrid`. Las pantallas con timestamps crudos
seleccionadas ahora muestran hora local. CRM, dashboard e informes usan el
helper comun para fechas/horas nuevas no fiscales.

## Warnings

Persisten warnings documentales historicos: monolito `app/main.py` y planes
completados antiguos sin contenido real.

## Rollback

Revertir helper, imports, filtros, cambios de templates y smoke test. No hay
migracion ni datos historicos que revertir.

## Memoria actualizada

Plan completado y episodio registrado. El estandar inicial queda cubierto por
smoke contra el desfase UTC -> Europe/Madrid en verano e invierno.

## Decisiones humanas

No se tocaron facturacion fiscal, backups reales, autenticacion, DB real ni
migraciones historicas.

## Proximos pasos

Extender el helper en fases posteriores a backups/exportaciones y a cualquier
pantalla restante que muestre timestamps crudos, manteniendo cambios pequenos y
tests por flujo.

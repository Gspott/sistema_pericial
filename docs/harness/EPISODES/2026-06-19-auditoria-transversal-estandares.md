# Episode: Auditoria Transversal Estandares

## Fecha

2026-06-19


## Tarea

Auditoria transversal del proyecto Sistema Pericial tras mejoras recientes de
Informe V2, PDF V2, anexos, laminas fotograficas, CRM, costes, valoraciones y
harness engineering.

## Plan asociado

auditoria-transversal-estandares.md


## Task Pack usado

`docs/harness/TASK_PACKS/harness_change.md`

## Objetivo

Diagnosticar el estado general, detectar mejoras parciales que deban
convertirse en estandares globales y proponer fases pequenas sin implementar
cambios funcionales.

## Archivos modificados

- `docs/harness/PLANS/completed/auditoria-transversal-estandares.md`
- `docs/harness/EPISODES/2026-06-19-auditoria-transversal-estandares.md`
- `docs/harness/METRICS.md` actualizado por `finish_harness_task.sh`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py` OK, con warnings existentes sobre monolito y
  planes completados vacios.
- `bash scripts/finish_harness_task.sh --smoke-scope docs` OK.
- `git diff --check` OK dentro del wrapper.

## Resultado

Auditoria completada y documentada. Se identifico Informe V2 como patron local
maduro de autosave con debounce, estado visual, `updated_at`, conflicto 409,
borrador local, fallback manual y smoke tests. Se detecto que el desfase de -2h
es coherente con mostrar `CURRENT_TIMESTAMP` de SQLite como hora local sin
conversion; el sistema mezcla `CURRENT_TIMESTAMP`, `datetime.now()`,
`date.today()` y `new Date()` sin helper comun de zona horaria.

## Warnings

Persisten warnings historicos de `audit_docs.py`: monolito `app/main.py` y
planes completados antiguos sin contenido real. No se corrigen en esta tarea.

## Rollback

Revertir los cambios documentales del plan/episodio y la actualizacion de
metricas si se quiere retirar la auditoria.

## Memoria actualizada

El plan completado contiene matriz por modulo, auditoria de autosave, auditoria
de zona horaria, estandares recomendados, fases de implementacion y nombres de
planes harness propuestos.

## Decisiones humanas

No hubo aprobacion para implementar cambios funcionales; la tarea se mantuvo en
auditoria/documentacion.

## Proximos pasos

Ejecutar fases pequenas con planes independientes, empezando por
`autosave-standard-docs-1` y `timezone-standard-docs-1`.

# Episode: Pericial V2 Implementation Plan

## Fecha

2026-06-06


## Tarea

Disenar la implementacion minima para un primer Workbench pericial V2 de escritorio operativo, sin implementar.

## Plan asociado

pericial-v2-implementation-plan.md


## Task Pack usado

`docs/harness/TASK_PACKS/doc_change.md`

## Objetivo

Identificar la ruta de menor esfuerzo para obtener el mayor salto de calidad en redaccion pericial desde escritorio, usando `019-26` como caso piloto.

## Archivos modificados

- `docs/harness/DOMAIN/pericial/PERICIAL_IMPLEMENTATION_PLAN_V2.md`
- `docs/harness/PLANS/completed/pericial-v2-implementation-plan.md`
- `docs/harness/EPISODES/2026-06-06-pericial-v2-implementation-plan.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecuto smoke completo: 136 passed.

## Resultado

Se crea un plan tecnico por fases con:

- auditoria de modelos, rutas, plantillas y componentes reutilizables;
- arquitectura minima para Workbench, metodologia, limitaciones, recomendaciones y actuaciones verificadas;
- matriz de reutilizacion, campos nuevos, entidades nuevas y complejidad;
- MVP para mejorar `019-26`;
- riesgos, compatibilidad, esfuerzo y orden recomendado.

## Warnings

No se implementa nada. La recomendacion principal es empezar por Workbench SSR de solo lectura antes de crear nuevos datos permanentes.

## Rollback

Eliminar `PERICIAL_IMPLEMENTATION_PLAN_V2.md` y revertir plan/episodio. No hay cambios de codigo, DB ni plantillas.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas para esta fase documental. Requeridas para cualquier implementacion real posterior.

## Proximos pasos

Implementar, en fase separada, `PERICIAL-WB-1`: Workbench pericial SSR de solo lectura/diagnostico para expedientes de patologias.

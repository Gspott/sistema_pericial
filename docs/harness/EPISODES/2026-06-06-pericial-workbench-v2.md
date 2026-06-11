# Episode: Pericial Workbench V2

## Fecha

2026-06-06


## Tarea

Definir documentalmente el futuro Workbench V2 de escritorio para redaccion pericial.

## Plan asociado

pericial-workbench-v2.md


## Task Pack usado

`docs/harness/TASK_PACKS/doc_change.md`

## Objetivo

Analizar el flujo real de trabajo del tecnico en el expediente `019-26` y definir una mesa de redaccion de escritorio para analizar, relacionar, argumentar, valorar y redactar informes periciales complejos.

## Archivos modificados

- `docs/harness/DOMAIN/pericial/PERICIAL_WORKBENCH_V2.md`
- `docs/harness/PLANS/completed/pericial-workbench-v2.md`
- `docs/harness/EPISODES/2026-06-06-pericial-workbench-v2.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecuto smoke completo: 136 passed.

## Resultado

Se crea `PERICIAL_WORKBENCH_V2.md` con:

- objetivo y problema UX;
- perfil de usuario;
- flujo real inferido de `019-26`;
- casos de uso;
- estructura de pantalla por panel izquierdo, central y derecho;
- fricciones del sistema actual;
- matriz de datos existentes, reorganizacion y campos futuros;
- priorizacion MVP/V2/V3;
- conclusion obligatoria sobre las tres herramientas de mayor productividad.

## Warnings

No se implementa nada. No se crean formularios, rutas, modelos, DB ni plantillas.

## Rollback

Eliminar el documento Workbench V2 y revertir plan/episodio. No hay cambios de codigo, DB ni plantillas.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas para esta fase documental. Requeridas para implementar cualquier vista real.

## Proximos pasos

Fase posterior propuesta: definir estrategia documental de MVP del Workbench, aun sin codigo, priorizando panel de evidencia contextual, inventario resumido y panel economico por actuaciones.

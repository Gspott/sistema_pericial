# Episode

## Fecha

2026-06-02

## Tarea

CRM-0: auditoria del dashboard desktop como centro operativo, CRM ligero y
panel de captacion para despacho pericial.

## Plan asociado

`docs/harness/PLANS/active/crm-0-dashboard-captacion-auditoria.md`

## Task Pack usado

Fase documental. El prompt solicito `docs_change`; el repositorio no contiene
`docs/harness/TASK_PACKS/docs_change.md`, por lo que se mantiene como cambio
documental con validacion de harness en scope docs.

## Objetivo

Auditar sin implementar funcionalidad:

- Dashboard actual.
- Emails corporativos y registro de emails enviados.
- Leads, contactos, tareas, clientes, propuestas y expedientes.
- Dependencias, riesgos, oportunidades de integracion y arquitectura minima.

## Archivos modificados

- `docs/crm_dashboard.md`
- `docs/harness/AGENT_MAPS/README.md`
- `docs/harness/AGENT_MAPS/crm_dashboard_map.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/2026-06-02-crm-0-dashboard-captacion-auditoria.md`
- `docs/harness/PLANS/active/crm-0-dashboard-captacion-auditoria.md`

## Validaciones ejecutadas

Pendiente de cierre:

- `python3 scripts/audit_docs.py`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

## Resultado

Se documenta que el sistema ya tiene una base comercial reutilizable:

- `leads`
- `lead_contactos`
- `lead_tareas`
- `clientes`
- `propuestas`
- `emails_enviados`
- `expedientes`

La recomendacion es no duplicar esas piezas. El primer paso funcional seguro
deberia ser un dashboard CRM read-only con datos existentes antes de crear
tablas nuevas.

## Warnings

- No existe task pack `docs_change.md`; conviene crear `crm_change.md` o una
  regla documental especifica para fases CRM.
- Crear `contactos_profesionales` sin estrategia de enlace con `leads` puede
  producir doble fuente de verdad.
- CRM-2 debe evitar SMTP real en smokes y no asumir respuestas por IMAP sin fase
  propia.

## Rollback

Revertir los cambios documentales de esta fase. No hay cambios en app, DB,
templates, static, uploads ni informes.

## Memoria actualizada

Si. Se anade documento tematico CRM y mapa de agente.

## Decisiones humanas

Pendiente: confirmar si la siguiente fase debe ser CRM-1A dashboard read-only
con datos existentes o CRM-1B esquema defensivo.

## Proximos pasos

1. CRM-1A: cockpit read-only de escritorio usando datos existentes.
2. CRM-1B: modelo minimo defensivo solo si queda validada la separacion entre
   lead, contacto profesional y oportunidad.

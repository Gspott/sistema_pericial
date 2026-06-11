# Episode: Crm 2A Leads Prospeccion

## Fecha

2026-06-04


## Tarea

CRM-2A Leads de prospeccion: convertir el modulo actual de leads en base de captacion comercial para administradores de fincas, abogados y otros prescriptores.

## Plan asociado

crm-2a-leads-prospeccion.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Reutilizar `leads` sin crear tablas nuevas para tipificar prescriptores, filtrar el listado, preparar seleccion multiple futura y exponer metricas de prospeccion en el dashboard CRM.

## Archivos modificados

- `app/routers/leads.py`
- `app/routers/dashboard.py`
- `templates/leads/listado.html`
- `templates/leads/form.html`
- `templates/leads/detalle.html`
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `tests/smoke/test_leads_prospeccion.py`
- `docs/harness/PLANS/completed/crm-2a-leads-prospeccion.md`
- `docs/harness/EPISODES/2026-06-04-crm-2a-leads-prospeccion.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-upgrade a full; 95 smokes OK)

## Resultado

Completado. `leads.origen` queda como tipo/categoria de prospeccion con opciones `administrador_fincas`, `abogado`, `arquitecto`, `inmobiliaria`, `aseguradora`, `empresa` y `otro`, conservando valores antiguos si ya existian.

El listado `/leads` incorpora filtros SSR por tipo, estado, localidad textual y fecha, tabla compacta con checkboxes `lead_ids` y una accion masiva deshabilitada para preparar fases futuras sin enviar emails. El dashboard CRM muestra contadores de administradores, abogados, pendientes contacto, respondidos y reuniones con enlaces seguros al listado filtrado.

## Warnings

`audit_docs` mantiene warning informativo existente: `app/main.py` supera el umbral de lineas.

## Rollback

Revertir los cambios listados. No hay migracion ni datos que revertir porque no se cambio esquema.

## Memoria actualizada

Plan completado, episodio registrado, metricas actualizadas por harness y backlog CRM actualizado.

## Decisiones humanas

No requeridas.

## Proximos pasos

CRM-2B podria convertir la seleccion multiple en acciones seguras no-email o preparar campanas manuales, manteniendo SMTP real fuera de alcance hasta fase propia.

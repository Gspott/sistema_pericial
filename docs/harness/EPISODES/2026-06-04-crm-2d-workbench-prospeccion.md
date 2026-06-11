# Episode: Crm 2D Workbench Prospeccion

## Fecha

2026-06-04


## Tarea

CRM-2D Workbench de Prospeccion Rapida para cargar contactos manuales en `leads` desde escritorio con minima friccion.

## Plan asociado

crm-2d-workbench-prospeccion.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Permitir localizar, revisar y cargar 30-50 administradores de fincas u otros prescriptores en una sesion de trabajo de alrededor de una hora, priorizando velocidad de introduccion, duplicados y trabajo desktop.

## Archivos modificados

- `app/routers/leads.py`
- `templates/leads/workbench_prospeccion.html`
- `templates/leads/listado.html`
- `templates/partials/_drawer_nav.html`
- `static/mobile.css`
- `tests/smoke/test_leads_prospeccion.py`
- `docs/harness/PLANS/completed/crm-2d-workbench-prospeccion.md`
- `docs/harness/EPISODES/2026-06-04-crm-2d-workbench-prospeccion.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-upgrade a full; 96 smokes OK)

## Resultado

Completado. Se crea `/leads/prospeccion` como mesa de trabajo desktop SSR con alta rapida, filtros de categoria/localidad/vista, tabla compacta de leads recientes, acciones de abrir lead, editar, `mailto:`, abrir web si se guardo en notas y marcar revisado.

No se crea tabla nueva. El workbench alimenta directamente `leads` con `estado='pendiente'`, `prioridad='prospeccion'` y `origen` como categoria. La deteccion de duplicados revisa email, telefono normalizado y empresa/nombre; si hay coincidencias, muestra aviso y permite crear de todos modos con confirmacion explicita.

Se factorizaron helpers de normalizacion, validacion, insercion y duplicados para que CRM-2E CSV pueda reutilizarlos.

## Warnings

`python3 -m pytest tests/smoke/test_leads_prospeccion.py` no pudo ejecutarse directamente porque el Python del shell no tiene `pytest`. El harness ejecuto los smokes con exito.

`audit_docs` mantiene warning informativo existente: `app/main.py` supera el umbral de lineas.

## Rollback

Revertir cambios de router, templates, CSS, smokes y documentacion harness de CRM-2D. No hay migracion ni esquema que revertir.

## Memoria actualizada

Plan completado, episodio registrado, metricas actualizadas por harness y backlog CRM actualizado.

## Decisiones humanas

No requeridas. Se evita tabla nueva por priorizar velocidad de carga y evitar doble fuente de verdad.

## Proximos pasos

CRM-2E puede implementar importacion CSV reutilizando normalizacion, validacion e identificacion de duplicados, sin scraping ni integraciones externas.

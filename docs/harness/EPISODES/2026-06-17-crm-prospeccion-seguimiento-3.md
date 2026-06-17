# Episode: Crm Prospeccion Seguimiento 3

## Fecha

2026-06-17


## Tarea

CRM-PROSPECCION-SEGUIMIENTO-3

## Plan asociado

crm-prospeccion-seguimiento-3.md


## Task Pack usado

email_change

## Objetivo

Anadir plantilla y flujo de seguimiento comercial a 10 dias para Administradores de fincas desde el Workbench CRM, manteniendo compatibilidad con las fases 1 y 2.

## Archivos modificados

- `app/services/crm_templates.py`
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-seguimiento-3.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-elevado a full)

## Resultado

Se anadio la plantilla `seguimiento_administrador_fincas_10d`, la accion inline "Enviar seguimiento" cuando hay presentacion/tarea de seguimiento, registro de email e historial, cambio de estado a `seguimiento_enviado`, resolucion de la tarea de seguimiento y creacion de revision comercial a 30 dias sin duplicados.

## Warnings

- `audit_docs.py` mantiene warnings historicos de planes completados vacios y monolito `app/main.py`.
- No se envio email real ni se tocaron SMTP/secretos.
- El estado `seguimiento_enviado` se usa como valor compatible en `leads.estado` sin migracion.

## Rollback

Revertir los cambios en servicio de plantillas, router CRM, template del Workbench y tests. No hay cambios de esquema ni datos reales.

## Memoria actualizada

Plan movido a `docs/harness/PLANS/completed/` y metricas actualizadas por el runner.

## Decisiones humanas

Sin aprobacion para envio real, migraciones o acciones masivas.

## Proximos pasos

`CRM-PROSPECCION-CAMPOS-4`: normalizar campos comerciales (`tipo_profesion`, `localidad`, `persona_contacto`, `plantilla_preferida`) y filtros sobre columnas defensivas si se aprueba migracion segura.

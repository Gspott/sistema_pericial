# Episode: Crm Prospeccion Workbench 1

## Fecha

2026-06-17


## Tarea

CRM-PROSPECCION-WORKBENCH-1

## Plan asociado

crm-prospeccion-workbench-1.md


## Task Pack usado

email_change

## Objetivo

Crear una primera vista SSR desktop de prospeccion comercial para leads, enfocada en Administradores de fincas, reutilizando leads, emails enviados, historial y tareas existentes.

## Archivos modificados

- `app/main.py`
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `templates/partials/_drawer_nav.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-workbench-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-elevado a full)

## Resultado

Workbench disponible en `/crm/prospeccion` con metricas, filtros, tabla desktop, envio de presentacion mockeable, registro de email enviado, contacto, cambio de estado a `pendiente_respuesta` y seguimiento automatico sin duplicar.

## Warnings

- `pytest` no esta disponible en el Python del sistema; se uso `./.venv/bin/pytest`.
- `audit_docs.py` mantiene warnings historicos de planes completados vacios y monolito `app/main.py`.
- La profesion y localidad no se normalizan en columnas nuevas; se infieren desde texto existente para no migrar datos reales.

## Rollback

Revertir router CRM, template, registro en `app/main.py`, enlace del drawer y test smoke. No hay cambios de esquema ni datos.

## Memoria actualizada

Plan movido a `docs/harness/PLANS/completed/` y metricas actualizadas automaticamente por el runner.

## Decisiones humanas

No hubo aprobacion para envio real ni migraciones, por lo que la fase queda limitada a UI/flujo y tests con mock.

## Proximos pasos

`CRM-PROSPECCION-PLANTILLAS-2`: normalizar plantillas comerciales, revisar campos CRM necesarios (`tipo_profesion`, `localidad`, `persona_contacto`) y plantear migracion defensiva si se aprueba.

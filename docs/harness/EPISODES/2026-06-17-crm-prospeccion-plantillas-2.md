# Episode: Crm Prospeccion Plantillas 2

## Fecha

2026-06-17


## Tarea

CRM-PROSPECCION-PLANTILLAS-2

## Plan asociado

crm-prospeccion-plantillas-2.md


## Task Pack usado

email_change

## Objetivo

Normalizar plantillas comerciales reutilizables para prospeccion CRM, empezando por Administradores de fincas, sin migraciones ni envio real.

## Archivos modificados

- `app/services/crm_templates.py`
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-plantillas-2.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-elevado a full)

## Resultado

La presentacion comercial se construye desde un servicio centralizado de plantillas, con registro inicial para `administrador_fincas`, variables seguras, fallback de contacto y preparacion para futuros tipos. El Workbench muestra la plantilla que se enviara y mantiene el bloqueo de leads sin email.

## Warnings

- `audit_docs.py` conserva warnings historicos de planes completados vacios y monolito `app/main.py`.
- No se creo editor de plantillas ni persistencia en DB.
- Solo existe plantilla activa para `administrador_fincas`; el fallback actual usa esa plantilla hasta que se creen las futuras.

## Rollback

Revertir `app/services/crm_templates.py`, cambios en `app/routers/crm.py`, `templates/crm/prospeccion.html` y tests asociados. No hay cambios de esquema ni datos reales.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/` y metricas actualizadas por el runner.

## Decisiones humanas

Sin aprobacion para envio real, cambios SMTP ni migraciones; se mantiene flujo mockeable y compatible.

## Proximos pasos

`CRM-PROSPECCION-CAMPOS-3`: decidir si se anaden columnas defensivas para `tipo_profesion`, `localidad`, `persona_contacto` y `plantilla_preferida`, con migracion segura sobre DB temporal.

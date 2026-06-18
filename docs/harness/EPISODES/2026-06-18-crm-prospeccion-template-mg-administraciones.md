# Episode: Crm Prospeccion Template Mg Administraciones

## Fecha

2026-06-18


## Tarea

CRM-PROSPECCION-TEMPLATE-MG-ADMINISTRACIONES

## Plan asociado

crm-prospeccion-template-mg-administraciones.md


## Task Pack usado

email_change

## Objetivo

Actualizar el cuerpo de la plantilla `presentacion_administrador_fincas` segun el texto indicado por el usuario, manteniendo el saludo parametrizado con `{nombre_destinatario}` y sin hardcodear `MG Administraciones` en la plantilla base.

## Archivos modificados

- `app/services/crm_templates.py`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-template-mg-administraciones.md`
- `docs/harness/EPISODES/2026-06-18-crm-prospeccion-template-mg-administraciones.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

## Resultado

Se elimino de la plantilla de presentacion el parrafo:

`Si actualmente tienen alguna comunidad con un IEE.CV pendiente, una incidencia de humedades o cualquier otra patología constructiva, estaré encantado de comentar el caso sin compromiso.`

El cierre queda en:

`Muchas gracias por su tiempo y quedo a su disposición para cualquier consulta o futura colaboración.`

seguido del P.D. existente. Se mantiene asunto, adjunto/imagen y firma automatica del sistema.

## Warnings

El harness elevo la validacion a scope `full` por cambios acumulados en el worktree. Hubo 1 skip por Playwright/Chromium no disponible en este entorno, ajeno a CRM/email.

## Rollback

Restaurar el parrafo eliminado en `PLANTILLA_ADMINISTRADOR_FINCAS.cuerpo` y revertir la asercion smoke asociada.

## Memoria actualizada

No aplica.

## Decisiones humanas

El texto recibido incluia `MG Administraciones` como destinatario concreto. Se mantuvo `{nombre_destinatario}` para conservar la personalizacion por lead.

## Proximos pasos

Previsualizar un lead real de `MG Administraciones` desde `/crm/prospeccion` para confirmar que el saludo se renderiza con el nombre del lead y que el adjunto sigue apareciendo.

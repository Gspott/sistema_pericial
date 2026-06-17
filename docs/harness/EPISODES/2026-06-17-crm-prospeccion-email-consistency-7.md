# Episode: Crm Prospeccion Email Consistency 7

## Fecha

2026-06-17


## Tarea
CRM-PROSPECCION-EMAIL-CONSISTENCY-7

## Plan asociado

crm-prospeccion-email-consistency-7.md


## Task Pack usado
email_change

## Objetivo
Eliminar firmas duplicadas en emails comerciales CRM y hacer que la previsualizacion refleje el remitente/firma real usados en el envio.

## Archivos modificados
- `app/services/email_templates.py`
- `app/services/crm_templates.py`
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-email-consistency-7.md`
- `docs/harness/EPISODES/2026-06-17-crm-prospeccion-email-consistency-7.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q` -> 23 passed.
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q` -> 29 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` -> scope elevado a full, 193 passed.

## Resultado
Se normalizo la identidad corporativa del email:

- `email_templates.py` es la fuente de verdad de nombre, cargo, telefono, email, web y WhatsApp.
- Las plantillas CRM de presentacion y seguimiento ya no contienen firma manual ni telefono/email/web.
- El cuerpo de los emails CRM salientes incluye una unica firma de texto plano.
- El HTML saliente sigue usando la firma corporativa automatica centralizada.
- La previsualizacion de `/crm/prospeccion` usa la misma identidad que el envio (`contacto@carlosblancoperito.es`) y elimina `info@carlosblancoperito.es`.
- Los logs `emails_enviados.cuerpo_texto` siguen guardando el contenido comercial editado, sin duplicar firma.

## Warnings
El preview no inspecciona el MIME final, pero consume la misma identidad corporativa centralizada que el envio. No se tocaron credenciales SMTP ni `.env`.

## Rollback
Revertir cambios de servicios/template/tests/docs de esta fase. No hay migraciones ni cambios de SMTP.

## Memoria actualizada
Metricas harness actualizadas por `finish_harness_task.sh`.

## Decisiones humanas
No se requirio aprobacion adicional porque no se tocaron SMTP real, `.env`, datos reales, migraciones ni modulos prohibidos.

## Proximos pasos
CRM-PROSPECCION-SENT-7: bandeja de enviados y revision de resultado comercial tras envios reales.

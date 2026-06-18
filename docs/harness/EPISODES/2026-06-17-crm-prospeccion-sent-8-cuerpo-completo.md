# Episode: Crm Prospeccion Sent 8 Cuerpo Completo

## Fecha

2026-06-17


## Tarea

CRM-PROSPECCION-SENT-8-CUERPO-COMPLETO

## Plan asociado

crm-prospeccion-sent-8-cuerpo-completo.md


## Task Pack usado

email_change

## Objetivo

Evitar que el cuerpo comercial registrado en `emails_enviados.cuerpo_texto` se trunque a 1000 caracteres, para que la bandeja CRM pueda mostrar el texto final enviado de forma util.

## Archivos modificados

- `app/services/email_log.py`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-sent-8-cuerpo-completo.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

## Resultado

`MAX_CUERPO_TEXTO` pasa de 1000 a 20000 caracteres. El smoke de envio de presentacion comprueba que el cuerpo guardado supera 1000 caracteres y conserva el cierre final.

## Warnings

Warnings documentales preexistentes sobre planes antiguos incompletos y monolito `app/main.py`.

## Rollback

Restaurar `MAX_CUERPO_TEXTO = 1000` y retirar la asercion de cuerpo largo.

## Memoria actualizada

La bandeja CRM de enviados puede consultar cuerpos comerciales completos dentro del limite ampliado; no guarda MIME completo ni adjuntos binarios.

## Decisiones humanas

No aplica. No se tocaron SMTP, `.env`, DB real ni IMAP.

## Proximos pasos

CRM-PROSPECCION-IMAP-SENT-9: copia real en carpeta Enviados del servidor.

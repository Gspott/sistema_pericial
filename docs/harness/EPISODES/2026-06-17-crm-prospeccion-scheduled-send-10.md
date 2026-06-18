# Episode: Crm Prospeccion Scheduled Send 10

## Fecha

2026-06-17


## Tarea

CRM-PROSPECCION-SCHEDULED-SEND-10

## Plan asociado

crm-prospeccion-scheduled-send-10.md


## Task Pack usado

email_change

## Objetivo

Crear un mecanismo manual y seguro para enviar emails CRM programados vencidos mediante servicio reutilizable y CLI con `--dry-run` y `--limit`.

## Archivos modificados

- `app/services/crm_scheduled.py`
- `scripts/send_scheduled_emails.py`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-scheduled-send-10.md`
- `docs/harness/EPISODES/2026-06-17-crm-prospeccion-scheduled-send-10.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app scripts`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

## Resultado

Se implemento `enviar_emails_programados_vencidos()` en `app/services/crm_scheduled.py`.

El servicio:

- localiza emails `estado='programado'` con `programado_para <= ahora`;
- respeta limite defensivo;
- permite `dry_run`;
- envia usando la infraestructura SMTP/IMAP existente;
- cambia el registro a `enviado` tras exito;
- conserva asunto y cuerpo final;
- mantiene adjunto PNG de presentacion cuando corresponde;
- crea seguimiento o revision posterior sin duplicar;
- omite futuros, cancelados y enviados;
- marca `estado='error'` si falla el envio.

Se añadio `scripts/send_scheduled_emails.py` para ejecucion manual.

## Warnings

El CLI sin `--dry-run` puede enviar emails reales si SMTP esta configurado y existen programados vencidos. Debe probarse primero con `--dry-run`. El harness elevo la validacion a `full` por cambios acumulados en rutas criticas del worktree.

## Rollback

Eliminar `app/services/crm_scheduled.py`, `scripts/send_scheduled_emails.py` y los tests añadidos. Los emails programados seguirian disponibles para confirmacion manual desde la agenda.

## Memoria actualizada

No aplica.

## Decisiones humanas

El usuario pidio no crear daemon complejo todavia; se implemento script manual preparado para cron/launchd futuro.

## Proximos pasos

Probar primero:

`python3 scripts/send_scheduled_emails.py --dry-run --limit 10`

Si el resultado es correcto, ejecutar manualmente sin `--dry-run` o programarlo despues con cron/launchd.

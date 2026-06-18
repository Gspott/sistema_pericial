# Episode: Email Imap Sent Copy 1

## Fecha

2026-06-17


## Tarea

EMAIL-IMAP-SENT-COPY-1

## Plan asociado

email-imap-sent-copy-1.md


## Task Pack usado

email_change

## Objetivo

Guardar una copia real del MIME enviado en la carpeta IMAP de enviados tras un SMTP exitoso, sin hacer depender el envio de que IMAP funcione.

## Archivos modificados

- `app/services/email_sender.py`
- `tests/smoke/test_email_mock.py`
- `docs/harness/PLANS/completed/email-imap-sent-copy-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

## Resultado

`enviar_mensaje_email()` mantiene SMTP como operacion principal y, tras exito, llama a `guardar_en_enviados_imap()`. El helper usa las credenciales SMTP existentes, deriva IMAP SSL/puerto estandar, busca carpeta `Sent`, `Sent Items`, `Enviados`, `INBOX.Sent`, `INBOX.Enviados` o una carpeta marcada `\Sent`, y hace `APPEND` del mismo MIME serializado con CRLF.

## Warnings

Si IMAP falla o no se encuentra carpeta de enviados, se registra warning y el envio sigue exitoso. La confirmacion real requiere prueba manual en Roundcube.

## Rollback

Revertir los cambios en `app/services/email_sender.py` y los tests IMAP. El envio volveria a ser solo SMTP.

## Memoria actualizada

La copia IMAP es best effort y no debe cambiar estado funcional ni `emails_enviados` si falla.

## Decisiones humanas

No aplica. No se tocaron `.env`, DNS, DKIM/SPF/DMARC, credenciales ni datos reales.

## Proximos pasos

Enviar un email real desde Sistema Pericial y verificar en Roundcube que aparece en `Enviados` o `Sent`, con asunto, destinatario, HTML, firma, adjuntos y `Message-ID`.

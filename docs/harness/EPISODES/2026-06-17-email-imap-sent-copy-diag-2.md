# Episode: Email Imap Sent Copy Diag 2

## Fecha

2026-06-17


## Tarea

EMAIL-IMAP-SENT-COPY-DIAG-2

## Plan asociado

email-imap-sent-copy-diag-2.md


## Task Pack usado

email_change

## Objetivo

Dar visibilidad operativa a la copia IMAP de enviados: conexion, login, LIST, carpeta detectada, APPEND, STATUS posterior y error exacto sin exponer contrasenas.

## Archivos modificados

- `app/services/email_sender.py`
- `scripts/diagnose_imap_sent.py`
- `tests/smoke/test_email_mock.py`
- `docs/harness/PLANS/completed/email-imap-sent-copy-diag-2.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app scripts`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py -q`
- `python3 scripts/diagnose_imap_sent.py --help`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`
- `git status --short`

## Resultado

`guardar_en_enviados_imap()` devuelve dict estructurado con `ok`, `conexion_ok`, `login_ok`, `append_ok`, `carpeta`, `error` y respuestas IMAP. Se anade `diagnosticar_imap_enviados()` y el CLI `scripts/diagnose_imap_sent.py`. El parser LIST contempla separadores `/` y `.`, carpetas `Sent`, `Sent Items`, `Enviados`, `INBOX.Sent`, `INBOX.Enviados`, `INBOX.Sent Items`, atributos `\Sent` y nombres IMAP UTF-7.

## Warnings

El CLI puede conectar al servidor real y `--append-test` guarda una prueba por IMAP; debe ejecutarse conscientemente. No envia SMTP ni toca CRM/DB.

## Rollback

Revertir `app/services/email_sender.py`, eliminar `scripts/diagnose_imap_sent.py` y retirar tests IMAP de diagnostico.

## Memoria actualizada

Para diagnostico real: `python3 scripts/diagnose_imap_sent.py`; para prueba de APPEND: `python3 scripts/diagnose_imap_sent.py --append-test`.

## Decisiones humanas

No aplica. No se tocaron `.env`, DNS, credenciales, CRM DB ni registros `emails_enviados`.

## Proximos pasos

Ejecutar el CLI en local con configuracion real, revisar carpeta detectada y, si procede, lanzar `--append-test` y comprobar Roundcube.

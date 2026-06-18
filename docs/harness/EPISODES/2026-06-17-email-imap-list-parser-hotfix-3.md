# Episode: Email Imap List Parser Hotfix 3

## Fecha

2026-06-17


## Tarea

EMAIL-IMAP-LIST-PARSER-HOTFIX-3

## Plan asociado

email-imap-list-parser-hotfix-3.md


## Task Pack usado

email_change

## Objetivo

Corregir el parser IMAP LIST para respuestas con separador entrecomillado y mailbox sin comillas, especialmente el caso real de Raiola `(\\HasNoChildren \\UnMarked \\Sent) "." INBOX.Sent`.

## Archivos modificados

- `app/services/email_sender.py`
- `tests/smoke/test_email_mock.py`
- `docs/harness/PLANS/completed/email-imap-list-parser-hotfix-3.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app scripts`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py -q`
- `python3 scripts/diagnose_imap_sent.py`
- `python3 scripts/diagnose_imap_sent.py --append-test`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`
- `git status --short`

## Resultado

El parser devuelve `atributos=["\\HasNoChildren", "\\UnMarked", "\\Sent"]`, `separador="."` y `nombre="INBOX.Sent"` para la respuesta real. La deteccion prioriza `\\Sent` y descarta carpetas cuyo nombre sea solo el separador. Diagnostico real detecto `INBOX.Sent`; `--append-test` termino con `append_ok=true`, `APPENDUID 1778787373 17` y `STATUS INBOX.Sent (MESSAGES 17 UIDNEXT 18)`.

## Warnings

La confirmacion visual final en Roundcube debe hacerla el usuario en la sesion web. A nivel IMAP, el APPEND ya fue aceptado por Raiola.

## Rollback

Revertir los cambios del parser y los tests de esta fase.

## Memoria actualizada

Raiola devuelve carpetas con separador `.` y mailbox sin comillas: `INBOX.Sent`. No asumir que el ultimo valor entrecomillado es el nombre de carpeta.

## Decisiones humanas

No aplica. No se tocaron `.env`, DNS, credenciales, CRM DB ni registros internos.

## Proximos pasos

Abrir Roundcube y comprobar el mensaje `[Sistema Pericial] Prueba IMAP Enviados` en Enviados/Sent.

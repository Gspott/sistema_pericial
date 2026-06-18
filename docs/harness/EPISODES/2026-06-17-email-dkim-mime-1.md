# Episode: Email Dkim Mime 1

## Fecha

2026-06-17


## Tarea

EMAIL-DKIM-MIME-1

## Plan asociado

email-dkim-mime-1.md


## Task Pack usado

email_change

## Objetivo

Diagnosticar y normalizar la construccion MIME de emails salientes para reducir riesgo de fallo DKIM por headers o serializacion no estandar.

## Archivos modificados

- `app/services/email_sender.py`
- `tests/smoke/test_email_mock.py`
- `docs/harness/PLANS/completed/email-dkim-mime-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`
- `git status --short`

## Resultado

El sender usa `EmailMessage(policy=policy.SMTP)`, genera `Date` y `Message-ID`, mantiene `From: Carlos Blanco <contacto@carlosblancoperito.es>` y expone `generar_mime_bytes()` para inspeccionar el MIME final CRLF sin enviar. El smoke verifica una sola cabecera `MIME-Version`, una sola `Content-Type` raiz, partes `text/plain` y `text/html`, remitente oficial y ausencia de `info@carlosblancoperito.es`.

## Warnings

No se puede garantizar `DKIM pass` sin envio real posterior y revision en Gmail. Warnings documentales preexistentes siguen informativos.

## Rollback

Revertir `app/services/email_sender.py` al constructor anterior y retirar el smoke MIME anadido.

## Memoria actualizada

Para diagnostico local de MIME, usar `app.services.email_sender.generar_mime_bytes(mensaje)`; no abre SMTP ni guarda MIME en DB.

## Decisiones humanas

No aplica. No se tocaron DNS, `.env`, SMTP real ni credenciales.

## Proximos pasos

Enviar un email real de prueba desde Sistema Pericial y verificar en Gmail > Mostrar original que DKIM/SPF/DMARC aparezcan como `pass`.

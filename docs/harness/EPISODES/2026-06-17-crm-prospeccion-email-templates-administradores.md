# Episode: Crm Prospeccion Email Templates Administradores

## Fecha

2026-06-17


## Tarea

CRM-PROSPECCION-EMAIL-TEMPLATES-ADMINISTRADORES

## Plan asociado

crm-prospeccion-email-templates-administradores.md


## Task Pack usado

email_change

## Objetivo

Actualizar las plantillas comerciales de administradores de fincas, anadir imagen corporativa inline/adjunta en el primer contacto y registrar fechas/estado comercial basico en CRM.

## Archivos modificados

- `app/services/crm_templates.py`
- `app/services/email_sender.py`
- `app/routers/crm.py`
- `app/database.py`
- `static/crm/carlos-blanco-presentacion-administradores.png`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `tests/smoke/test_email_mock.py`
- `docs/harness/PLANS/completed/crm-prospeccion-email-templates-administradores.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app scripts`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

## Resultado

Plantilla de presentacion actualizada a "Apoyo técnico para administradores de fincas" y seguimiento a "Disponibilidad para incidencias técnicas e IEE.CV". El primer contacto incluye PNG corporativo inline con CID y adjunto como PNG. Se anadieron columnas idempotentes en `leads`: `fecha_primer_contacto`, `fecha_segundo_contacto`, `apertura_email`, `respuesta_email`, `observaciones`. Los envios registran fecha de primer/segundo contacto y estado inicial de apertura/respuesta.

## Warnings

No se implemento tracking real de apertura ni respuesta automatica. `apertura_email` queda como `no_registrada` y `respuesta_email` como `pendiente` al enviar.

## Rollback

Revertir cambios en plantillas, sender, router, database, tests y retirar el asset PNG. Las columnas idempotentes pueden quedar inocuas en bases donde se hayan creado.

## Memoria actualizada

La imagen corporativa para administradores vive en `static/crm/carlos-blanco-presentacion-administradores.png` y se embebe con CID `carlos-blanco-presentacion-administradores@sistema-pericial`.

## Decisiones humanas

No aplica. No se tocaron SMTP real, `.env`, DNS, credenciales, facturacion, informes ni expedientes.

## Proximos pasos

Probar un envio real a una cuenta controlada y revisar que Gmail/Roundcube muestran la imagen inline y el adjunto PNG correctamente.

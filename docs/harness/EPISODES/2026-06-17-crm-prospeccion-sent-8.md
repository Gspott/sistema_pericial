# Episode: Crm Prospeccion Sent 8

## Fecha

2026-06-17


## Tarea

CRM-PROSPECCION-SENT-8

## Plan asociado

crm-prospeccion-sent-8.md


## Task Pack usado

email_change

## Objetivo

Corregir la programacion defensiva de emails desde el Workbench cuando falta `fecha_programada` y crear una bandeja CRM de consulta de emails registrados con detalle read-only.

## Archivos modificados

- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `templates/crm/prospeccion_agenda.html`
- `templates/crm/prospeccion_enviados.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-sent-8.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

## Resultado

- Programar sin fecha ya no devuelve JSON tecnico de FastAPI; redirige al Workbench con aviso claro.
- Programar con fecha mantiene `estado='programado'` y metadata `programado_para=...`.
- Nueva ruta `/crm/prospeccion/enviados` con tabla compacta y panel de detalle read-only.
- El detalle muestra contenido comercial guardado y vista final estimada con firma corporativa centralizada.
- El historial del lead enlaza cada email CRM con su detalle.

## Warnings

El harness mantiene warnings documentales preexistentes sobre planes antiguos con contenido incompleto y monolito `app/main.py`.

## Rollback

Revertir el diff de esta fase en router, templates, tests y docs. No hay migraciones ni cambios en SMTP/datos reales.

## Memoria actualizada

La consulta interna de emails enviados CRM vive en `/crm/prospeccion/enviados`. La copia real en carpeta Enviados del servidor queda fuera de alcance y se reserva para fase IMAP.

## Decisiones humanas

No aplica. No se tocaron SMTP, `.env`, DB real ni IMAP.

## Proximos pasos

CRM-PROSPECCION-IMAP-SENT-9: guardar copia real en carpeta Enviados del servidor mediante IMAP o mecanismo equivalente confirmado.

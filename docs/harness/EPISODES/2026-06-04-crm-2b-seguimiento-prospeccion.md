# Episode: Crm 2B Seguimiento Prospeccion

## Fecha

2026-06-04


## Tarea

CRM-2B Seguimiento automatico de prospeccion tras email manual de presentacion desde un lead.

## Plan asociado

crm-2b-seguimiento-prospeccion.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Evitar que un contacto de prospeccion se olvide despues de enviarle un correo de presentacion: crear una tarea pendiente a 10 dias y mostrarla en el dashboard.

## Archivos modificados

- `app/routers/emails.py`
- `app/routers/dashboard.py`
- `templates/emails/form.html`
- `templates/leads/detalle.html`
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_email_mock.py`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/completed/crm-2b-seguimiento-prospeccion.md`
- `docs/harness/EPISODES/2026-06-04-crm-2b-seguimiento-prospeccion.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-upgrade a full; 97 smokes OK)

## Resultado

Completado. El detalle de lead con email permite abrir `/emails/nuevo?lead_id=...`. Si el email manual se envia correctamente, se registra en `emails_enviados` con referencia al lead, el lead pasa a `email_enviado` y se crea una tarea `lead_tareas`:

- titulo: `Seguimiento tras email de presentación`
- tipo: `seguimiento`
- estado: `pendiente`
- fecha: hoy + 10 dias

Si el envio falla, se mantiene el registro de error existente y no se crea seguimiento. El dashboard muestra seguimientos vencidos/hoy con dias de retraso, enlace al lead, marcar hecha y acceso para crear nueva tarea desde el lead.

## Warnings

`audit_docs` mantiene warning informativo existente: `app/main.py` supera el umbral de lineas.

## Rollback

Revertir cambios listados. No hay migracion ni esquema que revertir.

## Memoria actualizada

Plan completado, episodio registrado, metricas actualizadas por harness y backlog CRM actualizado.

## Decisiones humanas

No requeridas. Se evita SMTP real en pruebas y no se anaden secuencias, campanas ni integraciones.

## Proximos pasos

CRM-2E/2F pueden apoyarse en estas tareas para importacion CSV o priorizacion de seguimiento, sin convertirlo en automatizacion de marketing.

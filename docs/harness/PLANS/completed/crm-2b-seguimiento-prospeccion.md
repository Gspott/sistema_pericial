# Crm 2B Seguimiento Prospeccion

# Objetivo

Evitar que los contactos de prospeccion se olviden tras enviar un correo de presentacion: si se envia desde un lead, crear automaticamente un seguimiento pendiente a 10 dias y hacerlo visible en el dashboard.

# Modulo

Emails corporativos manuales, leads, `lead_tareas`, dashboard CRM y smokes.

# Riesgo

Bajo/medio. Toca flujo de email manual pero no SMTP, no plantillas criticas, no adjuntos ni envio real en pruebas. Reutiliza `lead_tareas`, `emails_enviados` y `leads.estado`; no crea tablas ni cambia esquema.

# Archivos permitidos

Permitidos:
- `app/routers/emails.py`
- `app/routers/dashboard.py`
- `templates/emails/form.html`
- `templates/leads/detalle.html`
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_email_mock.py`
- `tests/smoke/test_dashboard_crm.py`
- documentacion harness de CRM-2B

# Archivos prohibidos

Prohibidos:
- SMTP/configuracion real, `app/services/email_sender.py` salvo lectura
- esquema/base de datos/migraciones
- facturacion, expedientes, informes, uploads, backups, secretos, logs y carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.

# Plan

- Permitir abrir `/emails/nuevo?lead_id=...` desde el detalle del lead.
- Mantener el envio manual existente, pero registrar referencia `lead` cuando exista contexto.
- Tras envio correcto, crear tarea en `lead_tareas` con tipo `seguimiento`, estado `pendiente` y fecha `hoy + 10 dias`.
- Actualizar el lead propio a `email_enviado`.
- No crear tarea si el envio falla.
- Hacer el dashboard mas explicito para seguimientos vencidos/hoy, con dias de retraso y acciones rapidas.
- Anadir smoke con envio mockeado que no abre SMTP real.

# Validaciones

Pendientes:
- `python3 -m compileall app tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir cambios de router/templates/CSS/smokes/documentacion. No hay migracion ni datos estructurales a revertir.

# Fuera de alcance

Envios automaticos, recordatorios por email, campanas, secuencias, WhatsApp, calendario externo, tareas recurrentes, integraciones y panel de configuracion.

# Aprobacion humana requerida

No prevista mientras no se toque SMTP real, esquema, facturacion, auth ni integraciones externas.

Estado: completado

# Crm Prospeccion Seguimiento 3

# Objetivo

Anadir plantilla y flujo de seguimiento comercial a 10 dias para Administradores de fincas desde `/crm/prospeccion`, reutilizando `lead_tareas`, `lead_contactos` y `emails_enviados` sin migraciones ni envio real en validacion.

# Modulo

CRM / Emails / Plantillas comerciales / Tareas de leads.

# Riesgo

Alto por tocar flujo de email. Sin cambios SMTP, sin migraciones y sin datos reales.

# Archivos permitidos

- `app/services/crm_templates.py`
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- Este plan, episodio y metricas harness

# Archivos prohibidos

- Bases SQLite reales
- `.env` y secretos
- `uploads/`, `backups/`, informes, fotos y logs
- Patologias, informes, valoraciones, facturacion y expedientes
- Cambios SMTP o envio real
- Migraciones destructivas

# Playbook aplicable

Task Pack sugerido: `email_change`.

- `docs/harness/PLAYBOOKS/emails.md`
- `docs/harness/PLAYBOOKS/jinja.md`

# Validaciones

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir cambios en plantillas CRM, router, template y tests. No hay cambios de esquema ni datos reales.

# Fuera de alcance

- Editor de plantillas.
- Persistencia de plantillas en DB.
- Acciones masivas.
- Envio real.
- Migrar estados/columnas de leads.

# Aprobacion humana requerida

- Envio real.
- Cambios SMTP/secretos.
- Migracion de esquema.
- Acciones masivas con envio efectivo.

Estado: completado

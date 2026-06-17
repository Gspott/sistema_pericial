# Crm Prospeccion Plantillas 2

# Objetivo

Normalizar plantillas comerciales reutilizables para prospeccion CRM, empezando por Administradores de fincas, sin romper `/crm/prospeccion` ni cambiar esquema de datos.

# Modulo

CRM / Emails / Plantillas comerciales.

# Riesgo

Alto por tocar flujo de email. Sin envio real y sin migraciones.

# Archivos permitidos

- `app/routers/crm.py`
- `app/services/crm_templates.py`
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
- Cierre con `bash scripts/finish_harness_task.sh`

# Rollback

Revertir servicio de plantillas, cambios del router/template y tests. No hay cambios de esquema ni datos.

# Fuera de alcance

- Editor de plantillas en UI.
- Plantillas persistidas en DB.
- Envio masivo real.
- Migrar leads existentes o normalizar columnas.
- Cambiar facturacion, informes, patologias, valoraciones o expedientes.

# Aprobacion humana requerida

- Envio real.
- Cambios SMTP/secretos.
- Migracion de esquema.
- Acciones masivas con envio efectivo.

Estado: completado

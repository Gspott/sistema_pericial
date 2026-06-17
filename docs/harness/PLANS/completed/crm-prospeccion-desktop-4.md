# Crm Prospeccion Desktop 4

# Objetivo
Convertir `/crm/prospeccion` en un Workbench desktop real de prospeccion comercial para trabajar esta semana con administradores de fincas: alta rapida, filtros, seleccion sin salir, previsualizacion editable de plantillas, envio controlado, programacion defensiva y seguimiento automatico.

# Modulo
CRM / captacion comercial / emails mock-safe.

# Riesgo
Medio-alto por tocar flujo de email y CRM. Mitigacion: no tocar SMTP ni `.env`, no tocar datos reales, no migraciones destructivas, mantener rutas existentes y ampliar smokes.

# Archivos permitidos
- `app/routers/crm.py`
- `app/services/crm_templates.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-desktop-4.md`
- `docs/harness/PLANS/completed/crm-prospeccion-desktop-4.md`
- `docs/harness/EPISODES/*crm-prospeccion-desktop-4*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos
- Bases SQLite reales, backups, uploads, informes, fotos, logs, `.env`.
- Patologias, informes, valoraciones, facturacion y expedientes salvo enlace no invasivo.
- SMTP real, workers o automatizacion real de envio.

# Playbook aplicable

Task Pack sugerido: `email_change`.
- `docs/harness/PLAYBOOKS/emails.md`
- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/base_datos.md`


# Validaciones
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback
Revertir cambios de router/template/tests/docs de esta fase. No se preve migracion de esquema; la programacion se almacena defensivamente como email log `estado=programado`.

# Fuera de alcance
- Automatizacion real de envio programado.
- CRM complejo, campañas masivas o workers.
- Edicion persistente de plantillas base desde UI.
- Nuevas tablas o cambios destructivos de modelo.

# Aprobacion humana requerida
Si aparece necesidad de tocar SMTP real, datos reales, migraciones no idempotentes o modulos prohibidos.

Estado: completado

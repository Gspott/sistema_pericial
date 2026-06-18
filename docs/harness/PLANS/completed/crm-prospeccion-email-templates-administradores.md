# Crm Prospeccion Email Templates Administradores

# Objetivo

Actualizar las plantillas comerciales de captacion para administradores de fincas, anadir imagen corporativa inline/adjunta en la presentacion y registrar fechas/estado comercial basico en CRM sin romper envios existentes.

# Modulo

CRM prospeccion / emails comerciales / plantillas / leads.

# Riesgo

Alto: afecta emails comerciales y anade columnas idempotentes a `leads`. Mitigacion: no tocar SMTP real ni credenciales, no migraciones destructivas, usar `asegurar_columna()` y smoke tests de email/CRM.

# Archivos permitidos

- `app/services/crm_templates.py`
- `app/services/email_sender.py`
- `app/services/email_templates.py`
- `app/routers/crm.py`
- `app/database.py`
- `static/crm/carlos-blanco-presentacion-administradores.png`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `tests/smoke/test_email_mock.py`
- `docs/harness/PLANS/active/crm-prospeccion-email-templates-administradores.md`
- `docs/harness/PLANS/completed/crm-prospeccion-email-templates-administradores.md`
- `docs/harness/EPISODES/*crm-prospeccion-email-templates-administradores*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- `.env`, SMTP real, DNS, credenciales, DB real, migraciones destructivas.
- Patologias, informes, valoraciones, facturacion y expedientes.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`
`docs/harness/PLAYBOOKS/base_datos.md`


# Validaciones

- `python3 -m compileall app scripts`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios en plantillas, sender, router, columnas defensivas y asset PNG. Las columnas anadidas pueden quedar inocuas si ya se crearon en una DB temporal/real.

# Fuera de alcance

- Tracking real de aperturas con pixel.
- Automatizaciones de tercer contacto.
- Modificar SMTP/DKIM/IMAP.
- Envio real desde tests.

# Aprobacion humana requerida

Si hiciera falta tocar credenciales, `.env`, DNS, envio real masivo o borrar/modificar datos reales.

Estado: completado

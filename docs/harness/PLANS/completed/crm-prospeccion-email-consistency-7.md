# Crm Prospeccion Email Consistency 7

# Objetivo
Eliminar firmas duplicadas en emails CRM y garantizar que la previsualizacion usa el mismo remitente/firma corporativa que el envio real.

# Modulo
CRM / prospeccion / emails comerciales.

# Riesgo
Medio: afecta contenido de emails comerciales. Mitigacion: no tocar SMTP ni `.env`, no migraciones, centralizar firma en `email_templates.py`, mantener logica de envio y ampliar smokes.

# Archivos permitidos
- `app/services/email_templates.py`
- `app/services/crm_templates.py`
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-email-consistency-7.md`
- `docs/harness/PLANS/completed/crm-prospeccion-email-consistency-7.md`
- `docs/harness/EPISODES/*crm-prospeccion-email-consistency-7*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos
- SMTP real, `.env`, datos reales, migraciones.
- Patologias, informes, valoraciones, facturacion y expedientes.

# Playbook aplicable

Task Pack sugerido: `email_change`.
- `docs/harness/PLAYBOOKS/emails.md`
- `docs/harness/PLAYBOOKS/jinja.md`


# Validaciones
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback
Revertir cambios de servicios CRM/email, template Workbench, tests y docs de esta fase. No hay migracion ni cambio de SMTP.

# Fuera de alcance
- Cambiar credenciales SMTP.
- Enviar emails reales.
- Redisenar agenda o Workbench.
- Adjuntos reales.

# Aprobacion humana requerida
Si aparece necesidad de tocar SMTP real, `.env`, datos reales, migraciones o modulos prohibidos.

Estado: completado

# Crm Prospeccion Sent 8

# Objetivo
Corregir el fallo de programacion sin fecha (`body.fecha_programada`) y crear una bandeja CRM de emails enviados/programados/cancelados para consultar el texto final registrado, remitente, destinatario, lead y vista estimada con firma corporativa.

# Modulo
CRM / prospeccion / emails enviados y programados.

# Riesgo
Medio: toca rutas CRM y consulta de registros de emails. Mitigacion: no tocar SMTP, no enviar emails reales, no migraciones, vista de enviados solo lectura y smokes ampliados.

# Archivos permitidos
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `templates/crm/prospeccion_agenda.html`
- `templates/crm/prospeccion_enviados.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-sent-8.md`
- `docs/harness/PLANS/completed/crm-prospeccion-sent-8.md`
- `docs/harness/EPISODES/*crm-prospeccion-sent-8*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos
- SMTP real, `.env`, datos reales, migraciones destructivas.
- IMAP o acceso al servidor de correo.
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
Revertir cambios de router/templates/tests/docs de esta fase. No hay migracion ni cambios de SMTP.

# Fuera de alcance
- Enviar emails reales.
- Guardar copia en carpeta Enviados via IMAP.
- Editar emails ya enviados.
- Borrar registros enviados.

# Aprobacion humana requerida
Si aparece necesidad de tocar SMTP real, `.env`, datos reales, migraciones, IMAP o modulos prohibidos.

Estado: completado

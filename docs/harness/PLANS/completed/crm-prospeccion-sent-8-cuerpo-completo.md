# Crm Prospeccion Sent 8 Cuerpo Completo

# Objetivo

Garantizar que `emails_enviados.cuerpo_texto` conserve el cuerpo comercial completo suficiente para consultar el texto final enviado desde CRM, evitando truncado prematuro a 1000 caracteres.

# Modulo

Emails / CRM prospeccion.

# Riesgo

Medio: toca servicio comun de log de emails. Mitigacion: no tocar SMTP, no cambiar esquema, no guardar MIME ni adjuntos binarios, ampliar solo limite de texto plano ya persistido en columna TEXT.

# Archivos permitidos

- `app/services/email_log.py`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-sent-8-cuerpo-completo.md`
- `docs/harness/PLANS/completed/crm-prospeccion-sent-8-cuerpo-completo.md`
- `docs/harness/EPISODES/*crm-prospeccion-sent-8-cuerpo-completo*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- SMTP, `.env`, IMAP, DB real, migraciones, adjuntos binarios o MIME completo.
- Patologias, informes, valoraciones, facturacion y expedientes.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`


# Validaciones

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback

Restaurar el limite anterior de `MAX_CUERPO_TEXTO` y retirar el test especifico.

# Fuera de alcance

- Copia real en Enviados por IMAP.
- Envio real.
- Cambios de esquema o migraciones.
- Edicion de emails enviados.

# Aprobacion humana requerida

Si hiciera falta tocar SMTP real, `.env`, datos reales, schema/migraciones o IMAP.

Estado: completado

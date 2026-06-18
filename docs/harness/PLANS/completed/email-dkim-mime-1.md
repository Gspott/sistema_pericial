# Email Dkim Mime 1

# Objetivo

Diagnosticar y corregir la construccion MIME de emails salientes generados por Sistema Pericial para maximizar compatibilidad DKIM/DMARC con Raiola/Gmail, sin enviar emails reales ni tocar DNS/SMTP/.env.

# Modulo

Emails corporativos / SMTP mock / CRM prospeccion.

# Riesgo

Alto: toca servicio comun de envio email. Mitigacion: cambio limitado a construccion local de `EmailMessage`, headers estandar, serializacion CRLF inspeccionable y tests smoke. No se enviaran emails reales.

# Archivos permitidos

- `app/services/email_sender.py`
- `app/services/email_templates.py`
- `app/routers/emails.py`
- `app/routers/crm.py` solo si es imprescindible por compatibilidad de llamada
- `tests/smoke/test_email_mock.py`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/email-dkim-mime-1.md`
- `docs/harness/PLANS/completed/email-dkim-mime-1.md`
- `docs/harness/EPISODES/*email-dkim-mime-1*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- `.env`, DNS, SMTP real, IMAP, datos reales, DB real, migraciones.
- Patologias, informes, valoraciones, facturacion y expedientes.
- Guardar MIME completo o adjuntos binarios en DB.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`


# Validaciones

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py -q`
- `git diff --check`
- `git status --short`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir cambios en `app/services/email_sender.py` y tests asociados. Volver a la construccion previa de `EmailMessage`.

# Fuera de alcance

- Garantizar DKIM pass sin prueba real posterior en Gmail.
- Cambiar DNS, selector DKIM, `.env`, credenciales SMTP o puerto.
- Enviar emails reales desde tests/desarrollo.
- Implementar IMAP o workers.

# Aprobacion humana requerida

Si hiciera falta tocar DNS, `.env`, SMTP real, credenciales, envio real o integraciones externas.

Estado: completado

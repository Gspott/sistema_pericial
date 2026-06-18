# Email Imap Sent Copy 1

# Objetivo

Guardar una copia real del MIME enviado en la carpeta IMAP de enviados tras un SMTP exitoso, sin convertir IMAP en operacion critica ni tocar `.env`, DNS o datos reales.

# Modulo

Emails corporativos / SMTP / IMAP append / CRM prospeccion.

# Riesgo

Alto: toca servicio comun de envio email y conexion externa IMAP en produccion. Mitigacion: SMTP sigue siendo operacion principal; IMAP es best effort, no rompe el envio, no expone credenciales y se valida con mocks.

# Archivos permitidos

- `app/services/email_sender.py`
- `tests/smoke/test_email_mock.py`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/email-imap-sent-copy-1.md`
- `docs/harness/PLANS/completed/email-imap-sent-copy-1.md`
- `docs/harness/EPISODES/*email-imap-sent-copy-1*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- `.env`, DNS, DKIM/SPF/DMARC, DB real, migraciones.
- Patologias, informes, valoraciones, facturacion y expedientes.
- Guardar MIME completo en DB o adjuntos binarios fuera del flujo email.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`


# Validaciones

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback

Revertir `app/services/email_sender.py` y tests de IMAP append. SMTP quedaria como unico envio.

# Fuera de alcance

- Enviar emails reales durante validacion automatica.
- Tocar `.env`, DNS, DKIM/SPF/DMARC o credenciales.
- Garantizar carpeta IMAP concreta sin prueba real posterior en Roundcube.
- Implementar workers o colas.

# Aprobacion humana requerida

Si hiciera falta modificar `.env`, cambiar credenciales/puertos reales, DNS o realizar envio real desde pruebas automatizadas.

Estado: completado

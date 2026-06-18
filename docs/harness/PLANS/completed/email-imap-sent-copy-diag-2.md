# Email Imap Sent Copy Diag 2

# Objetivo

Diagnosticar y corregir la copia IMAP real de enviados con visibilidad operativa: conexion, login, LIST, carpeta detectada, APPEND y errores estructurados sin exponer contrasenas.

# Modulo

Emails corporativos / SMTP / IMAP append / diagnostico CLI.

# Riesgo

Alto: toca servicio comun de envio email y facilita diagnostico contra servidor real. Mitigacion: no enviar SMTP desde el CLI; `--append-test` solo hace IMAP APPEND controlado, no toca CRM ni DB.

# Archivos permitidos

- `app/services/email_sender.py`
- `scripts/diagnose_imap_sent.py`
- `tests/smoke/test_email_mock.py`
- `docs/harness/PLANS/active/email-imap-sent-copy-diag-2.md`
- `docs/harness/PLANS/completed/email-imap-sent-copy-diag-2.md`
- `docs/harness/EPISODES/*email-imap-sent-copy-diag-2*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- `.env`, DNS, DKIM/SPF/DMARC, DB real, migraciones.
- CRM DB, `emails_enviados`, patologias, informes, valoraciones, facturacion y expedientes.
- Mostrar contrasenas o enviar SMTP real desde pruebas automatizadas.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`


# Validaciones

- `python3 -m compileall app scripts`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py -q`
- `git diff --check`
- `git status --short`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir `app/services/email_sender.py`, eliminar `scripts/diagnose_imap_sent.py` y retirar tests de diagnostico IMAP.

# Fuera de alcance

- Envio SMTP real desde automatismos.
- Cambios de credenciales, `.env`, DNS o proveedor.
- Tocar CRM o registros `emails_enviados`.

# Aprobacion humana requerida

Si hiciera falta modificar credenciales, `.env`, DNS o ejecutar cambios destructivos sobre carpetas IMAP.

Estado: completado

# Email Imap List Parser Hotfix 3

# Objetivo

Corregir el parser IMAP LIST para respuestas con separador entrecomillado y mailbox sin comillas, especialmente `(\\HasNoChildren \\UnMarked \\Sent) "." INBOX.Sent`, y validar APPEND real contra la carpeta correcta.

# Modulo

Emails / IMAP enviados / diagnostico CLI.

# Riesgo

Alto: afecta deteccion de carpeta de enviados usada tras SMTP. Mitigacion: cambio acotado al parser LIST, tests de formatos reales y diagnostico CLI controlado.

# Archivos permitidos

- `app/services/email_sender.py`
- `tests/smoke/test_email_mock.py`
- `docs/harness/PLANS/active/email-imap-list-parser-hotfix-3.md`
- `docs/harness/PLANS/completed/email-imap-list-parser-hotfix-3.md`
- `docs/harness/EPISODES/*email-imap-list-parser-hotfix-3*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- `.env`, DNS, credenciales, DB real, migraciones.
- CRM DB, `emails_enviados`, patologias, informes, valoraciones, facturacion y expedientes.
- Cambios destructivos en carpetas IMAP.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`


# Validaciones

- `python3 -m compileall app scripts`
- `./.venv/bin/pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py -q`
- `python3 scripts/diagnose_imap_sent.py`
- `python3 scripts/diagnose_imap_sent.py --append-test`
- `git diff --check`
- `git status --short`

# Rollback

Revertir parser y tests de esta fase. Volver a la deteccion previa.

# Fuera de alcance

- Tocar configuracion SMTP/IMAP real.
- Cambiar DNS/DKIM/SPF/DMARC.
- Tocar CRM o registros internos.

# Aprobacion humana requerida

Si hiciera falta modificar credenciales, `.env`, proveedor o borrar/renombrar carpetas IMAP.

Estado: completado

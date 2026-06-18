# Crm Prospeccion Scheduled Send 10

# Objetivo

Implementar un mecanismo manual y seguro para enviar automaticamente emails CRM programados vencidos mediante una funcion de servicio y un script CLI con `--dry-run` y `--limit`.

# Modulo

CRM prospeccion / emails programados.

# Riesgo

Alto: puede disparar envios reales si se ejecuta sin `--dry-run` en un entorno con SMTP configurado. Mitigacion: CLI explicito, limite defensivo, dry-run, filtros estrictos por estado y fecha, y tests con mock.

# Archivos permitidos

- `app/services/crm_scheduled.py`
- `scripts/send_scheduled_emails.py`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `tests/smoke/test_email_mock.py` si hace falta
- `docs/harness/PLANS/active/crm-prospeccion-scheduled-send-10.md`
- `docs/harness/PLANS/completed/crm-prospeccion-scheduled-send-10.md`
- `docs/harness/EPISODES/*crm-prospeccion-scheduled-send-10*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- `.env`, SMTP real, DNS, credenciales, DB real, migraciones destructivas.
- Patologias, informes, valoraciones, facturacion y expedientes.
- Daemon/worker persistente.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`


# Validaciones

- `python3 -m compileall app scripts`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback

Eliminar `app/services/crm_scheduled.py`, `scripts/send_scheduled_emails.py` y los tests asociados. Los emails programados seguirian disponibles para confirmacion manual desde agenda.

# Fuera de alcance

- Crear daemon, worker, cola, servicio launchd o cron instalado automaticamente.
- Enviar emails reales durante tests.
- Cambiar agenda/manual confirm o SMTP/IMAP.

# Aprobacion humana requerida

Antes de ejecutar el script real contra datos reales sin `--dry-run` o antes de instalar una automatizacion cron/launchd.

Estado: completado

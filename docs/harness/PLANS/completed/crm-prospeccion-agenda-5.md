# Crm Prospeccion Agenda 5

# Objetivo
Crear una bandeja/agenda desktop de emails programados para revisar, confirmar envio manual, cancelar o reprogramar, manteniendo compatibilidad con `emails_enviados.estado = 'programado'` creado en CRM-PROSPECCION-DESKTOP-4.

# Modulo
CRM / prospeccion / emails programados mock-safe.

# Riesgo
Medio-alto por tocar envio comercial. Mitigacion: sin worker automatico, sin envios masivos, sin SMTP real, sin `.env`, sin migraciones destructivas, confirmacion individual y tests smoke.

# Archivos permitidos
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `templates/crm/prospeccion_agenda.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-agenda-5.md`
- `docs/harness/PLANS/completed/crm-prospeccion-agenda-5.md`
- `docs/harness/EPISODES/*crm-prospeccion-agenda-5*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos
- Bases SQLite reales, backups, uploads, informes, fotos, logs, `.env`.
- Patologias, informes, valoraciones, facturacion y expedientes.
- SMTP real, workers o envio automatico de programados.

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
Revertir los cambios de router/template/tests/docs de esta fase. No se preve cambio de esquema; la fecha programada se mantiene en `emails_enviados.error_mensaje` como `programado_para=...`.

# Fuera de alcance
- Worker automatico de envio.
- Envio masivo o campañas.
- Nuevas tablas de agenda.
- Migraciones de datos reales.

# Aprobacion humana requerida
Si aparece necesidad de tocar SMTP real, `.env`, datos reales, migraciones no idempotentes, workers o modulos prohibidos.

Estado: completado

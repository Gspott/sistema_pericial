# Crm Prospeccion Pd Presentacion Administradores

# Objetivo

Actualizar solo el texto final P.D. de la plantilla `presentacion_administrador_fincas`, manteniendo asunto, cuerpo principal, imagen inline y adjunto PNG.

# Modulo

CRM prospeccion / plantillas email.

# Riesgo

Bajo-medio: toca texto comercial de email. Mitigacion: cambio literal acotado y smoke de CRM.

# Archivos permitidos

- `app/services/crm_templates.py`
- `tests/smoke/test_crm_prospeccion_workbench.py` si hace falta ajustar/verificar texto
- `docs/harness/PLANS/active/crm-prospeccion-pd-presentacion-administradores.md`
- `docs/harness/PLANS/completed/crm-prospeccion-pd-presentacion-administradores.md`
- `docs/harness/EPISODES/*crm-prospeccion-pd-presentacion-administradores*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- SMTP, `.env`, DNS, credenciales, DB real, migraciones.
- Patologias, informes, valoraciones, facturacion y expedientes.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`


# Validaciones

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`
- `git status --short`

# Rollback

Restaurar el P.D. anterior.

# Fuera de alcance

- Cambiar adjunto, imagen inline, firma, SMTP, seguimiento o Workbench.

# Aprobacion humana requerida

Si hiciera falta tocar credenciales, `.env`, SMTP real o datos reales.

Estado: completado

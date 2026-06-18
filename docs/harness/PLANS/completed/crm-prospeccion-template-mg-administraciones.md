# Crm Prospeccion Template Mg Administraciones

# Objetivo

Actualizar el cuerpo de la plantilla `presentacion_administrador_fincas` para ajustarlo al texto indicado por el usuario, manteniendo el saludo parametrizado con `{nombre_destinatario}` y conservando adjunto, asunto y firma automatica.

# Modulo

CRM prospeccion / plantillas comerciales.

# Riesgo

Bajo-medio: modifica texto comercial enviado a leads. Mitigacion: diff minimo y smoke de CRM.

# Archivos permitidos

- `app/services/crm_templates.py`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-template-mg-administraciones.md`
- `docs/harness/PLANS/completed/crm-prospeccion-template-mg-administraciones.md`
- `docs/harness/EPISODES/*crm-prospeccion-template-mg-administraciones*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- `.env`, SMTP, DNS, credenciales, DB real y migraciones.
- Patologias, informes, valoraciones, facturacion y expedientes.
- Adjuntos/imagen corporativa.

# Playbook aplicable

Task Pack sugerido: `email_change`.
`docs/harness/PLAYBOOKS/emails.md`


# Validaciones

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback

Restaurar el parrafo eliminado en `PLANTILLA_ADMINISTRADOR_FINCAS.cuerpo` y revertir la asercion de test asociada.

# Fuera de alcance

- Hardcodear `MG Administraciones` en la plantilla base.
- Cambiar asunto, seguimiento, adjunto, preview, SMTP o agenda.

# Aprobacion humana requerida

Si hubiera que enviar emails reales o tocar configuracion de correo/credenciales.

Estado: completado

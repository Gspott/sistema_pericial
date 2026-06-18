# Crm Prospeccion Preview Attachment Hotfix

# Objetivo

Corregir la previsualizacion del Workbench CRM para que la plantilla `presentacion_administrador_fincas` muestre el PNG corporativo previsto como adjunto antes de enviar o programar.

# Modulo

CRM prospeccion / preview de emails comerciales.

# Riesgo

Bajo-medio: cambio de UX en preview de email. No modifica SMTP ni envio real. Mitigacion: reutilizar constantes existentes del adjunto y smoke de CRM.

# Archivos permitidos

- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-preview-attachment-hotfix.md`
- `docs/harness/PLANS/completed/crm-prospeccion-preview-attachment-hotfix.md`
- `docs/harness/EPISODES/*crm-prospeccion-preview-attachment-hotfix*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- SMTP, `.env`, DNS, credenciales, DB real, migraciones.
- Patologias, informes, valoraciones, facturacion y expedientes.
- Adjuntos binarios salvo lectura indirecta por existencia ya usada por el envio.

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

Revertir metadata de adjunto en preview y la asercion smoke asociada.

# Fuera de alcance

- Cambiar envio SMTP, IMAP, firma corporativa, plantilla comercial, MIME o archivo adjunto.
- Implementar visualizacion inline real de la imagen dentro del modal si el requerimiento se limita a que conste el adjunto.

# Aprobacion humana requerida

Si hiciera falta enviar email real, tocar `.env`, SMTP, credenciales, datos reales o sustituir el PNG corporativo.

Estado: completado

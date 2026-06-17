# Crm Prospeccion Preview 6

# Objetivo
Implementar previsualizacion realista de email antes de enviar/programar desde `/crm/prospeccion`, con modal desktop, vistas Gmail escritorio/movil, cierre por boton/ESC/clic fuera e indicador local de revision sin persistencia.

# Modulo
CRM / prospeccion / preview de emails comerciales.

# Riesgo
Bajo-medio: cambio principalmente Jinja/CSS/JS en flujo de envio. Mitigacion: no tocar SMTP, no tocar backend de envio salvo reutilizar formularios existentes, no migraciones y smokes de no regresion.

# Archivos permitidos
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-preview-6.md`
- `docs/harness/PLANS/completed/crm-prospeccion-preview-6.md`
- `docs/harness/EPISODES/*crm-prospeccion-preview-6*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos
- Bases SQLite reales, backups, uploads, informes, fotos, logs, `.env`.
- SMTP real.
- Patologias, informes, valoraciones, facturacion y expedientes.
- Migraciones.

# Playbook aplicable

Task Pack sugerido: `email_change`.
- `docs/harness/PLAYBOOKS/emails.md`
- `docs/harness/PLAYBOOKS/jinja.md`


# Validaciones
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback
Revertir cambios de plantilla/tests/docs de esta fase. No hay cambios de esquema ni backend de envio.

# Fuera de alcance
- Enviar emails reales.
- Persistir aprobacion/revision en DB.
- Adjuntos reales si no existe dossier/PDF en el flujo actual.
- Redisenar agenda.

# Aprobacion humana requerida
Si aparece necesidad de tocar SMTP real, `.env`, datos reales, migraciones o modulos prohibidos.

Estado: completado

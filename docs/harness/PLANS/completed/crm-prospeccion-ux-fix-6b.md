# Crm Prospeccion Ux Fix 6B

# Objetivo
Eliminar fricciones del Workbench desktop: seleccionar leads clicando nombre/empresa, mantener filtros y scroll, resaltar la fila seleccionada y hacer que el cambio de plantilla actualice asunto/cuerpo automaticamente con confirmacion si hay edicion manual.

# Modulo
CRM / prospeccion / UX desktop.

# Riesgo
Bajo-medio: cambio principalmente de Jinja/CSS/JS del Workbench. Mitigacion: no tocar envio, agenda, SMTP, datos, migraciones ni modulos prohibidos; ampliar smokes.

# Archivos permitidos
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/active/crm-prospeccion-ux-fix-6b.md`
- `docs/harness/PLANS/completed/crm-prospeccion-ux-fix-6b.md`
- `docs/harness/EPISODES/*crm-prospeccion-ux-fix-6b*.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos
- SMTP real, `.env`, datos reales, bases SQLite reales.
- Agenda backend, logica de envio, migraciones.
- Patologias, informes, valoraciones, facturacion y expedientes.

# Playbook aplicable

Task Pack sugerido: `email_change`.
- `docs/harness/PLAYBOOKS/emails.md`
- `docs/harness/PLAYBOOKS/jinja.md`


# Validaciones
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `git status --short`

# Rollback
Revertir cambios de plantilla/tests/docs de esta fase. No hay cambios de esquema ni de logica de envio.

# Fuera de alcance
- AJAX/live update sin recarga.
- Persistir scroll o revision en base de datos.
- Redisenar agenda.
- Cambios SMTP/envio.

# Aprobacion humana requerida
Si aparece necesidad de tocar SMTP real, `.env`, datos reales, migraciones o modulos prohibidos.

Estado: completado

# Valoracion Docs Harness

# Objetivo

Actualizar documentacion normativa y memoria del harness con el flujo moderno
de valoracion inmobiliaria tras adaptar HTML/PDF, DOCX editable y completitud
no bloqueante.

# Modulo

Documentacion / harness / informes / UX.

# Riesgo

Bajo. Cambios documentales y de memoria operativa, sin codigo funcional.

# Archivos permitidos

- `docs/informes.md`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/AGENT_MAPS/critical_flows.md`
- `docs/harness/PATTERNS/build_informe_context_extension.md`
- `docs/harness/EPISODES/`
- `docs/harness/PLANS/active/valoracion-docs-harness.md`
- `docs/harness/METRICS.md` por cierre automatico

# Archivos prohibidos

- `app/`
- `templates/`
- `static/`
- DB real, datos reales, secretos, uploads, fotos reales, informes generados y backups
- Routers legacy
- Carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/docs_change.md`.

No existe task pack documental local en las rutas revisadas; aplicar politica
general de harness y documentos fuente.

# Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/finish_harness_task.sh`
- `python3 -m compileall app`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios documentales y episodio de valoracion moderna.

# Fuera de alcance

- Cambiar codigo funcional.
- Cambiar esquema, calculo u outputs adicionales.

# Aprobacion humana requerida

No requerida para documentacion de cambios ya validados.

Estado: completado

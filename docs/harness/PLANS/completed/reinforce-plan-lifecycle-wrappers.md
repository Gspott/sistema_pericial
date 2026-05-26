# Reinforce Plan Lifecycle Wrappers

# Objetivo

Reforzar el lifecycle de planes para que las tareas relevantes con cambios
empiecen y terminen mediante wrappers explicitos del harness, sin depender de
que el prompt recuerde crear o cerrar planes.

# Modulo

Harness/documentacion/scripts de validacion.

# Riesgo

Bajo. Cambios limitados a scripts y documentacion del harness.

# Archivos permitidos

- `scripts/start_harness_task.sh`
- `scripts/finish_harness_task.sh`
- `scripts/validate_harness.sh`
- `scripts/harness_close_plan.py`
- `AGENTS.md`
- `agents.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/EXECUTION_POLICY.md`
- `docs/harness/VALIDATION/runner.md`
- `docs/harness/METRICS.md`
- `docs/harness/PLANS/active/reinforce-plan-lifecycle-wrappers.md`

# Archivos prohibidos

- `app/`
- `templates/`
- `static/`
- Bases SQLite reales
- Datos reales, secretos, uploads, informes generados, fotos, backups y logs
- Routers legacy
- Carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `harness_change`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/validate_harness.sh`
- `bash -n scripts/start_harness_task.sh scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir los scripts nuevos, restaurar el runner y retirar las referencias a
los wrappers en documentacion.

# Fuera de alcance

- Crear estructuras `TASKS/` o `plans/` paralelas.
- Cambiar codigo funcional, templates o assets.
- Tocar datos reales o artefactos generados.

# Aprobacion humana requerida

No requerida para endurecimiento mecanico de harness. Requerida si se quisiera
reestructurar historico de planes o cambiar politica de ramas/git.

Estado: completado

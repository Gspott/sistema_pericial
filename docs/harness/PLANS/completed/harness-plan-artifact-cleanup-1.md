# Harness Plan Artifact Cleanup 1

# Objetivo

Evitar que planes creados desde la plantilla del harness terminen en
`docs/harness/PLANS/completed/` sin contenido operativo real.

# Modulo

Harness documental y scripts de ciclo de vida de planes.

# Riesgo

Medio. Cambia validacion y cierre de planes, pero no toca codigo funcional de
la aplicacion ni datos reales.

# Archivos permitidos

- `scripts/harness_close_plan.py`
- `scripts/audit_docs.py`
- `scripts/harness_plan_guard.py`
- `tests/smoke/test_harness_plan_guard.py`
- `docs/harness/VALIDATION/plan_quality.md`
- Artefactos de planes vacios sin valor documental.

# Archivos prohibidos

- Codigo funcional en `app/`, salvo imports de test inexistentes.
- Base de datos real, backups, uploads, informes, fotos, logs y secretos.
- Facturacion, propuestas, expedientes o informes funcionales.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/harness_change.md`.

Playbook operativo: `docs/harness/TASK_PACKS/harness_change.md`.

# Validaciones

- `pytest tests/smoke/test_harness_plan_guard.py -q`
- `pytest tests/smoke/test_harness_scope_resolver.py -q`
- `python3 scripts/audit_docs.py`
- `bash -n scripts/start_harness_task.sh scripts/finish_harness_task.sh scripts/validate_harness.sh`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios en scripts del harness, borrar el test nuevo y restaurar el
artefacto documental eliminado si hiciera falta para investigacion historica.

# Fuera de alcance

- Cambios funcionales en la aplicacion.
- Cambios de facturacion, propuestas, informes, expedientes o base de datos.
- Reescritura del modelo de planes del harness.

# Aprobacion humana requerida

Requerida si se quisiera borrar planes con contenido real o cambiar la filosofia
general de trazabilidad del harness. No requerida para bloquear plantillas
vacias ni para eliminar el artefacto vacio identificado.

# Harness Plan Artifact Cleanup 1 Validation

# Objetivo

Cerrar con el harness los cambios de calidad de planes tras la validacion
manual inicial, evitando crear otro plan vacio.

# Modulo

Harness documental.

# Riesgo

Medio. Solo valida scripts y documentacion del harness.

# Archivos permitidos

- Scripts de harness modificados.
- Tests smoke del guard de planes.
- Documentacion de validacion del harness.

# Archivos prohibidos

- Codigo funcional de la aplicacion.
- Datos reales, backups, uploads, informes, logs y secretos.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/harness_change.md`.

Task pack: `docs/harness/TASK_PACKS/harness_change.md`.

# Validaciones

- `python3 scripts/audit_docs.py`
- `pytest tests/smoke/test_harness_plan_guard.py tests/smoke/test_harness_scope_resolver.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

# Rollback

Eliminar este plan de validacion y revertir los cambios de harness si la regla
resulta demasiado estricta.

# Fuera de alcance

- Reabrir planes antiguos con contenido real.
- Cambios funcionales fuera de `scripts/` y `docs/harness/`.

# Aprobacion humana requerida

Requerida solo si se quisiera borrar planes historicos con contenido real.

Estado: completado

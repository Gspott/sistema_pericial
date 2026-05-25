# Execution Policy

# Objetivo

Crear `docs/harness/EXECUTION_POLICY.md` para definir limites de autonomia,
aprobacion humana, parada, backlog, legacy, validacion y aprendizaje.

# Modulo

Harness / autonomia operativa de Codex.

# Riesgo

Bajo-medio. Solo documentacion harness y auditoria documental; no cambia logica
de aplicacion.

# Archivos permitidos

- `docs/harness/EXECUTION_POLICY.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/GOLDEN_PRINCIPLES.md`
- `docs/harness/STATE/current_focus.md`
- `docs/harness/METRICS.md`
- `docs/harness/VALIDATION/drift_detection.md`
- `scripts/audit_docs.py`

# Archivos prohibidos

- `app/`, `templates/`, `static/`
- DB, datos reales, backups, uploads, informes, fotos, logs y secretos.

# Playbook aplicable

Task Pack sugerido: `bugfix`.
Playbook documental/harness.


# Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir los documentos de harness modificados y el check de auditoria.

# Fuera de alcance

- Automatizar aprobaciones humanas.
- Cambiar logica de aplicacion.
- Cambiar permisos reales del sistema operativo o del repo.

# Aprobacion humana requerida

Si la politica quisiera permitir acciones criticas automaticas.

Estado: completado

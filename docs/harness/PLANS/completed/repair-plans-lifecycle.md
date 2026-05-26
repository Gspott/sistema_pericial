# Repair Plans Lifecycle

# Objetivo

Auditar y reparar el lifecycle existente de `docs/harness/PLANS/` para que las
proximas fases relevantes queden registradas en `active/` y `completed/`.

# Modulo

Harness/documentacion/validacion.

# Riesgo

Bajo. Cambios limitados a harness, documentacion y runner de validacion.

# Archivos permitidos

- `docs/harness/PLANS/active/repair-plans-lifecycle.md`
- `docs/harness/PLANS/completed/`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/EXECUTION_POLICY.md`
- `docs/harness/VALIDATION/runner.md`
- `scripts/validate_harness.sh`
- `docs/harness/METRICS.md`

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

No aplica playbook funcional. Usar `GOLDEN_PRINCIPLES`, `EXECUTION_POLICY` y
documentacion de validacion del harness.

# Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios en documentos/scripts del harness y mover planes
retrospectivos fuera de `completed/` si hiciera falta.

# Fuera de alcance

- Crear una estructura `TASKS/`.
- Tocar app, templates, static o datos reales.
- Cambiar flujos funcionales.

# Aprobacion humana requerida

No requerida para documentacion y validacion mecanica de harness. Requerida si
se quisiera borrar planes historicos o reestructurar `PLANS/`.

Estado: completado

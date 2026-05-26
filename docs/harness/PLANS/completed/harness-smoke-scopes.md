# Harness Smoke Scopes

# Objetivo

Permitir scopes de validacion para reducir coste en fases pequenas sin relajar
checks criticos ni ocultar fallos.

# Modulo

Harness, validacion, wrappers y task packs.

# Riesgo

Medio. Cambia scripts de cierre/validacion; el comportamiento por defecto sigue
siendo `full`.

# Archivos permitidos

- `scripts/validate_harness.sh`
- `scripts/finish_harness_task.sh`
- `docs/harness/VALIDATION/runner.md`
- `docs/harness/VALIDATION/minimal_checks.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/EXECUTION_POLICY.md`
- `docs/harness/TASK_PACKS/README.md`
- `docs/harness/TASK_PACKS/harness_change.md`
- `docs/harness/TASK_PACKS/valoracion_change.md`

# Archivos prohibidos

- DB real, datos reales, uploads, informes, backups y secretos.
- Cambios funcionales de app/templates/static.
- Saltarse `audit_docs` o `git diff --check`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/harness_change.md`.

# Cambios ejecutados

- `validate_harness.sh` acepta `--smoke-scope docs|app|valoracion|full`.
- `finish_harness_task.sh` acepta `--smoke-scope` y lo delega al runner.
- Scope por defecto: `full`.
- `docs`: audit docs + diff check; skips explicitos para compile/js/smoke.
- `app`: audit docs + compile app/tests + JS + diff check; smoke skip explicito.
- `valoracion`: audit docs + compile app/tests + JS +
  `pytest tests/smoke -q -k valoracion` + diff check.
- `full`: comportamiento historico.
- Creado task pack `harness_change.md`.
- Actualizado `valoracion_change.md` para recomendar `--smoke-scope valoracion`
  salvo fases criticas.

# Validaciones

- `bash -n scripts/validate_harness.sh scripts/finish_harness_task.sh`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest tests/smoke -q`
- `git diff --check`
- Pendiente al cierre: `bash scripts/finish_harness_task.sh --smoke-scope valoracion`

# Rollback

Revertir scripts y docs de harness. El comportamiento previo era equivalente a
`--smoke-scope full`.

# Fuera de alcance

- Cambios de cobertura smoke.
- Nuevos tests funcionales.
- Cambios de app.

# Aprobacion humana requerida

No requerida. Si un scope causa dudas, usar `full`.

Estado: completado

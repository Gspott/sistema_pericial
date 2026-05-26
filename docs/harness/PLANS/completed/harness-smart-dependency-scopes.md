# Harness Smart Dependency Scopes

# Objetivo

Introducir smart dependency scopes en el harness para sugerir, elevar o advertir
cuando el scope solicitado no cubre los archivos modificados.

# Modulo

Harness, validacion, wrappers y tests smoke.

# Riesgo

Medio. Cambia la seleccion efectiva de validaciones, pero mantiene `full` como
default y conserva checks criticos.

# Archivos permitidos

- `scripts/harness_scope_resolver.py`
- `scripts/validate_harness.sh`
- `scripts/finish_harness_task.sh`
- `tests/smoke/test_harness_scope_resolver.py`
- `docs/harness/**`

# Archivos prohibidos

- DB real, datos reales, uploads, informes, backups y secretos.
- Cambios funcionales de app/templates/static.
- Routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/harness_change.md`.

# Cambios ejecutados

- Nuevo resolver `scripts/harness_scope_resolver.py`.
- `validate_harness.sh` calcula `required_scope` desde `git status` y eleva
  automaticamente scopes insuficientes.
- `finish_harness_task.sh` acepta `--allow-unsafe-scope` y lo delega.
- Override explicito `--allow-unsafe-scope` mantiene el scope pedido con warning.
- Tests del resolver cubren docs, valoracion, critico/full, static/app y
  override inseguro.
- Docs actualizadas en runner, policy, task packs y backlog.

# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_harness_scope_resolver.py -q`
- `python3 scripts/harness_scope_resolver.py --requested-scope docs templates/valoracion_testigos.html`
- `python3 scripts/harness_scope_resolver.py --requested-scope valoracion app/database.py`
- `python3 scripts/harness_scope_resolver.py --requested-scope docs --allow-unsafe-scope app/database.py`
- Pendientes al cierre: `python3 scripts/audit_docs.py`, `bash -n scripts/*.sh`,
  `bash scripts/finish_harness_task.sh --smoke-scope app`, `git diff --check`,
  `git status --short`.

# Rollback

Revertir resolver, wrappers, tests y docs. El comportamiento anterior queda
representado por `--smoke-scope full` sin smart upgrade.

# Fuera de alcance

- Grafo real de dependencias.
- IA/analisis semantico.
- Eliminar validaciones criticas.

# Aprobacion humana requerida

No requerida. Usar `full` ante duda.

Estado: completado

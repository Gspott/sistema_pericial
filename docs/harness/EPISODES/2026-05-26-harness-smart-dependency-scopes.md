# 2026-05-26 - Harness Smart Dependency Scopes

## Contexto

Los smoke scopes existian, pero la seleccion era manual. Se implemento un
resolver simple por paths para sugerir y elevar scopes insuficientes sin
introducir analisis dinamico ni dependencia oculta.

## Reglas Implementadas

- Solo documentacion (`docs/**`, `AGENTS.md`, `agents.md`, `README.md`):
  requerido `docs`.
- Valoracion (`templates/valoracion*`, `tests/smoke/test_valoracion*`,
  `tests/fixtures/valoracion*`, `app/services/informe.py`,
  `scripts/create_valoracion_demo_cases.py`): minimo `valoracion`.
- Static (`static/**`): minimo `app`.
- Criticos (`app/database.py`, auth/session/login/password, uploads, backups,
  PDF/DOCX, `templates/informes/`, `templates/propuestas/`, routers):
  requerido `full`.
- Otros cambios en `app/**`, `templates/**` o `tests/**`: minimo `app`.

## UX Del Runner

- Imprime `requested_scope`, `required_scope` y `effective_scope`.
- Si el scope pedido es insuficiente, imprime `[AUTO-UPGRADE]` y usa el scope
  requerido.
- `--allow-unsafe-scope` permite mantener el scope pedido, pero imprime warning
  y debe justificarse en el plan.

## Validacion

- Tests del resolver en `tests/smoke/test_harness_scope_resolver.py`.
- `bash -n` de wrappers.
- `audit_docs`.
- Smoke completo manual previo.
- Cierre con `bash scripts/finish_harness_task.sh --smoke-scope app`, que se
  auto-eleva a `full` por paths de harness/tests si corresponde.

## Limites

- Es una heuristica por paths, no un grafo de dependencias.
- Ante duda, cambios transversales o fases criticas, usar `full`.
- No elimina `audit_docs`, `git diff --check` ni lifecycle de planes.

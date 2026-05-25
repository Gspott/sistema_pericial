# Medium Backlog

Usar esta prioridad para mejoras de cobertura o seguridad operativa que reducen riesgo pero no bloquean el trabajo actual.

## Ampliar Smoke Tests

- Impacto: reduce regresiones en flujos comerciales, documentos y operaciones.
- Modulos: tests, harness.
- Riesgo: Medio.
- Task Pack recomendado: `docs/harness/TASK_PACKS/bugfix.md`.
- Validaciones minimas: `python3 -m compileall tests`, `pytest tests/smoke -q`.
- Bloqueo/no bloqueo: No bloquea tareas documentales; recomendado antes de cambios funcionales grandes.
- Dependencias: mantener fixtures temporales y no usar DB real.

## Limpieza Controlada De Artefactos Locales

- Impacto: reduce ruido de workspace y futuras auditorias.
- Modulos: repo, harness, git hygiene.
- Riesgo: Medio.
- Task Pack recomendado: `docs/harness/TASK_PACKS/bugfix.md`.
- Validaciones minimas: `git status --ignored --short`, `git status --short`, no tocar datos reales.
- Bloqueo/no bloqueo: No bloquea desarrollo.
- Dependencias: confirmar que solo se limpian `.DS_Store`, `__pycache__` y `.pytest_cache`; no incluir backups, uploads, fotos, informes ni logs.

## Auditar `seed_demo_data.py`

- Impacto: aclara si el script es herramienta demo segura o riesgo de escritura sobre DB real/uploads.
- Modulos: scripts, datos demo, seguridad workspace.
- Riesgo: Medio.
- Task Pack recomendado: `docs/harness/TASK_PACKS/db_change.md`.
- Validaciones minimas: auditoria solo lectura; no ejecutar script; no usar DB real.
- Bloqueo/no bloqueo: No bloquea tests actuales.
- Dependencias: decidir si debe documentarse como sandbox-only.

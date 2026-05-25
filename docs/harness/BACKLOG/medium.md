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

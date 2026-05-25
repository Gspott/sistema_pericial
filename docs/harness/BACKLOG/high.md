# High Backlog

Usar esta prioridad para problemas que no son emergencia inmediata, pero condicionan cambios seguros en modulos criticos.

## Monolito app/main.py

- Impacto: eleva riesgo de cambios cruzados y dificulta mantenimiento.
- Modulos: backend, expedientes, visitas, informes, auth.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: `python3 -m compileall app`, `pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea cambios quirurgicos; bloquea refactors grandes sin plan.
- Dependencias: ampliar smoke tests antes de extracciones por flujo.

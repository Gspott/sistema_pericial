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

## Cobertura Gastos

- Impacto: mejora seguridad sobre importacion, adjuntos y categorizacion.
- Modulos: gastos, base de datos, adjuntos.
- Riesgo: Alto si toca datos reales; Medio en tests sandbox.
- Task Pack recomendado: `docs/harness/TASK_PACKS/db_change.md` si hay esquema; bugfix si solo hay tests.
- Validaciones minimas: `pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea; priorizar antes de cambios en gastos.
- Dependencias: `docs/gastos.md`.

## Cobertura Emails

- Impacto: reduce riesgo de envio real accidental y rotura de plantillas.
- Modulos: emails, SMTP, propuestas, informes.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/email_change.md`.
- Validaciones minimas: smoke con mock/dry-run, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea; obligatorio antes de tocar envio real.
- Dependencias: no usar SMTP real; revisar playbook emails.

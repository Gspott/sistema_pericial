# High Backlog

Usar esta prioridad para problemas que no son emergencia inmediata, pero condicionan cambios seguros en modulos criticos.

## Drift PWA v4/v5

- Impacto: puede dejar clientes con cache/version de service worker incoherente.
- Modulos: PWA/mobile.
- Riesgo: Medio-alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/mobile_ui.md`.
- Validaciones minimas: `node --check ./static/pwa.js`, `node --check ./static/sw.js`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea docs; bloquea cambios PWA sin plan.
- Dependencias: revisar `docs/pwa.md` y playbook CSS/mobile antes de tocar service worker.

## Warning Starlette TemplateResponse

- Impacto: warning de compatibilidad futura en smoke tests.
- Modulos: backend/Jinja.
- Riesgo: Medio.
- Task Pack recomendado: `docs/harness/TASK_PACKS/bugfix.md`.
- Validaciones minimas: `python3 -m compileall app`, `pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea el runner; conviene resolver en fase dedicada.
- Dependencias: inspeccionar llamadas `TemplateResponse` sin refactorizar rutas.

## Monolito app/main.py

- Impacto: eleva riesgo de cambios cruzados y dificulta mantenimiento.
- Modulos: backend, expedientes, visitas, informes, auth.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: `python3 -m compileall app`, `pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea cambios quirurgicos; bloquea refactors grandes sin plan.
- Dependencias: ampliar smoke tests antes de extracciones por flujo.

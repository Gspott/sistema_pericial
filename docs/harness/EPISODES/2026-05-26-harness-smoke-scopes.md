# 2026-05-26 - Harness Smoke Scopes

## Contexto

El cierre de harness ejecutaba siempre la suite completa. Para fases pequenas,
especialmente documentales o acotadas de valoracion, esto aumentaba coste sin
necesidad. Se pidio introducir scopes sin relajar checks criticos.

## Cambios

- `scripts/validate_harness.sh` acepta `--smoke-scope docs|app|valoracion|full`.
- `scripts/finish_harness_task.sh` acepta `--smoke-scope` y lo pasa al runner.
- `full` sigue siendo el comportamiento por defecto.
- `audit_docs` y `git diff --check` se mantienen obligatorios en todos los
  scopes.
- Los skips se imprimen como `[SKIP]` con razon; no se silencian.
- Se creo `docs/harness/TASK_PACKS/harness_change.md`.
- Se actualizo `valoracion_change.md` para recomendar scope `valoracion` en
  fases acotadas y `full` en fases criticas.

## Scopes

- `docs`: documentacion/harness sin app.
- `app`: app pequena sin smoke especifico.
- `valoracion`: fases acotadas de valoracion con `pytest tests/smoke -q -k valoracion`.
- `full`: suite completa.

## Validaciones

- `bash -n scripts/validate_harness.sh scripts/finish_harness_task.sh`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest tests/smoke -q`
- `git diff --check`

## Riesgos

- Usar scopes pequenos en fases criticas podria ocultar fallos no relacionados.
  La regla documentada es usar `full` ante duda, para esquema, migraciones,
  PDF/DOCX moderno, calculo, uploads reales autorizados o cambios transversales.

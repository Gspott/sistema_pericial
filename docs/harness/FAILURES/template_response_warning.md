# TemplateResponse Warning

## Que Paso

Los smoke tests muestran warning de Starlette por uso antiguo de `TemplateResponse`.

## Causa Raiz

Algunas llamadas usan una firma compatible pero deprecada por Starlette.

## Deteccion

- `pytest tests/smoke -q`
- `bash scripts/validate_harness.sh`

## Impacto

No rompe ahora, pero puede convertirse en error al actualizar dependencias.

## Mitigacion

Resuelto migrando llamadas `TemplateResponse` a la firma recomendada `TemplateResponse(request, name, context)` sin cambiar contextos ni logica de rutas.

## Como Evitar Regresion

- Mantener smoke tests de rutas.
- No mezclar la correccion con refactors de templates o navegacion.
- Usar la firma nueva en cualquier renderizado server-side futuro.

## Smoke Tests Relacionados

- `tests/smoke/test_routes_basic.py`

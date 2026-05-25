# Smoke Test Context KeyError

## Que Paso

Los smoke tests pueden fallar con errores de contexto cuando una ruta o plantilla espera claves no preparadas por el fixture.

## Causa Raiz

Acoplamiento entre rutas, plantillas y datos iniciales. En tests sandbox, algunas claves reales no existen salvo que el contexto se construya igual que en produccion.

## Deteccion

- `pytest tests/smoke -q`
- errores tipo `KeyError` o fallo de render Jinja durante `TestClient`.

## Impacto

Puede bloquear tests aunque la app arranque, o revelar que una plantilla depende de datos no documentados.

## Mitigacion

Preferir fixtures temporales minimas y rutas GET no destructivas. Si falta una clave, documentar el contrato antes de ampliar mocks.

## Como Evitar Regresion

- No mockear media aplicacion.
- Mantener tests sandbox con DB temporal.
- Añadir claves al contexto real solo con plan funcional y validacion.

## Smoke Tests Relacionados

- `tests/smoke/test_routes_basic.py`
- `tests/smoke/test_informe_context.py`

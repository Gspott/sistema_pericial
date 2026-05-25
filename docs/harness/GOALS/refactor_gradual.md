# Goal: Refactor Gradual

## Objetivo

Reducir deuda tecnica sin poner en riesgo flujos reales.

## Tareas permitidas

- Extraer helpers pequenos cuando hay tests o validacion clara.
- Eliminar duplicacion local con comportamiento preservado.
- Documentar deuda y limites.

## Tareas prohibidas

- Reescribir `app/main.py` de golpe.
- Cambiar arquitectura por estetica.
- Mezclar refactor con cambios fiscales o auth.
- Introducir dependencias grandes.

## Criterios de terminado

- Comportamiento preservado.
- Diff pequeno.
- Rollback trivial.

## Validaciones obligatorias

- `python3 -m compileall app`.
- Tests/smoke del flujo tocado.
- `git diff --check`.


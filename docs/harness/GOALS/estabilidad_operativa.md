# Goal: Estabilidad Operativa

## Objetivo

Reducir fallos diarios y aumentar confianza en flujos existentes con cambios pequenos, reversibles y validados.

## Tareas permitidas

- Fixes acotados.
- Validaciones defensivas.
- Mensajes de error utiles.
- Tests de humo.
- Documentar riesgos recurrentes en playbooks.

## Tareas prohibidas

- Refactors amplios.
- Reescrituras de `app/main.py`.
- Cambios simultaneos en modulos criticos no relacionados.

## Criterios de terminado

- Bug reproducido o riesgo identificado.
- Cambio minimo aplicado.
- Validacion ejecutada.
- Rollback claro.

## Validaciones obligatorias

- `python3 -m compileall app` para Python.
- `git diff --check`.
- Validacion especifica del modulo.


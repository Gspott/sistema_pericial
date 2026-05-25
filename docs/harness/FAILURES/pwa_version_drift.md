# PWA Version Drift

## Que Paso

La auditoria detecta diferencia entre la version de registro del service worker en `static/pwa.js` y la version de cache en `static/sw.js`.

## Causa Raiz

Versionado PWA mantenido en mas de un sitio, con riesgo de quedar desincronizado.

## Deteccion

- `python3 scripts/audit_docs.py`
- `bash scripts/validate_harness.sh`

## Impacto

Puede provocar cache incoherente en clientes y comportamiento movil dificil de diagnosticar.

## Mitigacion

Resuelto alineando la version de registro con la version de cache activa. No se cambio la lista de assets ni la estrategia del service worker.

## Como Evitar Regresion

- No hardcodear versiones obsoletas.
- Mantener coincidentes la version de registro en `static/pwa.js` y la version de cache en `static/sw.js`.
- Validar todos los JS tocados.
- Mantener audit drift activo.

## Smoke Tests Relacionados

No hay smoke funcional PWA. Validacion actual: `node --check` y auditoria documental.

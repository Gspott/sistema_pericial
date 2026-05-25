# Mobile Partial Structure

## Cuando Usarlo

Cambios en Jinja/CSS/JS que afectan navegacion, drawer, CTAs o formularios mobile-first.

## Cuando NO Usarlo

- Rediseños grandes.
- SPA, React, Vue o frontend paralelo.
- Cambios PWA/service worker sin plan especifico.

## Estructura Recomendada

- Revisar `docs/ux.md` y `docs/pwa.md`.
- Reutilizar parciales existentes.
- Mantener drawer/hamburguesa como navegacion principal.
- CTAs contextuales solo si aportan contexto real.
- Validar JS tocado con `node --check`.

## Riesgos

- Navegacion duplicada.
- Formularios inutilizables en iPhone.
- JS imprescindible para POST criticos.

## Validaciones

- `node --check <archivo.js>` para cada JS modificado.
- `pytest tests/smoke -q`
- `bash scripts/validate_harness.sh`

## Anti-Patrones

- Crear navegacion superior paralela.
- Meter CSS disperso sin necesidad.
- Depender solo de JavaScript para flujos criticos.

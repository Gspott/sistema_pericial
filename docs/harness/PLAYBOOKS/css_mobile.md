# Playbook: CSS / Mobile

## Que leer primero

- `docs/ux.md`.
- `docs/pwa.md`.
- `static/mobile.css`.
- Template afectado.

## Archivos sensibles

- `static/mobile.css`.
- `static/app_shell.js`.
- `static/pwa.js`.
- `static/sw.js`.

## Acciones permitidas

- Ajustes mobile-first acotados.
- Mejorar legibilidad y tap targets.
- Validar JS tocado con `node --check`.

## Acciones prohibidas

- Introducir framework frontend.
- Crear navegacion paralela.
- Cambiar service worker sin aprobacion.
- Hardcodear versiones PWA nuevas sin decision.

## Validaciones

- Ejecutar `node --check` sobre cada archivo JS tocado.
- Para los JS principales del shell movil: `static/app_shell.js`, `static/pwa.js` y `static/sw.js`.
- Revision mobile.

## Senales de alarma

- Solapes.
- Botones que cambian de tamano.
- Drawer inutilizable.
- Cache PWA incoherente.

## Rollback

- Revertir CSS/JS.
- Indicar si el navegador necesita limpiar cache tras cambios PWA.

# PWA, JavaScript y cache

Documento tematico de PWA y JavaScript. La normativa resumida esta en `AGENTS.md`.

## Dependencias

Depende de:

- [docs/ux.md](ux.md)
- [docs/backend.md](backend.md)

Puede impactar:

- Navegacion movil.
- Sesiones y autenticacion.
- Cache/offline.
- Validaciones JS.

## Decisiones

Decision ID: PWA-001
Estado: Active
Categoria: PWA

Todo JS modificado debe validarse con `node --check <archivo.js>`.

Decision ID: PWA-002
Estado: Active
Categoria: PWA

El versionado PWA debe usar `/sw.js?v=<version>` o incremento explicito; no se permiten versiones fijas obsoletas.

## Madurez

- PWA: Activo.
- Service worker: Activo, sensible a cache de login/sesiones.
- Versionado PWA: Activo.
- Validacion JS: Activo.

## Principios

- JavaScript minimo, sin frameworks.
- Usar listeners simples y clases CSS para estados.
- Preferir progressive enhancement.
- No mover reglas criticas de negocio al navegador.
- Validar cualquier JS modificado con `node --check <archivo.js>`.

## Archivos

- `static/pwa.js`: registra `/sw.js?v=<version>` y controla ocultacion de `.top-nav` en movil.
- `static/app_shell.js`: abre/cierra drawer principal y acciones rapidas, sincroniza overlay y Escape.
- `static/sw.js`: service worker.

## Service worker

- No cachear login, sesiones ni rutas dinamicas.
- Las navegaciones usan `fetch(request)`, no cache-first.
- Cambiar `CACHE_NAME` cuando se modifiquen assets criticos cacheados.
- Actualizar version de registro del service worker cuando se modifique `static/sw.js` o assets criticos.
- No hardcodear versiones fijas u obsoletas de service worker/PWA.
- Evitar que el service worker interfiera con autenticacion.

## Validaciones

```bash
node --check <archivo.js>
```

Si aplica, validar cada archivo JS tocado con el mismo patron, incluyendo `static/app_shell.js` y `static/pwa.js`.

## Anti-patrones

- Validar solo `static/app_shell.js` si se tocaron otros JS.
- Cachear rutas dinamicas de sesion.
- Introducir frameworks o logica cliente compleja.
- Duplicar validaciones criticas que deben vivir en backend.

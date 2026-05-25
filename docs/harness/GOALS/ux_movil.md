# Goal: UX Movil

## Objetivo

Preservar y mejorar uso mobile-first en iPhone/Safari sin introducir navegacion paralela ni complejidad frontend.

## Tareas permitidas

- Ajustes CSS acotados.
- Mejoras de Jinja server-side.
- JS progresivo pequeno.
- Mejoras de drawer y formularios existentes.

## Tareas prohibidas

- React/Vue/SPA.
- Navegacion superior duplicada.
- Cambios PWA/service worker sin aprobacion.

## Criterios de terminado

- Mobile-first conservado.
- Drawer sigue siendo navegacion principal.
- No hay solapes ni acciones duplicadas.

## Validaciones obligatorias

- `node --check` si se toca JS.
- Revision visual mobile cuando sea posible.
- `python3 -m compileall app` si se toca backend.


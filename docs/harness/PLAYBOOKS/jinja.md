# Playbook: Jinja

## Que leer primero

- `docs/ux.md`.
- Template afectado.
- Partial relacionado en `templates/partials/`.
- Router que entrega el contexto.

## Archivos sensibles

- `templates/partials/_drawer_nav.html`.
- `templates/partials/_app_shell_start.html`.
- Templates de facturacion, informes y propuestas.

## Acciones permitidas

- Cambios pequenos de estructura o copy.
- Reutilizar partials existentes.
- Mantener formularios POST para acciones destructivas.

## Acciones prohibidas

- Duplicar navegacion principal.
- Mover reglas de negocio al template.
- Romper nombres de campos esperados por backend.

## Validaciones

- `python3 -m compileall app` si cambia contexto Python.
- Smoke de render.
- Revision mobile si aplica.

## Senales de alarma

- Formularios sin CS/ownership equivalente.
- Links GET destructivos.
- CTAs globales duplicados fuera del drawer.

## Rollback

- Revertir template.
- Restaurar partial anterior.


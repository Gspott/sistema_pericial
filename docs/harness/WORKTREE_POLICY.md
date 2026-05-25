# Worktree Policy

## Principios

- Una tarea grande debe aislarse en una rama o worktree dedicado.
- No mezclar modulos criticos en el mismo cambio.
- Mantener merges pequenos y reversibles.
- Evitar cambios funcionales y documentales amplios en el mismo lote.

## Combinaciones prohibidas sin plan

- Facturacion + frontend general.
- Autenticacion + informes.
- Backups/restore + base de datos.
- Deploy/acceso remoto + cambios de aplicacion.
- PWA/service worker + cambios de navegacion amplios.

## Criterio de separacion

Separar en tareas distintas cuando:

- Cambian validaciones obligatorias.
- Cambia el riesgo del modulo.
- Requiere aprobaciones humanas distintas.
- Afecta datos reales o fiscalidad.
- El rollback no puede explicarse en menos de cinco lineas.


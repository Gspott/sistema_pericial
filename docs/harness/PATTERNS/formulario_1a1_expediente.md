# Formulario 1a1 De Expediente

## Cuando Usarlo

Cuando una tabla extension 1:1 guarda datos estables vinculados a un expediente
sin modificar la tabla principal `expedientes`.

## Patron

- Validar ownership del expediente con `get_owned_expediente()`.
- GET: cargar fila extension si existe; si no, mostrar formulario vacio.
- POST: hacer upsert por `expediente_id`.
- Redirigir al detalle del expediente con 303.
- Mantener formularios server-side y mobile-first.
- Si hay datos legacy, mostrarlos como referencia solo lectura salvo que exista
  una accion explicita de migracion/copia.

## Anti-Patrones

- Copiar legacy automaticamente al abrir el formulario.
- Editar tablas legacy en la misma pantalla si el objetivo es mover la fuente
  principal.
- Crear APIs paralelas para un formulario server-side simple.
- Ocultar cambios de fuente de verdad sin smoke de `build_informe_context()`.

## Validaciones

- Smoke de GET formulario.
- Smoke de POST con DB temporal.
- Verificar que la tabla legacy no cambia.
- Verificar que `build_informe_context()` lee la nueva fuente.

# Formulario 1a1 De Visita

## Cuando Usarlo

Cuando una tabla extension 1:1 guarda datos observados en una visita sin
mezclarlos con datos estables del expediente.

## Patron

- Validar ownership mediante `get_owned_visita()`.
- GET: cargar fila extension si existe; si no, mostrar formulario vacio.
- POST: hacer upsert por `visita_id` y conservar `expediente_id`.
- Redirigir al flujo natural de visita con 303.
- Mantener formulario server-side y mobile-first.
- Mostrar legacy solo como referencia cuando ayude, sin copia automatica.

## Anti-Patrones

- Mover finalidad, documentacion, superficies, entorno, metodo o limitaciones a
  la visita.
- Editar la tabla legacy desde la nueva pantalla de transicion.
- Crear APIs paralelas para un formulario server-side simple.

## Validaciones

- Smoke de GET formulario.
- Smoke de POST con DB temporal.
- Verificar que la tabla legacy no cambia.
- Verificar que `build_informe_context()` lee la observacion nueva.

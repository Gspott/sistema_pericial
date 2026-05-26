# Visita Especifica Por Tipo De Informe

## Contexto

`nueva_visita.html` es compartido por patologias, inspeccion, habitabilidad y
valoracion. Cuando un tipo de informe ya tiene formularios especificos fuera de
la visita, el template no debe volver a mostrar campos generales que pertenecen
a expediente, testigos, ajustes o resultados.

## Patron

- Mantener una sola ruta server-side de visita si el flujo existente lo permite.
- Usar flags de contexto (`es_informe_valoracion`, `es_informe_inspeccion`, etc.)
  para ocultar bloques completos, no campos sueltos dispersos.
- Conservar nombres de campos esperados por backend para los tipos no afectados.
- Si se ocultan campos legacy, evitar que el POST los sobrescriba en blanco.
- Reutilizar tablas/fotos compatibles antes de pedir esquema nuevo.
- Registrar como backlog cualquier dato nuevo que necesite persistencia real.

## Aplicacion 2026-05-26

En visitas de valoracion, `nueva_visita.html` queda limitado a:

- Exterior del edificio.
- Reforma observada.
- Portal y contadores con observaciones en `valoracion_visita_observaciones` y
  fotos `visita_fotos.categoria='portal_contadores'`.
- Datos esenciales de visita.
- Acceso a registro de estancias.

Quedan fuera de la visita de valoracion los campos generales de encargo,
documentacion, identificacion, situacion legal, entorno, metodo, resultado,
limitaciones, comparables legacy y climatologia.

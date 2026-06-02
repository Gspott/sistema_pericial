# 2026-06-01 - Valoracion workbench UX-VAL-2

## Resumen

Se mejora el workbench SSR de valoracion con seleccion de testigo por query param y panel contextual mas tecnico.

## Cambios

- `GET /expediente/{expediente_id}/valoracion/workbench?testigo_id=...` selecciona un testigo del contexto.
- Si el `testigo_id` no pertenece al expediente, degrada al primer testigo y muestra advertencia no bloqueante.
- La tabla permite seleccionar testigos con enlaces por fila.
- El panel muestra datos economicos, unitarios, inclusion/exclusion, peso, similitud, fiabilidad, advertencias, incidencias y ajustes.
- Las acciones enlazan solo a rutas existentes: expediente, testigos clasicos, editar testigo y editar ajustes.

## Invariantes

- Sin SPA ni JavaScript obligatorio.
- Sin editor inline ni entidades nuevas.
- Sin cambios en patologias, inspecciones, informes ni DB real.
- Mantiene `build_informe_context()` como fuente de datos y fallback legacy.

## Pendiente

- QA visual manual con casos demo en escritorio y movil.
- Fase futura para filtros/segmentacion en la tabla sin convertirla en spreadsheet.

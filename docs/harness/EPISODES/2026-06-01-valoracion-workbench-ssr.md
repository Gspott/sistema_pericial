# 2026-06-01 - Valoracion workbench SSR

## Resumen

Primera version incremental del Workbench de Valoracion Inmobiliaria como vista SSR de escritorio.

## Cambios

- Nueva ruta `GET /expediente/{expediente_id}/valoracion/workbench`.
- Nuevo template `templates/valoracion_workbench.html` con CSS scoped.
- La vista reutiliza `build_informe_context()` para expediente, resumen de valoracion, comparables, ponderacion e incidencias.
- Smoke de render para expediente de valoracion y redireccion defensiva para expedientes no valoracion.

## Invariantes

- No sustituye formularios mobile-first existentes.
- No toca DB real, uploads reales, informes generados ni backups.
- No modifica HTML/PDF/DOCX ni calculo final.
- No introduce SPA ni frontend separado.

## Pendiente

- QA visual en escritorio y movil con casos demo.
- Fase futura para seleccion contextual real de testigo en panel lateral, sin SPA.

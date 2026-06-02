# 2026-05-27 - Valoración comparación 2B homogeneización

## Resumen

Se añadió homogeneización manual/semiestructurada por testigo vinculado a expediente, partiendo del €/m² inicial de Fase 2A.

## Cambios

- `valoracion_testigo_ajustes` se amplía defensivamente con campos de matriz.
- La fila legacy de ajustes se mantiene separada usando `variable` vacía.
- Servicio puro de comparación calcula ajustes porcentuales, ajustes por importe €/m² y ajustes cualitativos.
- Pantalla de ajustes permite listar, crear, editar y desactivar ajustes de homogeneización.
- `build_informe_context()` expone matriz, pasos, €/m² homogeneizado y advertencias.
- HTML/PDF y DOCX muestran matriz de homogeneización por comparable.

## Fuera de alcance

- No hay ponderación.
- No hay scoring.
- No hay outliers.
- No hay valor final automático.
- No hay scraping/OCR.

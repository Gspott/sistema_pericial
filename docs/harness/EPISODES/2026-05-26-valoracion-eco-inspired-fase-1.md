# 2026-05-26 - Valoración ECO-inspired fase 1

## Resumen

Se añadió una capa defensiva para valoración pericial con estructura inspirada en estándares ECO/805/2003, sin presentar el informe como tasación regulada.

## Cambios

- Columnas defensivas en `valoracion_expediente` para finalidad, base de valor, superficies profesionales, métodos e incidencias.
- Formulario server-side de datos estables ampliado con los nuevos bloques.
- `build_informe_context()` expone `valoracion_eco` y acceso compatible desde `valoracion["finalidad"]`, `valoracion["base_valor"]`, `valoracion["superficies"]`, `valoracion["metodos"]` e `valoracion["incidencias"]`.
- HTML/PDF moderno y DOCX editable muestran nota metodológica, finalidad, base, superficies, métodos e incidencias visibles.
- Smoke específico cubre datos completos, degradación incompleta, fallback legacy y DOCX.

## Fuera de alcance

- No se implementa cálculo final.
- No se implementa homogeneización avanzada.
- No se implementa scraping, OCR ni importación automática.
- No se migran datos legacy.

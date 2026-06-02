# 2026-06-01 - Valoracion workbench UX-VAL-3

## Resumen

Se anade productividad visual y QA tecnico al workbench SSR de valoracion.

## Cambios

- Barra superior de diagnostico: total, incluidos, excluidos, incompletos, advertencias, rango homogeneizado y diferencia relativa.
- Filtros SSR por `filtro=todos|incluidos|excluidos|advertencias|incompletos`.
- Ordenacion SSR por `ordenar=homogeneizado|peso|similitud|fiabilidad|fecha` y `dir=asc|desc`.
- La seleccion `testigo_id` se conserva si sigue visible y degrada con aviso si el filtro la oculta.
- Estado vacio claro cuando un filtro no deja testigos visibles.
- Leyenda visual de incluido, excluido, incompleto, advertencia e incidencia.

## Invariantes

- Sin JS obligatorio ni SPA.
- Sin edicion inline.
- Sin entidades nuevas ni calculos persistidos.
- Sin adopcion automatica de valor final.
- Reutiliza `build_informe_context()`, `comparables_valoracion` y `resumen_comparacion_valoracion`.

## Pendiente

- QA visual manual con casos demo en escritorio y movil.
- Posible fase futura de exportacion de vista de analisis, sin convertirla en spreadsheet completo.

# 2026-05-26 - Valoracion Quick Wins QA Visual

## Contexto

Se aplicaron quick wins derivados del QA visual de valoracion sin cambiar
modelo, esquema ni calculo. La fase se limito a presentacion, filtros
server-side y jerarquia visual.

## Cambios

- Biblioteca `/valoracion/testigos`:
  - filtros por tipologia, municipio, validacion y reutilizable;
  - busqueda libre conservada;
  - miniatura de la primera foto del testigo cuando existe.
- Seleccion por expediente:
  - filtro/busqueda server-side de testigos disponibles;
  - valores vinculados formateados con unidades;
  - `Quitar del expediente` diferenciado como accion secundaria/destructiva.
- Informe HTML/PDF moderno:
  - comparables con importes, superficies y valores unitarios formateados;
  - ocultacion de campos vacios tipo `-` en secciones de valoracion y
    comparables.
- Smokes actualizados para cubrir filtros, miniatura, formatos, accion
  destructiva, informe y fallback.

## QA Visual Sandbox

Se genero DB sandbox temporal con casos demo y se levanto app temporal en
`127.0.0.1:8766`. Verificacion mobile 390x844:

- Biblioteca con filtros visibles.
- Seleccion por expediente con filtros visibles.
- Informe con `EUR/m2`, `m2` y sin numeros crudos demo.
- Sin overflow horizontal.

## Fuera De Alcance

- No se compacto la seccion de comparables como tabla/resumen de mercado; queda
  como pendiente estructural porque implica redisenar el bloque.
- No scraping, OCR ni descarga remota.
- No calculo definitivo, metodo de coste ni migracion legacy.

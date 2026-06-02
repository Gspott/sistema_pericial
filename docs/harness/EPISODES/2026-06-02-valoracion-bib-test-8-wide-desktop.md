# Valoracion BIB-TEST-8 Wide Desktop

Fecha: 2026-06-02

## Objetivo

Mejorar la ergonomia desktop de la biblioteca de testigos, alta rapida y ficha
detalle, aprovechando mas anchura de pantalla sin cambiar logica ni romper
mobile-first.

## Cambios

- Biblioteca desktop: contenedor casi full-width, diagnostico mas compacto,
  filtros densos y tabla con padding reducido.
- Alta rapida: contenedor wide, pegado asistido lateral en escritorio ancho y
  formulario tecnico en columnas.
- Detalle de testigo: grid compacto para datos principales/caracteristicas y
  galeria de fotos mas densa.

## Invariantes

- CSS scoped dentro de cada template.
- Sin DB, calculos, informes, Workbench ni JS obligatorio.
- En mobile los layouts vuelven a una columna o mantienen scroll horizontal.

## Smokes

- Render de biblioteca con contenedor desktop.
- Render de alta rapida con contenedor y bloque de pegado asistido wide.
- Render de detalle con contenedor wide y galeria de fotos.

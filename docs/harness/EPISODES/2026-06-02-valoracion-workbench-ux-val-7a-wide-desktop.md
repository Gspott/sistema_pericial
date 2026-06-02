# Valoracion Workbench UX-VAL-7A Wide Desktop

Fecha: 2026-06-02

## Objetivo

Aprovechar mejor pantallas de escritorio en el Workbench de Valoracion,
reduciendo scroll vertical y aumentando densidad informativa sin cambiar logica.

## Cambios

- Contenedor del workbench casi full-width.
- Layout principal aproximado 72/28 entre tabla y panel.
- Cabecera, diagnostico y metricas mas compactas.
- Tabla con padding menor, tipografia compacta y badges mas pequenos.
- Panel lateral sticky solo en desktop.

## Invariantes

- CSS scoped al template `valoracion_workbench.html`.
- Sin DB, calculos, informes, biblioteca ni JS obligatorio.
- En mobile vuelve a una columna y conserva scroll horizontal.

## Smokes

- Render del workbench.
- Presencia de clase `workbench-wide-desktop`.
- Smokes existentes de seleccion, filtros, trazabilidad y microedicion siguen
  pasando.

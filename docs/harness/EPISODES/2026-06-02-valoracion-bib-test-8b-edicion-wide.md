# Valoracion BIB-TEST-8B Edicion Wide

Fecha: 2026-06-02

## Objetivo

Alinear el formulario completo de alta/edicion de testigos reutilizables con la
ergonomia desktop wide de la biblioteca, alta rapida y detalle.

## Cambios

- `valoracion_testigo_form.html` usa contenedor wide, hero contextual, secciones
  compactas y grid de 3/4 columnas en escritorio.
- En mobile degrada a una columna.
- Se incorporan campos tecnicos ya existentes de BIB-TEST-6 al formulario
  completo: exterior, balcon, patio, anos, aire acondicionado, calefaccion,
  certificacion energetica y anexos.
- Se mantienen rutas `GET/POST /valoracion/testigos/{id}/editar`.

## Invariantes

- Sin DB ni calculos.
- Sin Workbench ni informes.
- Sin SPA ni JavaScript obligatorio.
- Guardado server-side existente.

## Smokes

- GET edicion renderiza layout wide.
- POST edicion actualiza campos tecnicos.
- Smokes existentes de biblioteca, alta rapida, detalle, fotos y vinculos siguen
  pasando.

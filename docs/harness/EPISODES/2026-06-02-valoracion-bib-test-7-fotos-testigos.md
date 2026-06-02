# Valoracion BIB-TEST-7 Fotos De Testigos

Fecha: 2026-06-02

## Objetivo

Asociar fotografias o capturas manuales a testigos reutilizables para documentar
estado, calidades y evidencia visual del anuncio, sin scraping ni descarga
automatica de imagenes externas.

## Patron Usado

- Se reutiliza `testigos_valoracion_fotos`.
- Se reutiliza `guardar_uploads_contextuales()` con carpeta de uploads del
  entorno.
- En smokes, los uploads viven en ruta temporal configurada por el harness.
- La ficha del testigo muestra miniaturas y enlace "Ver foto".

## Validaciones De Upload

- Extensiones permitidas: JPG, JPEG, PNG, WEBP y GIF.
- Tipo MIME de imagen cuando viene informado.
- Tamano maximo por archivo: 10 MB.
- Ownership del testigo antes de guardar.

## Fuera De Alcance

- Descargar imagenes desde portales.
- Scraping, OCR o IA.
- Borrado fisico de fotos.
- Insercion automatica en informes.
- Optimizacion avanzada fuera del procesado existente.

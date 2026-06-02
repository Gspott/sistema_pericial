# 2026-05-26 - Valoración comparación 2A económicos

## Resumen

Se añadió una capa económica inicial para testigos de valoración, orientada al futuro método de comparación.

## Cambios

- Columnas defensivas en `testigos_valoracion` para precio depurado, superficie tomada, €/m² inicial, fuente, verificación, fiabilidad, similitud y observaciones económicas.
- Nuevo servicio puro `app/services/valoracion_comparacion.py`.
- Formulario de testigo ampliado con bloque "Datos económicos y fuente".
- Contexto de informe expone datos económicos y advertencias no bloqueantes por comparable.
- HTML/PDF y DOCX muestran nota de cálculo inicial.
- Smokes cubren cálculo puro, contexto, HTML, DOCX, fallback legacy y advertencias.

## Fuera de alcance

- Homogeneización.
- Ponderación.
- Scoring.
- Outliers.
- Valor final automático.
- Scraping/OCR.

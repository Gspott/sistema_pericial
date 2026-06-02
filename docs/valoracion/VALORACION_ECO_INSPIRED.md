# Valoración ECO-inspired

Esta línea de trabajo añade una capa de valoración pericial con estructura inspirada en estándares ECO/805/2003, sin convertir el informe en una tasación regulada ni usar esa finalidad como salida del sistema.

## Alcance

- Finalidad, alcance y fecha de valoración.
- Base de valor y definición aplicada.
- Superficies consideradas y superficie adoptada para cálculo.
- Métodos aplicados o descartados: comparación, coste, actualización de rentas y residual.
- Condicionantes, advertencias y limitaciones automáticas o manuales.

La prioridad funcional es trazabilidad, prudencia, justificación y defensa pericial. La capa no implementa cálculo final avanzado, homogeneización estadística, scoring ni automatización documental externa.

## Nota metodológica

El informe moderno debe mostrar una nota clara:

> El presente informe no constituye tasación hipotecaria regulada salvo que expresamente se indique y se cumplan los requisitos legales aplicables. Su estructura técnica se inspira en criterios de trazabilidad, prudencia y justificación propios de estándares profesionales de valoración.

## Reglas

- Mantener fallback legacy desde `valoracion_visita` y `comparables_valoracion`.
- El modelo nuevo prevalece sobre legacy cuando existe `valoracion_expediente`.
- No eliminar campos legacy hasta una fase específica de migración y QA.
- No introducir scraping, OCR ni cálculo definitivo sin fase propia.
- No usar datos reales en demos o smokes.

# Valoración por comparación

## Fase 2A: datos económicos iniciales

Esta fase prepara el dato económico de los testigos reutilizables para futuras fases de comparación profesional.

Alcance implementado:

- Precio ofertado.
- Precio depurado.
- Superficie tomada.
- Tipo de superficie tomada.
- Fuente, detalle, URL o referencia.
- Fecha del testigo y fecha de captura.
- Dato verificado y testigo visitado.
- Fiabilidad, similitud y observaciones económicas.
- Cálculo inicial de `precio_unitario_inicial`.

## Regla de cálculo inicial

`precio_unitario_inicial = precio_depurado / superficie_tomada`

Si no existe `precio_depurado`, se usa `precio_oferta` como fallback prudente. Si falta superficie tomada o precio utilizable, el cálculo no se realiza y se genera advertencia no bloqueante.

## Fuera de alcance

- No hay homogeneización.
- No hay ponderación.
- No hay scoring.
- No hay detección de outliers.
- No hay valor final automático.
- No hay scraping ni OCR.

## Fase 2B: homogeneización manual/semiestructurada

La fase 2B añade una matriz de homogeneización por testigo vinculado a expediente.

Cada ajuste puede ser:

- `porcentaje`: modifica secuencialmente el €/m² acumulado.
- `importe_m2`: suma o resta un importe €/m².
- `cualitativo_no_cuantificado`: se documenta, pero no modifica el cálculo.

Variables mínimas:

- superficie
- estado de conservación
- antigüedad
- planta
- ascensor
- ubicación
- calidad constructiva
- reformas
- anexos
- exterior/interior
- orientación
- fuente/negociación
- otro

El cálculo parte de `precio_unitario_inicial` y devuelve un `unitario_homogeneizado` trazable con pasos, efectos y advertencias.

La fase no calcula ponderaciones, scoring, outliers ni valor final automático.

Advertencias no bloqueantes:

- ajuste sin justificación;
- ajuste porcentual sin porcentaje;
- ajuste por importe €/m² sin importe;
- signo ausente en ajuste cuantificado;
- falta de €/m² inicial;
- ajuste total superior al 30%;
- testigo sin ajustes activos.

## Trazabilidad

El precio depurado debe ser trazable y justificable. La depuración puede recoger criterio profesional manual, pero no debe ocultar el precio ofertado original ni sobrescribirlo.

El informe debe mostrar la nota:

> Los valores unitarios iniciales no incorporan todavía homogeneización ni ponderación técnica salvo que se indique expresamente.

## Fase 2C: resumen comparativo y ponderación técnica

La fase 2C añade ponderación manual por testigo vinculado al expediente. El perito puede marcar si participa en el cálculo comparativo, asignar un peso porcentual, documentar representatividad y justificar ponderación o exclusión.

El resumen comparativo calcula métricas preparatorias:

- mínimo, máximo, media y mediana de €/m²;
- media ponderada si existen pesos;
- suma de pesos;
- propuesta unitaria orientativa.

Reglas:

- Se usa preferentemente `unitario_homogeneizado`.
- Si falta, se usa `precio_unitario_inicial` con advertencia.
- Si hay pesos y no suman 100%, se advierte.
- La propuesta orientativa usa el ponderado si los pesos son válidos; si no hay pesos, usa la mediana.
- El resultado no cierra automáticamente el valor final del inmueble.

Advertencias no bloqueantes:

- no hay testigos incluidos;
- menos de 3 testigos incluidos;
- pesos que no suman 100%;
- testigo incluido sin unitario homogeneizado;
- testigo excluido sin motivo;
- testigo ponderado sin motivo;
- dispersión elevada entre unitarios;
- propuesta orientativa no calculable.

La fase no implementa scoring, outliers complejos ni valor final automático.

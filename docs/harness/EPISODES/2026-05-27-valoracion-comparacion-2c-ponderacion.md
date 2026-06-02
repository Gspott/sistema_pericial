# 2026-05-27 - Valoracion comparacion 2C ponderacion

## Resumen

Se implementa la fase 2C del modulo de valoracion inmobiliaria: resumen comparativo y ponderacion tecnica no automatica de testigos vinculados al expediente.

## Cambios

- Columnas defensivas en `valoracion_expediente_testigos` para inclusion en calculo, peso, representatividad y motivos.
- Columnas defensivas preparatorias en `valoracion_resultados` para unitarios comparativos revisables.
- Servicio puro de resumen comparativo: media, mediana, rango, ponderado, suma de pesos y propuesta orientativa.
- `build_informe_context()` expone `valoracion["resumen_comparacion"]` y datos de ponderacion por comparable.
- HTML/PDF y DOCX incluyen seccion de resumen comparativo y nota de caracter preparatorio.
- Smoke 2C cubre servicio, contexto, HTML, DOCX y fallback legacy.

## Invariantes

- No se cierra automaticamente el valor final del inmueble.
- No hay scoring ni outliers complejos.
- No se elimina fallback legacy.
- No se tocan datos reales, uploads, informes generados ni backups.

## Pendiente

- Fase posterior para adopcion justificada del valor unitario por el perito.
- QA visual de tabla/resumen comparativo en movil con casos demo.

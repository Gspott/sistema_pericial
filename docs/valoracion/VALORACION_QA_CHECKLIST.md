# QA de valoración ECO-inspired

## Contexto

- El expediente de valoración expone `tipo_informe="valoracion"`.
- `build_informe_context()` no rompe patologías, inspección ni habitabilidad.
- El fallback legacy sigue devolviendo datos si no existe `valoracion_expediente`.
- `comparables_valoracion` sigue degradando a lista vacía si no hay testigos.

## UX

- El formulario de datos de valoración muestra finalidad/alcance, base de valor, superficies, métodos e incidencias.
- La visita queda reservada para observaciones físicas.
- Los campos son server-side y mobile-first.
- Los textos no presentan el informe como tasación regulada.

## Informe

- HTML/PDF contiene finalidad y alcance.
- HTML/PDF contiene base de valor.
- HTML/PDF contiene superficies consideradas y superficie adoptada.
- HTML/PDF contiene métodos aplicados y descartados.
- HTML/PDF contiene condicionantes, advertencias y limitaciones visibles.
- DOCX editable contiene las mismas secciones.
- No aparecen bloques de patologías en valoración.
- La sección de comparables muestra precio ofertado, precio depurado, superficie tomada y €/m² inicial cuando existan.
- El informe advierte que el €/m² inicial no incorpora homogeneización ni ponderación técnica.

## Comparación 2A

- `precio_unitario_inicial` se calcula con precio depurado y superficie tomada.
- Si no hay precio depurado, se usa precio ofertado.
- Si falta superficie tomada, no se calcula y se genera advertencia.
- Las advertencias por testigo no bloquean guardado ni emisión.
- El precio ofertado original no se sobrescribe.
- No hay scoring, outliers, ponderación ni valor final automático.

## Homogeneización 2B

- Los ajustes cuantificados modifican el €/m² inicial en orden.
- Los ajustes cualitativos aparecen en informe y no modifican el cálculo.
- Un ajuste sin justificación genera advertencia no bloqueante.
- Un testigo sin €/m² inicial no calcula homogeneización.
- La matriz aparece en HTML/PDF y DOCX.
- Fallback legacy sigue funcionando sin matriz.
- No hay ponderación, scoring, outliers ni valor final automático.

## Ponderación 2C

- La pantalla de testigos vinculados muestra resumen comparativo.
- Cada testigo vinculado permite editar inclusión en cálculo, peso, representatividad y motivos.
- Los pesos válidos suman 100%.
- Los pesos inválidos generan advertencia no bloqueante.
- Los testigos excluidos pueden documentar motivo.
- La media, mediana, rango y ponderado aparecen en HTML/PDF.
- DOCX editable contiene el resumen comparativo.
- El informe declara que el resumen es preparatorio y que la adopción corresponde al perito.
- Fallback legacy sigue funcionando.
- No hay scoring, outliers complejos ni cierre automático de valor final.

## Incidencias automáticas mínimas

- Falta referencia catastral.
- Falta superficie adoptada.
- Falta fecha de valoración.
- Falta finalidad.
- Menos de 3 testigos si comparación está aplicada.
- Testigos sin fuente.
- Ausencia de documentación registral.
- Ausencia de información catastral.

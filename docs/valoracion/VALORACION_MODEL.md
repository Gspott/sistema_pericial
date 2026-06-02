# Modelo de valoración

## Entidades actuales

- `valoracion_expediente`: datos estables del expediente y capa ECO-inspired.
- `valoracion_visita_observaciones`: observaciones físicas de visita.
- `testigos_valoracion`: biblioteca reutilizable de testigos.
- `valoracion_expediente_testigos`: vínculo expediente-testigo con snapshot.
- `valoracion_testigo_ajustes`: ajustes manuales por testigo vinculado.
- `valoracion_resultados`: resultados futuros por método.

## Testigos: datos económicos de comparación

`testigos_valoracion` incorpora una capa económica preparatoria:

- `precio_oferta`: precio original ofertado o indicado por la fuente.
- `precio_depurado`: precio ajustado manualmente de forma trazable, sin borrar el original.
- `precio_unitario_inicial`: €/m² simple antes de homogeneización.
- `superficie_tomada`: superficie usada para el €/m² inicial.
- `tipo_superficie_tomada`: construida, útil, registral, catastral u otra.
- `fuente_tipo`, `fuente_detalle`, `url_fuente`.
- `fecha_testigo`, `fecha_captura`.
- `dato_verificado`, `testigo_visitado`.
- `fiabilidad_dato`, `similitud_inmueble`, `estado_mercado`.
- `observaciones_economicas`.

`url_fuente` se mantiene como nombre canónico existente para la URL o referencia de fuente, evitando duplicar un campo `fuente_url`.

El cálculo de `precio_unitario_inicial` es preparatorio y no modifica `valor_unitario` legacy ni calcula valor final.

## Homogeneización

`valoracion_testigo_ajustes` mantiene compatibilidad con la fila legacy de ajustes manuales cuando `variable` está vacía.

Las filas de homogeneización semiestructurada usan `variable` informada y pueden incluir:

- `expediente_id`
- `testigo_id`
- `variable`
- `variable_otro`
- `valor_inmueble`
- `valor_testigo`
- `tipo_ajuste`
- `ajuste_porcentaje`
- `ajuste_importe_m2`
- `signo`
- `justificacion`
- `orden`
- `activo`

El valor homogeneizado es derivado y recalculable desde el testigo y sus ajustes activos. No se usa todavía para valor final automático.

## Campos ECO-inspired en expediente

Finalidad:
- `finalidad_valoracion`
- `finalidad_otro`
- `alcance_valoracion`
- `fecha_valoracion`

Base de valor:
- `base_valor`
- `base_valor_otro`
- `definicion_base_valor`

Superficies:
- `superficie_util`
- `superficie_construida`
- `superficie_registral`
- `superficie_catastral`
- `superficie_comprobada`
- `superficie_computable`
- `superficie_adoptada_calculo`
- `criterio_superficie_adoptada`

Métodos:
- comparación
- coste
- actualización de rentas
- residual

Cada método dispone de estado aplicado/descartado, justificación y observaciones.

Incidencias:
- `incidencias_condicionantes_manuales`
- `incidencias_advertencias_manuales`
- `incidencias_limitaciones_manuales`
- visibilidad automática/manual.

## Contexto de informe

`build_informe_context()` expone:

- `valoracion_eco`
- `valoracion["finalidad"]`
- `valoracion["base_valor"]`
- `valoracion["superficies"]`
- `valoracion["metodos"]`
- `valoracion["incidencias"]`
- `comparables_valoracion[*]["precio_unitario_inicial"]`
- `comparables_valoracion[*]["advertencias_calculo"]`
- `comparables_valoracion[*]["ajustes_homogeneizacion"]`
- `comparables_valoracion[*]["unitario_homogeneizado"]`
- `comparables_valoracion[*]["pasos_homogeneizacion"]`
- `comparables_valoracion[*]["advertencias_homogeneizacion"]`
- `comparables_valoracion[*]["incluido_calculo"]`
- `comparables_valoracion[*]["peso_porcentaje"]`
- `comparables_valoracion[*]["representatividad"]`
- `comparables_valoracion[*]["unitario_para_resumen"]`
- `valoracion["resumen_comparacion"]`
- `valoracion["comparacion"]["resumen"]`

La clave histórica `valoracion` sigue siendo iterable como lista para conservar compatibilidad con templates y smokes previos.

## Ponderación 2C

`valoracion_expediente_testigos` incorpora datos de ponderación no automática:

- `incluido_calculo`
- `peso_porcentaje`
- `motivo_ponderacion`
- `representatividad`
- `motivo_exclusion`
- `observaciones_ponderacion`

Estos campos pertenecen al vínculo expediente-testigo, no al testigo reusable. Permiten que un mismo testigo tenga peso o exclusión distinta en cada expediente.

`valoracion_resultados` queda preparado defensivamente para guardar, en fases posteriores, métricas revisables de comparación:

- unitarios mínimo, máximo, medio, mediana y ponderado;
- unitario recomendado;
- justificación del unitario recomendado;
- marca de resultado revisado.

La fase 2C no guarda ni adopta automáticamente el valor final del inmueble.

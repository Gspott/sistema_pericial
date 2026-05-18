# ADR-008 - Propuestas con lineas de servicio

Decision ID: PROP-001
Estado: Active
Categoria: Datos
Fecha/periodo: 2026-05
Fuente normativa: [docs/modelos_datos.md](../modelos_datos.md)

## Contexto

El generador de propuestas necesitaba separar servicios periciales, condiciones, exclusiones y honorarios sin convertir el sistema en un ERP ni romper propuestas antiguas.

## Decision

Las propuestas pueden usar `propuesta_lineas` como desglose estructurado de servicios. Cuando existen lineas, son la fuente economica de verdad y los importes agregados de `propuestas` se sincronizan desde ellas.

Las lineas admiten categorias, campos documentales de `incluye`, `no_incluye` y `condiciones`, y servicios rapidos que crean lineas normales: ratificacion judicial, desplazamientos/dietas, recargo por urgencia y suplemento por complejidad.

## Consecuencias

- Propuestas antiguas sin lineas siguen funcionando con importes globales.
- El PDF/imprimible muestra desglose de servicios cuando existe y fallback global cuando no existe.
- Los servicios rapidos no crean tablas, catalogos ni APIs paralelas.
- El calculo monetario debe redondear a 2 decimales y evitar importes negativos.
- Urgencia y complejidad se calculan sobre base imponible sin IVA para evitar doble IVA.
- El borrado de lineas requiere confirmacion server-side.

## Impacta a

- [docs/modelos_datos.md](../modelos_datos.md)
- [docs/backend.md](../backend.md)
- [docs/ux.md](../ux.md)
- [docs/informes.md](../informes.md)

## Sustituye / relacionado con

- Relacionado con `API-001`, porque los servicios rapidos son endpoints POST server-side y no APIs de negocio paralelas.

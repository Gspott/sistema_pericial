# 2026-05-25 - Valoracion Modelo Comparacion Diseno

## Resumen

Se diseno la evolucion segura del modelo de valoracion inmobiliaria para mover
datos estables desde visita hacia expediente y preparar testigos reutilizables
con ajustes/homogeneizacion trazable.

## Alcance

- Auditoria solo lectura de `expedientes`, `visitas`, `valoracion_visita`,
  `comparables_valoracion`, constantes de valoracion, formularios y contexto de
  informe.
- Matriz de decision campo a campo.
- Modelo futuro recomendado para datos estables, observaciones de visita,
  testigos reutilizables, vinculos expediente-testigo, ajustes y resultados.
- Roadmap por fases sin implementar esquema ni calculo.

## Limitacion

El PDF de referencia no estaba accesible como archivo adjunto en el workspace.
No se leyeron PDFs de `uploads/` por restriccion de seguridad.

## No Tocado

No se cambio esquema, DB real, datos reales, uploads, informes reales, backups,
routers legacy ni carpeta anidada `sistema_pericial/`.

## Plan

`valoracion-mover-campos-diseno.md`.

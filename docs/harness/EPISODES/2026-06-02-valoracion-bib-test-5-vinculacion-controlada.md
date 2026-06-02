# Valoracion BIB-TEST-5 Vinculacion Controlada

Fecha: 2026-06-02

## Objetivo

Permitir que la biblioteca desktop de testigos reutilizables pueda vincular un
testigo a un expediente de valoracion cuando la vista recibe `expediente_id`,
sin asignacion masiva ni mezcla de datos globales con criterios tecnicos del
expediente.

## Cambios

- La biblioteca desktop detecta contexto de expediente de valoracion propio y
  muestra "Anadir a este expediente" en cada testigo no vinculado.
- La ruta POST
  `/expedientes/{expediente_id}/valoracion/testigos/biblioteca/{testigo_id}/vincular`
  valida ownership, tipo `valoracion`, existencia del testigo y duplicados.
- El vinculo se guarda en `valoracion_expediente_testigos` con snapshot,
  `incluido` defensivo y sin peso ni representatividad global.
- Si el testigo ya estaba vinculado, no se crea un segundo vinculo.

## Reglas Confirmadas

- `testigos_valoracion` sigue siendo biblioteca maestra.
- `valoracion_expediente_testigos` sigue siendo el lugar para datos especificos
  del expediente.
- No se modifican informes, Workbench, calculos, uploads ni DB real.

## Smokes

- Render de biblioteca con `expediente_id` y accion contextual.
- Vinculacion valida con snapshot.
- Duplicado no crea segundo vinculo.
- Expediente no valoracion rechaza la operacion.
- Testigo inexistente rechaza la operacion.

## Pendientes

- Mantener futura asignacion masiva fuera de esta ruta hasta que exista fase
  propia con criterios de QA y rollback.
- Si se anade `return_to=workbench` desde UI, preservar filtros del Workbench
  en una fase separada.

# Valoracion Limpiar Nueva Visita

## Plan

`docs/harness/PLANS/active/valoracion-limpiar-nueva-visita.md`

## Resumen

Se limpio la pantalla `nueva_visita.html` para expedientes con
`tipo_informe='valoracion'`, manteniendo intactos patologias, inspeccion y
habitabilidad.

## Cambios

- La visita de valoracion muestra solo bloques propios de visita fisica:
  exterior del edificio, reforma observada, portal/contadores, datos esenciales
  y registro de estancias.
- Se ocultaron en valoracion: climatologia, ambito visible de visita, campos
  generales de valoracion, comparables legacy y acciones de patologias.
- Se reutiliza `visita_fotos` con categoria `portal_contadores` para fotografias
  de portal y cuadro de contadores.
- No se creo esquema para observaciones textuales de portal/contadores; queda en
  backlog.
- El guardado de visita ya no vacia `valoracion_visita` legacy cuando el
  formulario no envia campos `valoracion__*`.

## Validacion

- Smoke especifico: `tests/smoke/test_valoracion_nueva_visita_ux.py`.
- Validaciones finales delegadas al cierre del harness.

## Riesgos

- Las observaciones textuales especificas de portal/contadores no se persisten
  todavia sin cambio de esquema.
- `nueva_visita.html` sigue siendo un template compartido y conviene mantener
  smokes por tipo de informe.

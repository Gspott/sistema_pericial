# Valoracion Visita Portal Contadores DB

## Plan

`docs/harness/PLANS/active/valoracion-visita-portal-contadores-db.md`

## Resumen

Se persistieron las observaciones textuales del portal y del cuadro de
contadores dentro de `valoracion_visita_observaciones`, manteniendo las fotos en
`visita_fotos` con categoria `portal_contadores`.

## Cambios

- Columnas defensivas:
  - `observaciones_portal`
  - `observaciones_cuadro_contadores`
- `nueva_visita.html` muestra y guarda ambos campos en el bloque Portal y
  contadores.
- El formulario especifico `/visitas/{visita_id}/valoracion-observaciones`
  tambien carga y guarda ambos campos.
- `build_informe_context()` expone los valores en el grupo de estado de la
  valoracion, degradando a vacio si faltan columnas o datos.
- No se modifica `valoracion_visita` legacy.

## Validacion

- DB temporal crea columnas.
- POST server-side guarda observaciones.
- Fotos `portal_contadores` siguen funcionando mediante ruta existente.
- Contexto de informe expone observaciones.
- Smokes completos pasan antes del cierre.

## Fuera De Alcance

No se tocaron DB real, uploads reales, informes reales, calculo, PDF/DOCX ni
routers legacy.

# Valoracion Build Context

# Estado

Completado retrospectivo.

# Objetivo

Registrar la fase autonoma previa que preparo la fuente unica de datos moderna
para valoracion inmobiliaria en `build_informe_context()`, sin modificar
todavia HTML/PDF ni DOCX editable moderno.

# Modulo

Informes/contexto/harness.

# Alcance ejecutado

- `build_informe_context()` expuso claves compatibles:
  `tipo_informe`, `es_valoracion`, `valoracion` y
  `comparables_valoracion`.
- `valoracion` agrupo datos existentes de `valoracion_visita` por visita en
  secciones estables con titulo, campos y `hay_datos`.
- `comparables_valoracion` cargo registros vinculados a visitas del expediente
  con columnas legibles.
- Se cubrio degradacion controlada para expedientes de valoracion sin visita,
  sin `valoracion_visita`, sin comparables y para expedientes no valoracion.
- Smoke tests actualizados para comprobar compatibilidad y estructura de
  contexto.
- Pattern de contexto por tipo de informe actualizado en harness.

# Validaciones registradas

- `python3 scripts/audit_docs.py`: OK.
- `bash scripts/validate_harness.sh`: OK.
- `python3 -m compileall app`: OK.
- `git diff --check`: OK.

# Riesgos y limites

- Queda pendiente adaptar renderizado HTML/PDF moderno y DOCX editable moderno.
- Queda pendiente definir calculo, homogeneizacion y checklist de completitud.
- El plan no se creo antes de tocar archivos; este archivo repara la traza
  historica, pero no sustituye la obligacion futura de plan activo previo.

# No tocado

No se tocaron DB real, datos reales, secretos, uploads, fotos, informes
generados, backups, routers legacy ni carpeta anidada `sistema_pericial/`.

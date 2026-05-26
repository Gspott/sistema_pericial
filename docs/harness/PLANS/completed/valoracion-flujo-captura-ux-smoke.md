# Valoracion Flujo Captura UX Smoke

# Estado

Completado retrospectivo.

# Objetivo

Registrar la fase autonoma previa de mejora inicial del flujo de valoracion
inmobiliaria, centrada en captura de datos, UX minima y smoke tests, sin tocar
PDF/DOCX moderno ni calculo estructurado.

# Modulo

Informes/visitas/harness.

# Alcance ejecutado

- Backlog y harness actualizados para "Modernizar flujo de valoracion
  inmobiliaria".
- Mapa breve del flujo:
  expediente valoracion -> visita -> datos valoracion -> comparables -> informe.
- Smoke sandbox de valoracion con DB temporal.
- Registro/resumen de visita ajustado para ocultar referencias de patologias
  cuando `tipo_informe='valoracion'` y no aplican.
- Ayudas rapidas para campos frecuentes de valoracion sin JavaScript
  obligatorio y manteniendo edicion manual.
- Pendientes documentados fuera de alcance: mover campos estables a expediente,
  adaptar contexto/informes modernos, DOCX editable, calculo/homogeneizacion y
  checklist de completitud.

# Validaciones registradas

- `python3 scripts/audit_docs.py`: OK.
- `bash scripts/validate_harness.sh`: OK.
- `python3 -m compileall app`: OK.
- `git diff --check`: OK.

# Riesgos y limites

- El informe HTML/PDF moderno y el DOCX editable moderno seguian pendientes.
- No se hizo cambio de esquema ni migracion.
- No se implemento calculo ni homogeneizacion.
- El plan no se creo antes de tocar archivos; este archivo repara la traza
  historica, pero no sustituye la obligacion futura de plan activo previo.

# No tocado

No se tocaron DB real, datos reales, secretos, uploads, fotos, informes
generados, backups, routers legacy ni carpeta anidada `sistema_pericial/`.

# Valoracion Flow Audit

Fecha: 2026-05-25

## Resumen

Auditoria inicial del flujo de valoracion inmobiliaria antes de cambios
funcionales amplios.

## Hallazgos

- `tipo_informe='valoracion'` existe en expediente, detalle y visita.
- La captura principal vive en `templates/nueva_visita.html`.
- Los datos se guardan en `valoracion_visita` y los testigos en
  `comparables_valoracion`.
- El DOCX antiguo tiene generacion especifica de valoracion.
- HTML/PDF moderno y DOCX editable moderno siguen orientados a patologias y
  no deben tocarse sin fase especifica.
- Muchos campos de valoracion parecen estables del expediente, pero moverlos
  requiere plan de datos y migracion.

## Decisiones Operativas

- Empezar por smoke sandbox, limpieza UX y ayudas manuales sin cambiar modelo.
- Mantener formularios server-side y compatibilidad mobile-first.
- No activar routers legacy.
- No usar DB real, datos reales, uploads, fotos ni informes generados reales.

## Siguiente Accion Segura

Crear smoke flow de valoracion con DB temporal: expediente, visita,
`valoracion_visita`, comparable y `build_informe_context()` degradando sin
patologias.

## Pendientes Fuera De Alcance

- Mover campos estables a expediente.
- Adaptar HTML/PDF moderno.
- Adaptar DOCX editable moderno.
- Crear calculo u homogeneizacion de comparables.
- Definir checklist de completitud especifico de valoracion.

## Avance Posterior

2026-05-25: `build_informe_context()` expone `tipo_informe`,
`es_valoracion`, `valoracion` y `comparables_valoracion` para preparar la
adaptacion futura de HTML/PDF y DOCX editable sin tocar esos outputs.

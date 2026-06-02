# BIB-TEST-2 Alta Rapida Desktop De Testigos

Fecha: 2026-06-02

## Objetivo

Crear una experiencia SSR de escritorio para dar de alta testigos en la
biblioteca maestra desde portales inmobiliarios, sin sustituir el formulario
mobile-first existente.

## Cambios

- Nueva ruta `GET /valoracion/testigos/biblioteca/nuevo`.
- Nueva ruta `POST /valoracion/testigos/biblioteca/nuevo`.
- Nuevo template `templates/valoracion_testigo_biblioteca_form.html` con
  secciones compactas: fuente, identificacion/localizacion, datos economicos,
  superficies, calidad/verificacion y observaciones.
- Presets de fuente: Idealista, Fotocasa, Habitaclia, Pisos.com, Yaencontre y
  Otro.
- Acciones: guardar, guardar y crear otro, guardar y volver a biblioteca,
  cancelar.
- Si llega `expediente_id`, se conserva como retorno contextual, pero no se
  vincula automaticamente el testigo al expediente.
- Validacion SSR de numericos, superficie mayor que cero y URL http/https.

## Decisiones

- `referencia_testigo` actua como titulo/referencia del anuncio para evitar
  crear columna nueva.
- El €/m2 inicial se calcula con el servicio existente y se persiste como dato
  derivado del testigo, igual que en el alta normal.
- No se guarda peso, inclusion/exclusion ni representatividad global.

## Fuera de alcance

- Scraping, OCR, IA, extraccion automatica desde URL, deduplicacion automatica,
  importacion masiva, mapas, edicion inline y vinculacion automatica a
  expedientes.

## Riesgos

- La validacion de URL es deliberadamente basica; fases futuras de captura
  asistida podrian enriquecerla sin descargar contenido externo.

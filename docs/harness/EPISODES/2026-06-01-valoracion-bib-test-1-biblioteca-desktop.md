# BIB-TEST-1 Biblioteca Desktop De Testigos

Fecha: 2026-06-01

## Objetivo

Crear una vista SSR de escritorio para consultar la biblioteca maestra de
testigos/comparables reutilizables sin mezclarla con decisiones especificas de
expedientes.

## Cambios

- Nueva ruta `GET /valoracion/testigos/biblioteca`.
- Nuevo template `templates/valoracion_testigos_biblioteca.html` con tabla
  compacta desktop, diagnostico de calidad del dato, filtros SSR y ordenacion
  SSR.
- Filtros: municipio, tipologia, fuente, fiabilidad, verificacion e
  incompletos.
- Ordenacion: fecha, €/m2, precio, superficie y fiabilidad.
- Accesos secundarios desde la biblioteca mobile/cards y desde seleccion de
  testigos por expediente.
- Smokes para render, filtros, ordenacion valida, degradacion de orden invalido
  y estado vacio.

## Decisiones

- La biblioteca no guarda ni muestra peso, inclusion/exclusion ni
  representatividad global. Esos datos siguen viviendo en
  `valoracion_expediente_testigos` porque dependen de cada expediente.
- No se crean entidades nuevas ni se modifica esquema.

## Fuera de alcance

- Asignacion masiva a expedientes.
- Deduplicacion automatica.
- Mapas, IA, scoring avanzado, importacion masiva y edicion inline masiva.

## Riesgos

- La tabla desktop es deliberadamente ancha; en movil degrada con scroll
  horizontal y no reemplaza la vista mobile/cards.

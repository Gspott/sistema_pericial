# 2026-05-26 - Valoracion Menu Biblioteca Testigos

## Contexto

La biblioteca reusable de testigos ya existia en `/valoracion/testigos`, pero el
drawer izquierdo no tenia acceso global. El usuario pidio anadir el enlace justo
debajo de "Biblioteca de patologias".

## Cambios

- Anadido enlace "Biblioteca de testigos" en `templates/partials/_drawer_nav.html`.
- El enlace apunta a `/valoracion/testigos`.
- El estado activo usa el mismo patron del drawer con
  `path.startswith('/valoracion/testigos')`.
- Smoke ampliado para verificar que el enlace aparece despues de
  "Biblioteca de patologias".

## Fuera De Alcance

- No se tocaron formularios, DB, calculo, scraping/OCR ni rutas legacy.

# Valoracion Casos Demo

Fecha: 2026-05-26

## Objetivo

Crear casos ficticios completos de valoracion inmobiliaria para QA funcional de
UX, testigos reutilizables, ajustes, contexto de informe, HTML/PDF, DOCX,
completitud y calculo preparatorio.

## Casos

- Piso urbano estandar.
- Piso reformado premium.
- Caso incompleto problematico.
- Local comercial.
- Vivienda unifamiliar.

## Cambios

- Fixture reusable `tests/fixtures/valoracion_demo_cases.py`.
- Script sandbox `scripts/create_valoracion_demo_cases.py`.
- Smoke `tests/smoke/test_valoracion_demo_cases.py`.
- Patron `docs/harness/PATTERNS/valoracion_casos_demo.md`.

## Validaciones Cubiertas

- Cada caso crea expediente, valoracion de expediente, visita, observaciones, 6
  testigos, vinculos con snapshot y ajustes.
- Los casos completos crean resultado borrador en `valoracion_resultados`.
- El caso incompleto no crea resultado y mantiene advertencias de completitud.
- HTML moderno de valoracion se renderiza sin bloques de patologias.
- DOCX editable moderno empieza por `PK` y contiene secciones de valoracion.
- PDF se valida cuando Playwright/Chromium esta disponible en el entorno.

## Riesgos

- El calculo borrador usa media simple de unitarios ajustados y no debe
  confundirse con el futuro calculo profesional.
- No hay QA visual con screenshots en esta fase.
- Los datos son plausibles pero ficticios; no representan mercado real.

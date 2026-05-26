# 2026-05-26 - Valoracion Biblioteca Testigos

## Contexto

La valoracion inmobiliaria ya tenia base de `testigos_valoracion`, seleccion por
expediente, snapshot, ajustes manuales y fallback legacy desde
`comparables_valoracion`. La pantalla `/valoracion/testigos` era todavia un
listado basico y no funcionaba como biblioteca reusable.

## Cambios

- Se reforzo `/valoracion/testigos` como biblioteca server-side con busqueda
  simple por direccion, fuente, municipio, codigo postal, referencia, tipologia
  o estado de validacion.
- Se anadieron formatos profesionales para moneda, precio unitario, superficie
  y booleanos en la UI de testigos.
- Se creo detalle de testigo en `/valoracion/testigos/{testigo_id}` con datos
  completos, fuente/enlace, fotos manuales y expedientes donde se ha usado.
- Se habilito subida manual de fotos/capturas de testigo sobre
  `testigos_valoracion_fotos`, reutilizando uploads contextuales existentes.
- Se amplio el smoke de testigos para cubrir listado, formato, detalle,
  ownership y foto manual con DB/uploads temporales.

## Decisiones

- Las fotos pertenecen al testigo reusable, no al vinculo concreto con un
  expediente.
- La captura desde URL, OCR y scraping quedan fuera de esta fase. El flujo
  futuro sera: guardar URL, adjuntar captura/fotos, extraer datos de forma
  asistida y validar manualmente antes de usar el testigo.
- No se toca calculo, homogeneizacion automatica ni outputs PDF/DOCX.

## Riesgos

- La subida de fotos usa el mecanismo general de uploads; debe mantenerse bajo
  ownership del testigo y seguir validandose con smokes temporales.
- La biblioteca sigue sin soft delete especifico para testigos; no se implementa
  borrado en esta fase.

## Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_valoracion_testigos_reutilizables_form.py -q`
- Validaciones generales pendientes al cierre del plan.

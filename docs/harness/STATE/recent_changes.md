# Recent Changes

- Fase 2: smoke tests minimos para importacion y rutas basicas.
- Fase 3A: smoke tests de negocio seguros.
- Fase 3B: runner `scripts/validate_harness.sh`.
- Fase 3C: drift detection documental y estructural.
- Fase 4A: Task Packs operativos.
- Fase 4B: fuentes normativas, invariantes y specs de facturacion/gastos.
- Fase 4C: Golden Principles, mantenimiento y metricas.
- Fase 4D: memoria operativa persistente.
- Fix PWA drift: registro de service worker alineado con cache activa.
- Fix TemplateResponse: llamadas Jinja migradas a firma recomendada de Starlette.
- Smoke emails: cobertura mock sin SMTP real para servicio, adjunto y fallo simulado.
- Smoke gastos: cobertura sandbox para calculos, DB temporal, adjunto demo y deduplicado.
- Smoke flow propuesta-factura: cobertura de propuesta aceptada y factura borrador sin emision fiscal.
- Smoke flow expediente-informe: cobertura de expediente, visita, estancia y patologia sin generar PDF/DOCX.

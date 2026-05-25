# Build Informe Context Extension

## Cuando Usarlo

Cuando PDF, DOCX o plantilla de informe necesitan un dato nuevo o una correccion de composicion.

## Cuando NO Usarlo

- Cambios puramente visuales de CSS/print.
- Cambios que solo afectan una plantilla y duplican logica.
- Generacion PDF/DOCX real con datos sensibles.

## Estructura Recomendada

- Revisar `docs/informes.md`.
- Añadir o corregir datos en `build_informe_context()` o equivalente.
- Mantener una fuente compartida para PDF y DOCX.
- Degradar de forma controlada si faltan visita, fotos o patologias.

## Riesgos

- Divergencia PDF/DOCX.
- Plantillas con logica de negocio.
- Fallos por datos incompletos.

## Validaciones

- `pytest tests/smoke/test_informe_context.py -q`
- `pytest tests/smoke -q`
- `bash scripts/validate_harness.sh`

## Anti-Patrones

- Duplicar calculos en Jinja.
- Hacer que informe falle por datos secundarios ausentes.
- Mezclar refactor de rutas con cambios de contexto.

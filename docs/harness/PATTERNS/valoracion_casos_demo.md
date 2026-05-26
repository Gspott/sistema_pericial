# Valoracion Casos Demo

## Objetivo

Validar el flujo moderno de valoracion inmobiliaria con datos ficticios,
plausibles y reutilizables, sin tocar DB real ni archivos generados reales.

## Dataset

El dataset vive en `tests/fixtures/valoracion_demo_cases.py` y crea cinco casos:

- Piso urbano estandar: flujo completo residencial ordinario.
- Piso reformado premium: calidades superiores, reforma observada y ajustes por
  calidad.
- Caso incompleto problematico: acceso/documentacion incompleta y advertencias
  de completitud no bloqueantes.
- Local comercial: tipologia no residencial, ocupacion arrendada y mercado
  comercial.
- Vivienda unifamiliar: parcela, mayor superficie y mayor dispersion de
  comparables.

Cada caso contiene:

- `expedientes`.
- `valoracion_expediente`.
- `visitas`.
- `valoracion_visita_observaciones`.
- 6 `testigos_valoracion`.
- 6 vinculos en `valoracion_expediente_testigos` con snapshot.
- Ajustes en `valoracion_testigo_ajustes`.
- Resultado borrador en `valoracion_resultados` salvo el caso incompleto.

## Regeneracion Sandbox

Usar una ruta temporal fuera de `data/`, `uploads/`, `informes/`, `fotos/`,
`backups/` y la carpeta anidada `sistema_pericial/`:

```bash
python3 scripts/create_valoracion_demo_cases.py --db /tmp/valoracion_demo.db
```

Si la DB sandbox ya existe y se quiere anadir otra tanda:

```bash
python3 scripts/create_valoracion_demo_cases.py --db /tmp/valoracion_demo.db --append
```

El script rechaza rutas sensibles del proyecto y no lee `.env` real en los
smokes, porque el entorno de test lo sustituye por variables temporales.

## Validaciones

- Smoke de contexto: `build_informe_context()` devuelve valoracion, comparables
  y ajustes del modelo nuevo.
- Smoke HTML: `/informes/{id}/imprimir` renderiza valoracion y no patologias.
- Smoke PDF: `/generar-informe-pdf/{id}` devuelve `%PDF` cuando
  Playwright/Chromium esta disponible; se omite si el runtime no tiene navegador.
- Smoke DOCX: `generar_informe_docx_editable_bytes()` devuelve `PK` y secciones
  de valoracion.
- Smoke completitud: el caso incompleto mantiene advertencias no bloqueantes.

## Limitaciones

- Los datos son ficticios y no deben usarse como referencia de mercado real.
- El calculo de resultado es un borrador demo basado en media simple de
  unitarios ajustados; no sustituye el futuro motor de comparacion.
- No hay fotos reales ni uploads.
- No se valida maquetacion visual con captura de navegador en esta fase.

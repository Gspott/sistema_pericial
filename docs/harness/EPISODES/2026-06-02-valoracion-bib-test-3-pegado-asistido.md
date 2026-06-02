# BIB-TEST-3 Pegado Asistido Desktop

Fecha: 2026-06-02

## Objetivo

Anadir una ayuda SSR al alta rapida desktop para pegar texto bruto de anuncios
inmobiliarios y proponer campos sin guardar automaticamente.

## Cambios

- Se anadio `texto_anuncio_bruto` como campo temporal del formulario rapido.
- Se incorporo boton SSR `Analizar texto pegado`.
- El analisis es local y heuristico:
  - precio de oferta;
  - superficie tomada y tipo de superficie;
  - €/m2 si aparece;
  - portal/fuente si aparece Idealista, Fotocasa, Habitaclia, Pisos.com o
    Yaencontre;
  - habitaciones/banos como observacion;
  - titulo/referencia desde primera linea plausible.
- La previsualizacion muestra campos detectados, confianza y advertencias.
- Los valores detectados solo se aplican a campos vacios y quedan editables.

## Limites

- No hay scraping, OCR, IA externa ni conexion a URLs.
- No se verifica la veracidad de los datos.
- No se guarda nada al pulsar `Analizar texto pegado`.
- El guardado final sigue siendo manual con las acciones existentes.

## Riesgos

- Las heuristicas pueden fallar con formatos de anuncio ambiguos. Es una ayuda
  de captura, no una fuente de verdad.

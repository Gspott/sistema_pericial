# UX-VAL-9 Fotos De Testigos En Workbench

Fecha: 2026-06-02

## Objetivo

Mostrar fotos o capturas manuales de testigos vinculados en el Workbench de
Valoracion para apoyar comparacion visual de estado, reforma y calidades.

## Cambios

- La ruta SSR del workbench carga metadatos de `testigos_valoracion_fotos` para
  los `testigo_id` presentes en el contexto del expediente.
- La carga filtra por `testigos_valoracion.owner_user_id` del usuario actual
  para evitar mostrar evidencias de testigos ajenos.
- La tabla del workbench muestra un indicador compacto de numero de fotos.
- El panel contextual incorpora "Evidencia visual" con miniaturas, descripcion,
  origen, fecha y enlace "Ver foto".
- Si no hay fotos, el panel muestra un estado vacio discreto.

## Riesgos

- La galeria usa rutas `/uploads/...` ya existentes; no valida existencia fisica
  del archivo en render SSR.
- Las fotos son evidencia auxiliar y no sustituyen inspeccion ni verificacion
  tecnica.
- No se insertan fotos en informes en esta fase.

## Validacion

- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_valoracion_workbench.py -q`
- Validaciones completas del harness al cierre.

## Fuera De Alcance

- Subida de fotos desde workbench.
- Descarga automatica desde URLs externas.
- Scraping, OCR o IA.
- Cambios de calculo, ponderacion o valor final.
- Cambios en informes HTML/PDF/DOCX.

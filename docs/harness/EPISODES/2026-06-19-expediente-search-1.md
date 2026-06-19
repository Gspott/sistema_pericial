# EXPEDIENTE-SEARCH-1

Fecha: 2026-06-19

## Objetivo

Añadir un buscador global de solo lectura dentro del expediente activo para localizar texto persistido en los módulos principales.

## Diagnóstico

El detalle del expediente no tenía una búsqueda transversal. La información relevante estaba distribuida entre Informe V2, datos del expediente, visitas, estancias, patologías, fotos, documentación aportada, valoración y actuaciones/costes. Para el volumen previsto no se justifica introducir FTS, caché persistente ni dependencias externas.

## Cambios

- Se añadió búsqueda GET en `/detalle-expediente/{expediente_id}?q=...`.
- Se incorporó una sección plegable "Buscar en expediente" con resultados agrupados.
- Cada resultado muestra tipo, título, campo, contexto con coincidencia resaltada y enlace de apertura.
- La búsqueda es de solo lectura y salta tablas/columnas ausentes para mantener compatibilidad.
- Se añadió ancla `#documentacion-aportada` en el workbench pericial.
- Se añadieron smoke tests específicos de búsqueda global.

## Tablas y Campos Incluidos

- `informe_v2_capitulos`: título, contenido y estado.
- `informe_v2_metadatos`: título y subtítulo de portada.
- `expedientes`: datos identificativos, observaciones, notas jurídicas/periciales y campos textuales de patologías.
- `visitas`: fecha, técnico, observaciones y ámbito.
- `estancias`: nombre, tipo, planta, ventilación, acabados y observaciones.
- `registros_patologias` y `registros_patologias_exteriores`: elementos, patologías, observaciones y localizaciones.
- `visita_fotos`, `informe_v2_laminas_fotograficas` e `informe_v2_lamina_fotos`: descripciones, pies, subtítulos y observaciones.
- `expediente_documentos`: nombre visible, descripción, tipo documental, nombre/ruta de archivo y MIME.
- `valoracion_expediente`, `valoracion_visita` y `valoracion_visita_observaciones`: campos textuales persistidos de valoración.
- `actuaciones_reparacion` y `actuacion_partidas`: títulos, descripciones, observaciones y snapshots.

## Validaciones

- `python3 scripts/audit_docs.py` OK, con avisos históricos existentes sobre planes antiguos y monolito `app/main.py`.
- `python3 -m compileall app` OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "expediente_search"` OK, 2 passed.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "expediente_search or informe_v2"` OK, 35 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` OK, scope app, smoke omitido por el harness.
- `git diff --check` OK.

## Cierre

Plan movido a `docs/harness/PLANS/completed/expediente-search-1.md` mediante `finish_harness_task`.

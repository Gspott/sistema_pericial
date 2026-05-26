# High Backlog

Usar esta prioridad para problemas que no son emergencia inmediata, pero condicionan cambios seguros en modulos criticos.

## Monolito app/main.py

- Impacto: eleva riesgo de cambios cruzados y dificulta mantenimiento.
- Modulos: backend, expedientes, visitas, informes, auth.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: `python3 -m compileall app`, `pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea cambios quirurgicos; bloquea refactors grandes sin plan.
- Dependencias: ampliar smoke tests antes de extracciones por flujo.

## Decidir Destino De Carpeta Anidada `sistema_pericial/`

- Impacto: reduce riesgo de tocar copia equivocada, datos sensibles o entorno local anidado.
- Modulos: seguridad, workspace, datos locales.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/bugfix.md` con aprobacion humana.
- Validaciones minimas: auditoria solo lectura; no leer DB ni datos generados; `git status --short`.
- Bloqueo/no bloqueo: Bloquea limpiezas o reorganizaciones del workspace.
- Dependencias: decision humana sobre conservar, mover, archivar o eliminar tras backup verificado.

## Mapa `app/main.py` Vs Routers No Incluidos

- Impacto: evita borrar codigo que podria ser extraccion parcial y prepara refactor gradual seguro.
- Modulos: expedientes, visitas, estancias, patologias, informes.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: mapa de rutas, `python3 -m compileall app`, `pytest tests/smoke -q`.
- Bloqueo/no bloqueo: No bloquea cambios quirurgicos; bloquea limpieza de routers no incluidos.
- Dependencias: smoke tests por flujo y aprobacion antes de incluir o eliminar rutas.

## Crear Mapa Ruta A Ruta `app/main.py` Vs Routers Legacy

- Impacto: permite decidir que rutas pueden extraerse y cuales son obsoletas.
- Modulos: expedientes, visitas, estancias, patologias.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: auditoria solo lectura, `python3 scripts/audit_docs.py`.
- Bloqueo/no bloqueo: Bloquea cualquier `include_router()` de routers legacy.
- Dependencias: `docs/harness/AGENT_MAPS/main_vs_routers_map.md`.

## Smoke Ownership Expedientes/Visitas Antes De Extraccion

- Impacto: evita regresiones de seguridad al mover rutas desde `app/main.py`.
- Modulos: expedientes, visitas, auth, DB.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/bugfix.md`.
- Validaciones minimas: `python3 -m pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: Bloquea extraccion de rutas con `owner_user_id`.
- Dependencias: fixtures temporales y usuarios demo, sin DB real.

## Modernizar Flujo De Valoracion Inmobiliaria

- Impacto: mejora captura, UX movil y cobertura segura del tipo `valoracion` antes de adaptar outputs modernos.
- Modulos: expedientes, visitas, valoracion, comparables, informes, UX.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/informe_change.md` para contexto/output y `docs/harness/TASK_PACKS/bugfix.md` para UX/smoke.
- Validaciones minimas: `python3 scripts/audit_docs.py`, `pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea mejoras pequenas de captura; bloquea PDF/DOCX moderno, calculo estructurado y migraciones sin plan especifico.
- Dependencias: smoke flow de valoracion con DB temporal; no usar DB real, uploads, fotos ni informes generados reales.
- Pendientes:
  - Separar quick wins de captura/UX de la adaptacion de `build_informe_context()`.
  - Documentar campos estables candidatos a expediente antes de cualquier migracion.
  - Mantener DOCX antiguo como respaldo mientras HTML/PDF y DOCX editable no tengan valoracion moderna.
  - Evaluar mover campos estables de valoracion a expediente: solicitante, finalidad, identificacion del bien, superficies, situacion legal y documentacion base.
  - Adaptar `build_informe_context()` para exponer valoracion y comparables como fuente compartida de outputs modernos. Avance 2026-05-25: completado.
  - Adaptar `templates/informes/imprimir.html` para que el HTML/PDF moderno no renderice secciones de patologias en valoracion. Avance 2026-05-25: completado con smoke HTML.
  - Adaptar DOCX editable moderno para que use secciones especificas de valoracion desde el mismo contexto. Avance 2026-05-25: completado con smoke DOCX.
  - Planificar calculo/homogeneizacion de comparables antes de introducir importes numericos o campos derivados.
  - Crear checklist de completitud de valoracion: documentacion, superficies, situacion legal, entorno, metodo, comparables, resultado y limitaciones. Avance 2026-05-25: completado como advertencias no bloqueantes.
  - Decidir si los comparables necesitan fotos, fuente estructurada o trazabilidad documental adicional.
  - Implementar fase DB defensiva propuesta en `docs/harness/GOALS/valoracion_modelo_comparacion.md`: `valoracion_expediente`, observaciones de visita, testigos reutilizables, vinculos expediente-testigo, ajustes y resultados, solo con DB temporal. Avance 2026-05-25: completado con smoke temporal; incluye `testigos_valoracion_fotos` solo como metadatos, sin archivos reales.
  - Mantener `valoracion_visita` y `comparables_valoracion` como legacy/fallback hasta migracion sandbox aprobada.
  - Crear helpers de lectura del modelo nuevo y fallback legacy antes de exponer formularios. Avance 2026-05-25: completado en `build_informe_context()` con precedencia de modelo nuevo y smokes.
  - Crear formularios de datos estables de expediente usando los helpers, sin migracion automatica. Avance 2026-05-25: formulario minimo server-side completado para `valoracion_expediente`.
  - Crear formulario de observaciones de visita en `valoracion_visita_observaciones`, manteniendo `nueva_visita.html` legacy sin eliminar campos. Avance 2026-05-25: completado con GET/POST server-side y smoke de no modificacion legacy.
  - Crear formulario minimo de testigos reutilizables y seleccion por expediente, sin homogeneizacion automatica. Avance 2026-05-26: completado con snapshot por vinculo, ownership y smoke temporal.
  - Crear formulario de ajustes/homogeneizacion manual por testigo vinculado, sin calculo final automatico. Avance 2026-05-26: completado con validacion -20%/+20%, coeficiente total y valor unitario ajustado.
  - Crear casos demo ficticios de QA funcional para valoracion. Avance 2026-05-26: completado con cinco casos sandbox, script de regeneracion, smoke de contexto, HTML, DOCX y PDF si el runtime lo permite.
  - Limpiar `nueva_visita.html` para valoracion, dejando solo bloques de visita fisica y sacando campos generales ya movidos a expediente/testigos/ajustes. Avance 2026-05-26: completado con smoke de render y proteccion para no vaciar legacy oculto.
  - Persistir observaciones textuales especificas de portal y cuadro de contadores en modelo nuevo de visita. Avance 2026-05-26: completado con columnas defensivas `observaciones_portal` y `observaciones_cuadro_contadores`; las fotos siguen en `visita_fotos` con categoria `portal_contadores`.
  - Evolucionar `/valoracion/testigos` como biblioteca reutilizable con busqueda, cards profesionales, detalle, fuente/enlace, fotos manuales y formatos con unidades. Avance 2026-05-26: completado sin scraping/OCR ni descarga remota de imagenes.
  - Anadir acceso global "Biblioteca de testigos" en drawer izquierdo bajo "Biblioteca de patologias". Avance 2026-05-26: completado con smoke de orden del enlace.
  - QA visual de valoracion sobre casos demo: biblioteca, detalle, seleccion por expediente, informe HTML/PDF, mobile y comparables. Avance 2026-05-26: completado en sandbox; hallazgos en `docs/harness/EPISODES/2026-05-26-valoracion-qa-visual.md`.
  - Quick win detectado por QA: aplicar formato profesional a comparables del informe y testigos vinculados, evitando valores crudos como `200655.0`, `2388.75`, `84.0` o `1.0`.
  - Quick win detectado por QA: anadir filtros/busqueda contextual a seleccion de testigos por expediente; el select unico no escalara con biblioteca creciente.
  - Quick win detectado por QA: compactar comparables del informe en tabla/resumen de mercado responsive y ocultar campos vacios como `Testigos comparables: -`.
  - Aplicar quick wins de QA visual sin cambiar modelo ni calculo: formatos con unidades, ocultacion de campos vacios, filtros server-side, accion destructiva diferenciada y miniaturas de testigo cuando exista foto. Avance 2026-05-26: completado con smoke y QA visual sandbox.
  - Pendiente estructural tras quick wins: compactar comparables del informe como tabla/resumen de mercado responsive; no abordado para evitar rediseño mayor.
  - Disenar captura asistida futura de testigos desde URL/captura: pegar enlace, adjuntar capturas, OCR/manual asistido y extraccion semiautomatica, siempre con validacion humana y sin scraping en fases generales.
  - Siguiente paso recomendado: QA visual con Playwright/screenshots de las pantallas de valoracion y del informe imprimible usando los casos demo.

## Harness Smoke Scopes

- Impacto: reduce coste de cierre en fases pequenas sin cambiar el default
  conservador.
- Modulos: harness, validation runner, task packs.
- Riesgo: Medio.
- Avance 2026-05-26: `validate_harness.sh` y `finish_harness_task.sh` aceptan
  `--smoke-scope docs|app|valoracion|full`; `full` sigue siendo default.
- Invariantes: `audit_docs` y `git diff --check` son obligatorios en todos los
  scopes; los skips se declaran como `[SKIP]`.
- Avance 2026-05-26: smart dependency scopes implementados con resolver por
  paths, auto-upgrade de scopes insuficientes y override explicito
  `--allow-unsafe-scope`.

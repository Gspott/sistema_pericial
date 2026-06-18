# Episode: Pericial Pdf Generation Hang Hotfix 1

## Fecha

2026-06-18

## Tarea

PERICIAL-PDF-GENERATION-HANG-HOTFIX-1

## Plan asociado

pericial-pdf-generation-hang-hotfix-1.md

## Task Pack usado

`informe_change`

## Objetivo

Diagnosticar y proteger la generación PDF V2 con anexos frente a bloqueos
percibidos en expedientes reales grandes, sin modificar contenido técnico ni
PDFs originales.

## Archivos modificados

- `app/main.py`
- `app/services/pdf_annex_optimizer.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-generation-hang-hotfix-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-generation-hang-hotfix-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 59 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 248 passed.

## Resultado

Se añadio instrumentacion controlada al endpoint
`/generar-informe-v2-pdf/{expediente_id}`:

- `debug_pdf_pipeline=1` devuelve JSON de diagnostico y no renderiza PDF.
- `debug_pdf_pipeline=log` genera el PDF normal y emite pasos por logger.
- `debug_sin_paginacion=1` omite la segunda pasada de paginacion para aislar
  bloqueos en esa fase.

El diagnostico incluye perfil, anexos detectados, pesos de Anexo A/F, paginas
estimadas, disponibilidad de Ghostscript y pasos previstos.

La generacion normal conserva el flujo historico, pero para PDFs grandes usa
`FileResponse` con archivo temporal en lugar de `StreamingResponse` en memoria.
El temporal se elimina con `BackgroundTask` al completar la respuesta.

La sesion de optimizacion de anexos registra duracion cuando adopta una copia
optimizada. Los perfiles `email` y `judicial` mantienen timeout defensivo de
Ghostscript y fallback al PDF original si falla, tarda demasiado o no reduce.

## Diagnostico

El punto con mayor probabilidad de bloqueo queda acotado a las fases posteriores
al render principal: fusion de PDFs externos, optimizacion opcional de anexos,
paginacion final o entrega de bytes grandes al cliente.

En el expediente real `019-26` se habia validado previamente un PDF final de 247
paginas y 45.591.599 bytes. Ese tamaño esta dominado por anexos PDF externos;
la optimizacion de imagenes del cuerpo no explica el peso restante.

No se reproduce un bucle infinito en smoke tests. El hotfix añade herramientas
para aislar la fase exacta en ejecucion real y reduce el riesgo de bloqueo en la
entrega final usando respuesta desde fichero temporal para PDFs grandes.

## Tests añadidos

- Diagnostico `debug_pdf_pipeline=1` devuelve JSON y no PDF.
- `debug_sin_paginacion=1` evita llamar a `paginar_pdf_final_bytes`.
- `master` con anexo PDF pequeño responde y queda paginado.
- `email` con Ghostscript simulado lento hace timeout/fallback y responde.

## Warnings

El cierre harness escalo el scope a `full` porque el arbol contiene cambios
previos en rutas criticas no pertenecientes a esta tarea. No se revirtieron esos
cambios.

`audit_docs.py` mantiene warnings preexistentes sobre planes completados vacios
y tamano del monolito `app/main.py`.

## Rollback

Revertir los cambios del endpoint PDF V2, la duracion añadida al optimizador de
anexos y los smoke tests nuevos. No hay migraciones ni datos persistentes
nuevos.

## Memoria actualizada

Plan cerrado en
`docs/harness/PLANS/completed/pericial-pdf-generation-hang-hotfix-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas. No se instalan dependencias ni se cambia contenido de informe.

## Proximos pasos

Ejecutar en entorno real `019-26` con `debug_pdf_pipeline=log` y, si vuelve a
colgar, comparar con `debug_sin_paginacion=1` para separar paginacion final de
fusion/entrega.

## Ampliacion: paginacion final visible

Fecha: 2026-06-18.

Se amplio el hotfix para cubrir que la numeracion `Página X de Y` no aparecia
en el PDF completo con anexos.

### Diagnostico adicional

La llamada a paginacion estaba bien situada: despues del render principal y de
la fusion de anexos externos. Tambien se confirmo que el endpoint reasigna
`pdf_bytes` con el resultado paginado antes de responder, por lo que no se
detecta devolucion del buffer anterior.

La causa mas probable quedaba en la implementacion manual del overlay: usaba
`mediabox` y no normalizaba `/Rotate`. En PDFs externos rotados, escaneados o
con `cropbox` distinto, el texto podia quedar en una posicion no visible o con
orientacion no esperada. Ademas, los fallos de paginacion se silenciaban al
devolver el PDF original sin warning.

### Cambios adicionales

- `app/services/pdf_pagination.py` normaliza rotacion con
  `transfer_rotation_to_content()` antes de escribir la numeracion.
- La posicion del pie usa `cropbox` como area visible.
- `paginar_pdf_final_bytes()` acepta `debug=True`, registra paginas/tamanos y
  duracion, y emite warning si falla.
- El endpoint PDF V2 pasa `debug=True` a la paginacion cuando se usa
  `debug_pdf_pipeline=log`.
- Tests reforzados para todos los perfiles, pagina rotada, respuesta con
  `FileResponse`, bytes paginados y fallback con warning.

### Validaciones adicionales

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 63 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: smoke full OK,
  252 passed; fallo solo el paso de cierre automatico porque el plan completed
  ya existia, por lo que esta ampliacion queda consolidada manualmente.

### Validacion 019-26

No ejecutada en esta ampliacion porque no hay autorizacion explicita para leer
DB/uploads reales. La comprobacion recomendada es generar `019-26` con
`debug_pdf_pipeline=log` y verificar pagina 1, Anexo A, Anexo F y ultima pagina;
si hay bloqueo, repetir con `debug_sin_paginacion=1`.

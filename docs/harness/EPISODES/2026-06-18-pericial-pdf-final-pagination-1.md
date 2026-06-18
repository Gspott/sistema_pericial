# Episode: Pericial Pdf Final Pagination 1

## Fecha

2026-06-18

## Tarea

PERICIAL-PDF-FINAL-PAGINATION-1

## Plan asociado

pericial-pdf-final-pagination-1.md

## Task Pack usado

`informe_change`

## Objetivo

Añadir paginacion global y continua al PDF final del Informe V2, aplicada como
ultima pasada despues de fusionar anexos externos.

## Archivos modificados

- `app/main.py`
- `app/services/pdf_pagination.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-final-pagination-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-final-pagination-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 51 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 240 passed.

## Resultado

Se anadio `app/services/pdf_pagination.py` con configuracion extensible
`PDF_PAGINATION_CONFIG` y paginacion `Página X de Y`.

La segunda pasada se aplica en el endpoint PDF V2 despues de
`fusionar_pdf_informe_v2_con_anexos_integrados()` y antes de devolver el
`StreamingResponse`. Esto cubre cuerpo, portadillas, Anexo A, Anexo F y PDFs
externos ya fusionados.

La implementacion usa `pypdf` puro para evitar dependencias nuevas: toma ancho y
alto desde `page.mediabox`, añade un stream de texto por pagina y escribe un PDF
nuevo en memoria. Si el PDF no puede leerse, devuelve los bytes originales para
no romper la exportacion.

## Validacion manual 019-26

Se genero el expediente real `019-26` (`id=27`) con `master`, `email` y
`judicial` mediante `TestClient`, guardando copias temporales en `/tmp`.

Resultado:

- `master`: 247 paginas, 45.591.599 bytes.
- `email`: 247 paginas, 45.591.599 bytes.
- `judicial`: 247 paginas, 45.591.599 bytes.

Puntos verificados en los tres perfiles:

- Pagina 1 de 247: OK.
- Anexo A, pagina 13 de 247: OK.
- Pagina intermedia 124 de 247: OK.
- Anexo F, pagina 242 de 247: OK.
- Pagina final 247 de 247: OK.

El mismo peso en los tres perfiles confirma que el caso queda dominado por PDFs
externos/anexos que el fallback actual no reduce.

## Warnings

`reportlab` no esta instalado en el entorno, por lo que se descarto la estrategia
de overlay con ReportLab. La validacion manual con expediente real 019-26 no se
realizo con inspeccion visual humana de visor PDF, sino con generacion real e
inspeccion de texto extraido en puntos representativos.

`audit_docs.py` mantiene warnings preexistentes sobre planes completados vacios
y tamano del monolito `app/main.py`.

## Rollback

Revertir el servicio nuevo, la llamada final desde el endpoint y los tests de
paginacion. No hay migraciones ni datos persistentes nuevos.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/pericial-pdf-final-pagination-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas para la implementacion. La validacion manual con 019-26 queda
pendiente de ejecucion supervisada.

## Proximos pasos

Validar manualmente `master`, `email` y `judicial` en el expediente 019-26 y, en
una fase posterior, recalcular paginas del indice final si se necesita una tabla
de contenidos completamente dinamica.

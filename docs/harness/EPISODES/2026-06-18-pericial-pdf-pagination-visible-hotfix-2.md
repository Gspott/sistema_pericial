# Episode: Pericial Pdf Pagination Visible Hotfix 2

## Fecha

2026-06-18

## Tarea

PERICIAL-PDF-PAGINATION-VISIBLE-HOTFIX-2

## Plan asociado

pericial-pdf-pagination-visible-hotfix-2.md

## Task Pack usado

`informe_change`

## Objetivo

Garantizar que la numeracion `Página X de Y` sea visible en el PDF final V2,
incluyendo paginas del cuerpo, anexos externos escaneados, paginas horizontales
y paginas rotadas.

## Archivos modificados

- `app/services/pdf_pagination.py`
- `app/main.py`
- `requirements.txt`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-pagination-visible-hotfix-2.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-pagination-visible-hotfix-2.md`

## Diagnostico

La implementacion previa insertaba manualmente un stream de texto con pypdf. Ese
texto podia ser extraible, pero no garantizaba una capa visual robusta encima de
contenido escaneado, fondos oscuros, paginas rotadas o PDFs externos con
recursos complejos. Sin una caja de contraste, el texto podia quedar visualmente
perdido aunque estuviera presente en el contenido.

## Resultado

Se reemplazo la paginacion manual por overlays PDF generados con ReportLab:

- Caja blanca pequeña en el pie de pagina.
- Texto negro centrado `Página X de Y`.
- Tamaño real de pagina, con normalizacion previa de rotacion.
- Fusion con pypdf usando `merge_page(..., over=True)` despues de anadir la
  pagina al writer, para evitar warnings y escribir encima del contenido.

En modo `debug_pdf_pipeline=log`, la paginacion guarda temporalmente:

- `final_antes_paginacion.pdf`
- `final_despues_paginacion.pdf`
- `overlay_test_page_1.pdf`

Tambien registra paginas, tamaño antes/despues, duracion y carpeta debug.

## Tests añadidos/reforzados

- PDF simple con texto extraible.
- PDF multipagina con ultima pagina numerada.
- PDF de fondo oscuro con overlay visible y caja blanca.
- PDF horizontal y de tamaños distintos.
- PDF rotado, normalizado y numerado.
- Endpoint con `FileResponse` conserva bytes paginados.
- Endpoint con anexos sinteticos contiene numeracion en la ultima pagina.
- Fallback con warning si falla el overlay.

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 65 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 254 passed.

## Validacion visual

Se cubre con PDF sintetico de fondo oscuro generado por ReportLab: el overlay
fusionado contiene rectangulo blanco y texto negro, y el texto `Página 1 de 1`
es extraible. No hay Poppler instalado en este entorno, por lo que no se renderizo
PNG con `pdftoppm`.

## Validacion 019-26

No ejecutada porque no hay autorizacion explicita para leer/generar con DB y
uploads reales. El endpoint queda preparado para diagnostico con
`debug_pdf_pipeline=log`.

## Rollback

Revertir `app/services/pdf_pagination.py`, la llamada `debug_dir` desde
`app/main.py`, la dependencia `reportlab` y los smoke tests asociados. No hay
migraciones ni cambios en datos.

## Decisiones humanas

No requeridas para la implementacion. Validar `019-26` requiere autorizacion
explicita sobre datos reales.

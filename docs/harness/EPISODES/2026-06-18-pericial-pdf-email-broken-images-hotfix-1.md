# Episode: Pericial Pdf Email Broken Images Hotfix 1

## Fecha

2026-06-18

## Tarea

PERICIAL-PDF-EMAIL-BROKEN-IMAGES-HOTFIX-1

## Plan asociado

pericial-pdf-email-broken-images-hotfix-1.md

## Task Pack usado

`informe_change`

## Objetivo

Corregir fotografias rotas en el PDF V2 con perfiles `email` y `judicial`
cuando las imagenes del informe se sustituyen por copias temporales
optimizadas.

## Archivos modificados

- `app/main.py`
- `app/services/pdf_image_optimizer.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-email-broken-images-hotfix-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-email-broken-images-hotfix-1.md`

## Diagnostico

La plantilla PDF V2 consume el campo `url` de cada fotografia. El campo
sustituido era correcto, pero el optimizador lo reemplazaba por una ruta
`file://...` apuntando a la copia temporal optimizada.

El PDF V2 se renderiza con Playwright mediante `page.set_content(html)`. En ese
contexto las rutas `file://` quedan fuera del origen HTTP de la aplicacion y
pueden resolverse como imagen rota. La causa raiz no era limpieza prematura ni
campo incorrecto, sino una URL temporal no fiable para Chromium.

## Resultado

Las imagenes optimizadas se sirven ahora con URLs HTTP temporales:

`/pdf-temp-images/{token}/{archivo}`

El endpoint registra el directorio temporal en `app.state` antes del render y
lo retira en el `finally`, antes de borrar la carpeta. La ruta es publica como
`/uploads/` para que Chromium pueda cargarla sin sesion, pero usa token efimero
no adivinable y solo sirve archivos del directorio registrado.

Si la optimizacion de una imagen falla, el HTML conserva la URL original
`/uploads/...` en lugar de dejar un enlace roto. `master` no optimiza imagenes y
conserva las rutas originales.

Con `debug_pdf_pipeline=log` se registran, por imagen:

- campo usado por la plantilla: `url`;
- ruta original;
- URL optimizada;
- ruta temporal optimizada;
- existencia en disco antes del render.

## Tests añadidos/reforzados

- `email` renderiza HTML con `/pdf-temp-images/...`.
- La ruta optimizada existe durante el render.
- La URL temporal responde HTTP 200 durante el render.
- La URL temporal deja de responder tras finalizar el endpoint.
- `judicial` usa la misma ruta temporal resoluble.
- `master` conserva `/uploads/...`.
- Si la optimizacion falla, `email` hace fallback a `/uploads/...`.

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 64 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 253 passed.

## Validacion 019-26

No ejecutada porque no hay autorizacion explicita para leer/generar con DB y
uploads reales. El peso final indicado por usuario para `email` queda en torno a
38 MB; el foco de esta tarea es que las imagenes optimizadas sean visibles.

## Rollback

Revertir la ruta `/pdf-temp-images/...`, el registro temporal en `app.state`, la
generacion de URL publica temporal en `pdf_image_optimizer.py` y los smoke tests.
No hay migraciones ni cambios en uploads.

## Decisiones humanas

No requeridas. No se instalaron dependencias ni se modificaron fotos originales,
DOCX, CRM o base de datos.

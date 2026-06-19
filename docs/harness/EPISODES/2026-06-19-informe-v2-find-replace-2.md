# INFORME-V2-FIND-REPLACE-2

Fecha: 2026-06-19

## Objetivo

Mejorar la herramienta de buscar/reemplazar del Informe V2 Editor para revisar coincidencias con contexto y aprobar sustituciones una a una.

## Diagnóstico

La versión anterior solo devolvía un contador y permitía reemplazar un capítulo completo o todo el informe. Ese flujo era demasiado amplio para corregir referencias antiguas de anexos dentro de textos manuales, porque no permitía ver contexto ni aprobar cada aparición.

## Cambios

- La búsqueda devuelve coincidencias detalladas con capítulo, índice, texto encontrado y contexto antes/después.
- El editor muestra cada coincidencia en una lista con el texto encontrado resaltado.
- Cada coincidencia puede reemplazarse, omitirse o llevar al capítulo correspondiente.
- La acción global reemplaza únicamente coincidencias pendientes y requiere confirmación.
- Se elimina el botón visible de reemplazo en capítulo actual.
- El backend acepta `alcance=seleccion` y valida `updated_at` junto con la posición/texto esperado para evitar reemplazos obsoletos.

## Validaciones

- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "informe_v2_buscar_reemplazar"`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "informe_v2 or pdf_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`

## Cierre

Plan movido a `docs/harness/PLANS/completed/informe-v2-find-replace-2.md` y métricas actualizadas por el harness.

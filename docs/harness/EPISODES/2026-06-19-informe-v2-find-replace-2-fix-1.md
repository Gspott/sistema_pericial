# INFORME-V2-FIND-REPLACE-2-FIX-1

Fecha: 2026-06-19

## Objetivo

Corregir la búsqueda contextual del Informe V2 Editor para que encuentre texto real guardado en los capítulos aunque el formulario envíe campos de contenido vacíos.

## Causa Raíz

El helper de contenido para buscar/reemplazar priorizaba cualquier `contenido_<clave>` recibido en `FormData`. Si el campo llegaba vacío, la búsqueda usaba cadena vacía y no consultaba el contenido guardado, produciendo 0 coincidencias para textos existentes como `Anexo A` o `Anexo C`.

## Cambios

- El contenido enviado por el cliente se usa si trae texto.
- Si el campo llega vacío y existe capítulo guardado, se usa el contenido guardado como fuente de búsqueda.
- Se añadió test con capítulo 1 `Anexo C` y capítulo 2 `Anexo A`.
- Se verifica que buscar no modifica contenido y que el reemplazo individual mantiene validación `updated_at`.

## Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "buscar_reemplazar"`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "informe_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`

## Cierre

Plan movido a `docs/harness/PLANS/completed/informe-v2-find-replace-2-fix-1.md` y métricas actualizadas por el harness.

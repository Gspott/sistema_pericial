# Episode: Pericial Pdf External Annex Optimization 1

## Fecha

2026-06-18

## Tarea

PERICIAL-PDF-EXTERNAL-ANNEX-OPTIMIZATION-1

## Plan asociado

pericial-pdf-external-annex-optimization-1.md

## Task Pack usado

`informe_change`

## Objetivo

Diagnosticar y reducir, cuando sea posible, el peso añadido al PDF final por
PDFs externos fusionados como Anexo A documental y Anexo F de mediciones.

## Archivos modificados

- `app/main.py`
- `app/services/pdf_annex_optimizer.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-external-annex-optimization-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-external-annex-optimization-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 46 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 235 passed.

## Resultado

Se anadio `app/services/pdf_annex_optimizer.py` con diagnostico de tamano,
intento opcional de Ghostscript si esta disponible y fallback conservador con
`pypdf.compress_content_streams()`.

El editor de Informe V2 muestra aviso cuando existen anexos PDF externos,
desglosando Anexo A y Anexo F. La fusion integrada usa copias temporales
optimizadas en perfiles `email` y `judicial`; `master`, `informe_anexos` y el
perfil por defecto mantienen el comportamiento historico.

## Warnings

Ghostscript no esta instalado en el entorno local, por lo que la ruta validada
usa fallback `pypdf` o no optimiza si no hay reduccion real. PDFs escaneados con
imagenes internas pueden no reducirse con `pypdf`.

`audit_docs.py` mantiene warnings preexistentes sobre planes completados vacios
y tamano del monolito `app/main.py`.

## Rollback

Revertir el servicio nuevo, cambios de fusion/diagnostico/UI y tests. No hay
migraciones ni datos persistentes nuevos.

## Memoria actualizada

Plan cerrado en
`docs/harness/PLANS/completed/pericial-pdf-external-annex-optimization-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas.

## Proximos pasos

Medir un caso real comparando `master`, `solo_informe`, `email` y `judicial`.
Si el peso sigue dominado por PDFs escaneados, valorar una tarea especifica con
Ghostscript instalado o una estrategia controlada de raster/recompresion.

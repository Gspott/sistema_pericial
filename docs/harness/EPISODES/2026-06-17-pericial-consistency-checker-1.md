# Episode: Pericial Consistency Checker 1

## Fecha

2026-06-17


## Tarea

PERICIAL-CONSISTENCY-CHECKER-1

## Plan asociado

pericial-consistency-checker-1.md


## Task Pack usado

`informe_change`

## Objetivo

Crear una V1 de revision de coherencia pericial para expedientes, de solo
lectura y no bloqueante, con errores, advertencias, informacion y score
orientativo.

## Archivos modificados

- `app/services/pericial_consistency.py`
- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- `docs/harness/PLANS/completed/pericial-consistency-checker-1.md`
- `docs/harness/METRICS.md` mediante cierre harness
- `docs/harness/EPISODES/2026-06-17-pericial-consistency-checker-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app/services/pericial_consistency.py app/main.py`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`: OK, 5 passed.
- `python3 -m compileall app`: OK.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK; autoelevado a
  `full`, 197 passed, 1 skipped por Playwright/Chromium no disponible.

## Resultado

Implementado servicio `analizar_consistencia_expediente(expediente_id)` con
estructura estable y reglas V1:

- `EMPTY_CHAPTER`
- `PHOTO_NOT_REFERENCED`
- `PHOTO_REFERENCE_BROKEN`
- `ANNEX_NOT_REFERENCED`
- `ANNEX_REFERENCE_BROKEN`
- `ROOM_REFERENCE_UNKNOWN`
- `UNSUPPORTED_CONCLUSION_BASIC`
- `TIMELINE_INCONSISTENT_BASIC`

Integracion:

- Endpoint interno `GET /expedientes/{expediente_id}/revision-coherencia`
  protegido con ownership.
- Bloque "Revision de coherencia" en el panel de contexto del editor Informe
  V2, no imprimible y no bloqueante.

## Warnings

`audit_docs.py` mantiene warnings preexistentes sobre planes completados vacios
y tamano del monolito `app/main.py`.

El scope full incluyo cambios no relacionados ya presentes en el worktree
(`crm`, drawer, email templates), sin modificarlos en esta tarea.

## Rollback

Revertir los archivos modificados de esta tarea. No hay migraciones ni datos
persistentes nuevos.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/pericial-consistency-checker-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas. El cambio es pequeno, reversible, de solo lectura y no toca
generacion PDF/DOCX ni datos reales.

## Proximos pasos

Futuras fases pueden calibrar severidades, mapear numeracion real de figuras
del PDF V2 y ampliar revision juridica o risky statements con plan separado.

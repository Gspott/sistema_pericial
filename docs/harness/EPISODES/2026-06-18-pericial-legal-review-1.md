# Episode: Pericial Legal Review 1

## Fecha

2026-06-18


## Tarea

PERICIAL-LEGAL-REVIEW-1

## Plan asociado

pericial-legal-review-1.md


## Task Pack usado

`informe_change`

## Objetivo

Anadir una revision juridica informativa en Informe V2, integrada en el motor
de coherencia existente, sin bloquear guardado, edicion ni exportacion.

## Archivos modificados

- `app/services/pericial_consistency.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- `docs/harness/PLANS/completed/pericial-legal-review-1.md`
- `docs/harness/METRICS.md` mediante cierre harness
- `docs/harness/EPISODES/2026-06-18-pericial-legal-review-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app/services/pericial_consistency.py`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`:
  OK, 12 passed.
- `python3 -m compileall app`: OK.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK; autoelevado
  a `full`, 218 passed, 1 skipped por Playwright/Chromium no disponible.

## Resultado

El checker de coherencia devuelve ahora `revision_juridica` con incidencias de
categoria `revision_juridica`, severidad `warning`, fragmento, sugerencia y
enlace al capitulo cuando aplica.

Reglas V1:

- `LEGAL_EXCESSIVE_CERTAINTY`
- `LEGAL_ABSOLUTE_CAUSATION`
- `LEGAL_ATTRIBUTION_OF_LIABILITY`
- `LEGAL_INTENTIONALITY`
- `LEGAL_OVERCONCLUSIVE_LANGUAGE`

La UI del editor Informe V2 muestra la seccion
"Redaccion potencialmente impugnable" dentro de "Revision de coherencia".

## Warnings

`audit_docs.py` mantiene warnings preexistentes sobre planes completados vacios
y tamano del monolito `app/main.py`.

El cierre harness se autoelevo a `full` por cambios pendientes del worktree en
areas ajenas a esta tarea; no se tocaron en esta fase.

## Rollback

Revertir los archivos modificados de esta tarea. No hay migraciones ni datos
persistentes nuevos.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/pericial-legal-review-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas. Cambio pequeno, reversible, informativo y sin asesoramiento
juridico.

## Proximos pasos

Futuras fases pueden permitir marcar avisos como revisados, ajustar severidad
por tipo de informe o vincular sugerencias a soportes concretos de prueba.

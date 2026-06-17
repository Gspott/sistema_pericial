# Episode: Pericial Risky Statements 1

## Fecha

2026-06-17


## Tarea

PERICIAL-RISKY-STATEMENTS-1

## Plan asociado

pericial-risky-statements-1.md


## Task Pack usado

`informe_change`

## Objetivo

Anadir una revision informativa de afirmaciones pericialmente sensibles dentro
del motor de coherencia existente, sin bloquear guardado, edicion ni
exportacion.

## Archivos modificados

- `app/services/pericial_consistency.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- `docs/harness/PLANS/completed/pericial-risky-statements-1.md`
- `docs/harness/METRICS.md` mediante cierre harness
- `docs/harness/EPISODES/2026-06-17-pericial-risky-statements-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app/services/pericial_consistency.py`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`:
  OK, 8 passed.
- `python3 -m compileall app`: OK.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK.

## Resultado

El checker de coherencia detecta ahora afirmaciones sensibles con categoria
`riesgo_pericial`, tambien agrupadas en `riesgos_periciales`:

- `RISK_STRUCTURAL_COLLAPSE`
- `RISK_MECHANICAL_PROPERTIES`
- `RISK_CAUSATION_CERTAINTY`
- `RISK_LEGAL_RESPONSIBILITY`
- `RISK_CODE_COMPLIANCE`
- `RISK_URGENT_DANGER`

Cada incidencia conserva estructura homogenea e incluye `fragmento` cuando
aplica. El editor Informe V2 muestra la subseccion "Afirmaciones a revisar"
dentro de "Revision de coherencia".

## Warnings

`audit_docs.py` mantiene warnings preexistentes sobre planes completados vacios
y tamano del monolito `app/main.py`.

## Rollback

Revertir los archivos modificados de esta tarea. No hay migraciones ni datos
persistentes nuevos.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/pericial-risky-statements-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas. El cambio es pequeno, reversible, informativo y no toca PDF,
DOCX, DB ni CRM/prospeccion.

## Proximos pasos

En una fase futura se puede ajustar severidad por tipo de informe, permitir
silenciar avisos revisados o enriquecer soporte con referencias a ensayos,
catas, calculos o documentos concretos.

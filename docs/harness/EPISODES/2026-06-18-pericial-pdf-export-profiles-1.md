# Episode: Pericial Pdf Export Profiles 1

## Fecha

2026-06-18

## Tarea

PERICIAL-PDF-EXPORT-PROFILES-1

## Plan asociado

pericial-pdf-export-profiles-1.md

## Task Pack usado

`informe_change`

## Objetivo

Anadir perfiles de exportacion PDF para Informe V2 sin sustituir la generacion
actual ni modificar el contenido tecnico del informe.

## Archivos modificados

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-export-profiles-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-export-profiles-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 38 passed.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`:
  OK, 16 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 227 passed.

## Resultado

Informe V2 acepta `?perfil=` en la ruta PDF con perfiles `master`, `email`,
`judicial`, `solo_informe`, `informe_anexos` y `anexo_fotografico`.

El perfil por defecto conserva el comportamiento y nombre historicos. Los
perfiles explicitos generan nombre diferenciado. `solo_informe` omite la fusion
de anexos PDF integrados. `anexo_fotografico` queda preparado y responde 501 de
forma controlada porque no hay generacion separada sin refactor.

## Warnings

`audit_docs.py` mantiene warnings preexistentes sobre planes completados vacios
y tamano del monolito `app/main.py`.

## Rollback

Revertir los cambios de la tarea. No hay migraciones ni datos persistentes
nuevos.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/pericial-pdf-export-profiles-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas. El perfil de anexo fotografico se deja preparado para evitar un
refactor amplio fuera de alcance.

## Proximos pasos

PERICIAL-PDF-IMAGE-OPTIMIZATION-1 puede implementar compresion real, objetivos
de tamano y generacion separada del anexo fotografico si encaja con la
arquitectura PDF.

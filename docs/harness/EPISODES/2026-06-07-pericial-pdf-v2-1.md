# Episode: Pericial Pdf V2 1

## Fecha

2026-06-07


## Tarea

PERICIAL-PDF-V2-1: implementar la primera exportacion PDF independiente del
informe pericial V2.

## Plan asociado

pericial-pdf-v2-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/informe_change.md`

## Objetivo

Generar un PDF V2 profesional que consume como fuente principal y exclusiva los
capitulos persistidos en `informe_v2_capitulos`, sin sustituir ni modificar el
informe clasico.

## Archivos modificados

- `app/main.py`
- `app/services/informe.py`
- `templates/informes/v2_pdf.html`
- `templates/informe_v2_editor.html`
- `templates/pericial_workbench.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-v2-1.md`
- `docs/harness/EPISODES/2026-06-07-pericial-pdf-v2-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecuto smoke completo: 141 passed.

## Resultado

Se anade la ruta independiente:

- `GET /generar-informe-v2-pdf/{expediente_id}`

La ruta valida propiedad y tipo `patologias`, prepara un contexto V2 desde
`informe_v2_capitulos` y renderiza `templates/informes/v2_pdf.html` mediante
Playwright. El Workbench y el editor muestran la accion `Generar PDF V2`.

El PDF incluye portada, indice, los 12 capitulos editables V2 en orden y una
seccion de anexos preparada para PDF-V2-2.

## Warnings

`python3 scripts/audit_docs.py` mantiene warning informativo preexistente de
monolito estructural en `app/main.py`.

## Rollback

Revertir los archivos listados. El informe clasico queda separado y no requiere
migracion de rollback.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

PDF-V2-2: anexo fotografico y anexo de patologias reutilizando mecanismos
existentes sin leer ni exponer ficheros reales fuera del flujo autorizado.

# Episode: Pericial Case Linking 1

## Fecha

2026-06-25


## Tarea

Soporte inicial para expedientes derivados/relacionados sin duplicar evidencias
ni contenido tecnico-documental.

## Plan asociado

pericial-case-linking-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/db_change.md`

## Objetivo

Permitir crear un expediente nuevo desde otro, copiando solo datos permanentes
del inmueble y estructura base multiunidad, y registrar la relacion entre ambos
para mostrarla en detalle y workbench pericial.

## Archivos modificados

- `app/database.py`
- `app/main.py`
- `templates/crear_expediente_derivado.html`
- `templates/detalle_expediente.html`
- `templates/pericial_workbench.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-case-linking-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/pytest tests/smoke/test_pericial_workbench.py -q -k "expediente_derivado"`
- `.venv/bin/pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/pytest -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

## Resultado

OK. Se crea `expediente_relaciones` de forma idempotente, con tipos
`derivado`, `complementario` y `seguimiento`. La nueva ruta SSR
`/expedientes/{id}/crear-derivado` crea un expediente limpio y lo vincula al
origen. Detalle y workbench muestran origen/derivados con enlaces.

## Warnings

`audit_docs.py` conserva warnings historicos preexistentes sobre planes
completados sin contenido real y el aviso informativo de monolito en
`app/main.py`.

## Rollback

Revertir los archivos modificados. La tabla nueva no borra ni migra datos
existentes.

## Memoria actualizada

Plan completado movido a `docs/harness/PLANS/completed/` y metricas harness
actualizadas por `finish_harness_task.sh`.

## Decisiones humanas

No requirio aprobacion adicional: no hubo migracion destructiva, datos reales,
facturacion, autenticacion, backups/restore, secretos ni deploy.

## Proximos pasos

Fase futura: usar la relacion como antecedente textual opcional en el contexto
de informes derivados, sin fusionar PDFs ni copiar anexos automaticamente.

# Episode: Pericial Wb 2

## Fecha

2026-06-06


## Tarea

PERICIAL-WB-2: evolucionar el Workbench pericial SSR hacia redaccion asistida
de solo lectura, incorporando un borrador temporal del informe V2.

## Plan asociado

pericial-wb-2.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Mostrar en `/expedientes/{expediente_id}/pericial-workbench` un bloque
`Borrador informe V2` con textos derivados de datos existentes, sin persistir
informacion, sin crear campos y sin modificar generacion PDF/DOCX.

## Archivos modificados

- `app/main.py`
- `templates/pericial_workbench.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-wb-2.md`
- `docs/harness/EPISODES/2026-06-06-pericial-wb-2.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `bash scripts/finish_harness_task.sh` ejecuto smoke completo: 138 passed.

## Resultado

Se anade un borrador temporal para:

- resumen ejecutivo;
- metodologia;
- limitaciones;
- analisis causal;
- recomendaciones.

Cada bloque aparece marcado como texto generado automaticamente y requiere
revision tecnica. El contenido se calcula en memoria desde expediente, visitas,
climatologia, patologias, fotografias, actuaciones economicas, limitaciones
candidatas y recomendaciones candidatas.

## Warnings

`python3 scripts/audit_docs.py` mantiene warning informativo preexistente de
monolito estructural en `app/main.py`.

## Rollback

Revertir los archivos listados. No hay migraciones, tablas nuevas, campos nuevos
ni cambios en PDF/DOCX.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

PERICIAL-WB-3: revisar si conviene microedicion controlada de campos existentes
desde el Workbench o mantener otra fase de diagnostico antes de persistir.

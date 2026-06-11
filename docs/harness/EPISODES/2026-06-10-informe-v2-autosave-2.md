# Episode: Informe V2 Autosave 2

## Fecha

2026-06-10


## Tarea

INFORME-V2-AUTOSAVE-2: mejora de fiabilidad visual y protección frente a sobrescritura manual en el Editor V2.

## Plan asociado

informe-v2-autosave-2.md


## Task Pack usado

app_change

## Objetivo

Evitar que el editor indique `Guardado` sin una petición real de autosave y bloquear el guardado manual completo cuando existan capítulos con `updated_at` más reciente que el cargado por la página.

## Archivos modificados

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/informe-v2-autosave-2.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-10-informe-v2-autosave-2.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

## Resultado

El estado inicial del autosave pasa a `Listo para editar`. El estado `Guardado` solo se muestra después de una respuesta correcta de `/informes-v2/{expediente_id}/autosave`, incluyendo título de capítulo y hora de guardado.

Cada capítulo envía el `updated_at` que tenía al cargar la página. Tras un autosave correcto, el JavaScript actualiza ese valor oculto para que el guardado manual de la misma pestaña no se bloquee. Si al hacer guardado manual existe un capítulo con `updated_at` distinto al cargado, el servidor no sobrescribe y redirige con advertencia.

Los tests cubren estado inicial, cableado de hora/campo, error visible, conflicto por `updated_at`, guardado manual sin conflicto y autosave existente.

## Warnings

`scripts/audit_docs.py` mantiene el warning informativo preexistente de monolito estructural en `app/main.py`.

## Rollback

Retirar el helper de detección de conflictos, los campos ocultos `updated_at_*`, los ajustes del estado visual y los tests añadidos. No hay migraciones ni cambios de esquema.

## Memoria actualizada

Sí. `finish_harness_task.sh` cerró el plan y actualizó métricas.

## Decisiones humanas

No hubo decisiones humanas adicionales durante la implementación.

## Proximos pasos

Si se detectan sesiones concurrentes frecuentes, estudiar una pantalla de resolución de conflictos por capítulo. En esta fase se prioriza no perder contenido autosalvado.

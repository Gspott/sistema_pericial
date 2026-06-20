# Episode: Autosave Propuestas Formularios Largos 1

## Fecha

2026-06-19


## Tarea

Implementar `autosave-propuestas-formularios-largos-1`, ultimo paquete funcional del rollout `AUTOSAVE-ROLLOUT-1`, extendiendo el autosave estandar al formulario largo principal de propuestas.

## Plan asociado

autosave-propuestas-formularios-largos-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Reutilizar `static/js/autosave.js`, el componente visual estandar y el contrato JSON existente para proteger la edicion prolongada de propuestas persistidas, manteniendo el guardado manual como fallback y sin tocar facturacion, PDFs, emails ni acciones irreversibles.

## Archivos modificados

- `app/routers/propuestas.py`
- `templates/propuestas/form.html`
- `tests/smoke/test_autosave_propuestas_formularios_largos.py`
- `docs/harness/PLANS/completed/autosave-propuestas-formularios-largos-1.md`
- `docs/harness/EPISODES/2026-06-19-autosave-propuestas-formularios-largos-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- `.venv/bin/python -m pytest tests/smoke/test_autosave_propuestas_formularios_largos.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_propuestas_flow.py tests/smoke/test_flow_propuesta_factura.py tests/smoke/test_facturacion_asistente_propuesta.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Resultado

Autosave implantado en `GET/POST /propuestas/{propuesta_id}/editar` para propuestas persistidas:

- estado visual estandar en la plantilla;
- endpoint `POST /propuestas/{propuesta_id}/autosave`;
- contrato JSON estandar con `ok`, `updated_at`, `saved_at` y `message`;
- conflicto `409` cuando el `updated_at` del cliente no coincide;
- guardado manual protegido con el mismo `updated_at`;
- uso de `now_madrid_iso()` en escrituras de `updated_at` de propuesta para respetar `TIMEZONE-STANDARD-1`.

La creacion de propuesta queda sin autosave porque no hay entidad persistida. Las lineas de propuesta se documentan como pendiente potencial porque mezclan textos largos con importes, IVA, recalculo de totales y acciones estructurales.

## Warnings

`audit_docs.py` conserva warnings historicos de planes completados vacios y monolito `app/main.py`; no estan introducidos por este paquete.

## Rollback

Revertir los cambios listados en este episodio. No hay migraciones ni modificaciones de bases SQLite reales.

## Memoria actualizada

Plan y episodio harness actualizados. El cierre formal se completo con `bash scripts/finish_harness_task.sh`.

## Decisiones humanas

No requerida aprobacion adicional: el paquete no toca facturacion fiscal, generacion documental, emails, bases reales ni migraciones.

## Proximos pasos

Si se quiere autosave en lineas de propuesta, abrir plan independiente para separar edicion textual de acciones economicas/estructurales antes de aplicar autosave.

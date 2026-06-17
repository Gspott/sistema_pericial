# Episode: Crm Prospeccion Desktop 4

## Fecha

2026-06-17


## Tarea
CRM-PROSPECCION-DESKTOP-4

## Plan asociado

crm-prospeccion-desktop-4.md


## Task Pack usado
email_change

## Objetivo
Convertir `/crm/prospeccion` en un Workbench desktop-first de prospeccion comercial, optimizado para alta rapida de leads, filtrado de administradores de fincas, seleccion sin salir de pantalla, previsualizacion editable de plantilla, envio controlado, programacion defensiva y seguimiento automatico.

## Archivos modificados
- `app/routers/crm.py`
- `app/services/crm_templates.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-desktop-4.md`
- `docs/harness/EPISODES/2026-06-17-crm-prospeccion-desktop-4.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q` -> 12 passed antes de ampliar smokes.
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q` -> 22 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` -> scope elevado a full, 186 passed.
- `git diff --check`

## Resultado
Implementado Workbench desktop en tres zonas:

- Columna izquierda con alta rapida, filtros, vistas rapidas y acciones prioritarias.
- Zona central con tabla compacta, seleccion de lead mediante `lead_id` y acciones inline basicas.
- Panel derecho persistente con datos del lead, selector de plantilla, asunto/cuerpo renderizados, edicion manual, envio inmediato, programacion defensiva, acciones recomendadas e historial breve.

El alta rapida usa columnas existentes de `leads` y guarda metadatos de persona/localidad/tipo en `notas`, evitando migraciones. El envio editado registra en `emails_enviados` el asunto/cuerpo final y mantiene la creacion de seguimiento a 10 dias. La programacion no envia email real ni crea worker: registra `emails_enviados.estado = 'programado'` con fecha prevista en `error_mensaje`.

## Warnings
La programacion queda como registro operativo pendiente; no existe automatizacion de envio en esta fase. Los archivos CRM de fases anteriores continuan sin trackear en Git en este worktree.

## Rollback
Revertir los archivos modificados de esta fase. No hay migracion de esquema ni cambios destructivos de datos.

## Memoria actualizada
Metricas harness actualizadas por `finish_harness_task.sh`.

## Decisiones humanas
No se requirio aprobacion adicional porque no se tocaron SMTP real, `.env`, datos reales, migraciones ni modulos prohibidos.

## Proximos pasos
CRM-PROSPECCION-AGENDA-5: revisar correos programados desde el Workbench, confirmar/envio manual y cerrar el ciclo de agenda sin automatizacion masiva.

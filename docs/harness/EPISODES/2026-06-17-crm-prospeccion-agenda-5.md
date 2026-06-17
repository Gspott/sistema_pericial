# Episode: Crm Prospeccion Agenda 5

## Fecha

2026-06-17


## Tarea
CRM-PROSPECCION-AGENDA-5

## Plan asociado

crm-prospeccion-agenda-5.md


## Task Pack usado
email_change

## Objetivo
Crear una agenda/bandeja desktop de emails programados para revisar, confirmar envio manual, cancelar o reprogramar, sin worker automatico ni envios masivos.

## Archivos modificados
- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `templates/crm/prospeccion_agenda.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-agenda-5.md`
- `docs/harness/EPISODES/2026-06-17-crm-prospeccion-agenda-5.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q` -> 20 passed.
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q` -> 26 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` -> scope elevado a full, 190 passed.

## Resultado
Implementada `/crm/prospeccion/agenda` con tabla compacta de emails programados y panel derecho de revision:

- lista `emails_enviados.estado = 'programado'`;
- muestra destinatario, lead, tipo/plantilla, asunto, fecha programada y estado;
- permite revisar y editar asunto/cuerpo antes de confirmar;
- confirma envio individual reutilizando la infraestructura mock-safe existente;
- actualiza el registro programado a `estado = 'enviado'` y tipo comercial definitivo;
- aplica seguimiento a 10 dias para presentaciones y revision a 30 dias para seguimientos, sin duplicar tareas;
- permite cancelar sin borrar (`estado = 'cancelado'`);
- permite reprogramar actualizando `programado_para=...` dentro de `error_mensaje`.

## Warnings
La fecha programada sigue almacenada en `emails_enviados.error_mensaje` por compatibilidad con CRM-PROSPECCION-DESKTOP-4. No hay automatizacion real de envio.

## Rollback
Revertir los cambios de esta fase. No hay migraciones ni cambios destructivos de esquema.

## Memoria actualizada
Metricas harness actualizadas por `finish_harness_task.sh`.

## Decisiones humanas
No se requirio aprobacion adicional porque no se tocaron SMTP real, `.env`, datos reales, workers ni modulos prohibidos.

## Proximos pasos
CRM-PROSPECCION-RESPUESTAS-6: registrar respuesta/no respuesta, preparar estados de ciclo comercial y pequenas acciones de cierre tras llamada/email.

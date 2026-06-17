# Episode: Crm Prospeccion Preview 6

## Fecha

2026-06-17


## Tarea
CRM-PROSPECCION-PREVIEW-6

## Plan asociado

crm-prospeccion-preview-6.md


## Task Pack usado
email_change

## Objetivo
Anadir una previsualizacion realista del email comercial antes de enviar o programar desde `/crm/prospeccion`, reduciendo errores antes de contactar administradores de fincas.

## Archivos modificados
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-preview-6.md`
- `docs/harness/EPISODES/2026-06-17-crm-prospeccion-preview-6.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q` -> 21 passed.
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q` -> 27 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` -> scope elevado a full, 191 passed.

## Resultado
Implementado modal grande de previsualizacion en el panel derecho del Workbench:

- boton `Previsualizar`;
- modal desktop 80-90% de pantalla con cierre por boton, ESC nativo de `dialog` y clic fuera;
- cabecera simulada con De, Para, Asunto y Fecha;
- cuerpo renderizado con saltos reales mediante `white-space: pre-wrap`;
- firma visible de Carlos Blanco;
- seccion de adjuntos prevista;
- pestanas `Gmail escritorio` y `Gmail movil`;
- botones `Volver a editar`, `Programar envio` y `Enviar ahora`;
- indicador local `✓ Revisado antes de enviar`.

El modal lee en cliente el asunto/cuerpo actuales, por lo que editar, volver a previsualizar y enviar usa el texto final sin rutas nuevas.

## Warnings
No se implementa preview de adjuntos reales porque el flujo CRM actual no asocia dossier/PDF a estos emails. La aprobacion queda solo en memoria de la pagina, no persistida.

## Rollback
Revertir cambios de plantilla/tests/docs de esta fase. No hay migracion ni cambios backend de envio.

## Memoria actualizada
Metricas harness actualizadas por `finish_harness_task.sh`.

## Decisiones humanas
No se requirio aprobacion adicional porque no se tocaron SMTP real, `.env`, datos reales, migraciones ni modulos prohibidos.

## Proximos pasos
CRM-PROSPECCION-SENT-7: mejorar bandeja de enviados/resultado posterior para revisar envios reales, respuestas y siguientes acciones.

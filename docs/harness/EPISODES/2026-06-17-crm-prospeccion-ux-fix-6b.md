# Episode: Crm Prospeccion Ux Fix 6B

## Fecha

2026-06-17


## Tarea
CRM-PROSPECCION-UX-FIX-6B

## Plan asociado

crm-prospeccion-ux-fix-6b.md


## Task Pack usado
email_change

## Objetivo
Reducir clicks innecesarios en el Workbench de prospeccion: seleccion de lead desde nombre/empresa y cambio automatico de plantilla con proteccion de ediciones manuales.

## Archivos modificados
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-ux-fix-6b.md`
- `docs/harness/EPISODES/2026-06-17-crm-prospeccion-ux-fix-6b.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas
- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q` -> 23 passed.
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_email_mock.py tests/smoke/test_routes_basic.py -q` -> 29 passed.
- `bash scripts/finish_harness_task.sh --smoke-scope app` -> scope elevado a full, 193 passed.

## Resultado
Implementadas dos mejoras de UX:

- El nombre/empresa del lead es ahora el selector principal del Workbench, conserva filtros mediante query string y guarda/restaura scroll de ventana y tabla con `sessionStorage`.
- La fila seleccionada queda resaltada con fondo, borde izquierdo e indicador visual.
- La accion independiente `Abrir lead` se conserva en el panel derecho.
- El selector de plantilla ya no necesita boton intermedio; al cambiar dispara el formulario automaticamente.
- Si asunto/cuerpo fueron editados manualmente, se pide confirmacion antes de sustituirlos por la nueva plantilla; si se cancela, se restaura la plantilla anterior.
- El modal grande de previsualizacion de CRM-PROSPECCION-PREVIEW-6 se mantiene.

## Warnings
El cambio de lead/plantilla sigue usando GET con recarga de la vista, no AJAX. Se conserva scroll para que la experiencia se sienta continua.

## Rollback
Revertir cambios de plantilla/tests/docs de esta fase. No hay migraciones ni cambios backend de envio.

## Memoria actualizada
Metricas harness actualizadas por `finish_harness_task.sh`.

## Decisiones humanas
No se requirio aprobacion adicional porque no se tocaron SMTP real, `.env`, datos reales, agenda backend, migraciones ni modulos prohibidos.

## Proximos pasos
CRM-PROSPECCION-SENT-7: bandeja de enviados y gestion de resultado posterior a envios reales.

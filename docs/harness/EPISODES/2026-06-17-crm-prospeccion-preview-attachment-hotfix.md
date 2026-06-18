# Episode: Crm Prospeccion Preview Attachment Hotfix

## Fecha

2026-06-17


## Tarea

CRM-PROSPECCION-PREVIEW-ATTACHMENT-HOTFIX

## Plan asociado

crm-prospeccion-preview-attachment-hotfix.md


## Task Pack usado

email_change

## Objetivo

Corregir la previsualizacion del Workbench CRM para que la plantilla `presentacion_administrador_fincas` muestre el PNG corporativo previsto como adjunto antes de enviar o programar.

## Archivos modificados

- `app/routers/crm.py`
- `templates/crm/prospeccion.html`
- `tests/smoke/test_crm_prospeccion_workbench.py`
- `docs/harness/PLANS/completed/crm-prospeccion-preview-attachment-hotfix.md`
- `docs/harness/EPISODES/2026-06-17-crm-prospeccion-preview-attachment-hotfix.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `./.venv/bin/pytest tests/smoke/test_crm_prospeccion_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`
- `git status --short`

## Resultado

El panel de preview recibe ahora `preview_email.adjunto_nombre` cuando la plantilla seleccionada es la presentacion de administradores de fincas y el PNG existe en `static/crm/`.

El modal muestra `Adjuntos: 📎 carlos-blanco-presentacion-administradores.png` tanto en la vista escritorio como en la vista movil. El JS conserva el fallback `Sin adjuntos previstos` para plantillas sin adjunto.

## Warnings

El harness elevo la validacion a scope `full` por cambios acumulados en rutas criticas del worktree. La auditoria documental mantiene warnings historicos/preexistentes sobre planes completados antiguos y el monolito `app/main.py`.

## Rollback

Eliminar `adjunto_nombre` del preview, volver a `data-attachment-name=""` y restaurar el texto fijo `Adjuntos: Sin adjuntos previstos`.

## Memoria actualizada

No aplica.

## Decisiones humanas

El usuario reporto que el archivo adjunto no aparecia en la previsualizacion del email.

## Proximos pasos

Abrir `/crm/prospeccion`, seleccionar un administrador de fincas y pulsar `Previsualizar` para confirmar visualmente que el adjunto aparece antes de enviar.

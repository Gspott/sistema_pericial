# Episode: Autosave Crm Costes 1

## Fecha

2026-06-19


## Tarea

Implantacion reversible del rollout `AUTOSAVE-ROLLOUT-1` en la subfase
`autosave-crm-costes-1`.

## Plan asociado

autosave-crm-costes-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Extender `AUTOSAVE-STANDARD-1` a edicion persistida y segura de CRM y Costes,
sin reimplementar infraestructura comun, sin migraciones y con guardado manual
intacto.

## Archivos modificados

- `app/routers/crm.py`
- `app/routers/costes.py`
- `templates/crm/prospeccion.html`
- `templates/costes/detalle.html`
- `tests/smoke/test_autosave_crm_costes.py`
- `docs/harness/PLANS/completed/autosave-crm-costes-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- `.venv/bin/python -m pytest tests/smoke/test_autosave_crm_costes.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_autosave_crm_costes.py tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Resultado

Implantado autosave en:

- Notas del lead seleccionado en `templates/crm/prospeccion.html`.
- Edicion de partida existente en `templates/costes/detalle.html`.

Se reutiliza `static/js/autosave.js` y
`templates/components/autosave_status.html`.

Concurrencia:

- `leads` usa `updated_at` real.
- `costes_conceptos` usa `updated_at` real.
- Los formularios manuales reciben `updated_at` y evitan sobrescrituras
  silenciosas.

Queda fuera:

- Alta rapida de leads.
- Envio/programacion de emails CRM.
- Agenda CRM.
- Capturas/OCR, importaciones BC3 y uploads.
- Descompuestos, validacion y borrados de partidas.
- Propuestas y facturacion.

Smoke cubierto:

- Render del contrato comun en CRM y Costes.
- Persistencia y recarga de notas CRM.
- Conflicto 409 en notas CRM.
- Persistencia y recarga de descripcion de coste.
- Conflicto 409 en Costes.
- Regresion proporcional de smokes existentes CRM/Costes.

## Warnings

`audit_docs.py` conserva warnings historicos:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

## Rollback

Retirar endpoints `/crm/prospeccion/leads/{lead_id}/notas/autosave`,
`/crm/prospeccion/leads/{lead_id}/notas` y `/costes/{concepto_id}/autosave`;
retirar atributos `data-autosave-*`, hidden `updated_at`, includes del
componente visual en las dos plantillas y retirar el smoke especifico. Los
guardados manuales quedan intactos.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/autosave-crm-costes-1.md`.

## Decisiones humanas

No se requirio aprobacion humana. No se tocaron datos reales, bases SQLite,
esquema, backups, uploads, OCR, BC3, propuestas, facturacion ni deploy.

## Proximos pasos

- Abrir plan independiente si se quiere autosave para capturas/OCR separando
  borrador textual de creacion de partida.
- Continuar el rollout posterior con formularios largos de propuestas cuando
  proceda.

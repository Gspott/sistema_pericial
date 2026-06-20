# Episode: Autosave Standard 1

## Fecha

2026-06-19


## Tarea

Implantacion inicial del estandar transversal `AUTOSAVE-STANDARD-1` y piloto en Valoracion Workbench.

## Plan asociado

autosave-standard-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Crear una infraestructura comun de autoguardado basada en el patron de Informe V2 y aplicarla de forma acotada a la microedicion de testigos del Workbench de valoracion, manteniendo el boton manual como fallback.

## Archivos modificados

- `static/js/autosave.js`
- `templates/components/autosave_status.html`
- `templates/valoracion_workbench.html`
- `app/main.py`
- `app/services/informe.py`
- `tests/smoke/test_valoracion_workbench.py`
- `docs/harness/PATTERNS/autosave_standard.md`
- `docs/harness/PLANS/completed/autosave-standard-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- `.venv/bin/python -m pytest tests/smoke/test_valoracion_workbench.py -q -k "autosave or microedicion"`
- `.venv/bin/python -m pytest tests/smoke/test_valoracion_workbench.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Resultado

Infraestructura comun creada y piloto funcional en Valoracion Workbench:

- estados visuales `ready`, `dirty`, `saving`, `saved`, `error` y `conflict`;
- eventos `input`, `change` y `blur`;
- debounce configurable por formulario;
- POST AJAX reusable con `FormData`;
- contrato JSON estandar con `ok`, `updated_at`, `saved_at` y `message`;
- conflicto `409` cuando el `updated_at` del cliente no coincide con el registro actual;
- reintento simple en fallo de red;
- proteccion `beforeunload` si quedan cambios pendientes;
- guardado manual conservado y protegido tambien por `updated_at`.

## Warnings

`audit_docs.py` sigue informando warnings historicos no introducidos en esta tarea:

- `app/main.py` supera el umbral informativo de lineas.
- Hay planes completados antiguos con secciones vacias.

## Rollback

Retirar el endpoint `/expediente/{expediente_id}/valoracion/workbench/testigo/{testigo_id}/autosave`, quitar los atributos `data-autosave-*` del formulario de microedicion, retirar el include del componente y dejar el submit manual existente.

## Memoria actualizada

Nuevo patron harness documentado en `docs/harness/PATTERNS/autosave_standard.md`.

## Decisiones humanas

No hubo decisiones adicionales requeridas. La extension a patologias, visitas, CRM, costes y propuestas queda fuera de esta fase.

## Proximos pasos

- Plan posterior sugerido: `autosave-patologias-visitas-1`.
- Plan posterior sugerido: `autosave-crm-costes-1`.
- Plan posterior sugerido: `autosave-propuestas-formularios-largos-1`.

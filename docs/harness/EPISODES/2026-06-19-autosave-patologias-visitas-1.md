# Episode: Autosave Patologias Visitas 1

## Fecha

2026-06-19


## Tarea

Primera implantacion reversible del rollout `AUTOSAVE-ROLLOUT-1` en la subfase `autosave-patologias-visitas-1`.

## Plan asociado

autosave-patologias-visitas-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Extender `AUTOSAVE-STANDARD-1` a formularios de visita ya existentes, con foco en informacion de campo y observaciones tecnicas, sin migrar datos ni reimplementar la infraestructura comun.

## Archivos modificados

- `app/main.py`
- `templates/nueva_visita.html`
- `templates/editar_visita.html`
- `templates/valoracion_visita_observaciones.html`
- `static/mobile.css`
- `tests/smoke/test_valoracion_nueva_visita_ux.py`
- `docs/harness/PLANS/completed/autosave-patologias-visitas-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- `.venv/bin/python -m pytest tests/smoke/test_valoracion_nueva_visita_ux.py -q -k "autosave or visita"`
- `.venv/bin/python -m pytest tests/smoke/test_valoracion_nueva_visita_ux.py tests/smoke/test_valoracion_visita_observaciones_form.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Resultado

Implantado autosave en:

- ficha principal de visita existente desde `templates/nueva_visita.html`;
- ficha legacy `templates/editar_visita.html`;
- observaciones de portal/contadores en visita de valoracion;
- pantalla independiente `templates/valoracion_visita_observaciones.html`.

Se reutiliza `static/js/autosave.js` y `templates/components/autosave_status.html`. El CSS comun del estado de autosave se movio a `static/mobile.css` para evitar copiar estilos por modulo.

Concurrencia:

- `valoracion_visita_observaciones` usa su `updated_at` real.
- `visitas` no tiene `updated_at` y no se migro el esquema; se usa un token equivalente calculado desde campos editables y expuesto bajo el contrato `updated_at`.

Smoke cubierto:

- render del contrato comun;
- persistencia y recarga de visita;
- conflicto 409 en visita;
- persistencia y conflicto 409 en observaciones de valoracion.

## Warnings

`audit_docs.py` conserva warnings historicos:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

## Rollback

Retirar endpoints `/visitas/{visita_id}/autosave` y `/visitas/{visita_id}/valoracion-observaciones/autosave`, atributos `data-autosave-*`, includes del componente en los tres templates y tests añadidos. El guardado manual queda intacto.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/autosave-patologias-visitas-1.md`.

## Decisiones humanas

No se requirio aprobacion humana. No se tocaron datos reales, esquema, backups, uploads, facturacion, autenticacion ni deploy.

## Proximos pasos

- Siguiente bloque recomendado dentro de subfase 1: `autosave-patologias-registros-1`, para registros interiores/exteriores.
- Siguiente bloque recomendado: `autosave-patologias-mapas-1`, para mapas y cuadrantes.
- Despues continuar con `autosave-crm-costes-1`.

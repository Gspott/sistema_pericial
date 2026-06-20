# Episode: Autosave Patologias Registros 1

## Fecha

2026-06-19


## Tarea

Implantacion reversible del rollout `AUTOSAVE-ROLLOUT-1` en la subfase
`autosave-patologias-registros-1`.

## Plan asociado

autosave-patologias-registros-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Extender `AUTOSAVE-STANDARD-1` a registros de patologias interiores y
exteriores ya persistidos, sin crear infraestructura nueva, sin migraciones y
con guardado manual intacto.

## Archivos modificados

- `app/main.py`
- `templates/editar_registro.html`
- `templates/editar_registro_exterior.html`
- `tests/smoke/test_autosave_patologias_registros.py`
- `docs/harness/PLANS/completed/autosave-patologias-registros-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- `.venv/bin/python -m pytest tests/smoke/test_autosave_patologias_registros.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Resultado

Implantado autosave en:

- Edicion de registros interiores: `templates/editar_registro.html`.
- Edicion de registros exteriores: `templates/editar_registro_exterior.html`.

Se reutiliza `static/js/autosave.js` y
`templates/components/autosave_status.html`.

Concurrencia:

- Las tablas `registros_patologias` y `registros_patologias_exteriores` no
  tienen `updated_at`.
- No se migro el esquema.
- Se usa un token equivalente calculado sobre campos editables y devuelto bajo
  el contrato estandar `updated_at`.

Smoke cubierto:

- Render del contrato comun de autosave.
- Persistencia y recarga en registro interior.
- Conflicto 409 en registro interior.
- Persistencia y recarga en registro exterior.
- Conflicto 409 en registro exterior.
- Presencia de estados/reintento/beforeunload desde el JS comun.

## Warnings

`audit_docs.py` conserva warnings historicos:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

## Rollback

Retirar endpoints `/patologias/registros/{registro_id}/autosave` y
`/patologias/registros-exteriores/{registro_id}/autosave`, retirar atributos
`data-autosave-*`, hidden `updated_at`, includes del componente visual en las
dos plantillas y retirar el smoke especifico. El guardado manual queda intacto.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/autosave-patologias-registros-1.md`.

## Decisiones humanas

No se requirio aprobacion humana. No se tocaron datos reales, bases SQLite,
esquema, backups, uploads, fotos, CRM, costes, propuestas, estancias ni
mapas/cuadrantes.

## Proximos pasos

- Mantener mapas/cuadrantes fuera de este paquete y abrir
  `autosave-patologias-mapas-1` si se decide abordar ese flujo.
- Continuar el rollout posterior con `autosave-crm-costes-1` cuando proceda.

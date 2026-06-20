# Episode: Autosave Estancias Cuadrantes 1

## Fecha

2026-06-19


## Tarea

Implantacion reversible del rollout `AUTOSAVE-ROLLOUT-1` en la subfase
`autosave-estancias-cuadrantes-1`.

## Plan asociado

autosave-estancias-cuadrantes-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/bugfix.md`

## Objetivo

Extender `AUTOSAVE-STANDARD-1` a la edicion de estancias y cuadrantes de mapa
de patologias ya persistidos, sin reimplementar infraestructura comun, sin
migraciones y con guardado manual intacto.

## Archivos modificados

- `app/main.py`
- `templates/editar_estancia.html`
- `templates/editar_cuadrante_mapa_patologia.html`
- `tests/smoke/test_autosave_estancias_cuadrantes.py`
- `docs/harness/PLANS/completed/autosave-estancias-cuadrantes-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- `.venv/bin/python -m pytest tests/smoke/test_autosave_estancias_cuadrantes.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_autosave_estancias_cuadrantes.py tests/smoke/test_autosave_patologias_registros.py tests/smoke/test_valoracion_nueva_visita_ux.py -q -k "autosave or visita"`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Resultado

Implantado autosave en:

- Edicion de estancias: `templates/editar_estancia.html`.
- Edicion de cuadrantes de mapa de patologias:
  `templates/editar_cuadrante_mapa_patologia.html`.

Se reutiliza `static/js/autosave.js` y
`templates/components/autosave_status.html`.

Concurrencia:

- `estancias` y `cuadrantes_mapa_patologia` no tienen `updated_at`.
- No se migro el esquema.
- Se usa token equivalente calculado desde campos editables y devuelto bajo el
  contrato estandar `updated_at`.

Queda fuera:

- `definir_estancias.html`, porque gestiona altas/listados sin editor largo por
  entidad persistida.
- `editar_mapa_patologia.html`, porque mezcla texto con filas/columnas e imagen
  base; requiere plan especifico si se separa edicion textual de estructural.
- Fotos, borrados de fotos e imagen base.

Smoke cubierto:

- Render del contrato comun en estancia y cuadrante.
- Persistencia y recarga en estancia.
- Conflicto 409 en estancia.
- Persistencia y recarga en cuadrante.
- Conflicto 409 en cuadrante.
- Regresion proporcional de autosave de visitas y patologias.

## Warnings

`audit_docs.py` conserva warnings historicos:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

## Rollback

Retirar endpoints `/estancias/{estancia_id}/autosave` y
`/mapas-patologia/cuadrantes/{cuadrante_id}/autosave`, retirar atributos
`data-autosave-*`, hidden `updated_at`, includes del componente visual en las
dos plantillas y retirar el smoke especifico. El guardado manual queda intacto.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/autosave-estancias-cuadrantes-1.md`.

## Decisiones humanas

No se requirio aprobacion humana. No se tocaron datos reales, bases SQLite,
esquema, backups, uploads, fotos, CRM, costes, propuestas, facturacion ni
deploy.

## Proximos pasos

- Abrir plan independiente si se quiere autosave textual para
  `editar_mapa_patologia.html` separando campos estructurales.
- Continuar el rollout posterior con `autosave-crm-costes-1` cuando proceda.

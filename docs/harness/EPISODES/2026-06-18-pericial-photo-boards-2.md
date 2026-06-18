# Episode: Pericial Photo Boards 2

## Fecha

2026-06-18


## Tarea

PERICIAL-PHOTO-BOARDS-2

## Plan asociado

pericial-photo-boards-2.md


## Task Pack usado

`informe_change`

## Objetivo

Convertir las laminas fotograficas V1 en una herramienta editorial: pies
editables, observaciones, layouts canonicos V2, ordenacion interna de fotos y
render PDF mas profesional.

## Archivos modificados

- `app/database.py`
- `app/main.py`
- `templates/informe_v2_editor.html`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-photo-boards-2.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-photo-boards-2.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 78 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 267 passed.

## Resultado

- Se añade migracion idempotente `observacion` a
  `informe_v2_lamina_fotos`.
- Se mantienen `subtitulo`, `layout`, `pie_foto` como columnas idempotentes
  para compatibilidad con bases existentes.
- Los layouts canonicos V2 son `comparativa_2`, `comparativa_4`,
  `antes_despues` y `cronologica`.
- Los layouts V1 `dos_fotos` y `cuatro_fotos` se normalizan como aliases para
  no romper laminas existentes.
- El editor permite editar titulo, subtitulo y layout de la lamina.
- Cada foto de lamina permite editar pie libre y observacion.
- Cada foto puede subirse o bajarse dentro de la lamina.
- El PDF renderiza `LAMINA COMPARATIVA Nº n`, subtitulo, `Figura n`,
  observacion y etiquetas de antes/despues o secuencia cronologica.
- Las fotos originales no se modifican y el pipeline de optimizacion/paginacion
  sigue siendo el existente.

## Warnings

La V2 no implementa drag-and-drop, referencias cruzadas finales ni exportacion
independiente. La seleccion de fuentes fotograficas sigue limitada a
`visita_fotos`.

## Rollback

Revertir columna `observacion`, helpers/rutas de edicion de laminas/fotos,
cambios de UI/PDF y smoke tests asociados. Las fotos originales quedan intactas.

## Memoria actualizada

Metricas actualizadas por `finish_harness_task.sh` y plan cerrado en
`docs/harness/PLANS/completed/pericial-photo-boards-2.md`.

## Decisiones humanas

No requeridas. Se mantiene el bloque tras Anexo B para no ocupar Anexo D, que
ya pertenece a valoracion economica detallada.

## Proximos pasos

Futuras fases pueden añadir drag-and-drop, seleccion desde otras fuentes de
foto, referencias cruzadas reales y exportacion independiente de laminas.

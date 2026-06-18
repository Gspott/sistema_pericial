# Episode: Pericial Photo Boards 1

## Fecha

2026-06-18


## Tarea

PERICIAL-PHOTO-BOARDS-1

## Plan asociado

pericial-photo-boards-1.md


## Task Pack usado

`informe_change`

## Objetivo

Permitir crear laminas fotograficas comparativas para Informe V2 y renderizarlas
en el PDF sin modificar fotografias originales ni alterar los anexos B/C
existentes.

## Archivos modificados

- `app/database.py`
- `app/main.py`
- `templates/informe_v2_editor.html`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-photo-boards-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-photo-boards-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 73 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 262 passed.

## Resultado

- Se crean dos tablas minimas:
  `informe_v2_laminas_fotograficas` e `informe_v2_lamina_fotos`.
- El editor Informe V2 muestra el bloque `Laminas comparativas`, permite crear
  composiciones de 2 fotos, 4 fotos, antes/despues o cronologicas, y permite
  reordenar/eliminar laminas.
- Las laminas se insertan en el PDF como bloque fotografico posterior al Anexo
  B, con titulo, subtitulo opcional, fotos proporcionadas y pies individuales.
- Las fotos se pasan con contrato `archivo` + `url`, por lo que los perfiles
  optimizados reutilizan el pipeline existente de imagenes temporales.
- El Anexo C y los anexos D/E/F mantienen su numeracion y flujo actuales.

## Warnings

La V1 solo permite seleccionar fotografias de `visita_fotos`. No incorpora aun
fotos de fichas de estancia o patologias que no esten normalizadas en esa tabla.
No se implementa edicion avanzada de pies ni drag-and-drop.

## Rollback

Retirar tablas/helpers/rutas de laminas, eliminar el bloque del editor y la
seccion PDF posterior al Anexo B. No hay cambios sobre fotografias originales.

## Memoria actualizada

Metricas actualizadas mediante `python3 scripts/harness_metrics.py` y plan
cerrado en `docs/harness/PLANS/completed/pericial-photo-boards-1.md`.

## Decisiones humanas

No requeridas. Se elige insertar las laminas despues del Anexo B en lugar de
crear un Anexo D nuevo porque el Anexo D ya esta ocupado por valoracion
economica detallada.

## Proximos pasos

Futuras fases pueden añadir edicion completa de pies, seleccion desde otras
fuentes fotograficas estructuradas y miniaturas de previsualizacion.

# Episode: Pericial Annex A Profile 1

## Fecha

2026-06-18

## Tarea

PERICIAL-ANNEX-A-PROFILE-1

## Plan asociado

pericial-annex-a-profile-1.md

## Task Pack usado

`informe_change`

## Objetivo

Convertir el Anexo A documental del Informe V2 en un bloque estructurado con
indice documental y ficha previa para cada PDF externo incorporado.

## Archivos modificados

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-annex-a-profile-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-annex-a-profile-1.md`

## Resultado

La fusion del Anexo A genera ahora:

- Indice documental previo a los PDFs externos.
- Numeracion estable `A.1`, `A.2`, etc. segun el orden de fusion actual.
- Ficha documental previa a cada PDF.
- Metadatos visibles: nombre, tipo/categoria, paginas, tamano, fecha,
  descripcion y observaciones cuando existen.

La estructura de metadatos deja preparados `pagina_inicio_final` y
`pagina_fin_final`, sin calcularlos todavia.

Si un PDF externo no puede leerse, la ficha se genera igualmente y el numero de
paginas aparece como `No disponible`. Los PDFs originales no se modifican.

## UI

El editor Informe V2 muestra un resumen no bloqueante:

`Anexo A documental: n documentos · n paginas · n MB`

## Tests añadidos/reforzados

- Generacion de indice documental.
- Numeracion `A.1`, `A.2`.
- Ficha previa de documento.
- Original PDF no modificado.
- Documento corrupto/ausente no rompe la fusion.
- Endpoint PDF conserva paginacion final tras indice/fichas.
- Diagnostico de peso sigue funcionando.

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 69 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 258 passed.

## Warnings

No se valido contra el expediente real `019-26`, porque requiere acceso a
DB/uploads reales. La validacion se realizo con documentos sinteticos de una y
varias paginas, incluyendo PDF corrupto.

## Rollback

Revertir helpers de indice/ficha documental, cambios en fusion del Anexo A,
resumen de editor y smoke tests asociados. No hay migraciones ni cambios en
uploads.

## Decisiones humanas

No requeridas. No se modifica PDF original, DOCX, CRM ni esquema DB.

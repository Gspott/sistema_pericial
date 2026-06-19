# Episode: Pericial Pdf V2 Document Order 1

## Fecha

2026-06-18


## Tarea

PERICIAL-PDF-V2-DOCUMENT-ORDER-1

## Plan asociado

pericial-pdf-v2-document-order-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/informe_change.md`

## Objetivo

Separar en el PDF V2 master los anexos técnicos de la documentación aportada
por terceros. La documentación aportada deja de ser `Anexo A` y pasa a un
bloque final independiente con relación documental y portadillas `Documento n`.

## Archivos modificados

- `templates/informes/v2_pdf.html`
- `app/main.py`
- `app/services/informe.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-v2-document-order-1.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-v2-document-order-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `bash scripts/start_harness_task.sh PERICIAL-PDF-V2-DOCUMENT-ORDER-1 docs/harness/TASK_PACKS/informe_change.md`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2_anexo_a_genera_indice_y_ficha_documental or pdf_v2_fusiona_conclusiones_y_renderiza_anexos_derivados"`

## Resultado

El informe PDF V2 renderiza ahora los anexos técnicos como:

- Anexo A. Reportaje fotográfico
- Anexo B. Fichas de daños por estancia
- Anexo C. Valoración económica detallada
- Anexo D. Análisis de ejecución de la partida nº 4
- Anexo E. Justificación de mediciones

La documentación aportada se renderiza al final como
`DOCUMENTACIÓN APORTADA AL EXPEDIENTE`, con portadilla, relación documental y
documentos numerados como `Documento 1`, `Documento 2`, etc.

La fusión con `pypdf` deja de insertar los documentos aportados antes del
reportaje fotográfico y los añade al final del master, conservando los PDFs
externos sin modificar. El PDF de mediciones se sigue insertando en el punto
técnico correspondiente, ahora `E.4`.

## Warnings

`audit_docs.py` mantiene warnings históricos del repositorio sobre
`app/main.py` monolítico y planes completados antiguos sin contenido real.
No se han introducido warnings nuevos asociados a esta tarea.

## Rollback

Revertir los cambios en la plantilla PDF V2, los helpers de fusión/renderizado,
la segunda pasada de índice y los tests smoke adaptados.

## Memoria actualizada

No aplica fuera de la documentación harness y métricas generadas por el cierre
normal.

## Decisiones humanas

Solicitud directa del usuario. No se reescribió contenido manual guardado por
el usuario aunque contenga referencias antiguas `E.*` o `F.*`; solo se
actualizaron referencias automáticas generadas por el sistema.

## Proximos pasos

Revisión visual local de un `perfil=master` con documentos aportados y PDF de
mediciones para confirmar saltos de página y orden final en un caso real de
prueba.

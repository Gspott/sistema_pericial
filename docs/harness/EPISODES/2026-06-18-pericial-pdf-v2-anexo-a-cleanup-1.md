# Episode: Pericial Pdf V2 Anexo A Cleanup 1

## Fecha

2026-06-18


## Tarea

Correccion funcional de numeracion y duplicidad de la documentacion aportada
en Anexo A del PDF V2.

## Plan asociado

pericial-pdf-v2-anexo-a-cleanup-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/informe_change.md`

## Objetivo

La relacion documental debe ser una introduccion sin numeracion, los documentos
aportados reales deben empezar en A.1 y no debe insertarse una segunda tabla o
listado documental durante la fusion de PDFs externos.

## Archivos modificados

- `templates/informes/v2_pdf.html`
- `app/main.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-v2-anexo-a-cleanup-1.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2_master_con_anexo_pequeno_responde or pdf_v2_integra_anexo_a_como_portadilla_mas_documento or pdf_v2_fusion_integrada_usa_ruta_optimizada_si_procede"`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-upgrade a `full`)

## Resultado

Implementado. El HTML del Anexo A muestra `Relación de documentación aportada`
sin prefijo A.1. La numeracion inicial de documentos pasa de `len + 2` a
`len + 1`, por lo que el primer documento real es A.1. La fusion integrada deja
de insertar `generar_paginas_indice_anexo_a_v2()`, eliminando la tabla/listado
duplicado posterior.

## Warnings

`audit_docs.py` mantiene warnings historicos sobre planes completados sin
contenido real y monolito `app/main.py`; no son introducidos por esta tarea.
La funcion de indice ReportLab queda disponible para compatibilidad interna,
pero ya no se inserta en la fusion integrada del PDF final.

## Rollback

Revertir cambios en plantilla, numeracion/fusion de Anexo A, tests, plan/episodio
y metrica de esta tarea.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/` y metrica de planes completados
incrementada por el runner.

## Decisiones humanas

Solicitud humana directa: la relacion documental no consume numeracion y no
debe haber tabla/listado repetido.

## Proximos pasos

Revision manual de PDF V2 `master` con varios documentos PDF externos para
confirmar visualmente la secuencia A.1, A.2, A.3.

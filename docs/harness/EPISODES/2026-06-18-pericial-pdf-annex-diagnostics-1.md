# Episode: Pericial Pdf Annex Diagnostics 1

## Fecha

2026-06-18

## Tarea

PERICIAL-PDF-ANNEX-DIAGNOSTICS-1

## Plan asociado

pericial-pdf-annex-diagnostics-1.md

## Task Pack usado

`informe_change`

## Objetivo

Mostrar en el editor Informe V2 un diagnostico claro del peso estimado del PDF
final, diferenciando cuerpo principal, Anexo A, Anexo F, otros anexos y total.

## Archivos modificados

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-annex-diagnostics-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-annex-diagnostics-1.md`

## Resultado

El helper `diagnosticar_peso_anexos_pdf_v2()` devuelve ahora:

- `nivel`: verde, amarillo o rojo.
- `anexos_pesados`.
- `avisos`.
- Aviso para total estimado superior a 20 MB.
- Aviso para anexos individuales de mas de 10 MB.
- Aviso cuando Anexo A representa mas del 70 % del peso estimado.

El editor Informe V2 muestra un bloque compacto `Peso estimado del PDF` dentro
de `Exportar PDF`, con desglose de informe principal, Anexo A, Anexo F, otros
anexos y total estimado.

El bloque mantiene la exportacion no bloqueante y muestra texto orientativo:
Email/Judicial puede intentar comprimir anexos externos con Ghostscript, pero
los escaneos pesados pueden seguir ocupando mucho.

## Tests añadidos/reforzados

- El helper devuelve desglose estable.
- El editor muestra `Peso estimado del PDF`.
- El editor muestra aviso con anexo individual > 10 MB.
- El editor muestra aviso con total > 20 MB.
- El editor no rompe si no hay anexos.
- El endpoint PDF sigue cubierto por smoke de workbench.

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 68 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 257 passed.

## Warnings

No se valido contra el expediente real `019-26`, porque requiere acceso a
DB/uploads reales. La mejora usa datos sinteticos en smoke tests.

## Rollback

Revertir el enriquecimiento de `diagnosticar_peso_anexos_pdf_v2()`, el bloque
del editor y los smoke tests asociados. No hay migraciones ni datos persistentes
nuevos.

## Decisiones humanas

No requeridas. No se modifica PDF, DOCX, CRM ni esquema de base de datos.

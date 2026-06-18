# Episode: Pericial Pdf V2 Design 4

## Fecha

2026-06-18


## Tarea

Refinamiento sobrio del PDF V2: portada, Anexo A y pie profesional sin
branding de Sistema Pericial.

## Plan asociado

pericial-pdf-v2-design-4.md


## Task Pack usado

`docs/harness/TASK_PACKS/informe_change.md`

## Objetivo

Mejorar la percepcion profesional del documento emitido por el perito, incorporar
los datos profesionales solicitados, eliminar duplicidad de expediente en el pie
y simplificar metadatos internos del Anexo A.

## Archivos modificados

- `templates/informes/v2_pdf.html`
- `app/services/informe.py`
- `app/main.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-v2-design-4.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2_endpoint_solo_informe_devuelve_pdf_paginado or pdf_v2_master_con_anexo_pequeno_responde"`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-upgrade a `full`)

## Resultado

Implementado. La portada usa mas aire y datos profesionales fijos de Carlos
Blanco, Arquitecto Tecnico, Colegiado nº 5866. El pie de Playwright no duplica
expediente: izquierda datos profesionales, derecha expediente una sola vez. Las
portadillas generadas del Anexo A eliminan paginas, tamano, fecha de
incorporacion y categoria, manteniendo numero, nombre, descripcion/observaciones
y estado de incorporacion. La relacion documental HTML del Anexo A queda mas
limpia.

## Warnings

`audit_docs.py` mantiene warnings historicos sobre planes completados sin
contenido real y monolito `app/main.py`; no son introducidos por esta tarea.
La paginacion final sigue siendo el overlay existente, por lo que la revision
visual manual continua recomendada.

## Rollback

Revertir cambios en plantilla, servicio, portadillas, test, plan/episodio y
metrica de esta tarea. No hay migraciones ni dependencias nuevas.

## Memoria actualizada

Plan cerrado en `docs/harness/PLANS/completed/` y metrica de planes completados
incrementada por el runner.

## Decisiones humanas

Solicitud humana directa de no introducir branding de Sistema Pericial y usar
datos profesionales concretos del perito.

## Proximos pasos

Generar y revisar visualmente PDF V2 `solo_informe` y `master` con anexos A
externos de prueba para confirmar portada, portadillas y pie final.

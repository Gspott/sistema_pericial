# Episode: Costes Ive 1E Diagnostico

## Fecha

2026-06-06


## Tarea

Implementar COSTES-IVE-1E diagnóstico.

## Plan asociado

costes-ive-1e-diagnostico.md


## Task Pack usado

`docs/harness/TASK_PACKS/app_change.md`

## Objetivo

Seguir el ciclo de vida de `MOOA12a` desde texto OCR hasta parser, JSON guardado, contexto GET y template de revisión.

## Archivos modificados

- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/completed/costes-ive-1e-diagnostico.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1e-diagnostico.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh` ejecutó smoke completo: 126 passed.

## Resultado

Con el OCR exacto indicado, el ciclo completo conserva `MOOA12a`:

- Parser: `datos_parseados["descompuestos"]` contiene `MOOA12a` y `%`.
- JSON guardado en captura: `datos_extraidos_json.datos_parseados.descompuestos` contiene ambos.
- Contexto GET revisión: `descompuestos_sugeridos` contiene ambos.
- HTML renderizado: aparecen `MOOA12a`, `Peón ordinario construcción` y `Costes directos complementarios`.

No se reproduce la desaparición con ese texto exacto. Causa probable en uso real: JSON antiguo, captura no reextraída o texto OCR real distinto del supuesto.

## Warnings

No se modifica OCR ni parser porque no se reproduce descarte con el texto OCR indicado.

## Rollback

Revertir test y documentos harness.

## Memoria actualizada

No se actualiza memoria global.

## Decisiones humanas

No requeridas.

## Proximos pasos

Comparativa de partida de proyecto vs IVE.

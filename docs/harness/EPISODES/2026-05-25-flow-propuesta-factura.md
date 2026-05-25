# Episode: Flow Propuesta Factura

## Fecha

2026-05-25

## Tarea

Smoke flow propuesta aceptada -> factura borrador.

## Plan asociado

flow-propuesta-factura.md

## Task Pack usado

facturacion_change

## Objetivo

Validar con SQLite temporal que una propuesta demo con lineas puede pasar a
estado aceptada y generar una factura borrador vinculada, sin emision fiscal,
Verifactu, SMTP, numeracion real ni datos reales.

## Archivos modificados

- `tests/smoke/test_flow_propuesta_factura.py`
- `docs/harness/PLANS/completed/flow-propuesta-factura.md`
- `docs/harness/STATE/recent_changes.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-05-25-flow-propuesta-factura.md`

## Validaciones ejecutadas

- `.venv/bin/python -m pytest tests/smoke/test_flow_propuesta_factura.py -q`
- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `python3 -m compileall tests`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Resultado

Test aislado creado y validado. La validacion completa del harness paso, conto
21 smoke tests y cerro el plan activo automaticamente.

## Warnings

El flujo replica la logica segura de creacion de borrador con helpers internos,
pero no llama a la ruta HTTP porque requiere contexto de autenticacion y
redireccion.

## Rollback

Eliminar el test nuevo y revertir las entradas documentales de memoria/episodio.

## Memoria actualizada

- `docs/harness/STATE/recent_changes.md`
- `docs/harness/METRICS.md`
- Episodio actual.

## Decisiones humanas

No se ha solicitado tocar numeracion fiscal, emision, Verifactu ni SMTP.

## Proximos pasos

Mantener fuera de este smoke la emision fiscal real y cubrirla solo con pack
especifico y aprobacion humana.

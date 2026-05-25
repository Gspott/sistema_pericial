# Episode: Main Vs Routers Audit

## Fecha

2026-05-25

## Tarea

Auditoria solo lectura de duplicidad entre `app/main.py` y routers no incluidos.

## Plan asociado

No se creo plan activo porque la tarea original fue auditoria solo lectura.

## Task Pack usado

safe_refactor como referencia conceptual; no se hicieron cambios de codigo.

## Objetivo

Persistir el hallazgo de que `expedientes.py`, `visitas.py`, `estancias.py` y
`patologias.py` no estan listos para `include_router()` y deben tratarse como
extraccion parcial/legacy.

## Archivos modificados

- `docs/harness/AGENT_MAPS/main_vs_routers_map.md`
- `docs/harness/AGENT_MAPS/route_map.md`
- `docs/harness/FAILURES/routers_not_included_legacy.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/BACKLOG/low.md`
- `docs/harness/STATE/known_risks.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-05-25-main-vs-routers-audit.md`

## Validaciones ejecutadas

- Pendiente de cierre: `python3 scripts/audit_docs.py`
- Pendiente de cierre: `bash scripts/validate_harness.sh`
- Pendiente de cierre: `git diff --check`
- Pendiente de cierre: `git status --short`

## Resultado

Se registra mapa operativo y failure para impedir activacion accidental de
routers legacy.

## Warnings

Los routers legacy pueden contener informacion util para refactor gradual, pero
no son fuente funcional actual.

## Rollback

Revertir solo los documentos de harness creados o actualizados en esta tarea.

## Memoria actualizada

- Agent maps.
- Failure registry.
- Backlog.
- Known risks.
- Metricas.

## Decisiones humanas

Pendiente decidir estrategia de extraccion o archivo historico tras mapa ruta a
ruta completo.

## Proximos pasos

Crear smoke de ownership expedientes/visitas antes de cualquier extraccion.

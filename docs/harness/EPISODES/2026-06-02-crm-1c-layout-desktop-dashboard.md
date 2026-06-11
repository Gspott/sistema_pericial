# Episode: Crm 1C Layout Desktop Dashboard

## Fecha

2026-06-02


## Tarea

Ajustar solo el layout visual desktop del dashboard CRM para que deje de
aparecer como columna estrecha y use una composicion tipo cockpit.

## Plan asociado

crm-1c-layout-desktop-dashboard.md


## Task Pack usado

`docs/harness/TASK_PACKS/mobile_ui.md`

## Objetivo

Dar anchura real desktop al dashboard, con cabecera/filtros/KPIs a ancho
completo, zona principal para Hoy/Actividad/Captacion y lateral para
Comunicacion/Campanas/Pipeline, manteniendo movil en una columna.

## Archivos modificados

- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/completed/crm-1c-layout-desktop-dashboard.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
  - Auto-upgrade a scope `full`.
  - `92 passed`.

## Resultado

Completado. Se anadieron clases de layout a las secciones del dashboard y CSS
scoped `.dashboard-*` para una rejilla desktop de 12 columnas entre 1280-1440px
aprox., sin modificar logica Python, consultas, rutas ni esquema.

## Warnings

- Warning informativo existente: `app/main.py` supera el umbral de monolito.
- No se hizo QA visual con navegador en esta fase.

## Rollback

Revertir `templates/dashboard.html`, `static/mobile.css` y
`tests/smoke/test_dashboard_crm.py`. No hay cambios de datos ni rutas.

## Memoria actualizada

- Plan completado en `docs/harness/PLANS/completed/`.
- Backlog CRM actualizado en `docs/harness/BACKLOG/high.md`.
- Metricas recalculadas por `scripts/harness_metrics.py`.

## Decisiones humanas

La fase queda limitada a layout visual. El modelo defensivo con tablas se
mantiene aplazado como CRM-1D candidato o fase futura.

## Proximos pasos

QA visual manual o con navegador cuando se disponga de Browser/plugin expuesto.
No avanzar a esquema CRM sin fase y aprobacion separadas.

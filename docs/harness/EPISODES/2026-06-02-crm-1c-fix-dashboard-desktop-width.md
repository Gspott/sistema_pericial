# Episode: Crm 1C Fix Dashboard Desktop Width

## Fecha

2026-06-02


## Tarea

Corregir que `/dashboard` siguiera renderizando como columna estrecha tras
CRM-1C.

## Plan asociado

crm-1c-fix-dashboard-desktop-width.md


## Task Pack usado

`docs/harness/TASK_PACKS/mobile_ui.md`

## Objetivo

Aplicar un selector especifico de pagina y un override real contra el ancho
global `.page`, manteniendo movil apilado y sin tocar logica Python.

## Archivos modificados

- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/completed/crm-1c-fix-dashboard-desktop-width.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
  - Auto-upgrade a scope `full`.
  - `93 passed`.

## Resultado

Completado. El dashboard ahora declara `body.dashboard-cockpit-page`, carga
`/static/mobile.css?v=11` para evitar CSS cacheado y aplica reglas especificas
`body.dashboard-cockpit-page .dashboard-cockpit` con ancho desktop y minimo de
1200px cuando la pantalla lo permite.

## Warnings

- No se pudo validar con captura/navegador: los Python disponibles fuera del
  harness no tienen `uvicorn` para levantar servidor temporal sin instalar
  dependencias.
- Warning informativo existente: `app/main.py` supera el umbral de monolito.

## Rollback

Revertir `templates/dashboard.html`, `static/mobile.css` y
`tests/smoke/test_dashboard_crm.py`. No hay cambios de datos, rutas ni esquema.

## Memoria actualizada

- Plan completado en `docs/harness/PLANS/completed/`.
- Backlog CRM actualizado en `docs/harness/BACKLOG/high.md`.
- Metricas recalculadas por `scripts/harness_metrics.py`.

## Decisiones humanas

La correccion queda limitada a CSS/template/smoke. No se toca service worker ni
versiones PWA globales; solo el querystring del CSS en el dashboard.

## Proximos pasos

Revisar visualmente en navegador local. Si persiste estrecho, inspeccionar
reglas computadas de `.app-content`, `.page` y `.dashboard-cockpit` en DevTools.

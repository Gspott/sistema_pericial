# Episode: Crm 1C Fix 2 Dashboard Width Diagnosis

## Fecha

2026-06-02


## Tarea

CRM-1C-FIX-2: diagnosticar por que `/dashboard` seguia estrecho y corregir el contenedor real que limitaba el ancho, sin tocar logica Python, rutas, consultas, datos ni esquema.

## Plan asociado

crm-1c-fix-2-dashboard-width-diagnosis.md


## Task Pack usado

`docs/harness/TASK_PACKS/mobile_ui.md`

## Objetivo

Permitir que el dashboard CRM use ancho desktop real, 1200-1440px cuando la pantalla lo permite, manteniendo el apilado movil y acotando los overrides a `body.dashboard-cockpit-page`.

## Archivos modificados

- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/completed/crm-1c-fix-2-dashboard-width-diagnosis.md`
- `docs/harness/EPISODES/2026-06-02-crm-1c-fix-2-dashboard-width-diagnosis.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `rg -n "max-width|width:|margin: 0 auto|margin-left: auto|margin-right: auto|\\.page|\\.container|\\.app-content|main|section" templates/dashboard.html templates/partials/_app_shell_start.html templates/partials/_app_shell_end.html static/mobile.css`
- `python3 -m compileall tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app` (auto-upgrade a full; 93 smokes OK)

## Resultado

Completado. El selector global limitante era `.page { width: 100%; max-width: 920px; margin: 0 auto; }`. Se corrigio la estructura semantica del dashboard para no anidar un `<main class="page ...">` dentro del `<main class="app-content">` del shell y se reemplazo por `<div class="page dashboard-page dashboard-cockpit">`.

Se anadio un override especifico sobre la ruta real `body.dashboard-cockpit-page .app-shell > .app-content > .dashboard-cockpit.page`, con `max-width: 1440px !important` en desktop y `min-width: 1200px` desde 1492px de viewport. El smoke comprueba la clase de pagina, la estructura `div`, la ausencia del `main` anidado y el selector CSS especifico.

## Warnings

`python3 -m pytest tests/smoke/test_dashboard_crm.py` no pudo ejecutarse directamente porque el Python de shell no tiene `pytest` instalado. El harness canonico si ejecuto los smokes con exito.

`audit_docs` mantiene warning informativo existente: `app/main.py` supera el umbral de lineas.

## Rollback

Revertir los cambios de `templates/dashboard.html`, `static/mobile.css`, `tests/smoke/test_dashboard_crm.py` y la documentacion harness de esta fase.

## Memoria actualizada

Plan completado, episodio registrado, metricas actualizadas por harness y backlog de dashboard actualizado.

## Decisiones humanas

No requeridas.

## Proximos pasos

QA visual manual/navegador en `/dashboard` sobre escritorio real si el entorno local de ejecucion del usuario esta levantado.

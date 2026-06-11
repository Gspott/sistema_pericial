# Episode: Crm 1A Dashboard Readonly

## Fecha

2026-06-02


## Tarea

Implementar CRM-1A como cockpit desktop read-only en `/dashboard`, reutilizando
datos existentes y sin abrir nuevas entidades CRM.

## Plan asociado

crm-1a-dashboard-readonly.md


## Task Pack usado

`docs/harness/TASK_PACKS/mobile_ui.md`

## Objetivo

Responder "que necesita hacer hoy el despacho" con secciones Hoy, Captacion,
Comunicacion, Pipeline y Administracion secundaria.

## Archivos modificados

- `app/routers/dashboard.py`
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/completed/crm-1a-dashboard-readonly.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `node --check` de `static/app_shell.js`, `static/pwa.js` y `static/sw.js`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
  - Auto-upgrade a scope `full`.
  - `92 passed`.

## Resultado

Completado. El dashboard muestra un cockpit SSR read-only con tareas de lead,
seguimientos proximos, leads recientes, propuestas pendientes, emails enviados,
pipeline defensivo por estados existentes y administracion secundaria.

## Warnings

- Warning informativo existente: `app/main.py` supera el umbral de monolito.
- No se hizo QA visual con navegador en esta fase.

## Rollback

Revertir `app/routers/dashboard.py`, `templates/dashboard.html`,
`static/mobile.css` y `tests/smoke/test_dashboard_crm.py`. No hay migracion ni
datos persistidos que revertir.

## Memoria actualizada

- Plan completado en `docs/harness/PLANS/completed/`.
- Backlog CRM actualizado en `docs/harness/BACKLOG/high.md`.
- Metricas recalculadas por `scripts/harness_metrics.py`.

## Decisiones humanas

No hizo falta aprobacion adicional: fase read-only, sin esquema, sin SMTP real,
sin integraciones externas y sin tocar datos reales.

## Proximos pasos

CRM-1B queda como fase separada para modelo defensivo si se aprueba. CRM-2/3
deben seguir sin SMTP real ni integraciones externas hasta plan especifico.

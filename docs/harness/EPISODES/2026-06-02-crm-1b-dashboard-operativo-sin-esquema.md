# Episode: Crm 1B Dashboard Operativo Sin Esquema

## Fecha

2026-06-02


## Tarea

Implementar CRM-1B como evolucion operativa del dashboard CRM sin crear
esquema nuevo.

## Plan asociado

crm-1b-dashboard-operativo-sin-esquema.md


## Task Pack usado

`docs/harness/TASK_PACKS/mobile_ui.md`

## Objetivo

Anadir navegacion segura, filtros simples, estados visuales, acciones ya
soportadas y bloque de campanas/proximos pasos al cockpit desktop.

## Archivos modificados

- `app/routers/dashboard.py`
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/completed/crm-1b-dashboard-operativo-sin-esquema.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- `python3 -m compileall app tests`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
  - Auto-upgrade a scope `full`.
  - `92 passed`.
- `python3 scripts/audit_docs.py`

## Resultado

Completado. El dashboard permite filtrar por periodo/tipo/estado, navegar a
leads, propuestas, expedientes y clientes cuando existe ruta segura, enlazar
relaciones de emails enviados cuando apuntan a entidad existente, marcar tareas
de lead como hechas mediante el POST existente y preparar campanas manuales sin
crear entidad nueva.

## Warnings

- Warning informativo existente: `app/main.py` supera el umbral de monolito.
- La ruta de detalle de email no existe; los emails se muestran sin enlace
  propio y solo enlazan su entidad relacionada si existe referencia.
- No se hizo QA visual con navegador en esta fase.

## Rollback

Revertir `app/routers/dashboard.py`, `templates/dashboard.html`,
`static/mobile.css` y `tests/smoke/test_dashboard_crm.py`. No hay migracion ni
datos persistidos fuera de acciones de usuario existentes.

## Memoria actualizada

- Plan completado en `docs/harness/PLANS/completed/`.
- Backlog CRM actualizado en `docs/harness/BACKLOG/high.md`.
- Metricas recalculadas por `scripts/harness_metrics.py`.

## Decisiones humanas

La orden humana de CRM-1B priorizo dashboard operativo sin nuevo esquema. El
modelo defensivo con tablas queda aplazado como CRM-1C candidato o fase futura.

## Proximos pasos

Evaluar QA visual desktop/mobile del cockpit. Si se retoma modelo CRM propio,
abrir fase separada con task pack de DB y smoke sobre SQLite temporal.

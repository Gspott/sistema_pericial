# Episode: Desktop Expediente Detalle 1

## Fecha

2026-06-20


## Tarea

Implementar `desktop-expediente-detalle-1` como primera referencia aplicada de
`DESKTOP-WORKBENCH-STANDARD-1`.

## Plan asociado

desktop-expediente-detalle-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/documentation.md`

## Objetivo

Convertir `templates/detalle_expediente.html` en una vista desktop workbench a
partir de 1280px, manteniendo rutas, permisos, contexto backend, persistencia,
logica de negocio y comportamiento movil.

## Archivos modificados

- `templates/detalle_expediente.html`
- `tests/smoke/test_expediente_desktop_workbench.py`
- `docs/harness/PLANS/completed/desktop-expediente-detalle-1.md`
- `docs/harness/EPISODES/2026-06-20-desktop-expediente-detalle-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_expediente_desktop_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope docs` (auto-upgrade a `app` por template/test)

## Resultado

Se anadio una capa desktop responsive en `detalle_expediente.html`:

- `desktop-shell`;
- `desktop-toolbar`;
- `desktop-sidebar`;
- `desktop-main`;
- `desktop-inspector`;
- `desktop-panel`;
- `desktop-summary-grid`;
- `desktop-timeline`;
- `desktop-quick-actions`.

La capa se activa con `@media (min-width: 1280px)`. Las barras laterales y
acciones desktop permanecen ocultas fuera de ese breakpoint para preservar el
flujo mobile-first.

No se modifico `app/main.py`. La auditoria confirma que la ruta mantiene:

- `get_current_user(request)`;
- `get_owned_expediente(... current_user["id"])`;
- `require_row(...)`;
- mismo contexto y mismas dependencias existentes.

El smoke cubre render de clases desktop, acciones principales, expediente sin
datos opcionales y contenido SSR sin depender de JavaScript nuevo.

## Warnings

`audit_docs.py` conserva warnings historicos no introducidos por este paquete:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

## Rollback

Revertir `templates/detalle_expediente.html`, retirar el smoke nuevo y revertir
plan/episodio. No hay cambios backend, DB ni migraciones.

## Memoria actualizada

Plan activo documenta auditoria backend/template y matriz de contexto.
Plan cerrado en `docs/harness/PLANS/completed/desktop-expediente-detalle-1.md`.

## Decisiones humanas

No requerida aprobacion adicional. No se tocaron datos reales, backend,
facturacion, PDFs, emails, permisos ni persistencia.

## Proximos pasos

Siguiente paquete recomendado: `desktop-informe-v2-hardening-1` o una fase de
pulido visual medido de `desktop-expediente-detalle-1` con capturas Playwright
desktop/movil si se quiere validacion visual.

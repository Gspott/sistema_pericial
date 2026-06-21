# Episode: Desktop Workbench Qhd 1

## Fecha

2026-06-20


## Tarea

Incorporar soporte QHD (2560x1440) como resolucion de referencia de
productividad en `DESKTOP-WORKBENCH-STANDARD-1`.

## Plan asociado

desktop-workbench-qhd-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/harness_change.md`

## Objetivo

Documentar QHD como entorno principal de escritorio para trabajo postvisita y
de oficina, definir breakpoints desktop recomendados y revisar
`desktop-expediente-detalle-1` para evitar ancho desaprovechado en 2560x1440.

## Archivos modificados

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `templates/detalle_expediente.html`
- `tests/smoke/test_expediente_desktop_workbench.py`
- `docs/harness/PLANS/active/desktop-workbench-qhd-1.md`
- `docs/harness/EPISODES/2026-06-20-desktop-workbench-qhd-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest tests/smoke/test_expediente_desktop_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

## Resultado

Se consolido QHD como referencia principal:

- entorno desktop: 2560x1440, QHD, 16:9;
- uso principal: expedientes, informes, valoracion, costes, CRM, propuestas,
  facturacion, documentos, fotos, busqueda y dashboard;
- resoluciones minimas de validacion: 1280x800, 1366x768, 1440x900,
  1920x1080 y 2560x1440;
- reglas de aprovechamiento horizontal para >=1920px y >=2560px.

En `detalle_expediente.html` se conservaron rutas, contexto y funcionalidades.
Solo se anadieron breakpoints CSS desktop:

- >=1920px: shell hasta 1840px y paneles mas amplios;
- >=2560px: uso de casi todo el ancho disponible y columna central minima de
  1200px.

El smoke especifico comprueba que la template renderiza los breakpoints
1280px, 1920px y 2560px.

## Warnings

`audit_docs.py` mantiene warnings historicos no introducidos por esta fase:
monolito `app/main.py` y planes completados antiguos con secciones vacias.

## Rollback

Revertir los cambios en el estándar, guard transversal, template y smoke. No
hay cambios backend, DB, rutas, permisos ni persistencia.

## Memoria actualizada

Plan activo documenta diagnostico, archivos permitidos, validaciones y fuera de
alcance. Tras cierre, debe quedar como plan completado.

## Decisiones humanas

No requerida aprobacion adicional. La fase se mantuvo en documentacion y CSS
responsive desktop.

## Proximos pasos

Aplicar la matriz de resoluciones a futuros Desktop Workbench y, cuando sea
viable, complementar smokes SSR con capturas visuales Playwright en 1280,
1920 y 2560.

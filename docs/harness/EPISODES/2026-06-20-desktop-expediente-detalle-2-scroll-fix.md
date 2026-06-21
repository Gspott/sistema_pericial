# Episode: Desktop Expediente Detalle 2 Scroll Fix

## Fecha

2026-06-20


## Tarea

Implementar `desktop-expediente-detalle-2-scroll-fix`.

## Plan asociado

desktop-expediente-detalle-2-scroll-fix.md


## Task Pack usado

`docs/harness/TASK_PACKS/harness_change.md`

## Objetivo

Corregir el recorte del panel "Estructura del inmueble" en desktop/QHD sin
cambiar rutas, consultas, permisos, persistencia, logica de negocio ni mobile.

## Archivos modificados

- `templates/detalle_expediente.html`
- `tests/smoke/test_expediente_desktop_workbench.py`
- `docs/harness/PLANS/active/desktop-expediente-detalle-2-scroll-fix.md`
- `docs/harness/EPISODES/2026-06-20-desktop-expediente-detalle-2-scroll-fix.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest tests/smoke/test_expediente_desktop_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

## Resultado

La causa era la combinacion de sidebar sticky y arbol largo:

- `.desktop-sidebar` usaba `position: sticky` y `top: 82px`;
- no tenia `max-height`;
- no tenia `overflow-y`;
- si el arbol superaba el alto visible, el final podia quedar fuera de alcance.

Se mantuvo la sidebar sticky y se hizo scrollable solo en desktop:

- `align-self: start`;
- `max-height: calc(100vh - 106px)`;
- `overflow-y: auto`;
- `overscroll-behavior: contain`;
- `padding-right: 4px`.

El smoke verifica que siguen renderizando `.desktop-sidebar`,
`.desktop-panel`, "Estructura del inmueble", el caso sin estancias, y las reglas
de scroll interno.

## Warnings

Warnings historicos de `audit_docs.py` no introducidos por esta fase:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

No se pudo generar captura real: no hay Playwright Python, Playwright Node ni
Chrome/Chromium/Firefox headless disponibles en el entorno. Se hizo
comprobacion tecnica del contrato CSS por viewport.

## Rollback

Revertir las reglas CSS nuevas de `.desktop-sidebar`, las aserciones del smoke
y la documentacion harness de esta fase. No hay backend ni datos que revertir.

## Memoria actualizada

Plan activo documenta auditoria de propiedades `height`, `max-height`,
`overflow`, `position` y `align-self`, causa exacta y validacion por viewport.

## Decisiones humanas

No se requirio aprobacion adicional porque el cambio fue CSS desktop + smoke.

## Proximos pasos

Para sidebars futuras de Desktop Workbench, cualquier columna sticky que pueda
contener listas largas debe declarar desde el primer corte una estrategia de
scroll: sidebar scrollable o panel interno scrollable con `max-height`
documentado.

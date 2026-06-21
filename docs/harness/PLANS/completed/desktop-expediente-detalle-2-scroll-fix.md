# Desktop Expediente Detalle 2 Scroll Fix

# Objetivo

Corregir el recorte de la estructura de estancias en el Desktop Workbench de
detalle de expediente cuando la sidebar sticky contiene un arbol largo,
especialmente en QHD 2560x1440.

El cambio debe ser exclusivamente de layout/CSS y tests SSR de proteccion.

# Modulo

Expedientes / detalle de expediente.

Template afectado:

- `templates/detalle_expediente.html`

Smoke afectado:

- `tests/smoke/test_expediente_desktop_workbench.py`

# Riesgo

Bajo-medio. Pantalla central de expediente, pero el cambio se limita a CSS
desktop dentro de `@media (min-width: 1280px)`. No toca backend, rutas,
consultas, permisos ni persistencia.

# Archivos permitidos

- `templates/detalle_expediente.html`
- `tests/smoke/test_expediente_desktop_workbench.py`
- `docs/harness/PLANS/active/desktop-expediente-detalle-2-scroll-fix.md`
- `docs/harness/EPISODES/2026-06-20-desktop-expediente-detalle-2-scroll-fix.md`

# Archivos prohibidos

- `app/` salvo auditoria de lectura.
- Rutas, permisos, persistencia, consultas, BD y migraciones.
- PDFs, emails, datos reales, backups, uploads, informes generados, fotos y
  logs.
- Comportamiento movil y flujos mobile-first de visita.

# Playbook aplicable

Task Pack sugerido: `harness_change`.

Playbooks/patrones revisados:

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/css_mobile.md`
- `docs/ux.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest tests/smoke/test_expediente_desktop_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

# Rollback

Revertir las reglas CSS nuevas de `.desktop-sidebar` y las aserciones
adicionales del smoke. No hay datos ni backend que revertir.

# Fuera de alcance

- Cambios de logica de negocio.
- Cambios de rutas, permisos, persistencia o consultas.
- Nuevas metricas, queries, endpoints o JavaScript.
- Cambios en comportamiento movil.

# Aprobacion humana requerida

No requerida mientras se mantenga como CSS desktop y smoke SSR. Requerida si se
toca backend, datos, rutas, permisos, persistencia, PDF, email o BD.


# Auditoria layout

Propiedades revisadas:

- `.desktop-shell`: `max-width: 1680px` en >=1280px, `1840px` en >=1920px y
  `max-width: none` en >=2560px. No causa recorte vertical.
- `.desktop-sidebar`: `display: grid`, `align-content: start`,
  `position: sticky`, `top: 82px`; no tenia `max-height` ni `overflow-y`.
- `.desktop-inspector`: comparte sticky con sidebar, pero no contiene el arbol
  largo de estancias.
- `.desktop-panel`: no tenia height/max-height/overflow que recortase.
- `.desktop-room-panel`: solo `padding-bottom`, sin overflow propio.

Causa exacta:

La sidebar izquierda era sticky con `top: 82px` y podia ser mas alta que el
viewport. Al no tener altura maxima ni scroll interno, cuando el arbol de
estancias superaba la altura visible, la parte inferior podia quedar fuera del
area alcanzable mientras la columna permanecia pegada.

# Solucion aplicada

Se eligio Opcion A: mantener sidebar sticky pero scrollable.

Reglas aplicadas solo en desktop >=1280px:

- `align-self: start`;
- `max-height: calc(100vh - 106px)`;
- `overflow-y: auto`;
- `overscroll-behavior: contain`;
- `padding-right: 4px`.

El calculo usa el `top: 82px` existente y deja 24px de margen inferior visible.

# Validacion visual prevista

Comprobacion manual/tecnica en resoluciones objetivo:

- 1280x800.
- 1366x768.
- 1440x900.
- 1920x1080.
- 2560x1440.

Casos a revisar:

- expediente pequeno con pocas estancias;
- expediente medio con 10-20 estancias;
- expediente grande con muchas estancias por plantas.

Resultado esperado:

- el ultimo elemento del panel es alcanzable mediante scroll de sidebar;
- no hay contenido oculto por sticky;
- no hay scroll horizontal;
- el panel principal e inspector mantienen layout.

# Estado

Completado pendiente de validacion y cierre.

Estado: completado

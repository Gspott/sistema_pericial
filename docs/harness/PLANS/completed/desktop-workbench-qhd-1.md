# Desktop Workbench Qhd 1

# Objetivo

Incorporar 2560x1440 (QHD, 16:9) como resolucion de referencia principal para
productividad en `DESKTOP-WORKBENCH-STANDARD-1` y revisar la primera reference
implementation `desktop-expediente-detalle-1`.

El objetivo es normativo y de layout desktop: no cambia rutas, permisos,
persistencia, consultas ni comportamiento movil.

# Modulo

Harness / patrones desktop workbench.

Revision acotada de `templates/detalle_expediente.html`.

# Riesgo

Medio-bajo. El cambio principal es documental. El unico ajuste de UI es CSS
responsive scoped a `@media (min-width: 1920px)` y `@media (min-width: 2560px)`
en una template ya adaptada a desktop.

# Archivos permitidos

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `templates/detalle_expediente.html`
- `tests/smoke/test_expediente_desktop_workbench.py`
- `docs/harness/PLANS/active/desktop-workbench-qhd-1.md`
- `docs/harness/EPISODES/2026-06-20-desktop-workbench-qhd-1.md`

# Archivos prohibidos

- Bases SQLite reales, backups, uploads, informes generados, fotos y logs.
- Migraciones, PDFs, emails, secretos, service worker, facturacion fiscal,
  autenticacion y permisos.
- `app/` y rutas backend.
- Carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `harness_change`.

Playbooks/patrones revisados:

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/css_mobile.md`


# Validaciones

- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest tests/smoke/test_expediente_desktop_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios en el estándar, guard transversal, template y smoke. No hay
cambios de datos, backend ni persistencia.

# Fuera de alcance

- Logica de negocio.
- Rutas, permisos, consultas, persistencia o migraciones.
- BD, datos reales, PDFs, emails y facturacion.
- Redisenar el flujo movil o densificar pantallas de visita en campo.

# Aprobacion humana requerida

No requerida mientras se mantenga como documentación y CSS responsive desktop.
Requerida si se toca persistencia, permisos, facturacion, PDF, email, datos
reales o rutas backend.


# Diagnostico inicial

- El estándar desktop workbench no declaraba QHD como resolucion de referencia.
- `desktop-expediente-detalle-1` ya implementaba tres columnas desde 1280px.
- La template limitaba `.desktop-shell` a `max-width: 1680px`, suficiente para
  1920px pero estrecho para 2560x1440.
- No se detecto necesidad de tocar backend, rutas, permisos ni consultas.

# Cambios aplicados

- Documentado entorno de referencia 2560x1440 QHD.
- Documentados principios obligatorios para evitar ancho util desperdiciado.
- Documentadas resoluciones minimas de validacion y breakpoints recomendados.
- Reflejada la referencia QHD en `PROJECT-STANDARDS-GUARD-1`.
- Anandidos breakpoints CSS desktop para >=1920px y >=2560px en
  `detalle_expediente.html`.
- Actualizado smoke para comprobar presencia de los breakpoints QHD.

# Estado

Completado pendiente de validacion y cierre.

Estado: completado

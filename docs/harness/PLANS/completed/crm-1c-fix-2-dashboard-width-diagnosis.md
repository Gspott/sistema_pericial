# Crm 1C Fix 2 Dashboard Width Diagnosis

# Objetivo

Diagnosticar por que `/dashboard` seguia renderizando estrecho tras CRM-1C-FIX y corregir exclusivamente la estructura/CSS del dashboard para que el contenedor principal pueda ocupar 1200-1440px en escritorio cuando la pantalla lo permite.

# Modulo

Dashboard CRM en `templates/dashboard.html`, estilos acotados en `static/mobile.css` y smoke de dashboard CRM.

# Riesgo

Bajo/medio: cambio visual y semantico de contenedor HTML dentro del app shell. No se modifica logica Python, rutas, consultas, datos, esquema ni integraciones.

# Archivos permitidos

Permitidos:
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- documentacion harness de esta fase

# Archivos prohibidos

Prohibidos:
- esquema o migraciones de base de datos
- routers/modelos/helpers Python de negocio
- SMTP, emails reales o integraciones externas
- secretos, uploads, backups, informes generados, logs y carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/mobile_ui.md`.

# Diagnostico

- No existe `templates/base.html` en la aplicacion inspeccionada; la estructura compartida se compone con `templates/partials/_app_shell_start.html` y `_app_shell_end.html`.
- La estructura real es `body.dashboard-cockpit-page > .app-shell > main.app-content > dashboard`.
- El selector global que limita el ancho es `.page { width: 100%; max-width: 920px; margin: 0 auto; }` en `static/mobile.css`.
- `dashboard.html` tenia un `<main class="page dashboard-page dashboard-cockpit">` dentro del `<main class="app-content">` del shell. Se sustituye por `<div class="page dashboard-page dashboard-cockpit">`.
- Se anade un override especifico para la ruta real del dashboard: `body.dashboard-cockpit-page .app-shell > .app-content > .dashboard-cockpit.page`, con `max-width: 1440px` en desktop y `min-width: 1200px` cuando la pantalla lo permite.


# Validaciones

Pendientes:
- `python3 -m compileall tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir los cambios de `templates/dashboard.html`, `static/mobile.css`, `tests/smoke/test_dashboard_crm.py` y la documentacion harness de esta fase.

# Fuera de alcance

Python de negocio, consultas, rutas, esquema, datos, emails reales, SMTP, integraciones externas, redisenos globales y optimizacion mobile intensiva.

# Aprobacion humana requerida

No prevista para este cambio acotado.

Estado: completado

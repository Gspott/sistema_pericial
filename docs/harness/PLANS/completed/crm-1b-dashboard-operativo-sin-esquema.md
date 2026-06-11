# Crm 1B Dashboard Operativo Sin Esquema

# Objetivo

Convertir el dashboard CRM read-only de CRM-1A en cockpit operativo de
navegacion y seguimiento, sin cambiar esquema ni crear entidades CRM.

# Modulo

Dashboard, UX desktop SSR, enlaces read-only a entidades existentes y acciones
POST ya soportadas en leads/tareas.

# Riesgo

Medio. Riesgo principal: ampliar el dashboard hacia CRM paralelo, crear
acciones mutables nuevas o tocar email real. Mitigacion: sin tablas nuevas, sin
SMTP, sin integraciones externas, filtros por query params, acciones limitadas
a rutas existentes y smoke con DB temporal.

# Decision de alcance

`docs/crm_dashboard.md` dejaba "CRM-1B" como modelo minimo defensivo con tablas.
La orden humana de esta fase redefine CRM-1B como dashboard operativo sin nuevo
esquema. El modelo defensivo queda para una fase posterior con aprobacion y task
pack de DB si se retoma.

# Archivos permitidos

- `app/routers/dashboard.py`
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/active/crm-1b-dashboard-operativo-sin-esquema.md`
- `docs/harness/EPISODES/`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- DB real, migraciones, `app/database.py`, backups, uploads, informes, fotos,
  logs, secretos y `.env`.
- Carpeta anidada `sistema_pericial/`.
- SMTP, emails reales, integraciones externas, service worker/PWA, facturacion
  fiscal y workflows de expedientes/patologias/inspecciones/propuestas.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/mobile_ui.md`.

Playbooks usados:

- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/css_mobile.md`

# Validaciones

- `python3 -m compileall app tests`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `python3 scripts/audit_docs.py`
- Smoke afectado: `tests/smoke/test_dashboard_crm.py`

# Rollback

Revertir cambios en `app/routers/dashboard.py`, `templates/dashboard.html`,
`static/mobile.css` y `tests/smoke/test_dashboard_crm.py`. No hay esquema ni
datos persistidos que revertir.

# Fuera de alcance

Crear tablas CRM, crear detalle de email, nuevas APIs de negocio, SMTP/email
real, Google Business, WhatsApp, Apple Calendar, APIs externas, analytics,
service worker, redisenos globales y cambios de mobile-first.

# Aprobacion humana requerida

No requerida para esta fase sin esquema y con rutas existentes. Requerida para
cualquier fase posterior con DB, SMTP, integraciones, facturacion o cambios de
workflow.

Estado: completado

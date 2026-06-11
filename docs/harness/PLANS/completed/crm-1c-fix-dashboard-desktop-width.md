# Crm 1C Fix Dashboard Desktop Width

# Objetivo

Corregir el layout desktop de `/dashboard` para que el cockpit use anchura real
y no quede limitado por la regla global `.page { max-width: 920px; }` ni por
CSS cacheado.

# Modulo

Template y CSS scoped del dashboard.

# Riesgo

Bajo-medio. Riesgo principal: afectar otras paginas o romper mobile-first.
Mitigacion: selector especifico `body.dashboard-cockpit-page`, cache-busting
solo en `templates/dashboard.html` y reglas CSS limitadas a `.dashboard-*`.

# Diagnostico

- El template cargaba `/static/mobile.css?v=10`; un navegador/PWA podia seguir
  sirviendo CSS anterior.
- El body no tenia clase especifica de pagina para sobreescribir con certeza el
  wrapper global.
- La regla global `.page` fija `max-width: 920px`; se anade override especifico
  del dashboard sin cambiar otras paginas.

# Archivos permitidos

- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/active/crm-1c-fix-dashboard-desktop-width.md`
- `docs/harness/EPISODES/`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- Logica Python, rutas, consultas, DB real, migraciones, SMTP/email real,
  integraciones externas, secretos, uploads, backups, informes, fotos, logs y
  carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/mobile_ui.md`.

Playbooks usados:

- `docs/harness/PLAYBOOKS/css_mobile.md`
- `docs/harness/PLAYBOOKS/jinja.md`

# Validaciones

- `python3 -m compileall tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- Smoke dashboard actualizado para clase de pagina, cache-busting y CSS de
  layout desktop.

# Rollback

Revertir `templates/dashboard.html`, `static/mobile.css` y
`tests/smoke/test_dashboard_crm.py`. No hay cambios de datos ni rutas.

# Fuera de alcance

Cambios Python, datos, rutas, esquemas, acciones CRM, service worker,
integraciones, SMTP/email real y redisenos globales.

# Aprobacion humana requerida

No requerida para fix visual acotado. Requerida si se necesitara tocar logica,
datos, service worker o integraciones.

Estado: completado

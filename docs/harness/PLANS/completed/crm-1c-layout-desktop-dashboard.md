# Crm 1C Layout Desktop Dashboard

# Objetivo

Ajustar unicamente el layout visual del dashboard CRM para que aproveche la
anchura real de escritorio, conservando la funcionalidad CRM-1A/1B.

# Modulo

Dashboard SSR, template y CSS mobile-first acotado a clases `dashboard-*`.

# Riesgo

Medio-bajo. Riesgo principal: romper mobile-first o afectar estilos globales.
Mitigacion: no tocar Python, consultas, rutas ni esquema; CSS scoped al
dashboard con media queries desktop.

# Archivos permitidos

- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/active/crm-1c-layout-desktop-dashboard.md`
- `docs/harness/EPISODES/`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/METRICS.md`

# Archivos prohibidos

- `app/routers/dashboard.py` y cualquier logica Python.
- DB real, migraciones, SMTP, emails reales, integraciones externas, secretos,
  uploads, backups, informes, fotos, logs y carpeta anidada `sistema_pericial/`.
- Estilos globales fuera de lo imprescindible para `.dashboard-*`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/mobile_ui.md`.

Playbooks usados:

- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/css_mobile.md`

# Validaciones

- `python3 -m compileall tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- Smoke afectado: `tests/smoke/test_dashboard_crm.py`

# Rollback

Revertir `templates/dashboard.html`, `static/mobile.css` y
`tests/smoke/test_dashboard_crm.py`. No hay datos, rutas ni esquema que
revertir.

# Fuera de alcance

Cambiar consultas, rutas, acciones, esquema, entidades CRM, integraciones,
SMTP/email real, redisenos globales, service worker y mobile-first global.

# Aprobacion humana requerida

No requerida para esta fase visual acotada. Requerida si se detecta necesidad
de cambiar logica Python, rutas, datos o integraciones.

Estado: completado

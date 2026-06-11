# Crm 1A Dashboard Readonly

# Objetivo

Implementar CRM-1A: cockpit desktop read-only en `/dashboard` usando datos
existentes de leads, tareas, propuestas, emails enviados y expedientes, sin
cambios de esquema ni integraciones.

# Modulo

Dashboard, UX desktop SSR, lecturas read-only de leads/propuestas/emails/
expedientes y administracion secundaria.

# Riesgo

Medio. Riesgo principal: crear un CRM paralelo, tocar email real, leer datos
sensibles o desplazar mobile-first. Mitigacion: no crear tablas, no enviar
emails, no tocar SMTP, consultas defensivas, limites bajos y CSS acotado al
dashboard.

# Archivos permitidos

- `app/routers/dashboard.py`
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/test_dashboard_crm.py`
- `docs/harness/PLANS/active/crm-1a-dashboard-readonly.md`
- `docs/harness/EPISODES/`
- `docs/harness/METRICS.md`
- `docs/harness/BACKLOG/high.md`

# Archivos prohibidos

- DB real, backups, uploads, informes, fotos, logs, secretos y `.env`.
- Carpeta anidada `sistema_pericial/`.
- SMTP, integraciones externas, service worker/PWA, facturacion fiscal,
  propuestas mutables, expedientes mutables y workflows de inspeccion.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/mobile_ui.md`.

Playbooks usados:

- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/css_mobile.md`

# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `node --check` de `static/app_shell.js`, `static/pwa.js` y `static/sw.js`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- Smoke nuevo: `tests/smoke/test_dashboard_crm.py`.
- El cierre del harness autoelevo a scope `full` y ejecuto `92 passed`.

# Rollback

Revertir los cambios en `app/routers/dashboard.py`,
`templates/dashboard.html`, `static/mobile.css` y
`tests/smoke/test_dashboard_crm.py`. No hay migraciones ni datos persistidos que
revertir.

# Fuera de alcance

Crear tablas CRM, modificar esquema, enviar emails, cambiar SMTP, leer
respuestas, CalDAV, WhatsApp, analitica externa, facturacion fiscal, backups,
mobile-first global, service worker y flujos de expedientes/patologias/
inspecciones/propuestas/facturacion.

# Aprobacion humana requerida

No requerida para esta fase read-only y reversible. Requerida en fases
posteriores que creen esquema, toquen SMTP/email real, integraciones externas o
facturacion.

Estado: completado

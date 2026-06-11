# Crm 0 Dashboard Captacion Auditoria

# Objetivo

Auditar el estado actual del dashboard, captacion, emails, leads, clientes,
propuestas y expedientes para disenar la evolucion del dashboard desktop como
centro operativo CRM ligero del despacho.

No implementar funcionalidad en esta fase.

# Modulo

Dashboard / leads / clientes / propuestas / emails / expedientes / harness.

# Riesgo

Bajo en esta fase porque es documental. Riesgo alto en fases futuras si se crea
CRM paralelo, se toca SMTP real, se duplican datos de leads/contactos o se
modifica DB sin plan.

# Archivos permitidos

- `docs/crm_dashboard.md`
- `docs/harness/AGENT_MAPS/`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`
- `docs/harness/PLANS/active/crm-0-dashboard-captacion-auditoria.md`

# Archivos prohibidos

- `app/`
- `templates/`
- `static/`
- DB real, datos reales, secretos, uploads, informes generados, backups y logs.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy de expedientes, visitas, estancias y patologias.

# Playbook aplicable

Fase documental. El prompt solicito `docs_change`, pero el repositorio no tiene
`docs/harness/TASK_PACKS/docs_change.md`; se usa cierre de harness con scope
docs y se documenta el pendiente de crear un pack CRM/documental si procede.


# Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

# Rollback

Revertir los cambios documentales de esta fase. No requiere restaurar DB ni
uploads.

# Fuera de alcance

- Crear tablas CRM.
- Cambiar `/dashboard`.
- Tocar emails reales, SMTP, respuestas o integraciones externas.
- Cambiar mobile-first.
- Tocar patologias, inspecciones o expedientes.
- Crear SPA, APIs paralelas o automatizaciones.

# Aprobacion humana requerida

Requerida para cualquier fase futura que toque DB real, secretos, SMTP real,
CalDAV, WhatsApp Business, analitica externa o migraciones de datos.

# Hallazgos

- El dashboard actual ya consulta leads, `lead_tareas`, propuestas, expedientes,
  facturacion, IVA, gastos y backups.
- `leads`, `lead_contactos` y `lead_tareas` son la base reutilizable para
  seguimiento comercial ligero.
- `emails_enviados` es el log unico que debe reutilizar CRM-2.
- `propuestas` ya enlaza con lead, cliente y expediente, y sirve como etapa de
  pipeline.
- Falta contacto profesional reutilizable, oportunidad CRM, campana CRM y
  timeline general.

# Cambios aplicados

- Documento de auditoria y arquitectura: `docs/crm_dashboard.md`.
- Mapa de agente: `docs/harness/AGENT_MAPS/crm_dashboard_map.md`.
- Backlog de fases CRM.
- Episode de auditoria CRM-0.

Situacion: listo para cierre.

Estado: completado

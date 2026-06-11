# Crm 2D Workbench Prospeccion

# Objetivo

Crear un Workbench de Prospeccion Desktop para introducir manualmente 30-50 contactos en una sesion de aproximadamente una hora, priorizando velocidad de carga, minima friccion, deteccion de duplicados y alta directa en `leads`.

# Modulo

Leads/prospeccion CRM, templates SSR, CSS acotado y smokes.

# Riesgo

Bajo/medio. Se anade una vista y POST SSR sobre `leads`, sin SMTP, sin integraciones externas y sin cambios en facturacion, expedientes, informes ni workflows operativos. Se evita crear tabla nueva para no duplicar fuente de verdad ni frenar la carga rapida.

# Archivos permitidos

Permitidos:
- `app/routers/leads.py`
- `templates/leads/workbench_prospeccion.html`
- `templates/leads/listado.html`
- `templates/partials/_drawer_nav.html`
- `static/mobile.css`
- `tests/smoke/test_leads_prospeccion.py`
- documentacion harness de CRM-2D

# Archivos prohibidos

Prohibidos:
- esquema/base de datos y migraciones
- SMTP, emails reales, servicios de envio e integraciones externas
- facturacion, expedientes, informes, uploads, backups, secretos, logs y carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.

# Decision de almacenamiento

No se crea tabla nueva. Aunque el concepto del prompt menciona `Pendiente revisar -> Preparado -> Lead creado`, la necesidad operativa inmediata es cargar contactos rapido. Crear staging propio generaria doble captura y doble fuente de verdad. En CRM-2D el workbench crea `leads` directamente con `estado='pendiente'`, `prioridad='prospeccion'` y `origen` como categoria, reutilizando validacion e insercion de lead. La mesa de trabajo lista los leads recientes de prospeccion para revisar, editar o marcar como revisados.

# Plan

- Factorizar helpers reutilizables para normalizar contacto, validar payload, insertar lead y detectar duplicados por email, telefono y empresa.
- Crear `GET /leads/prospeccion` como vista desktop SSR con formulario compacto y tabla operativa.
- Crear `POST /leads/prospeccion` para alta rapida con aviso de duplicados no bloqueante mediante confirmacion.
- Crear accion segura `POST /leads/prospeccion/{lead_id}/revisado` que marca el lead propio como `contactado`.
- Anadir acceso desde Leads y drawer.
- Anadir CSS `prospecting-*` acotado al workbench.
- Anadir smoke de render, alta rapida, duplicados y marcado revisado.

# Validaciones

Pendientes:
- `python3 -m compileall app tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir cambios de router, templates, CSS, smokes y documentacion harness de CRM-2D. No hay migracion ni datos estructurales a revertir.

# Fuera de alcance

Scraping, bots, CSV, APIs nuevas, automatizaciones complejas, SMTP, envio de emails, campanas reales, tablas CRM/staging, cambios de facturacion/expedientes/informes.

# Aprobacion humana requerida

No prevista mientras no se cree esquema nuevo ni se toque SMTP/integraciones/facturacion/auth.

Estado: completado

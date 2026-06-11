# Crm 2A Leads Prospeccion

# Objetivo

Convertir `leads` en repositorio principal de prospeccion comercial para administradores de fincas, abogados y otros prescriptores, sin crear tablas ni tocar SMTP/integraciones.

# Modulo

Leads CRM, dashboard CRM y smokes asociados.

# Riesgo

Bajo/medio. Se reutilizan columnas existentes (`origen`, `estado`, `created_at/updated_at`, `notas`, `mensaje`, `servicio_solicitado`) y se anaden filtros/listado UI. No hay cambios de esquema, datos reales, SMTP ni envio automatico.

# Archivos permitidos

Permitidos:
- `app/routers/leads.py`
- `app/routers/dashboard.py`
- `templates/leads/listado.html`
- `templates/leads/form.html`
- `templates/leads/detalle.html`
- `templates/dashboard.html`
- `static/mobile.css`
- `tests/smoke/*`
- documentacion harness de CRM-2A

# Archivos prohibidos

Prohibidos:
- `app/database.py` salvo lectura
- SMTP, servicios de envio real, integraciones externas
- facturacion, expedientes, informes, uploads, backups, secretos, logs y carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.

# Plan

- Reutilizar `leads.origen` como tipo/categoria de prospeccion con opciones controladas y compatibilidad con origenes antiguos.
- Ampliar estados permitidos de lead para prospeccion ligera sin crear workflow complejo.
- Anadir filtros SSR por tipo, estado, localidad textual y fecha.
- Sustituir listado card-clickable por tabla/lista compacta con checkboxes de seleccion multiple y acciones masivas deshabilitadas.
- Integrar metricas de prospeccion en dashboard CRM con consultas agregadas limitadas.
- Cubrir render/filtros/ownership con smokes.

# Validaciones

Pendientes:
- `python3 -m compileall app tests`
- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir cambios en router/template/CSS/smokes y documentacion harness de CRM-2A. No hay migracion ni datos a revertir.

# Fuera de alcance

Crear tablas CRM, campanas reales, acciones masivas ejecutables, envio automatico de emails, SMTP, APIs externas, lectura de respuestas, workflows complejos y cambios de esquema.

# Aprobacion humana requerida

No prevista mientras no se cambie esquema, SMTP, facturacion, auth ni integraciones externas.

Estado: completado

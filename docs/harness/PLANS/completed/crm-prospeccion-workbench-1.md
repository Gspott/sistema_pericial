# Crm Prospeccion Workbench 1

# Objetivo

Diagnosticar el estado real del CRM comercial y crear una primera vista SSR de escritorio `/crm/prospeccion` para prospeccion de leads, enfocada en Administradores de fincas, reutilizando tablas y servicios existentes sin tocar datos reales ni enviar emails reales durante validacion.

# Modulo

CRM / Leads / Emails / Dashboard comercial.

# Riesgo

Alto por tocar flujo de email. Base de datos sin cambio de esquema en esta fase.

# Archivos permitidos

- `app/routers/leads.py`
- `app/routers/crm.py` si encaja mejor como router separado
- `app/main.py` solo para registrar router
- Servicio CRM nuevo o servicios de email existentes si hace falta para plantillas
- `templates/crm/*`
- `templates/partials/_drawer_nav.html`
- `tests/smoke/*crm*`, `tests/smoke/*email*`, `tests/smoke/*routes*`
- Este plan activo y cierre en `docs/harness/PLANS/completed/`

# Archivos prohibidos

- Bases SQLite reales
- `.env` y secretos
- `uploads/`, `backups/`, informes, fotos y logs
- Patologias, informes, valoraciones, facturacion y expedientes salvo enlace de lectura ya existente
- Cambios SMTP o envio real
- Migraciones destructivas o borrado de datos

# Playbook aplicable

Task Pack sugerido: `email_change`.

- `docs/harness/PLAYBOOKS/emails.md`
- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/base_datos.md` solo como referencia defensiva, sin cambio de esquema previsto

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `pytest tests/smoke/test_email_mock.py tests/smoke/test_crm_prospeccion_workbench.py tests/smoke/test_routes_basic.py -q`
- `git diff --check`
- `git status --short`
- Cierre con `bash scripts/finish_harness_task.sh` si el scope resultante pasa

# Rollback

- Revertir router/template/tests del Workbench.
- Quitar registro del router en `app/main.py` si se crea router separado.
- Mantener intactas tablas y datos existentes.

# Fuera de alcance

- Envio masivo real.
- Nueva arquitectura SPA/API paralela.
- Modificar CRM mobile existente.
- Crear columnas nuevas para profesion/localidad/persona de contacto.
- Cambiar facturacion, informes, patologias, valoracion o expedientes.
- Migrar datos reales o limpiar leads existentes.

# Aprobacion humana requerida

- Enviar emails reales.
- Cambios SMTP o secretos.
- Migracion de esquema o normalizacion de leads reales.
- Accion masiva con envio efectivo.

Estado: completado
